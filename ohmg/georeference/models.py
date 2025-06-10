import os
import uuid
import json
from datetime import timedelta
import logging
from typing import Union
from pathlib import Path
from osgeo import gdal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.gis.db import models
from django.contrib.gis.geos import Polygon, Point
from django.core.files import File
from django.core.files.storage import get_storage_class
from django.core.mail import send_mass_mail
from django.utils import timezone

from ohmg.core.models import (
    Document,
    Region,
    RegionCategory,
    Layer,
)
from ohmg.georeference.georeferencer import Georeferencer
from ohmg.georeference.splitter import Splitter
from ohmg.core.utils import (
    full_reverse,
    random_alnum,
)

logger = logging.getLogger(__name__)


class GCP(models.Model):
    class Meta:
        verbose_name = "GCP"
        verbose_name_plural = "GCPs"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pixel_x = models.IntegerField(null=True, blank=True)
    pixel_y = models.IntegerField(null=True, blank=True)
    geom = models.PointField(null=True, blank=True, srid=4326)
    note = models.CharField(null=True, blank=True, max_length=255)
    gcp_group = models.ForeignKey("GCPGroup", on_delete=models.CASCADE)

    created = models.DateTimeField(auto_now_add=True, editable=False, null=False, blank=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="created_by",
        on_delete=models.CASCADE,
    )
    last_modified = models.DateTimeField(auto_now=True, editable=False, null=False, blank=False)
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="modified_by",
        on_delete=models.CASCADE,
    )


class GCPGroup(models.Model):
    TRANSFORMATION_CHOICES = (
        ("tps", "tps"),
        ("poly1", "poly1"),
        ("poly2", "poly2"),
        ("poly3", "poly3"),
    )

    class Meta:
        verbose_name = "GCP Group"
        verbose_name_plural = "GCP Groups"

    crs_epsg = models.IntegerField(null=True, blank=True)
    transformation = models.CharField(
        null=True,
        blank=True,
        choices=TRANSFORMATION_CHOICES,
        max_length=20,
    )
    region2 = models.OneToOneField(
        Region,
        models.CASCADE,
        null=True,
        blank=True,
    )

    def __str__(self):
        if self.region2:
            return self.region2.title
        else:
            return str(self.pk)

    @property
    def gcps(self):
        return GCP.objects.filter(gcp_group=self)

    @property
    def gdal_gcps(self):
        gcp_list = []
        for gcp in self.gcps:
            geom = gcp.geom.clone()
            geom.transform(self.crs_epsg)
            p = gdal.GCP(geom.x, geom.y, 0, gcp.pixel_x, gcp.pixel_y)
            gcp_list.append(p)
        return gcp_list

    @property
    def as_geojson(self):
        geo_json = {"type": "FeatureCollection", "features": []}

        for gcp in self.gcps:
            coords = json.loads(gcp.geom.geojson)["coordinates"]
            newcoords = [coords[1], coords[0]]
            # see note on this variable in settings.py
            if settings.SWAP_COORDINATE_ORDER is True:
                newcoords = coords
            geo_json["features"].append(
                {
                    "type": "Feature",
                    "properties": {
                        "id": str(gcp.pk),
                        "image": [gcp.pixel_x, gcp.pixel_y],
                        "username": gcp.last_modified_by.username,
                        "note": gcp.note,
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": newcoords,
                    },
                }
            )
        return geo_json

    def as_points_file(self):
        content = "mapX,mapY,pixelX,pixelY,enable\n"
        for gcp in self.gcps:
            geom = gcp.geom.clone()
            geom.transform(self.crs_epsg)
            # pixel_y must be inverted b/c qgis puts origin at top left corner
            content += f"{geom.x},{geom.y},{gcp.pixel_x},-{gcp.pixel_y},1\n"

        return content

    def save_from_geojson(self, geojson, region, transformation=None):
        group = (
            region.gcpgroup
            if hasattr(region, "gcpgroup")
            else GCPGroup.objects.create(region2=region)
        )

        group.crs_epsg = 3857  # don't see this changing any time soon...
        group.transformation = transformation
        group.save()

        gcps_new, gcps_mod, gcps_del = 0, 0, 0

        # first remove any existing gcps that have been deleted
        for gcp in group.gcps:
            if str(gcp.id) not in [i["properties"].get("id") for i in geojson["features"]]:
                gcps_del += 0
                gcp.delete()

        for feature in geojson["features"]:
            id = feature["properties"].get("id", str(uuid.uuid4()))
            username = feature["properties"].get("username")
            user = get_user_model().objects.get(username=username)
            gcp, created = GCP.objects.get_or_create(
                id=id, defaults={"gcp_group": group, "created_by": user}
            )
            if created:
                gcps_new += 1

            pixel_x = feature["properties"]["image"][0]
            pixel_y = feature["properties"]["image"][1]
            new_pixel = (pixel_x, pixel_y)
            old_pixel = (gcp.pixel_x, gcp.pixel_y)
            lng = feature["geometry"]["coordinates"][0]
            lat = feature["geometry"]["coordinates"][1]

            new_geom = Point(lat, lng, srid=4326)

            # only update the point if one of its coordinate pairs have changed,
            # this also triggered when new GCPs have None for pixels and geom.
            if (
                new_pixel != old_pixel
                or not new_geom.equals(gcp.geom)
                or gcp.note != feature["properties"]["note"]
            ):
                gcp.note = feature["properties"]["note"]
                gcp.pixel_x = new_pixel[0]
                gcp.pixel_y = new_pixel[1]
                gcp.geom = new_geom
                gcp.last_modified_by = user
                gcp.save()
                if not created:
                    gcps_mod += 1
        gcps_ct = len(geojson["features"])
        logger.info(
            f"GCPGroup {group.pk} | GCPs ct: {gcps_ct}, new: {gcps_new}, mod: {gcps_mod}, del: {gcps_del}"
        )
        group.save()
        return group


def set_upload_location(instance, filename):
    """this function has to return the location to upload the file"""
    return os.path.join(f"{instance.type}s", filename)


def delete_expired_session_locks():
    """Look at all current SessionLocks, and if one is expired and it's session is
    still on the "input" stage, then delete the session (the lock will be deleted as well)
    """
    locks = SessionLock.objects.all()
    if locks.count() > 0:
        sessions = set([i.session for i in locks])
        logger.info(f"{locks.count()} SessionLock(s) currently exist from {len(sessions)} sessions")
    now = timezone.now().timestamp()
    stale = set()
    for lock in locks:
        if now > lock.expiration.timestamp() and lock.session.stage == "input":
            stale.add(lock.session.pk)

    if stale:
        logger.info(f"deleting {len(stale)} stale session(s): {','.join([str(i) for i in stale])}")
        SessionBase.objects.filter(pk__in=stale).delete()


def get_default_session_data(session_type):
    """Return a dict of the keys/types for a sessions's data field.
    Also used for type-checking during validation."""

    if session_type == "p":
        return {
            "split_needed": bool(),
            "cutlines": list(),
            "divisions": list(),
        }
    elif session_type == "g":
        return {
            "gcps": dict(),
            "transformation": str(),
            "epsg": int(),
        }
    elif session_type == "t":
        return {
            "mask_ewkt": str(),
        }
    else:
        raise Exception(f"Invalid session type: {session_type}")


class PrepSessionManager(models.Manager):
    _type = "p"

    def get_queryset(self):
        return super(PrepSessionManager, self).get_queryset().filter(type=self._type)

    def create(self, **kwargs):
        kwargs.update(
            {
                "type": self._type,
                "data": get_default_session_data(self._type),
            }
        )
        return super(PrepSessionManager, self).create(**kwargs)


class GeorefSessionManager(models.Manager):
    _type = "g"

    def get_queryset(self):
        return super(GeorefSessionManager, self).get_queryset().filter(type=self._type)

    def create(self, **kwargs):
        kwargs.update(
            {
                "type": self._type,
                "data": get_default_session_data(self._type),
            }
        )
        return super(GeorefSessionManager, self).create(**kwargs)


SESSION_TYPES = (
    ("p", "Preparation"),
    ("g", "Georeference"),
)
SESSION_STAGES = (
    ("input", "input"),
    ("processing", "processing"),
    ("finished", "finished"),
)


class SessionBase(models.Model):
    type = models.CharField(
        max_length=1,
        choices=SESSION_TYPES,
        blank=True,
    )
    stage = models.CharField(
        max_length=11,
        choices=SESSION_STAGES,
        default="input",
    )
    status = models.CharField(
        max_length=50,
        default="getting user input",
    )
    doc2 = models.ForeignKey(
        Document,
        models.SET_NULL,
        null=True,
        blank=True,
    )
    reg2 = models.ForeignKey(
        Region,
        models.SET_NULL,
        null=True,
        blank=True,
    )
    lyr2 = models.ForeignKey(
        Layer,
        models.SET_NULL,
        null=True,
        blank=True,
    )
    data = models.JSONField(
        default=dict,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    user_input_duration = models.IntegerField(
        blank=True,
        null=True,
    )
    date_created = models.DateTimeField(
        default=timezone.now,
    )
    date_modified = models.DateTimeField(
        default=timezone.now,
    )
    date_run = models.DateTimeField(
        blank=True,
        null=True,
    )
    note = models.CharField(
        blank=True,
        null=True,
        max_length=255,
    )

    def start(self):
        self.lock_resources()

    def run(self):
        raise NotImplementedError("Must be implemented in proxy models.")

    def undo(self):
        raise NotImplementedError("Must be implemented in proxy models.")

    def lock_resources(self):
        """Calls the add_lock method on this session's resources, passing this
        session in to supply the details for the lock."""
        for obj in [self.doc2, self.reg2, self.lyr2]:
            if obj:
                add_lock(self, obj)

    def unlock_resources(self):
        """Calls the remove_lock method on this session's resources."""
        for obj in [self.doc2, self.reg2, self.lyr2]:
            if obj:
                remove_lock(self, obj)

    def extend_locks(self):
        """Extends the expiration time for all of the locks on this session's.
        Quiet fail if the resources are not currently locked."""
        for lock in self.locks.all():
            lock.extend()

    def serialize(self):
        # handle the non- js-serializable attributes
        doc_id, layer_alt, d_create, d_mod, d_run = None, None, None, None, None
        d_run_d, d_run_t = None, None
        if self.doc:
            doc_id = self.doc.pk
        if self.lyr:
            layer_alt = self.lyr.pk
        if self.date_created:
            d_create = self.date_created.strftime("%Y-%m-%d - %H:%M")
        if self.date_modified:
            d_mod = self.date_modified.strftime("%Y-%m-%d - %H:%M")
        if self.date_run:
            d_run = self.date_run.strftime("%Y-%m-%d - %H:%M")
            d_run_d = self.date_run.strftime("%Y-%m-%d")
            d_run_t = self.date_run.strftime("%H:%M")

        return {
            "id": self.pk,
            "type": self.get_type_display(),
            "document": doc_id,
            "layer": layer_alt,
            "stage": self.stage,
            "status": self.status,
            "note": self.note,
            "data": self.data,
            "user": {
                "name": self.user.username,
                "profile": full_reverse("profile_detail", args=(self.user.username,)),
            },
            "date_created": d_create,
            "date_modified": d_mod,
            "date_run": d_run,
            "date_run_date": d_run_d,
            "date_run_time": d_run_t,
        }

    def update_stage(self, stage, save=True):
        self.stage = stage
        logger.info(f"{self.__str__()} | stage: {self.stage}")
        if save:
            self.save(update_fields=["stage"])

    def update_status(self, status, save=True):
        self.status = status
        logger.info(f"{self.__str__()} | status: {self.status}")
        if save:
            self.save(update_fields=["status"])

    def validate_data(self):
        """Compares the contents of the session's data field with the
        appropriate set of keys and types for this session type. Does not
        validate data value content like GeoJSON, etc."""

        for k, v in self.data.items():
            lookup = get_default_session_data(self.type)
            if k not in lookup.keys():
                raise KeyError(f"{self.__str__()} data | Invalid key: {k}")
            if not isinstance(v, type(lookup[k])):
                raise TypeError(
                    f"{self.__str__()} data | Invalid type: {k} is {type(v)}, must be {type(lookup[k])}"
                )

    def save(self, *args, **kwargs):
        self.validate_data()
        self.date_modified = timezone.now()
        return super(SessionBase, self).save(*args, **kwargs)

    def send_email_notification(self, subject, message):
        data_tuple = (
            (subject, message, settings.DEFAULT_FROM_EMAIL, [settings.ADMIN_EMAIL]),
            # (subject, message, settings.DEFAULT_FROM_EMAIL, [self.user.email]),
        )
        send_mass_mail(data_tuple)


class PrepSession(SessionBase):
    objects = PrepSessionManager()

    class Meta:
        proxy = True
        verbose_name = "Preparation Session"
        # hack: prepend spaces for sort in Django admin
        verbose_name_plural = "   Preparation Sessions"

    def __str__(self):
        return f"Preparation Session ({self.pk})"

    def output_regions(self):
        if self.doc2:
            return self.doc2.regions.all()
        else:
            return None

    def run(self):
        """
        Runs the document split process based on prestored segmentation info
        that has been generated for this document. New Documents are made for
        each child image, DocumentLinks are created to link this parent
        Document with its children.
        """

        self.date_run = timezone.now()
        # first time the session is run, calculate the user input time (seconds)
        if self.user_input_duration is None:
            timediff = timezone.now() - self.date_created
            self.user_input_duration = timediff.seconds

        self.update_stage("processing")

        output = []
        map_cat = RegionCategory.objects.get(slug="map")
        if self.data["split_needed"] is False:
            # create Region that matches this document
            w, h = self.doc2.image_size
            region = Region.objects.create(
                boundary=Polygon([[0, 0], [0, h], [w, h], [w, 0], [0, 0]]),
                document=self.doc2,
                created_by=self.user,
                category=map_cat,
            )

            if self.doc2.file:
                with self.doc2.file.open("rb") as openf:
                    region.file.save(self.doc2.file.name, File(openf))
            else:
                logger.warning(f"[WARNING] {self.doc2} is missing file")
            output.append(region)

        else:
            self.update_status("splitting document image")
            s = Splitter(image_file=self.doc2.file)
            self.data["divisions"] = s.generate_divisions(self.data["cutlines"])
            new_images = s.split_image()

            for div_no, file_path in enumerate(new_images, start=1):
                self.update_status(f"creating new region [{div_no}]")

                # get division by index in the original list that was passed to the splitter
                # would be better to have these returned with the new_images, ultimately
                div = self.data["divisions"][div_no - 1]
                div_polygon = Polygon(div)
                region = Region.objects.create(
                    boundary=div_polygon,
                    document=self.doc2,
                    division_number=div_no,
                    created_by=self.user,
                    category=map_cat,
                )

                source_path = Path(file_path)
                with open(source_path, "rb") as openf:
                    region.file.save(source_path.name, File(openf))

                os.remove(file_path)
                output.append(region)

        self.update_status("success", save=False)
        self.update_stage("finished", save=False)
        self.save()

        self.doc2.prepared = True
        self.doc2.save()

        self.unlock_resources()

        processing_time = timezone.now() - self.date_run
        self.send_email_notification(
            f"✔️ Prepared: {self.doc2}",
            f""""Preparation completed for {self.doc2}.
    • session id: {self.pk}
    • user: {self.user.username}
    • result: {self.note}
    • user input duration: {self.user_input_duration}
    • processing time: {processing_time.seconds}
    """,
        )

        return output

    def undo(self, keep_session=False):
        if not self.doc2:
            return

        downstream = any([hasattr(i, "layer") for i in self.doc2.regions.all()])
        if downstream:
            msg = "can't undo prep session with downstream georeferencing"
            logger.warning(msg)
            return {"success": False, "message": msg}

        for region in self.doc2.regions.all():
            region.delete()

        self.doc2.prepared = False
        self.doc2.save()
        logger.info(f"PrepSession {self.pk} reversed. Document {self.doc2.pk} now unprepared.")

        if not keep_session:
            self.delete()

        return {"success": True, "message": "session undo completed"}

    def generate_final_status_note(self):
        if self.data["split_needed"] is False:
            n = "no split needed"
        else:
            pks = [str(i.pk) for i in self.output_regions()]
            n = f"split into {len(pks)} new docs ({', '.join(pks)})"
        return n

    def save(self, *args, **kwargs):
        self.type = "p"
        if not self.pk:
            self.data = get_default_session_data(self.type)
        if self.stage == "finished":
            self.note = self.generate_final_status_note()
        return super(PrepSession, self).save(*args, **kwargs)


class GeorefSession(SessionBase):
    objects = GeorefSessionManager()

    class Meta:
        proxy = True
        verbose_name = "Georeference Session"
        # hack: prepend spaces for sort in Django admin
        verbose_name_plural = "  Georeference Sessions"

    def __str__(self):
        return f"Georeference Session ({self.pk})"

    def generate_final_status_note(self):
        try:
            gcp_ct = len(self.data["gcps"]["features"])
            n = f"{gcp_ct} GCPs used"
        except KeyError:
            n = "error reading GCPs"
        return n

    def run(self):
        layer = None
        if hasattr(self.reg2, "layer"):
            layer = self.reg2.layer

        self.date_run = timezone.now()
        # first time the session is run, calculate the user input time (seconds)
        if self.user_input_duration is None:
            timediff = timezone.now() - self.date_created
            self.user_input_duration = timediff.seconds

        self.update_stage("processing", save=False)
        self.update_status("initializing georeferencer", save=False)
        self.save()

        try:
            # assume EPSG code for now, as making this completely
            # flexible is still in-development. see views.py line 277
            crs_code = f"EPSG:{self.data['epsg']}"
            g = Georeferencer(
                crs=crs_code,
                transformation=self.data["transformation"],
                gcps_geojson=self.data["gcps"],
            )
        except Exception as e:
            self.update_stage("finished", save=False)
            self.update_status("failed", save=False)
            self.note = f"{e}"
            self.save()

            self.unlock_resources()
            return None

        self.update_status("warping")
        try:
            in_path = (
                self.reg2.file.url if self.reg2.file.url.startswith("http") else self.reg2.file.path
            )
            local_path = g.make_cog(in_path)
        except Exception as e:
            logger.error(e)
            self.update_stage("finished", save=False)
            self.update_status("failed", save=False)
            self.note = f"{e}"
            self.save()
            return None

        self.update_status("saving control points")

        # save the successful gcps to the canonical GCPGroup for the document
        GCPGroup().save_from_geojson(
            self.data["gcps"],
            self.reg2,
            self.data["transformation"],
        )

        self.update_status("creating layer")

        ## if there was no existing layer, create a new object by copying
        ## the document and saving it without a pk
        existing_file_name = layer.file.name if (layer and layer.file) else None
        if layer is None:
            logger.debug("no existing layer, creating new layer now")

            layer = Layer.objects.create(
                created_by=self.user,
                last_updated_by=self.user,
                region=self.reg2,
            )
            layer.save(skip_map_lookup_update=True)
        else:
            layer.last_updated_by = self.user
            layer.save(skip_map_lookup_update=True)
            logger.debug(f"updating existing layer, {layer} ({layer.pk})")

        ## regardless of whether there was an old layer or not, overwrite
        ## the file with the newly georeferenced tif.
        session_ct = GeorefSession.objects.filter(reg2=self.reg2).exclude(pk=self.pk).count()
        file_name = f"{layer.slug}__{random_alnum(6)}_{str(session_ct).zfill(2)}.tif"

        with open(local_path, "rb") as openf:
            layer.file.save(file_name, File(openf))
        logger.debug(f"new geotiff saved to layer, {layer.slug} ({layer.pk})")

        # remove now-obsolete tif files
        os.remove(local_path)
        if existing_file_name:
            storage = get_storage_class()()
            if storage.exists(name=existing_file_name):
                storage.delete(name=existing_file_name)

        layer.save(set_thumbnail=True)
        self.lyr2 = layer

        # add the layer to the main-content LayerSet
        layer.layerset2 = layer.map.get_layerset("main-content", create=True)
        layer.save()

        # saving the layerset now will update its extent
        layer.layerset2.save()

        self.reg2.georeferenced = True
        self.reg2.save()

        self.reg2.map.update_item_lookup()

        self.update_stage("finished", save=False)
        self.update_status("success", save=False)
        self.save()

        self.unlock_resources()

        processing_time = timezone.now() - self.date_run
        self.send_email_notification(
            f"✔️ Georeferenced: {self.lyr2}",
            f"""Georeferencing completed for {self.lyr2}.
    • session id: {self.pk}
    • user: {self.user.username}
    • result: {self.note}
    • user input duration: {self.user_input_duration}
    • processing time: {processing_time.seconds}
    """,
        )

        return layer

    def save(self, *args, **kwargs):
        self.type = "g"
        if not self.pk:
            self.data = get_default_session_data(self.type)
        if self.stage == "finished" and self.status == "success":
            self.note = self.generate_final_status_note()
        return super(GeorefSession, self).save(*args, **kwargs)


def add_lock(session: Union[PrepSession, GeorefSession], obj: Union[Document, Region, Layer]):
    ct = ContentType.objects.get_for_model(obj)
    SessionLock.objects.create(
        session=session,
        target_type=ct,
        target_id=obj.pk,
        user=session.user,
    )


def remove_lock(session: Union[PrepSession, GeorefSession], obj: Union[Document, Region, Layer]):
    ct = ContentType.objects.get_for_model(obj)
    session.locks.filter(target_type=ct, target_id=obj.pk).delete()


def default_expiration_time():
    return timezone.now() + timedelta(seconds=settings.GEOREFERENCE_SESSION_LENGTH)


class SessionLock(models.Model):
    """Used to lock a resource attached to a given session."""

    session = models.ForeignKey(
        SessionBase,
        on_delete=models.CASCADE,
        related_name="locks",
    )
    target_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_id = models.PositiveIntegerField()
    target = GenericForeignKey("target_type", "target_id")
    expiration = models.DateTimeField(default=default_expiration_time)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Session Lock"
        verbose_name_plural = "Session Locks"

    def __str__(self):
        return (
            f"{self.session} --> {self.target._meta.object_name} ({self.target} {self.target_id})"
        )

    def extend(self):
        self.expiration += timedelta(seconds=settings.GEOREFERENCE_SESSION_LENGTH)
        self.save()

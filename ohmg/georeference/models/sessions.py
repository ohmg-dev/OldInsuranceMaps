import os
import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.core.files import File
from django.core.mail import send_mass_mail
from django.utils import timezone

from ohmg.georeference.models import (
    GCPGroup,
    ItemBase,
    Document,
    Layer,
    DocumentLink
)
from ohmg.georeference.georeferencer import Georeferencer
from ohmg.georeference.splitter import Splitter
from ohmg.utils import (
    full_reverse,
    random_alnum,
)

logger = logging.getLogger(__name__)

def delete_expired_sessions():
    """ Look at all currently locked resources, and if a resource's session is
    due to expire, delete that session which will in turn unlock the resource.
    """
    locked_items = ItemBase.objects.filter(lock_enabled=True)
    if locked_items.count() > 0:
        logger.info(f"{locked_items.count()} locked item(s)")
    now = timezone.now().timestamp()
    for resource in locked_items:
        if now > resource.lock_details['expiration']:
            try:
                session = SessionBase.objects.get(pk=resource.lock_details['session_id'])
                # only delete a session if it hasn't been submitted.
                if session.stage == "input":
                    logger.info(f"deleting session {session.pk} to unlock resource {resource.pk}")
                    session.delete()
            except SessionBase.DoesNotExist:
                logger.warn(f"error during session cleanup. can't find SessionBase object for resource {resource.pk}. unlocking.")
                resource.remove_lock()

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

    _type = 'p'

    def get_queryset(self):
        return super(PrepSessionManager, self).get_queryset().filter(type=self._type)

    def create(self, **kwargs):
        kwargs.update({
            'type': self._type,
            'data': get_default_session_data(self._type),
        })
        return super(PrepSessionManager, self).create(**kwargs)

class GeorefSessionManager(models.Manager):

    _type = 'g'

    def get_queryset(self):
        return super(GeorefSessionManager, self).get_queryset().filter(type=self._type)

    def create(self, **kwargs):
        kwargs.update({
            'type': self._type,
            'data': get_default_session_data(self._type),
        })
        return super(GeorefSessionManager, self).create(**kwargs)

SESSION_TYPES = (
    ('p', 'Preparation'),
    ('g', 'Georeference'),
)
SESSION_STAGES = (
    ('input', 'input'),
    ('processing', 'processing'),
    ('finished', 'finished'),
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
    doc = models.ForeignKey(
        Document,
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="doc",
    )
    lyr = models.ForeignKey(
        Layer,
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="lyr",
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
        if self.type == "p":
            self.doc.set_status("splitting")
        elif self.type == "g":
            self.doc.set_status("georeferencing")
            if self.lyr:
                self.lyr.set_status("georeferencing")

        self.lock_resources()

    def run(self):
        raise NotImplementedError("Must be implemented in proxy models.")

    def undo(self):
        raise NotImplementedError("Must be implemented in proxy models.")

    def lock_resources(self):
        """Calls the add_lock method on this session's resources, passing this
        session in to supply the details for the lock."""
        if self.doc:
            self.doc.add_lock(self)
        if self.lyr:
            self.lyr.add_lock(self)

    def unlock_resources(self):
        """Calls the remove_lock method on this session's resources."""
        if self.doc:
            self.doc.remove_lock()
        if self.lyr:
            self.lyr.remove_lock()

    def extend_locks(self):
        """Extends the expiration time for all of the locks on this session's.
        Quiet fail if the resources are not currently locked."""
        if self.doc:
            self.doc.extend_lock()
        if self.lyr:
            self.lyr.extend_lock()

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
                "profile": full_reverse("profile_detail", args=(self.user.username, )),
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
                raise TypeError(f"{self.__str__()} data | Invalid type: {k} is {type(v)}, must be {type(lookup[k])}")

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

    @property
    def georeferenced_downstream(self):
        """Returns True if the related document or its children (if it
        has been split) have already been georeferenced."""

        if self.data["split_needed"] is True:
            docs_to_check = self.get_child_docs()
        else:
            docs_to_check = [self.doc]

        return any([d.status == "georeferenced" for d in docs_to_check])

    def get_child_docs(self):
        child_ids = DocumentLink.objects.filter(source=self.doc).values_list("target_id", flat=True)
        return list(Document.objects.filter(pk__in=child_ids))

    def run(self):
        """
        Runs the document split process based on prestored segmentation info
        that has been generated for this document. New Documents are made for
        each child image, DocumentLinks are created to link this parent
        Document with its children.
        """

        # if self.stage == "processing" or self.stage == "finished":
        #     logger.warn(f"{self.__str__()} | abort run: session is already processing or finished.")
        #     return

        self.date_run = timezone.now()
        # first time the session is run, calculate the user input time (seconds)
        if self.user_input_duration is None:
            timediff = timezone.now() - self.date_created
            self.user_input_duration = timediff.seconds

        self.update_stage("processing")
        self.doc.set_status("splitting")

        if self.data['split_needed'] is False:
            self.doc.set_status("prepared")
            self.doc.remove_lock()
        else:
            self.update_status("splitting document image")
            s = Splitter(image_file=self.doc.file.path)
            self.data['divisions'] = s.generate_divisions(self.data['cutlines'])
            new_images = s.split_image()

            for n, file_path in enumerate(new_images, start=1):
                self.update_status(f"creating new document [{n}]")
                fname = os.path.basename(file_path)
                new_doc = Document.objects.get(pk=self.doc.pk)
                new_doc.pk = None
                new_doc.thumbnail = None

                new_doc.title = f"{self.doc.title} [{n}]"
                with open(file_path, "rb") as openf:
                    new_doc.file.save(fname, File(openf))
                new_doc.save(set_thumbnail=True, set_slug=True)

                os.remove(file_path)

                ct = ContentType.objects.get(app_label="georeference", model="document")
                DocumentLink.objects.create(
                    source=self.doc,
                    target_type=ct,
                    target_id=new_doc.pk,
                    link_type='split',
                )

                # must delete the parent cached_property so it will be properly
                # recreated now that the DocumentLink exists
                try:
                    del new_doc.parent
                except AttributeError:
                    pass
                new_doc.remove_lock()
                new_doc.set_status("prepared")
                new_doc.save()

            self.doc.set_status("split")
            self.doc.remove_lock()

        self.update_status("success", save=False)
        self.update_stage("finished", save=False)
        self.save()

        processing_time = timezone.now() - self.date_run
        self.send_email_notification(
            f"✔️ Prepared: {self.doc}",
            f""""Preparation completed for {self.doc}.
 • session id: {self.pk}
 • user: {self.user.username}
 • result: {self.note}
 • user input duration: {self.user_input_duration}
 • processing time: {processing_time.seconds}
"""
        )

        return

    def undo(self, keep_session=False):
        """Reverses the effects of this preparation session: remove child documents and
        links to them, then delete this session."""

        # first check to make sure this determination can be reversed.
        if self.georeferenced_downstream is True:
            logger.warn(f"Removing PrepSession {self.pk} even though downstream georeferencing has occurred.")

        # if a split was made, remove all descendant documents before deleting
        for doc in self.get_child_docs():
            doc.delete()

        DocumentLink.objects.filter(source=self.doc).delete()

        self.doc.set_status("unprepared")
        self.doc.save()

        if not keep_session:
            self.delete()

    def generate_final_status_note(self):

        if self.data['split_needed'] is False:
            n = "no split needed"
        else:
            pks = [str(i.pk) for i in self.get_child_docs()]
            n = f"split into {len(pks)} new docs ({', '.join(pks)})"
        return n

    def save(self, *args, **kwargs):
        self.type = 'p'
        if not self.doc:
            logger.warn(f"{self.__str__()} has no Document.")
        if not self.pk:
            self.data = get_default_session_data(self.type)
        if self.stage == "finished":
            self.note = self.generate_final_status_note()
        return super(PrepSession, self).save(*args, **kwargs)

    def serialize(self):

        if self.date_run:
            date = (self.date_run.month, self.date_run.day, self.date_run.year)
            date_str = self.date_run.strftime("%Y-%m-%d")
            datetime = self.date_run.strftime("%Y-%m-%d - %H:%M")
        else:
            date = (None, None, None)
            date_str = ""
            datetime = ""

        return {
            "allow_reset": not self.georeferenced_downstream,
            "user": {
                "name": self.user.username,
                "profile": full_reverse("profile_detail", args=(self.user.username, )),
            },
            "date": date,
            "date_str": date_str,
            "datetime": datetime,
            "split_needed": self.data['split_needed'],
            "divisions_ct": len(self.get_child_docs()),
        }


class GeorefSession(SessionBase):
    objects = GeorefSessionManager()

    class Meta:
        proxy = True
        verbose_name = "Georeference Session"
        # hack: prepend spaces for sort in Django admin
        verbose_name_plural = "  Georeference Sessions"

    def __str__(self):
        return f"Georeference Session ({self.pk})"

    def run(self, return_vrt=False):

        logger.debug("in run()")

        # short-cut here to use this session data to produce a vrt of the warped original
        if return_vrt:
            crs_code = f"EPSG:{self.data['epsg']}"
            g = Georeferencer(
                crs=crs_code,
                transformation=self.data['transformation'],
                gcps_geojson=self.data['gcps'],
            )
            vrt_path = g.warp(self.doc.file.path, return_vrt=True)
            return vrt_path

        doc_previous_status = self.doc.status
        self.doc.set_status("georeferencing")

        ## get existing layer resource if it exists, e.g.
        ## if the document has already been georeferenced.
        layer = self.doc.get_layer()
        if layer:
            layer.set_status("georeferencing")

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
                transformation=self.data['transformation'],
                gcps_geojson=self.data['gcps'],
            )
        except Exception as e:
            self.update_stage("finished", save=False)
            self.update_status("failed", save=False)
            self.note = f"{e}"
            self.save()
            # revert to (presumed) previous status
            self.doc.set_status(doc_previous_status)
            if layer:
                layer.set_status("georeferenced")
            return None
        self.update_status("warping")
        try:
            out_path = g.warp(self.doc.file.path)
        except Exception as e:
            logger.error(e)
            self.update_stage("finished", save=False)
            self.update_status("failed", save=False)
            self.note = f"{e}"
            self.save()
            # revert to (presumed) previous status
            self.doc.set_status(doc_previous_status)
            if layer:
                layer.set_status("georeferenced")
            return None

        # self.transformation_used = g.transformation["id"]
        self.update_status("creating layer")

        ## if there was no existing layer, create a new object by copying
        ## the document and saving it without a pk
        if layer is None:
            logger.debug("no existing layer, creating new layer now")

            layer = Layer.objects.create(
                title = self.doc.title.replace(",", " -"),
                owner = self.doc.owner,
            )
            layer.save()

            # create new DocumentLink here
            ct = ContentType.objects.get(app_label="georeference", model="layer")
            DocumentLink.objects.create(
                source=self.doc,
                target_type=ct,
                target_id=layer.pk,
                link_type='georeference',
            )
            existing_file_path = None
        else:
            logger.debug(f"updating existing layer, {layer.slug} ({layer.pk})")
            existing_file_path = layer.file.path

        ## regardless of whether there was an old layer or not, overwrite
        ## the file with the newly georeferenced tif.
        session_ct = GeorefSession.objects.filter(doc=self.doc).exclude(pk=self.pk).count()
        file_name = f"{layer.slug}__{random_alnum(6)}_{str(session_ct).zfill(2)}.tif"
        # file_name = f"{layer.slug}.tif"
        with open(out_path, "rb") as openf:
            layer.file.save(file_name, File(openf))
        logger.debug(f"new geotiff saved to layer, {layer.slug} ({layer.pk})")
        os.remove(out_path)
        if existing_file_path:
            os.remove(existing_file_path)

        layer.set_status("georeferenced", save=False)
        layer.save(set_thumbnail=True, set_extent=True)
        self.lyr = layer

        # hack around to add the layer to the main-content AnnotationSet
        pdoc = self.doc
        if pdoc.parent:
            pdoc = pdoc.parent
        try:
            from ohmg.loc_insurancemaps.models import Sheet
            volume = Sheet.objects.get(doc=pdoc).volume
            layer.vrs = volume.get_layer_set("main-content")
            layer.save()
        except Sheet.DoesNotExist:
            logger.warn(f"error getting Sheet for document {pdoc.pk}")

        self.update_status("saving control points")

        # save the successful gcps to the canonical GCPGroup for the document
        GCPGroup().save_from_geojson(
            self.data['gcps'],
            self.doc,
            self.data['transformation'],
        )

        self.doc.set_status("georeferenced")
        self.doc.remove_lock()

        self.update_stage("finished", save=False)
        self.update_status("success", save=False)
        self.save()

        processing_time = timezone.now() - self.date_run
        self.send_email_notification(
            f"✔️ Georeferenced: {self.lyr}",
            f"""Georeferencing completed for {self.lyr}.
 • session id: {self.pk}
 • user: {self.user.username}
 • result: {self.note}
 • user input duration: {self.user_input_duration}
 • processing time: {processing_time.seconds}
"""
        )

        return layer

    def generate_final_status_note(self):

        try:
            gcp_ct = len(self.data['gcps']['features'])
            n = f"{gcp_ct} GCPs used"
        except KeyError:
            n = "error reading GCPs"
        return n

    def save(self, *args, **kwargs):
        self.type = 'g'
        if not self.doc:
            logger.warn(f"{self.__str__()} has no Document.")
        if not self.pk:
            self.data = get_default_session_data(self.type)
        if self.stage == "finished" and self.status == "success":
            self.note = self.generate_final_status_note()
        return super(GeorefSession, self).save(*args, **kwargs)

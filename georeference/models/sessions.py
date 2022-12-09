import os
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.core.files import File
from django.db.models import signals
from django.utils import timezone

from geonode.documents.models import Document as GNDocument
from geonode.geoserver.signals import geoserver_post_save
from geonode.layers.models import Layer as GNLayer
from geonode.layers.utils import file_upload

from georeference.models.resources import (
    GCPGroup,
    LayerMask,
    GeoreferencedDocumentLink,
    SplitDocumentLink,
    ItemBase,
    Document,
    Layer,
    DocumentLink
)
from georeference.georeferencer import Georeferencer
from georeference.splitter import Splitter
from georeference.utils import (
    full_reverse,
    TKeywordManager,
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
                logger.info(f"delete session {session.pk} to unlock resource {resource.pk}")
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

class TrimSessionManager(models.Manager):

    _type = 't'

    def get_queryset(self):
        return super(TrimSessionManager, self).get_queryset().filter(type=self._type)

    def create(self, **kwargs):
        kwargs.update({
            'type': self._type,
            'data': get_default_session_data(self._type),
        })
        return super(TrimSessionManager, self).create(**kwargs)

SESSION_TYPES = (
    ('p', 'Preparation'),
    ('g', 'Georeference'),
    ('t', 'Trim'),
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
    document = models.ForeignKey(
        GNDocument,
        models.SET_NULL,
        null=True,
        blank=True,
    )
    layer = models.ForeignKey(
        GNLayer,
        models.SET_NULL,
        null=True,
        blank=True,
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
    data = JSONField(
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
        print("document:", self.doc)
        print("layer:", self.lyr)
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

    def extend(self, delta_kwargs=None):
        """
        Advances the date_create of this session by the default session length,
        effectively protecting this session from auto-removal for an additional
        length of time.

        Optional delta_kwargs argument can take a dictionary of timedelta
        keyword arguments, e.g. {"hours":1} or {"minutes":10} to overwrite
        the settings.GEOREFERENCE_SESSION_LENGTH value (which is in seconds).
        """

        if delta_kwargs is None:
            delta_kwargs = {"seconds": settings.GEOREFERENCE_SESSION_LENGTH}

        delta = timedelta(**delta_kwargs)
        self.date_created += delta
        self.save(update_fields=['date_created'])

    def serialize(self):

        # handle the non- js-serializable attributes
        doc_id, layer_alt, d_create, d_mod, d_run = None, None, None, None, None
        d_run_d, d_run_t = None, None
        if self.document:
            doc_id = self.document.pk
        if self.layer:
            layer_alt = self.layer.alternate
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

    def get_document_for_layer(self):

        if self.layer is None:
            return None
        ct = ContentType.objects.get(app_label="layers", model="layer")
        try:
            document = GeoreferencedDocumentLink.objects.get(
                content_type=ct,
                object_id=self.layer.pk,
            ).document
            return document
        except GNDocument.DoesNotExist:
            return None

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


    def delete_expired_sessions(self, session_type=None, delta_kwargs=None):
        """
        DEPRECATED: THIS WAS THE OLD METHOD, NO LONGER IN USE
        This method will remove all session instances whose creation
        datetime is older than the specified interval.

        Optional delta_kwargs argument can take a dictionary of timedelta
        keyword arguments, e.g. {"hours":1} or {"minutes":10} to overwrite
        the settings.GEOREFERENCE_SESSION_LENGTH value (which is in seconds).

        PrepSession, GeorefSession, and TrimSession instances must be used
        here in order for the proper pre_delete signals to be emitted.
        """

        if delta_kwargs is None:
            delta_kwargs = {"seconds": settings.GEOREFERENCE_SESSION_LENGTH}

        cutoff = timezone.now() - timedelta(**delta_kwargs)
        models = []
        if session_type in [None, "p"]:
            models.append(PrepSession)
        if session_type in [None, "g"]:
            models.append(GeorefSession)
        if session_type in [None, "t"]:
            models.append(TrimSession)

        for model in models:
            sessions = model.objects.filter(stage="input", date_created__lt=cutoff)
            if sessions.exists():
                ids = [str(i) for i in sessions.values_list('pk', flat=True)]
                ids_str = ",".join(ids)
                sessions.delete()
                msg = f"Deleted expired {model.__name__} ({len(ids)}): {ids_str}"
                logger.info(msg)

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

    def get_children(self):
        """ DEPRECATED SOON: use get_child_docs instead
        Returns a list of all the child documents that have been created
        by a split operation from this session."""

        ct = ContentType.objects.get(app_label="documents", model="document")
        child_ids = SplitDocumentLink.objects.filter(
            document=self.document,
            content_type=ct,
        ).values_list("object_id", flat=True)
        return list(GNDocument.objects.filter(pk__in=child_ids))

    def get_child_docs(self):
        child_ids = DocumentLink.objects.filter(source=self.doc).values_list("target_id", flat=True)
        return list(Document.objects.filter(pk__in=child_ids))

    def run_legacy(self):
        """
        DEPRECATED: Retained temporarily for reference 11/5/22
        Runs the document split process based on prestored segmentation info
        that has been generated for this document. New Documents are made for
        each child image, SplitDocumentLinks are created to link this parent
        Document with its children. The parent document is also marked as
        metadata_only so that it no longer shows up in the search page lists.
        """

        if self.stage == "processing" or self.stage == "finished":
            logger.warn(f"{self.__str__()} | abort run: session is already processing or finished.")
            return

        self.date_run = timezone.now()

        self.update_stage("processing")
        tkm = TKeywordManager()
        tkm.set_status(self.document, "splitting")

        if self.data['split_needed'] is False:
            tkm.set_status(self.document, "prepared")
            self.document.metadata_only = False
            self.document.save()
        else:
            self.update_status("splitting document image")
            s = Splitter(image_file=self.document.doc_file.path)
            self.data['divisions'] = s.generate_divisions(self.data['cutlines'])
            new_images = s.split_image()

            for n, file_path in enumerate(new_images, start=1):
                self.update_status(f"creating new document [{n}]")
                fname = os.path.basename(file_path)
                new_doc = GNDocument.objects.get(pk=self.document.pk)
                new_doc.pk = None
                new_doc.id = None
                new_doc.uuid = None
                new_doc.thumbnail_url = None
                new_doc.metadata_only = False
                new_doc.title = f"{self.document.title} [{n}]"
                with open(file_path, "rb") as openf:
                    new_doc.doc_file.save(fname, File(openf))
                new_doc.save()

                os.remove(file_path)

                ct = ContentType.objects.get(app_label="documents", model="document")
                SplitDocumentLink.objects.create(
                    document=self.document,
                    content_type=ct,
                    object_id=new_doc.pk,
                )

                for r in self.document.regions.all():
                    new_doc.regions.add(r)
                tkm.set_status(new_doc, "prepared")

            if len(new_images) > 1:
                self.document.metadata_only = True
                self.document.save()

            tkm.set_status(self.document, "split")

        self.update_status("success", save=False)
        self.update_stage("finished", save=False)
        self.save()
        return

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
        return

    def undo_legacy(self):
        """Reverses the effects of this preparation session: remove child documents and
        links to them, then delete this session."""

        # first check to make sure this determination can be reversed.
        if self.georeferenced_downstream is True:
            logger.warn(f"Removing PrepSession {self.pk} even though downstream georeferencing has occurred.")

        # if a split was made, remove all descendant documents before deleting
        for child in self.get_children():
            child.delete()

        SplitDocumentLink.objects.filter(document=self.document).delete()

        TKeywordManager().set_status(self.document, "unprepared")
        self.document.metadata_only = False
        self.document.save()
        self.delete()

    def undo(self, keep_session=False):
        """Reverses the effects of this preparation session: remove child documents and
        links to them, then delete this session."""

        # first check to make sure this determination can be reversed.
        # MUST BE RE-EVALUATED
        # if self.georeferenced_downstream is True:
        #     logger.warn(f"Removing PrepSession {self.pk} even though downstream georeferencing has occurred.")

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
            "divisions_ct": len(self.get_children()),
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

    def run_legacy(self):

        tkm = TKeywordManager()
        tkm.set_status(self.document, "georeferencing")

        signals.post_save.disconnect(geoserver_post_save, sender=GNLayer)

        self.date_run = timezone.now()
        self.update_stage("processing", save=False)
        self.update_status("initializing georeferencer", save=False)
        self.save()

        try:
            g = Georeferencer(
                transformation=self.data['transformation'],
                epsg_code=self.data['epsg'],
            )
            g.load_gcps_from_geojson(self.data['gcps'])
        except Exception as e:
            self.update_stage("finished", save=False)
            self.update_status("failed", save=False)
            self.note = f"{e}"
            self.save()
            # revert to previous tkeyword status
            tkm.set_status(self.document, "prepared")
            return None
        self.update_status("warping")
        try:
            out_path = g.make_tif(self.document.doc_file.path)
        except Exception as e:
            self.update_stage("finished", save=False)
            self.update_status("failed", save=False)
            self.note = f"{e}"
            self.save()
            # revert to previous tkeyword status
            tkm.set_status(self.document, "prepared")
            return None

        # self.transformation_used = g.transformation["id"]
        self.update_status("creating layer")

        ## need to remove commas from the titles, otherwise the layer will not
        ## be valid in the catalog list when trying to add it to a Map. the 
        ## message in the catalog will read "Missing OGC reference metadata".
        title = self.document.title.replace(",", " -")

        ## first look to see if there is a layer alreaded linked to this document.
        ## this would indicate that it has already been georeferenced, and in this
        ## case the existing layer should be overwritten.
        existing_layer = None
        try:
            link = GeoreferencedDocumentLink.objects.get(document=self.document)
            existing_layer = GNLayer.objects.get(pk=link.object_id)
        except (GeoreferencedDocumentLink.DoesNotExist, GNLayer.DoesNotExist):
            pass

        ## create the layer, passing in the existing_layer if present
        layer = file_upload(
            out_path,
            layer=existing_layer,
            overwrite=True,
            title=title,
            user=self.user,
        )

        ## if there was no existing layer, create a new link between the
        ## document and the new layer
        if existing_layer is None:
            ct = ContentType.objects.get(app_label="layers", model="layer")
            GeoreferencedDocumentLink.objects.create(
                document=self.document,
                content_type=ct,
                object_id=layer.pk,
            )

            # set attributes in the layer straight from the document
            for keyword in self.document.keywords.all():
                layer.keywords.add(keyword)
            for region in self.document.regions.all():
                layer.regions.add(region)
            GNLayer.objects.filter(pk=layer.pk).update(
                date=self.document.date,
                abstract=self.document.abstract,
                category=self.document.category,
                license=self.document.license,
                restriction_code_type=self.document.restriction_code_type,
                attribution=self.document.attribution,
            )

        self.layer = layer
        self.update_status("saving control points")

        # save the successful gcps to the canonical GCPGroup for the document
        GCPGroup().save_from_geojson(
            self.data['gcps'],
            self.document,
            self.data['transformation'],
        )

        ## now reconnect the geoserver post_save receiver and run final layer save.
        signals.post_save.connect(geoserver_post_save, sender=GNLayer)
        layer.save()

        # if existing_layer is not None:
        #     self.update_status("regenerating thumbnail")
        #     thumb = create_thumbnail(layer, overwrite=True)
        #     GNLayer.objects.filter(pk=layer.pk).update(thumbnail_url=thumb)

        tkm.set_status(self.document, "georeferenced")
        tkm.set_status(layer, "georeferenced")

        self.update_stage("finished", save=False)
        self.update_status("success", save=False)
        self.save()

        return layer

    def run(self):

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
            g = Georeferencer(
                transformation=self.data['transformation'],
                epsg_code=self.data['epsg'],
            )
            g.load_gcps_from_geojson(self.data['gcps'])
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
            out_path = g.make_tif(self.doc.file.path)
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

        return layer

    def undo(self, undo_all=False):
        """
        Remove this GeorefSession and revert the Document/Layer to previous
        state. If undo_all is True, revert all sessions (clean slate).

        If this is the only GeorefSession on the Document, or if undo_all
        is True, then remove the Layer and set the document to "prepared".
        Otherwise, reapply the latest session after removing this one.

        If undo_all is False and this isn't the most recent session on
        the Document, abort the undo operation.
        """

        tkm = TKeywordManager()

        ##  get all of the sessions for this document, ordered so most recent is first
        sessions = GeorefSession.objects.filter(document=self.document).order_by("-date_run")
        if self != list(sessions)[0] and undo_all is False:
            logger.warn(f"{self.__str__()} | can't undo this session, it's not the latest one.")
            return
        else:
            logger.info(f"{self.__str__()} | undo session (undo_all = {undo_all})")

        ## If this is the only session, or undo_all is True then wipe the slate clean
        if sessions.count() == 1 or undo_all is True:

            ## find and delete the Layer
            layer = None
            try:
                link = GeoreferencedDocumentLink.objects.get(document=self.id)
                layer = GNLayer.objects.get(id=link.object_id)
            except (GeoreferencedDocumentLink.DoesNotExist, GNLayer.DoesNotExist):
                pass

            if layer is None:
                logger.debug(f"{self.__str__()} | no Layer to delete")
            else:
                logger.debug(f"{self.__str__()} | delete Layer: {layer}")
                layer.delete()

            ## remove the link between the Document and the Layer
            try:
                GeoreferencedDocumentLink.objects.get(document=self.document.id).delete()
                logger.debug(f"{self.__str__()} | delete GeoreferencedDocumentLink")
            except GeoreferencedDocumentLink.DoesNotExist:
                logger.debug(f"{self.__str__()} | no GeoreferencedDocumentLink to delete")

            ## remove all sessions
            logger.info(f"{self.__str__()} | delete all sessions: {[s.pk for s in sessions]}")
            sessions.delete()
            GCPGroup.objects.filter(document=self.document).delete()
            tkm.set_status(self.document, "prepared")

        ## otherwise delete this session and then re-run the latest one before it.
        else:
            logger.info(f"{self.__str__()} | deleted")
            docid = self.document.pk
            self.delete()

            #reaquire sessions, seems like it may be necessary??
            sessions = GeorefSession.objects.filter(document_id=docid).order_by("-date_run")
            latest = list(sessions)[0]
            logger.info(f"{latest.__str__()} | re-run session")
            latest.run()

            # finally, for all previous sessions reset the newly re-created layer
            for s in sessions:
                s.layer = latest.layer
                s.save()

    def generate_final_status_note(self):

        try:
            gcp_ct = len(self.data['gcps']['features'])
            n = f"{gcp_ct} GCPs used"
        except KeyError:
            n = f"error reading GCPs"
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


class TrimSession(SessionBase):
    objects = TrimSessionManager()

    class Meta:
        proxy = True
        verbose_name = "Trim Session"
        # hack: prepend spaces for sort in Django admin
        verbose_name_plural = " Trim Sessions"

    def __str__(self):
        return f"Trim Session ({self.pk})"

    def run(self):

        self.update_stage("processing", save=False)
        self.date_run = timezone.now()
        self.save()
        tkm = TKeywordManager()
        tkm.set_status(self.layer, "trimming")

        document = self.get_document_for_layer()
        if document is not None:
            tkm.set_status(document, "trimming")

        # create/update a LayerMask for this layer and apply it as style
        if self.data['mask_ewkt']:
            
            mask = GEOSGeometry(self.data['mask_ewkt'])
            lm, created = LayerMask.objects.get_or_create(
                layer=self.layer,
                defaults={"polygon": mask}
            )
            if not created:
                lm.polygon = mask
                lm.save()
            lm.apply_mask()

            tkm.set_status(self.layer, "trimmed")
            if document is not None:
                tkm.set_status(document, "trimmed")

        self.update_stage("finished", save=False)
        self.update_status("success", save=False)
        self.save()

    def undo(self):

        tkm = TKeywordManager()
        tkm.set_status(self.layer, "georeferenced")
        document = self.get_document_for_layer()

        if document is not None:
            tkm.set_status(document, "georeferenced")

        LayerMask.objects.filter(layer=self.layer).delete()

        self.update_status("unapplied")

    def save(self, *args, **kwargs):
        self.type = 't'
        if not self.layer:
            logger.warn(f"{self.__str__()} has no Layer.")
        if not self.pk:
            self.data = get_default_session_data(self.type)
        return super(TrimSession, self).save(*args, **kwargs)

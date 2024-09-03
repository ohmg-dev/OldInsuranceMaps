import os
import logging
from itertools import chain
from datetime import datetime
from pathlib import Path

from natsort import natsorted

from django.conf import settings
from django.contrib.gis.db import models
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q, F
from django.utils.functional import cached_property
from django.urls import reverse

from ohmg.core.utils import (
    full_reverse,
    slugify,
    get_jpg_from_jp2_url,
    MONTH_CHOICES,
    DAY_CHOICES,
)
from ohmg.core.storages import OverwriteStorage
from ohmg.core.renderers import (
    get_image_size,
    get_extent_from_file,
    generate_document_thumbnail_content,
    generate_layer_thumbnail_content,
    convert_img_to_pyramidal_tiff,
)
from ohmg.places.models import Place

logger = logging.getLogger(__name__)


class MapGroup(models.Model):

    MAP_PREFIX_CHOICES = (
        ("volume", "volume"),
        ("part", "part"),
    )

    MAP_PREFIX_ABBREVIATIONS = {
        "volume": "Vol.",
        "part": "Pt.",
    }

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100)
    year_start = models.IntegerField(blank=True, null=True)
    year_end = models.IntegerField(blank=True, null=True)
    creator = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200)
    map_prefix = models.CharField(
        max_length=10,
        choices=MAP_PREFIX_CHOICES,
        null=True,
        blank=True,
        help_text="The preferred term for referring to maps within this map group."
    )

    class Meta:
        verbose_name_plural = "Map Groups"

    def __str__(self):
        return self.title


class Map(models.Model):

    STATUS_CHOICES = (
        ("not started", "not started"),
        ("initializing...", "initializing..."),
        ("ready", "ready"),
    )

    ACCESS_CHOICES = (
        ("none", "none"),
        ("sponsor", "sponsor"),
        ("any", "any"),
    )

    DOCUMENT_PREFIX_CHOICES = (
        ("page", "page"),
        ("sheet", "sheet"),
        ("plate", "plate"),
        ("part", "part"),
    )

    DOCUMENT_PREFIX_ABBREVIATIONS = {
        "page": "p",
        "sheet": "s",
        "plate": "pl",
        "part": "pt",
    }

    identifier = models.CharField(max_length=100, primary_key=True)
    slug = models.SlugField(max_length=100)
    title = models.CharField(max_length=200)
    year = models.IntegerField(blank=True, null=True)
    month = models.IntegerField(
        blank=True,
        null=True,
        choices=MONTH_CHOICES
    )
    day = models.IntegerField(
        blank=True,
        null=True,
        choices=DAY_CHOICES
    )
    creator = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )
    publisher = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )
    volume_number = models.CharField(
        max_length=25,
        null=True,
        blank=True,
        help_text="Volume number (or name?), if this map is included in a MapGroup."
    )
    document_page_type = models.CharField(
        max_length=10,
        choices=DOCUMENT_PREFIX_CHOICES,
        null=True,
        blank=True,
        help_text="The preferred term for referring to documents within this map."
    )
    iiif_manifest = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=STATUS_CHOICES[0][0],
    )
    create_date = models.DateTimeField(auto_now_add=True)
    load_date = models.DateTimeField(null=True, blank=True)
    document_sources = models.JSONField(
        null=True,
        blank=True,
        default=dict,
    )
    document_lookup = models.JSONField(
        null=True,
        blank=True,
        default=dict,
    )
    layer_lookup = models.JSONField(
        null=True,
        blank=True,
        default=dict,
    )
    item_lookup = models.JSONField(
        null=True,
        blank=True,
        default=dict,
    )
    locales = models.ManyToManyField(
        Place,
        blank=True,
    )
    mapgroup = models.ForeignKey(
        MapGroup,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="maps"
    )
    access = models.CharField(
        max_length=50,
        choices=ACCESS_CHOICES,
        default="any"
    )
    sponsor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="maps_sponsored",
    )
    loaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="maps_loaded"
    )

    def __str__(self):
        return self.title
    
    @property
    def regions(self):
        return Region.objects.filter(document__in=self.documents.all()).order_by('title')
    
    @property
    def layers(self):
        return Layer.objects.filter(region__in=self.regions).order_by('title')

    @cached_property
    def prep_sessions(self):
        from ohmg.georeference.models.sessions import PrepSession
        sessions = []
        for document in self.documents:
            sessions = list(chain(sessions, PrepSession.objects.filter(doc=document)))
        return sessions

    @cached_property
    def georef_sessions(self):
        from ohmg.georeference.models.sessions import GeorefSession
        sessions = []
        for doc in self.get_all_docs():
            sessions += list(chain(sessions, GeorefSession.objects.filter(doc=doc)))
        return sessions
    
    @property
    def extent(self):
        ls = self.get_layerset('main-content')
        if ls:
            return ls.extent
        else:
            return None

    @property
    def gt_exists(self):
        return True if self.get_layerset('main-content').mosaic_geotiff else False

    @property
    def mj_exists(self):
        return True if self.get_layerset('main-content').mosaic_json else False

    @property
    def stats(self):
        items = self.sort_lookups()
        unprep_ct = len(items['unprepared'])
        prep_ct = len(items['prepared'])
        georef_ct = len(items['georeferenced'])
        percent = 0
        if georef_ct > 0:
            percent = int((georef_ct / (unprep_ct + prep_ct + georef_ct)) * 100)

        main_lyrs_ct = 0
        main_anno = self.get_layerset('main-content')
        if main_anno.annotations:
            main_lyrs_ct = len(main_anno.annotations)
        mm_ct, mm_todo, mm_percent = 0, 0, 0
        if main_lyrs_ct != 0:
            # make sure 0/0 appears at the very bottom, then 0/1, 0/2, etc.
            mm_percent = main_lyrs_ct * .000001
        mm_display = f"0/{main_lyrs_ct}"
        if main_anno.multimask is not None:
            mm_ct = len(main_anno.multimask)
            mm_todo = main_lyrs_ct - mm_ct
            if mm_ct > 0 and main_lyrs_ct > 0:
                mm_display = f"{mm_ct}/{main_lyrs_ct}"
                mm_percent = mm_ct / main_lyrs_ct
                mm_percent += main_lyrs_ct * .000001

        return {
            "unprepared_ct": unprep_ct,
            "prepared_ct": prep_ct,
            "georeferenced_ct": georef_ct,
            "percent": percent,
            "mm_ct": mm_todo,
            "mm_display": mm_display,
            "mm_percent": mm_percent,
        }

    def get_locale(self, serialized=False):
        """ Returns the first locale in the list of related locales.
        This is a patch in use until the frontend is ready for multiple
        locales per item."""
        if len(self.locales.all()) > 0:
            locale = self.locales.all()[0]
            if serialized:
                return locale.serialize()
            else:
                return locale
        else:
            return None

    def get_layerset(self, cat_slug:str, create:bool=False):
        from ohmg.georeference.models import LayerSet, LayerSetCategory
        try:
            layerset = LayerSet.objects.get(map=self, category__slug=cat_slug)
        except LayerSet.DoesNotExist:
            if create:
                category = LayerSetCategory.objects.get(slug=cat_slug)
                layerset = LayerSet.objects.create(
                    map=self,
                    category=category
                )
                logger.debug(f"created new LayerSet: {self.pk} - {cat_slug}")
            else:
                layerset = None
        return layerset

    def create_documents(self, get_files=False):
        """ TODO: This method is still 100% reliant on having LOC content in the
        document_sources field. """
        self.set_status("initializing...")
        if self.document_sources:
            from ohmg.core.importers.loc_sanborn import LOCParser
            for fileset in self.document_sources:
                parsed = LOCParser(fileset=fileset)
                document, created = Document.objects.get_or_create(
                    map=self,
                    source_url=parsed.jp2_url,
                    iiif_info=parsed.iiif_service,
                    page_number=parsed.sheet_number,
                )
                logger.debug(f"created new? {created} {document} ({document.pk})")
                if get_files:
                    document.download_file()
        self.set_status("ready")

    def remove_sheets(self):
        for document in self.documents:
            document.delete()

    def set_status(self, status):
        self.status = status
        self.save(update_fields=['status'])

    def update_place_counts(self):

        locale = self.get_locale()
        if locale is not None:
            with transaction.atomic():
                locale.volume_count += 1
                locale.volume_count_inclusive += 1
                locale.save(update_fields=["volume_count", "volume_count_inclusive"])
                parents = locale.direct_parents.all()
                while parents:
                    new_parents = []
                    for p in parents:
                        p.volume_count_inclusive += 1
                        p.save(update_fields=["volume_count_inclusive"])
                        new_parents += list(p.direct_parents.all())
                    parents = new_parents

    def get_absolute_url(self):
        return f"/map/{self.pk}/"
    
    def update_item_lookup(self):
        from ohmg.core.api.schemas import (DocumentSchema, RegionSchema, LayerSchema)
        regions = self.regions
        items = {
            "unprepared": [DocumentSchema.from_orm(i).dict() for i in self.documents.filter(prepared=False)],
            "prepared": [RegionSchema.from_orm(i).dict() for i in regions.filter(georeferenced=False, is_map=True)],
            "georeferenced": [LayerSchema.from_orm(i).dict() for i in self.layers],
            "nonmaps": [RegionSchema.from_orm(i).dict() for i in regions.filter(is_map=False)],
            "processing": {
                "unprep": 0,
                "prep": 0,
                "geo_trim": 0,
            }
        }
        for cat in ["unprepared", "prepared", "georeferenced", "nonmaps"]:
            items[cat] = natsorted(items[cat], key=lambda k: k['title'])
        self.item_lookup = items
        self.save(update_fields=['item_lookup'])

    def get_session_summary(self):

        from ohmg.georeference.models import SessionBase
        sessions = SessionBase.objects.filter(
            Q(doc2__map_id=self.pk)
            | Q(reg2__document__map_id=self.pk)
            # | Q(lyr2__region__document__map_id=self.pk)
        ).prefetch_related()

        prep_sessions = sessions.filter(type="p")
        georef_sessions = sessions.filter(type="g")

        def _get_session_user_summary(session_list):
            users = session_list.values_list("user__username", flat=True)
            user_dict = {}
            for name in users:
                user_dict[name] = user_dict.get(name, {
                    "ct": 0,
                    "name": name,
                })
                user_dict[name]['ct'] += 1
            return sorted(user_dict.values(), key=lambda item: item.get("ct"), reverse=True)

        prep_ct = prep_sessions.count()
        georef_ct = georef_sessions.count()
        summary = {
            'prep_ct': prep_ct,
            'prep_contributors': _get_session_user_summary(prep_sessions),
            'georef_ct': georef_ct,
            'georef_contributors': _get_session_user_summary(georef_sessions),
        }
        return summary

    def save(self, set_slug=False, *args, **kwargs):

        if set_slug or not self.slug:
            self.slug = slugify(self.title, join_char="_")

        return super(self.__class__, self).save(*args, **kwargs)


class Document(models.Model):
    """Documents are the individual source files that are directly attached to Maps.
    They represent pages in an atlas or even just a single scan of a map."""

    title = models.CharField(max_length=200, default="untitled document")
    slug = models.SlugField(max_length=100)
    map = models.ForeignKey(
        Map,
        on_delete=models.CASCADE,
        related_name="documents"
    )
    page_number = models.CharField(max_length=10, null=True, blank=True)
    prepared = models.BooleanField(default=False)
    file = models.FileField(
        upload_to='documents',
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    thumbnail = models.FileField(
        upload_to='thumbnails',
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    source_url = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Storing a source_url allows the file to be downloaded at any point after "\
            "the instance has been created."
    )
    iiif_info = models.JSONField(null=True, blank=True)
    load_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    @cached_property
    def image_size(self):
        return get_image_size(Path(self.file.path)) if self.file else None

    def create_from_file(self, file_path: Path, volume=None, sheet_no=None):

        tif_path = convert_img_to_pyramidal_tiff(file_path)

        sheet = Document(
            volume=volume,
            source=file_path,
        )
        sheet.save()

        with open(tif_path, "rb") as openf:
            sheet.file.save(Path(tif_path).name, File(openf))
        return sheet

    def download_file(self):

        log_prefix = f"{self.__str__()} |"
        logger.info(f"{log_prefix} start load")

        if not self.source_url:
            logger.warn(f"{log_prefix} no source_url - cancelling download")
            return

        if not self.file:
            jpg_path = get_jpg_from_jp2_url(self.source_url)
            with open(jpg_path, "rb") as new_file:
                self.file.save(f"{self.slug}.jpg", File(new_file))

        self.load_date = datetime.now()
        self.save()

    def set_thumbnail(self):
        if self.file is not None:
            if self.thumbnail:
                self.thumbnail.delete()
            path = self.file.path
            name = os.path.splitext(os.path.basename(path))[0]
            content = generate_document_thumbnail_content(path)
            tname = f"{name}-doc-thumb.jpg"
            self.thumbnail.save(tname, ContentFile(content))

    def save(self, set_slug=False, set_thumbnail=False, *args, **kwargs):

        if set_thumbnail or (self.file and not self.thumbnail):
            self.set_thumbnail()

        if set_slug or not self.slug:
            title = self.map.__str__()
            if self.page_number:
                title += f" {self.map.DOCUMENT_PREFIX_ABBREVIATIONS[self.map.document_page_type]}{self.page_number}"
            self.slug = slugify(title, join_char="_")

        if self.regions.all().count() > 0:
            self.prepared = True

        self.title = self.map.title
        if self.page_number:
            self.title += f" {self.map.DOCUMENT_PREFIX_ABBREVIATIONS[self.map.document_page_type]}{self.page_number}"

        return super(self.__class__, self).save(*args, **kwargs)


class Region(models.Model):

    title = models.CharField(max_length=200, default="untitled region")
    slug = models.SlugField(max_length=100)
    boundary = models.PolygonField(
        null=True,
        blank=True,
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="regions"
    )
    division_number = models.IntegerField(null=True, blank=True)
    is_map = models.BooleanField(default=True)
    georeferenced = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="region_created_by",
    )
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    file = models.FileField(
        upload_to='regions',
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    thumbnail = models.FileField(
        upload_to='thumbnails',
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    gcp_group = models.OneToOneField(
        "georeference.GCPGroup",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        self.title

    @cached_property
    def image_size(self):
        return get_image_size(Path(self.file.path)) if self.file else None

    @property
    def _base_urls(self):
        return {
            "thumbnail": self.thumbnail.url if self.thumbnail else "",
            "image": self.file.url if self.file else "",
        }

    def set_thumbnail(self):
        if self.file is not None:
            if self.thumbnail:
                self.thumbnail.delete()
            path = self.file.path
            name = os.path.splitext(os.path.basename(path))[0]
            content = generate_document_thumbnail_content(path)
            tname = f"{name}-reg-thumb.jpg"
            self.thumbnail.save(tname, ContentFile(content))

    def save(self, set_slug=False, set_thumbnail=False, *args, **kwargs):

        if set_thumbnail or (self.file and not self.thumbnail):
            self.set_thumbnail()

        if set_slug or not self.slug:
            display_name = self.document.__str__()
            if self.division_number:
                display_name += f" [{self.division_number}]"
            self.slug = slugify(display_name, join_char="_")

        if hasattr(self, 'layer'):
            self.georeferenced = True
        
        self.title = self.document.title
        if self.division_number:
            self.title += f" [{self.division_number}]"

        return super(self.__class__, self).save(*args, **kwargs)


class Layer(models.Model):

    title = models.CharField(max_length=200, default="untitled layer")
    slug = models.SlugField(max_length=100)
    region = models.OneToOneField(
        Region,
        on_delete=models.CASCADE,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="layers_created",
    )
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="layers_updated",
    )
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    extent = models.JSONField(null=True, blank=True)
    file = models.FileField(
        upload_to='layers',
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    thumbnail = models.FileField(
        upload_to='thumbnails',
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    layerset = models.ForeignKey(
        "georeference.LayerSet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="layers"
    )

    def __str__(self):
        return self.title

    @property
    def urls(self):
        urls = self._base_urls
        doc = self.get_document()
        urls.update({
            "resource": full_reverse("resource_detail", args=(self.pk, )),
            # remove detail and progress_page urls once InfoPanel has been fully
            # deprecated and volume summary has been updated.
            # note the geonode: prefix is still necessary until non-geonode
            # layer and document detail pages are created.
            "detail": f"/layers/geonode:{self.slug}" if self.slug else "",
            "progress_page": f"/layers/geonode:{self.pk}#georeference" if self.slug else "",
            # redundant, I know, but a patch for now
            "cog": settings.MEDIA_HOST.rstrip("/") + urls['image'],
        })
        if doc is not None:
            urls.update({
                "georeference": doc.urls['georeference'],
                "document": doc.urls['image'],
            })
        return urls

    def get_sessions(self, serialize=False):
        return self.get_document().get_sessions(serialize=serialize)

    def get_split_summary(self):
        return self.get_document().get_split_summary()

    def get_georeference_summary(self):
        return self.get_document().get_georeference_summary()
    
    def set_thumbnail(self):
        if self.file is not None:
            if self.thumbnail:
                self.thumbnail.delete()
            path = self.file.path
            name = os.path.splitext(os.path.basename(path))[0]
            content = generate_layer_thumbnail_content(path)
            tname = f"{name}-lyr-thumb.jpg"
            self.thumbnail.save(tname, ContentFile(content))

    def set_extent(self):
        """ https://gis.stackexchange.com/a/201320/28414 """
        if self.file is not None:
            self.extent = get_extent_from_file(Path(self.file.path))
            self.save(update_fields=["extent"])

    def set_layerset(self, layerset):

        # if it's the same vrs then do nothing
        if self.layerset == layerset:
            logger.debug(f"{self.pk} same as existing layerset, no action")
            return

        # make sure to clean up the existing multimask in the current vrs if necessary
        if self.layerset:
            if self.layerset.multimask and self.slug in self.layerset.multimask:
                del self.layerset.multimask[self.slug]
                self.layerset.save(update_fields=["multimask"])
                logger.warn(f"{self.pk} removed layer from existing multimask in layerset {self.layerset.pk}")
        self.layerset = layerset
        self.save(update_fields=["layerset"])
        logger.info(f"{self.pk} added to layerset {self.layerset} ({self.layerset.pk})")

        # little patch in here to make sure the new Map objects get added to the layerset,
        # before everything is shifted away from the Volume model
        if not layerset.map:
            layerset.map = self.region.document.map
            layerset.save()

    def save(self,
        set_slug: bool=False,
        set_thumbnail: bool=False,
        set_extent: bool=False,
        *args, **kwargs
    ):

        if set_slug or not self.slug:
            self.slug = slugify(self.region.__str__(), join_char="_")

        if set_thumbnail or (self.file and not self.thumbnail):
            self.set_thumbnail()

        if set_extent or (self.file and not self.extent):
            self.set_extent()

        self.title = self.region.title

        return super(self.__class__, self).save(*args, **kwargs)
import os
import json
import logging
from datetime import datetime
from pathlib import Path

from natsort import natsorted

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.gis.db import models
from django.contrib.gis.geos import Polygon, MultiPolygon, GEOSGeometry
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from ohmg.core.utils import (
    slugify,
    download_image,
    copy_local_file_to_cache,
    convert_img_format,
    get_session_user_summary,
    MONTH_CHOICES,
)
from ohmg.core.storages import OverwriteStorage
from ohmg.core.renderers import (
    get_image_size,
    get_extent_from_file,
    generate_document_thumbnail_content,
    generate_layer_thumbnail_content,
)
from ohmg.places.models import Place

logger = logging.getLogger(__name__)


class MapGroup(models.Model):
    class Meta:
        verbose_name_plural = "      Map Groups"

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
        help_text="The preferred term for referring to maps within this map group.",
    )

    def __str__(self):
        return self.title


class Map(models.Model):
    class Meta:
        verbose_name_plural = "    Maps"

    ACCESS_CHOICES = (
        ("none", "none"),
        ("sponsor", "sponsor"),
        ("any", "any"),
    )
    ACCESS_LEVEL_CHOICES = (
        ("public", "Public"),
        ("restricted", "Restricted"),
        ("none", "None"),
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
    month = models.IntegerField(blank=True, null=True, choices=MONTH_CHOICES)
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
        help_text="Volume number (or name?), if this map is included in a MapGroup.",
    )
    document_page_type = models.CharField(
        max_length=10,
        choices=DOCUMENT_PREFIX_CHOICES,
        null=True,
        blank=True,
        help_text="The preferred term for referring to documents within this map.",
    )
    iiif_manifest = models.JSONField(null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    load_date = models.DateTimeField(null=True, blank=True)
    loading_documents = models.BooleanField(
        default=False,
        help_text="true only when document files are being loaded for this map",
    )
    document_sources = models.JSONField(
        null=True,
        blank=True,
        default=dict,
    )
    item_lookup = models.JSONField(
        null=True,
        blank=True,
        default=dict,
    )
    featured = models.BooleanField(default=False, help_text="show in featured section")
    hidden = models.BooleanField(
        default=False,
        help_text="this map will be excluded from api calls (but url available directly)",
    )
    locales = models.ManyToManyField(
        Place,
        blank=True,
    )
    mapgroup = models.ForeignKey(
        MapGroup, null=True, blank=True, on_delete=models.SET_NULL, related_name="maps"
    )
    access = models.CharField(max_length=50, choices=ACCESS_CHOICES, default="any")
    access_level = models.CharField(max_length=50, choices=ACCESS_LEVEL_CHOICES, default="any")
    user_access = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="maps_allowed",
    )
    group_access = models.ManyToManyField(
        Group,
        blank=True,
        related_name="maps_allowed",
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
        related_name="maps_loaded",
    )

    def __str__(self):
        return self.title

    @property
    def regions(self):
        return Region.objects.filter(document__in=self.documents.all()).order_by("title")

    @property
    def layers(self):
        return Layer.objects.filter(region__in=self.regions).order_by("title")

    @property
    def extent(self):
        layerset_extents = []
        for ls in self.layerset_set.all():
            if ls.extent:
                poly = Polygon().from_bbox(ls.extent)
                layerset_extents.append(poly)
        if layerset_extents:
            return MultiPolygon(layerset_extents).extent
        else:
            return None

    @property
    def gt_exists(self):
        return (
            True
            if self.get_layerset("main-content")
            and self.get_layerset("main-content").mosaic_geotiff
            else False
        )

    @property
    def mj_exists(self):
        return (
            True
            if self.get_layerset("main-content") and self.get_layerset("main-content").mosaic_json
            else False
        )

    @property
    def stats(self):
        unprep_ct = len(self.item_lookup["unprepared"])
        prep_ct = len(self.item_lookup["prepared"])
        georef_ct = len(self.item_lookup["georeferenced"])
        percent = 0
        if georef_ct > 0:
            percent = int((georef_ct / (unprep_ct + prep_ct + georef_ct)) * 100)

        main_layerset = self.get_layerset("main-content")
        if main_layerset:
            main_lyrs_ct = main_layerset.layer_set.count()
        else:
            main_lyrs_ct = 0
        mm_ct, mm_todo, mm_percent = 0, 0, 0
        if main_lyrs_ct != 0:
            # make sure 0/0 appears at the very bottom, then 0/1, 0/2, etc.
            mm_percent = main_lyrs_ct * 0.000001
        mm_display = f"0/{main_lyrs_ct}"
        if main_layerset and main_layerset.multimask is not None:
            mm_ct = len(main_layerset.multimask)
            mm_todo = main_lyrs_ct - mm_ct
            if mm_ct > 0 and main_lyrs_ct > 0:
                mm_display = f"{mm_ct}/{main_lyrs_ct}"
                mm_percent = mm_ct / main_lyrs_ct
                mm_percent += main_lyrs_ct * 0.000001

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
        """Returns the first locale in the list of related locales.
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

    def get_layerset(self, cat_slug: str, create: bool = False):
        try:
            layerset = LayerSet.objects.get(map=self, category__slug=cat_slug)
        except LayerSet.DoesNotExist:
            if create:
                category = LayerSetCategory.objects.get(slug=cat_slug)
                layerset = LayerSet.objects.create(map=self, category=category)
                logger.debug(f"created new LayerSet: {self.pk} - {cat_slug}")
            else:
                layerset = None
        return layerset

    def create_documents(self):
        """Iterates the list of items in self.document_sources and create Document
        objects for each one. If get_files=True, load files from their path.

        A document source entry should look like:
        {
            path: <url (required)>
            iiif_info: <url to iiif info.json document (optional)>
            page_number: <str for page id (optional but must be unique across all documents in list)>
        }
        """
        for source in self.document_sources:
            document, created = Document.objects.get_or_create(
                map=self,
                page_number=source["page_number"],
            )
            document.source_url = source["path"]
            document.iiif_info = source["iiif_info"]
            document.save(skip_map_lookup_update=True)
            if created:
                logger.debug(f"{document} ({document.pk}) created.")
        logger.debug(f"Map {self.title} ({self.pk}) has {len(self.documents.all())} Documents")
        self.update_item_lookup()

    def load_all_document_files(self, username, overwrite=False):
        self.loading_documents = True
        self.save()
        for document in natsorted(self.documents.all(), key=lambda k: k.title):
            if not document.file and not overwrite:
                try:
                    document.load_file_from_source(username, overwrite=True)
                except Exception as e:
                    logger.error(f"error loading document {document.pk}: {e}")
                    document.loading_file = False
                    document.save()
        self.loading_documents = False
        self.save()

    def remove_sheets(self):
        for document in self.documents:
            document.delete()

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
        from ohmg.core.api.schemas import DocumentSchema, RegionSchema, LayerSchema

        regions = self.regions
        items = {
            "unprepared": [
                DocumentSchema.from_orm(i).dict() for i in self.documents.filter(prepared=False)
            ],
            "prepared": [
                RegionSchema.from_orm(i).dict()
                for i in regions.filter(georeferenced=False, is_map=True)
            ],
            "georeferenced": [LayerSchema.from_orm(i).dict() for i in self.layers],
            "nonmaps": [RegionSchema.from_orm(i).dict() for i in regions.filter(is_map=False)],
            "processing": {
                "unprep": 0,
                "prep": 0,
                "geo_trim": 0,
            },
        }
        for cat in ["unprepared", "prepared", "georeferenced", "nonmaps"]:
            items[cat] = natsorted(items[cat], key=lambda k: k["title"])
        self.item_lookup = items
        self.save(update_fields=["item_lookup"])

    def get_session_summary(self):
        from ohmg.georeference.models import SessionBase

        sessions = SessionBase.objects.filter(
            Q(doc2__map_id=self.pk) | Q(reg2__document__map_id=self.pk)
            # | Q(lyr2__region__document__map_id=self.pk)
        ).prefetch_related()

        prep_sessions = sessions.filter(type="p")
        georef_sessions = sessions.filter(type="g")

        prep_ct = prep_sessions.count()
        georef_ct = georef_sessions.count()
        summary = {
            "prep_ct": prep_ct,
            "prep_contributors": get_session_user_summary(prep_sessions),
            "georef_ct": georef_ct,
            "georef_contributors": get_session_user_summary(georef_sessions),
        }
        return summary

    def save(self, set_slug=False, *args, **kwargs):
        if set_slug or not self.slug:
            self.slug = slugify(self.title, join_char="_")

        return super(self.__class__, self).save(*args, **kwargs)


class Document(models.Model):
    """Documents are the individual source files that are directly attached to Maps.
    They represent pages in an atlas or even just a single scan of a map."""

    class Meta:
        verbose_name_plural = "   Documents"

    title = models.CharField(max_length=200, default="untitled document")
    nickname = models.CharField(max_length=200, null=True, blank=True)
    slug = models.SlugField(max_length=100)
    map = models.ForeignKey(Map, on_delete=models.CASCADE, related_name="documents")
    page_number = models.CharField(max_length=10, null=True, blank=True)
    prepared = models.BooleanField(default=False)
    loading_file = models.BooleanField(default=False)
    file = models.FileField(
        upload_to="documents",
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    image_size = ArrayField(
        models.IntegerField(),
        size=2,
        null=True,
        blank=True,
    )
    thumbnail = models.FileField(
        upload_to="thumbnails",
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    source_url = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Storing a source_url allows the file to be downloaded at any point after "
        "the instance has been created.",
    )
    iiif_info = models.JSONField(null=True, blank=True)
    load_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    @property
    def layers(self):
        return Layer.objects.filter(region_id__in=self.regions.all().values_list("id", flat=True))

    @property
    def lock(self):
        from ohmg.georeference.models import SessionLock

        ct = ContentType.objects.get_for_model(self)
        locks = SessionLock.objects.filter(target_type=ct, target_id=self.pk)
        if locks.exists():
            return locks[0]
        else:
            return None

    def load_file_from_source(self, username, overwrite=False):
        log_prefix = f"{self.__str__()} |"
        logger.info(f"{log_prefix} start load")
        self.loading_file = True
        self.save()

        if self.source_url:
            src_url = self.source_url
        elif self.iiif_info:
            src_url = self.iiif_info.replace("info.json", "full/full/0/default.jpg")
        elif self.source_url:
            src_url = self.source_url
        else:
            logger.warning(f"{log_prefix} no source_url or iiif_info - cancelling download")
            return

        if self.file != "" and not overwrite:
            logger.warning(f"{log_prefix} won't overwrite existing file")
            return

        src_path = Path(src_url)
        tmp_path = Path(settings.CACHE_DIR, "images", src_path.name)

        if src_url.startswith("http"):
            out_file = download_image(src_url, tmp_path, use_cache=not overwrite)
            if out_file is None:
                logger.error(f"can't get {src_url} -- skipping")
                return
        else:
            copy_local_file_to_cache(src_path, tmp_path)

        if not src_url.endswith(".jpg"):
            tmp_path = convert_img_format(tmp_path, force=True)

        if not tmp_path.exists():
            logger.error(f"{log_prefix} can't retrieve source: {src_url}. Moving to next Document.")
            return

        with open(tmp_path, "rb") as new_file:
            self.file.save(f"{self.slug}{tmp_path.suffix}", File(new_file))

        self.load_date = datetime.now()
        self.loading_file = False
        if self.map.loaded_by is None:
            self.map.loaded_by = get_user_model().objects.get(username=username)
            self.map.load_date = self.load_date
            self.map.save(update_fields=["loaded_by", "load_date"])
        self.save(set_thumbnail=True)

    def set_thumbnail(self):
        if self.file is not None:
            if self.thumbnail:
                self.thumbnail.delete()
            path = self.file.path
            name = os.path.splitext(os.path.basename(path))[0]
            content = generate_document_thumbnail_content(path)
            tname = f"{name}-doc-thumb.jpg"
            self.thumbnail.save(tname, ContentFile(content))

    def save(
        self,
        set_slug: bool = False,
        set_thumbnail: bool = False,
        set_image_size: bool = False,
        skip_map_lookup_update: bool = False,
        *args,
        **kwargs,
    ):
        # attach this flag which is checked on the post_save signal receiver
        self.skip_map_lookup_update = skip_map_lookup_update

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

        self.nickname = self.map.title
        if self.page_number and self.nickname:
            self.nickname = f"{self.map.document_page_type} {self.page_number}"

        if set_image_size or not self.image_size:
            self.image_size = get_image_size(Path(self.file.path)) if self.file else None

        return super(self.__class__, self).save(*args, **kwargs)


class Region(models.Model):
    class Meta:
        verbose_name_plural = "  Regions"

    title = models.CharField(max_length=200, default="untitled region")
    nickname = models.CharField(max_length=200, null=True, blank=True)
    slug = models.SlugField(max_length=100)
    boundary = models.PolygonField(
        null=True,
        blank=True,
    )
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="regions")
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
        upload_to="regions",
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    image_size = ArrayField(
        models.IntegerField(),
        size=2,
        null=True,
        blank=True,
    )
    thumbnail = models.FileField(
        upload_to="thumbnails",
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )

    def __str__(self):
        return self.title

    @cached_property
    def map(self) -> Map:
        return self.document.map

    @property
    def transformation(self):
        if hasattr(self, "gcpgroup"):
            return self.gcpgroup.transformation
        else:
            return None

    @property
    def gcps_geojson(self):
        if hasattr(self, "gcpgroup"):
            return self.gcpgroup.as_geojson
        else:
            return None

    @property
    def lock(self):
        from ohmg.georeference.models import SessionLock

        ct = ContentType.objects.get_for_model(self)
        locks = SessionLock.objects.filter(target_type=ct, target_id=self.pk)
        if locks.exists():
            return locks[0]
        else:
            return None

    def set_thumbnail(self):
        if self.file is not None:
            if self.thumbnail:
                self.thumbnail.delete()
            path = self.file.path
            name = os.path.splitext(os.path.basename(path))[0]
            content = generate_document_thumbnail_content(path)
            tname = f"{name}-reg-thumb.jpg"
            self.thumbnail.save(tname, ContentFile(content))

    def save(
        self,
        set_slug: bool = False,
        set_thumbnail: bool = False,
        set_image_size: bool = False,
        skip_map_lookup_update: bool = False,
        *args,
        **kwargs,
    ):
        # attach this flag which is checked on the post_save signal receiver
        self.skip_map_lookup_update = skip_map_lookup_update

        if set_thumbnail or (self.file and not self.thumbnail):
            self.set_thumbnail()

        if set_slug or not self.slug:
            display_name = self.document.__str__()
            if self.division_number:
                display_name += f" [{self.division_number}]"
            self.slug = slugify(display_name, join_char="_")

        self.title = self.document.title
        if self.division_number:
            self.title += f" [{self.division_number}]"

        self.nickname = self.document.nickname
        if self.division_number and self.nickname:
            self.nickname += f" [{self.division_number}]"

        if set_image_size or not self.image_size:
            self.image_size = get_image_size(Path(self.file.path)) if self.file else None

        return super(self.__class__, self).save(*args, **kwargs)


class Layer(models.Model):
    class Meta:
        verbose_name_plural = " Layers"

    title = models.CharField(max_length=200, default="untitled layer")
    nickname = models.CharField(max_length=200, null=True, blank=True)
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
    extent = ArrayField(
        models.FloatField(),
        size=4,
        null=True,
        blank=True,
    )
    file = models.FileField(
        upload_to="layers",
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    thumbnail = models.FileField(
        upload_to="thumbnails",
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    layerset2 = models.ForeignKey(
        "core.LayerSet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return self.title

    @cached_property
    def map(self) -> Map:
        return self.region.document.map

    @property
    def lock(self):
        from ohmg.georeference.models import SessionLock

        ct = ContentType.objects.get_for_model(self)
        locks = SessionLock.objects.filter(target_type=ct, target_id=self.pk)
        if locks.exists():
            return locks[0]
        else:
            return None

    def set_thumbnail(self):
        if self.file is not None:
            if self.thumbnail:
                self.thumbnail.delete()
            path = self.file.path
            name = os.path.splitext(os.path.basename(path))[0]
            content = generate_layer_thumbnail_content(path)
            tname = f"{name}-lyr-thumb.jpg"
            self.thumbnail.save(tname, ContentFile(content))

    def set_layerset(self, layerset):
        # if it's the same LayerSet then do nothing
        if self.layerset2 == layerset:
            logger.debug(
                f"Layer {self.pk} already in LayerSet {layerset} ({layerset.pk}), no action"
            )
            return

        # make sure to clean up the existing multimask in the current vrs if necessary
        existing_obj = LayerSet.objects.get(pk=self.layerset2.pk) if self.layerset2 else None
        delete_existing = False
        if existing_obj:
            if existing_obj.multimask and self.slug in existing_obj.multimask:
                del existing_obj.multimask[self.slug]
                existing_obj.save(update_fields=["multimask"])
                logger.info(
                    f"Layer {self.pk} removed from existing multimask in LayerSet {existing_obj.pk}"
                )
            if existing_obj.layer_set.all().count() == 1:
                delete_existing = True
        self.layerset2 = layerset
        self.save(update_fields=["layerset2"])
        logger.info(f"Layer {self.pk} added to LayerSet {self.layerset2} ({self.layerset2.pk})")

        if delete_existing:
            msg = f"Emptied LayerSet {existing_obj} ({existing_obj.pk}) deleted"
            existing_obj.delete()
            logger.info(msg)

        # little patch in here to make sure the new Map objects get added to the layerset,
        # before everything is shifted away from the Volume model
        if not layerset.map:
            layerset.map = self.region.document.map

        # save here to trigger a recalculation of the layerset's extent
        layerset.save()

    def get_creators(self):
        from ohmg.georeference.models import SessionBase

        sessions = SessionBase.objects.filter(Q(doc2=self.region.document) | Q(reg2=self.region))
        user_list = get_session_user_summary(sessions)
        return [
            {
                "id": f"https://oldinsurancemaps.net/profile/{i['name']}",
                "type": "Person",
            }
            for i in user_list
        ]

    def save(
        self,
        set_slug: bool = False,
        set_thumbnail: bool = False,
        set_extent: bool = True,
        skip_map_lookup_update: bool = False,
        *args,
        **kwargs,
    ):
        # attach this flag which is checked on the post_save signal receiver
        self.skip_map_lookup_update = skip_map_lookup_update

        if set_slug or not self.slug:
            self.slug = slugify(self.region.__str__(), join_char="_")

        if set_thumbnail or (self.file and not self.thumbnail):
            self.set_thumbnail()

        if set_extent and self.file:
            self.extent = get_extent_from_file(Path(self.file.path))

        self.title = self.region.title
        self.nickname = self.region.nickname

        return super(self.__class__, self).save(*args, **kwargs)


class LayerSetCategory(models.Model):
    class Meta:
        verbose_name_plural = "Layer Set Categories"

    slug = models.CharField(max_length=50)
    description = models.CharField(max_length=200, null=True, blank=True)
    display_name = models.CharField(max_length=50)

    def __str__(self):
        return self.display_name if self.display_name else self.slug


class LayerSet(models.Model):
    class Meta:
        verbose_name_plural = "Layer Sets"

    map = models.ForeignKey(
        Map,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    category = models.ForeignKey(
        LayerSetCategory,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    multimask = models.JSONField(null=True, blank=True)
    mosaic_geotiff = models.FileField(
        upload_to="mosaics",
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    mosaic_json = models.FileField(
        upload_to="mosaics",
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    extent = ArrayField(
        models.FloatField(),
        size=4,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.map} - {self.category}"

    def layer_display_list(self):
        """For display in the admin interface only."""
        li = [
            f"<li><a href='/admin/core/layer/{i.pk}/change'>{i}</a></li>"
            for i in self.layer_set.all()
        ]
        return mark_safe("<ul>" + "".join(li) + "</ul>")

    layer_display_list.short_description = "Layers"

    @property
    def mosaic_cog_url(self):
        """return the public url to the mosaic COG for this annotation set. If
        no COG exists, return None."""
        url = None
        if self.mosaic_geotiff:
            url = settings.MEDIA_HOST.rstrip("/") + self.mosaic_geotiff.url
        return url

    @property
    def mosaic_json_url(self):
        """return the public url to the mosaic JSON for this annotation set. If
        no mosaic JSON exists, return None."""
        url = None
        if self.mosaic_json:
            url = settings.MEDIA_HOST.rstrip("/") + self.mosaic_json.url
        return url

    @property
    def multimask_extent(self):
        """Calculate an extent based on all layers in this layerset's
        multimask. If there is no multimask, return None."""
        extent = None
        if self.multimask:
            feature_polygons = []
            for v in self.multimask.values():
                poly = Polygon(v["geometry"]["coordinates"][0])
                feature_polygons.append(poly)
            if len(feature_polygons) > 0:
                extent = MultiPolygon(feature_polygons, srid=4326).extent
        return extent

    @property
    def multimask_geojson(self):
        if self.multimask:
            multimask_geojson = {"type": "FeatureCollection", "features": []}
            for layer, geojson in self.multimask.items():
                geojson["properties"] = {"layer": layer}
                multimask_geojson["features"].append(geojson)
            return multimask_geojson
        else:
            return None

    def validate_multimask_geojson(self, multimask_geojson):
        errors = []
        for feature in multimask_geojson["features"]:
            lyr = feature["properties"]["layer"]
            try:
                geom_str = json.dumps(feature["geometry"])
                g = GEOSGeometry(geom_str)
                if not g.valid:
                    logger.warning(f"{self} | invalid mask: {lyr} - {g.valid_reason}")
                    errors.append((lyr, g.valid_reason))
            except Exception as e:
                logger.warning(f"{self} | improper GeoJSON in multimask")
                errors.append((lyr, e))
        return errors

    def update_multimask_from_geojson(self, multimask_geojson):
        errors = self.validate_multimask_geojson(multimask_geojson)
        if errors:
            return errors

        if multimask_geojson["features"]:
            self.multimask = {}
            for feature in multimask_geojson["features"]:
                self.multimask[feature["properties"]["layer"]] = feature
        else:
            self.multimask = None
        self.save(update_fields=["multimask"])

    def save(self, *args, **kwargs):
        extents = self.layer_set.all().values_list("extent", flat=True)
        layer_extents = []
        for extent in extents:
            if extent:
                poly = Polygon().from_bbox(extent)
                layer_extents.append(poly)
        if layer_extents:
            combined = MultiPolygon(layer_extents)
            self.extent = combined.extent

        return super(self.__class__, self).save(*args, **kwargs)

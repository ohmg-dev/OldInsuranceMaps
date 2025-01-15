import os
import logging
from itertools import chain
from datetime import datetime
from pathlib import Path

from natsort import natsorted

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.utils.functional import cached_property

from ohmg.core.utils import (
    slugify,
    download_image,
    copy_local_file_to_cache,
    convert_img_format,
    MONTH_CHOICES,
    DAY_CHOICES,
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

    class Meta:
        verbose_name_plural = "Map Groups"

    def __str__(self):
        return self.title


class Map(models.Model):
    STATUS_CHOICES = (
        ("not started", "not started"),
        ("initializing...", "initializing..."),
        ("document load error", "document load error"),
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
    month = models.IntegerField(blank=True, null=True, choices=MONTH_CHOICES)
    day = models.IntegerField(blank=True, null=True, choices=DAY_CHOICES)
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
        ls = self.get_layerset("main-content")
        if ls:
            return ls.extent
        else:
            return None

    @property
    def gt_exists(self):
        return True if self.get_layerset("main-content").mosaic_geotiff else False

    @property
    def mj_exists(self):
        return True if self.get_layerset("main-content").mosaic_json else False

    @property
    def stats(self):
        unprep_ct = len(self.item_lookup["unprepared"])
        prep_ct = len(self.item_lookup["prepared"])
        georef_ct = len(self.item_lookup["georeferenced"])
        percent = 0
        if georef_ct > 0:
            percent = int((georef_ct / (unprep_ct + prep_ct + georef_ct)) * 100)

        main_layerset = self.get_layerset("main-content")
        main_lyrs_ct = main_layerset.layers.count()
        mm_ct, mm_todo, mm_percent = 0, 0, 0
        if main_lyrs_ct != 0:
            # make sure 0/0 appears at the very bottom, then 0/1, 0/2, etc.
            mm_percent = main_lyrs_ct * 0.000001
        mm_display = f"0/{main_lyrs_ct}"
        if main_layerset.multimask is not None:
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
        from ohmg.georeference.models import LayerSet, LayerSetCategory

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

    def create_documents(self, get_files=False):
        """Iterates the list of items in self.document_sources and create Document
        objects for each one. If get_files=True, load files from their path.

        A document source entry should look like:
        {
            path: <url (required)>
            iiif_info: <url to iiif info.json document (optional)>
            page_number: <str for page id (optional but must be unique across all documents in list)>
        }
        """
        self.set_status("initializing...")
        try:
            for source in self.document_sources:
                document, created = Document.objects.get_or_create(
                    map=self,
                    page_number=source["page_number"],
                )
                document.source_url = source["path"]
                document.iiif_info = source["iiif_info"]
                document.save()
                if created:
                    logger.debug(f"{document} ({document.pk}) created.")

            logger.debug(f"Map {self.title} ({self.pk}) has {len(self.documents.all())} Documents")
            if get_files:
                for document in natsorted(self.documents.all(), key=lambda k: k.title):
                    document.load_file_from_source()
        except Exception as e:
            logger.error(e)
            self.set_status("document load error")
            raise e
        self.set_status("ready")

    def remove_sheets(self):
        for document in self.documents:
            document.delete()

    def set_status(self, status):
        self.status = status
        self.save(update_fields=["status"])

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
                DocumentSchema.from_orm(i).dict()
                for i in self.documents.filter(prepared=False).exclude(file="")
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

        def _get_session_user_summary(session_list):
            users = session_list.values_list("user__username", flat=True)
            user_dict = {}
            for name in users:
                user_dict[name] = user_dict.get(
                    name,
                    {
                        "ct": 0,
                        "name": name,
                    },
                )
                user_dict[name]["ct"] += 1
            return sorted(user_dict.values(), key=lambda item: item.get("ct"), reverse=True)

        prep_ct = prep_sessions.count()
        georef_ct = georef_sessions.count()
        summary = {
            "prep_ct": prep_ct,
            "prep_contributors": _get_session_user_summary(prep_sessions),
            "georef_ct": georef_ct,
            "georef_contributors": _get_session_user_summary(georef_sessions),
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
    nickname = models.CharField(max_length=200, null=True, blank=True)
    slug = models.SlugField(max_length=100)
    map = models.ForeignKey(Map, on_delete=models.CASCADE, related_name="documents")
    page_number = models.CharField(max_length=10, null=True, blank=True)
    prepared = models.BooleanField(default=False)
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

    def load_file_from_source(self, overwrite=False):
        log_prefix = f"{self.__str__()} |"
        logger.info(f"{log_prefix} start load")

        if not self.source_url:
            logger.warning(f"{log_prefix} no source_url - cancelling download")
            return

        if self.file != "" and not overwrite:
            logger.warning(f"{log_prefix} won't overwrite existing file")
            return

        src_path = Path(self.source_url)
        tmp_path = Path(settings.CACHE_DIR, "images", src_path.name)

        if self.source_url.startswith("http"):
            out_file = download_image(self.source_url, tmp_path)
            if out_file is None:
                logger.error(f"can't get {self.source_url} -- skipping")
                return
        else:
            copy_local_file_to_cache(src_path, tmp_path)

        if not self.source_url.endswith(".jpg"):
            tmp_path = convert_img_format(tmp_path, force=True)

        if not tmp_path.exists():
            logger.error(
                f"{log_prefix} can't retrieve source: {self.source_url}. Moving to next Document."
            )
            return

        with open(tmp_path, "rb") as new_file:
            self.file.save(f"{self.slug}{tmp_path.suffix}", File(new_file))

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

    def save(
        self,
        set_slug: bool = False,
        set_thumbnail: bool = False,
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

        self.image_size = get_image_size(Path(self.file.path)) if self.file else None

        return super(self.__class__, self).save(*args, **kwargs)


class Region(models.Model):
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
    gcp_group = models.OneToOneField(
        "georeference.GCPGroup",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return self.title

    @cached_property
    def map(self) -> Map:
        return self.document.map

    @property
    def tranformation(self):
        if self.gcp_group:
            return self.gcp_group.transformation
        else:
            return None

    @property
    def gcps_geojson(self):
        if self.gcp_group:
            return self.gcp_group.as_geojson
        else:
            return None

    @property
    def _base_urls(self):
        return {
            "thumbnail": self.thumbnail.url if self.thumbnail else "",
            "image": self.file.url if self.file else "",
        }

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

        self.image_size = get_image_size(Path(self.file.path)) if self.file else None

        return super(self.__class__, self).save(*args, **kwargs)


class Layer(models.Model):
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
    layerset = models.ForeignKey(
        "georeference.LayerSet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="layers",
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

    @property
    def urls(self):
        urls = self._base_urls
        doc = self.get_document()
        urls.update(
            {
                "resource": f"/layer/{self.pk}",
                # remove detail and progress_page urls once InfoPanel has been fully
                # deprecated and volume summary has been updated.
                # note the geonode: prefix is still necessary until non-geonode
                # layer and document detail pages are created.
                "detail": f"/layers/geonode:{self.slug}" if self.slug else "",
                "progress_page": f"/layers/geonode:{self.pk}#georeference" if self.slug else "",
                # redundant, I know, but a patch for now
                "cog": settings.MEDIA_HOST.rstrip("/") + urls["image"],
            }
        )
        if doc is not None:
            urls.update(
                {
                    "georeference": doc.urls["georeference"],
                    "document": doc.urls["image"],
                }
            )
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
                logger.warning(
                    f"{self.pk} removed layer from existing multimask in layerset {self.layerset.pk}"
                )
        self.layerset = layerset
        self.save(update_fields=["layerset"])
        logger.info(f"{self.pk} added to layerset {self.layerset} ({self.layerset.pk})")

        # little patch in here to make sure the new Map objects get added to the layerset,
        # before everything is shifted away from the Volume model
        if not layerset.map:
            layerset.map = self.region.document.map

        # save here to trigger a recalculation of the layerset's extent
        layerset.save()

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

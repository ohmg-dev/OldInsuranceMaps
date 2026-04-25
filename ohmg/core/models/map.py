import logging

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.gis.db import models
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.db import transaction
from django.db.models import Q
from natsort import natsorted

from ohmg.places.models import Place

from ..utils import (
    MONTH_CHOICES,
    get_session_user_summary,
    slugify,
)

logger = logging.getLogger(__name__)


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
        "core.MapGroup",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="maps",
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
    document_ct = models.IntegerField(
        default=0,
    )
    unprepared_ct = models.IntegerField(
        default=0,
    )
    region_ct = models.IntegerField(
        default=0,
    )
    prepared_ct = models.IntegerField(
        default=0,
    )
    layer_ct = models.IntegerField(
        default=0,
    )
    main_layer_ct = models.IntegerField(
        default=0,
    )
    skip_ct = models.IntegerField(
        default=0,
    )
    nonmap_ct = models.IntegerField(
        default=0,
    )
    completion_pct = models.IntegerField(
        default=0,
    )
    multimask_ct = models.IntegerField(
        default=0,
    )
    multimask_rank = models.DecimalField(
        max_digits=7,
        decimal_places=6,
        default=0.000000,
    )

    def __str__(self):
        return self.title

    @property
    def regions(self):
        from .region import Region

        return Region.objects.filter(document__in=self.documents.all()).order_by("title")

    @property
    def layers(self):
        from .layer import Layer

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
        skipped_ct = len(self.item_lookup["skipped"])
        percent = 0
        if georef_ct > 0:
            percent = int((georef_ct / (unprep_ct + prep_ct + georef_ct)) * 100)

        main_layerset = self.get_layerset("main-content")
        if main_layerset:
            main_lyrs_ct = main_layerset.get_layers().count()
        else:
            main_lyrs_ct = 0
        mm_ct, mm_todo, mm_percent = 0, 0, 0
        if main_lyrs_ct != 0:
            # make sure 0/0 appears at the very bottom, then 0/1, 0/2, etc.
            mm_percent = main_lyrs_ct * 0.000001
        mm_display = f"0/{main_lyrs_ct}"
        if main_layerset:
            mm_ct = len(main_layerset.multimask_geojson["features"])
            mm_todo = main_lyrs_ct - mm_ct
            if mm_ct > 0 and main_lyrs_ct > 0:
                mm_display = f"{mm_ct}/{main_lyrs_ct}"
                mm_percent = mm_ct / main_lyrs_ct
                mm_percent += main_lyrs_ct * 0.000001

        return {
            "unprepared_ct": unprep_ct,
            "prepared_ct": prep_ct,
            "georeferenced_ct": georef_ct,
            "skipped_ct": skipped_ct,
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
        from .layerset import LayerSet, LayerSetCategory

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
        from .document import Document

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
        from ohmg.api.schemas import DocumentSchema, LayerSchema, RegionSchema

        regions = self.regions
        items = {
            "unprepared": [
                DocumentSchema.from_orm(i).dict() for i in self.documents.filter(prepared=False)
            ],
            "prepared": [
                RegionSchema.from_orm(i).dict()
                for i in regions.filter(georeferenced=False, category__slug="map").exclude(
                    skipped=True
                )
            ],
            "georeferenced": [LayerSchema.from_orm(i).dict() for i in self.layers],
            "nonmaps": [
                RegionSchema.from_orm(i).dict() for i in regions.exclude(category__slug="map")
            ],
            "skipped": [RegionSchema.from_orm(i).dict() for i in regions.filter(skipped=True)],
            "processing": {
                "unprep": 0,
                "prep": 0,
                "geo_trim": 0,
            },
        }
        for cat in ["unprepared", "prepared", "georeferenced", "nonmaps", "skipped"]:
            items[cat] = natsorted(items[cat], key=lambda k: k["title"])
        self.item_lookup = items

        document_ct = self.documents.all().count()
        unprepared_ct = len(items["unprepared"])
        region_ct = self.regions.count()
        prepared_ct = len(items["prepared"])
        layer_ct = self.layers.count()
        skip_ct = len(items["skipped"])
        nonmap_ct = len(items["nonmaps"])

        completion_pct = 0
        if layer_ct > 0:
            completion_pct = int((layer_ct / (unprepared_ct + prepared_ct + layer_ct)) * 100)

        multimask_ct, multimask_rank = 0, 0
        main_layerset = self.get_layerset("main-content")
        if main_layerset:
            main_lyrs_ct = main_layerset.get_layers().count()
        else:
            main_lyrs_ct = 0

        if main_lyrs_ct != 0:
            # make sure 0/0 appears at the very bottom, then 0/1, 0/2, etc.
            multimask_rank = main_lyrs_ct * 0.000001

        if main_layerset:
            multimask_ct = len(main_layerset.multimask_geojson["features"])
            if multimask_ct > 0 and main_lyrs_ct > 0:
                pct = multimask_ct / main_lyrs_ct
                multimask_rank += pct * 0.000001

        self.document_ct = document_ct
        self.unprepared_ct = unprepared_ct
        self.region_ct = region_ct
        self.prepared_ct = prepared_ct
        self.layer_ct = layer_ct
        self.main_layer_ct = main_lyrs_ct
        self.skip_ct = skip_ct
        self.nonmap_ct = nonmap_ct
        self.completion_pct = completion_pct
        self.multimask_ct = multimask_ct
        self.multimask_rank = multimask_rank

        self.save(
            update_fields=[
                "item_lookup",
                "document_ct",
                "unprepared_ct",
                "region_ct",
                "prepared_ct",
                "layer_ct",
                "main_layer_ct",
                "skip_ct",
                "nonmap_ct",
                "completion_pct",
                "multimask_ct",
                "multimask_rank",
            ]
        )

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

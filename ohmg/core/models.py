import os
import logging
from itertools import chain
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.contrib.gis.db import models
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import transaction
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

    @cached_property
    def documents(self):
        return Document.objects.filter(map=self).order_by("page_number")

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

    def get_layersets(self, geospatial:bool=False):
        from ohmg.georeference.models import LayerSet
        sets = LayerSet.objects.filter(volume=self)
        if geospatial:
            sets = sets.filter(category__is_geospatial=True)
        return sets

    def create_documents(self, get_files=False):
        """ This method is still 100% reliant on having LOC content in the
        document_sources field. """
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
            for doc in self.documents.all():
                doc.download_file()

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

    def get_all_docs(self):
        all_documents = []
        for sheet in self.sheets:
            all_documents += sheet.real_docs
        return all_documents

    def get_absolute_url(self):
        return f"/map/{self.pk}/"

    def get_urls(self):

        viewer_url = ""
        if self.get_locale():
            viewer_url = reverse("viewer", args=(self.get_locale().slug,)) + f"?{self.identifier}=100"

        return {
            "summary": reverse("map_summary", args=(self.identifier,)),
            "viewer": viewer_url,
        }

    def refresh_lookups(self):
        """Clean and remake document_lookup and layer_lookup fields
        for this Volume by examining the original loaded Sheets and
        re-evaluating every descendant Document and LayerV1.
        """

        if len(self.document_lookup) > 0 or len(self.layer_lookup) > 0:
            self.document_lookup = {}
            self.layer_lookup = {}
            self.save(update_fields=["document_lookup", "layer_lookup"])

        for document in self.get_all_docs():
            self.update_doc_lookup(document, update_layer=True)

    def update_doc_lookup(self, document, update_layer=False):
        """Serialize the input document, and save it into
        this volume's lookup table. If an int is passed, it will be used
        as a primary key lookup.

        If update_layer=True, also trigger the update of the layer
        lookup for the georeference layer from this document
        (if applicable)."""
        from ohmg.georeference.models.resources import Document

        if isinstance(document, Document):
            data = document.serialize(serialize_layer=False, include_sessions=True)
        elif str(document).isdigit():
            data = Document.objects.get(pk=document).serialize(serialize_layer=False, include_sessions=True)
        else:
            logger.warn(f"cannot update_doc_lookup with this input: {document} ({type(document)}")
            return

        # hacky method for pulling out the sheet number from the title
        try:
            data["page_str"] = data['title'].split("|")[-1].split("p")[1]
        except IndexError:
            data["page_str"] = data['title']

        self.document_lookup[data['id']] = data
        self.save(update_fields=["document_lookup"])

        if update_layer is True and data['layer']:
            self.update_lyr_lookup(data['layer'])

    def update_lyr_lookup(self, layer):
        """Serialize the input layer id (pk), and save it into
        this volume's lookup table."""
        from ohmg.georeference.models.resources import LayerV1

        if isinstance(layer, LayerV1):
            data = layer.serialize(serialize_document=False, include_sessions=True)
        else:
            try:
                data = LayerV1.objects.get(slug=layer).serialize(serialize_document=False, include_sessions=True)
            except Exception as e:
                logger.warn(f"{e} | cannot update_lyr_lookup with this input: {layer} ({type(layer)}")
                return

        # hacky method for pulling out the sheet number from the title
        try:
            data["page_str"] = data['title'].split("|")[-1].split("p")[1]
        except IndexError:
            data["page_str"] = data['title']

        # even more hacky method of creating a sort order from this page_str
        try:
            data['sort_order'] = float(data['page_str'])
        except ValueError:
            if "[" in data['page_str']:
                s = data['page_str'].split("[")
                try:
                    n1 = int(s[0].replace("R","").replace("L",""))
                    n2 = s[1].rstrip("]")
                    data['sort_order'] = float(f"{n1}.{n2}")
                except Exception as e:
                    logger.warn(f"error making sort_order for {data['title']}: {e}")
                    data['sort_order'] = 0
            else:
                data['sort_order'] = 0
        except Exception as e:
            logger.warn(e)
            data['sort_order'] = 0

        self.layer_lookup[data['slug']] = data
        self.save(update_fields=["layer_lookup"])

    def sort_lookups(self):

        sorted_items = {
            "unprepared": [],
            "prepared": [],
            "georeferenced": [],
            "nonmaps": [],
            "processing": {
                "unprep": 0,
                "prep": 0,
                "geo_trim": 0,
            }
        }
        for v in self.document_lookup.values():
            if v['status'] in ["unprepared", "splitting"]:
                sorted_items['unprepared'].append(v)
                if v['status'] == "splitting":
                    sorted_items['processing']['unprep'] += 1
            if v['status'] in ["prepared", "georeferencing"]:
                sorted_items['prepared'].append(v)
                if v['status'] == "georeferencing":
                    sorted_items['processing']['prep'] += 1
            if v['status'] in ["georeferenced", "trimming", "trimmed"]:
                sorted_items['georeferenced'].append(v)
                if v['status'] == "trimming":
                    sorted_items['processing']['geo_trim'] += 1
            if v['status'] == "nonmap":
                sorted_items['nonmaps'].append(v)

        sorted_items['layers'] = list(self.layer_lookup.values())

        sorted_items['unprepared'].sort(key=lambda item: item.get("slug"))
        sorted_items['prepared'].sort(key=lambda item: item.get("slug"))
        sorted_items['georeferenced'].sort(key=lambda item: item.get("slug"))
        sorted_items['layers'].sort(key=lambda item: item.get("slug"))
        sorted_items['nonmaps'].sort(key=lambda item: item.get("slug"))

        return sorted_items

    def get_user_activity_summary(self):

        def _get_session_user_summary(session_dict):
            users = [i['user']['name'] for i in session_dict.values()]
            user_info = [{
                "ct": users.count(i),
                "name": i,
                "profile": reverse('profile_detail', args=(i, ))
            } for i in set(users)]
            user_info.sort(key=lambda item: item.get("ct"), reverse=True)
            return user_info

        prep_sessions, georef_sessions = {}, {}
        for item in list(self.document_lookup.values()) + list(self.layer_lookup.values()):
            for sesh in item['session_data']:
                if sesh['type'] == "Preparation":
                    prep_sessions[sesh['id']] = sesh
                elif sesh['type'] == "Georeference":
                    georef_sessions[sesh['id']] = sesh

        return {
            'prep_ct': len(prep_sessions),
            'prep_contributors': _get_session_user_summary(prep_sessions),
            'georef_ct': len(georef_sessions),
            'georef_contributors': _get_session_user_summary(georef_sessions),
        }

    def serialize(self, include_session_info=False):
        """Serialize this Volume into a comprehensive JSON summary."""

        # a quick, in-place check to see if any layer thumbnails are missing,
        # and refresh that layer lookup if so.
        for k, v in self.layer_lookup.items():
            if "missing_thumb" in v["urls"]["thumbnail"]:
                self.update_lyr_lookup(k)

        # now sort all of the lookups (by status) into a single set of items
        items = self.sort_lookups()

        unprep_ct = len(items['unprepared'])
        prep_ct = len(items['prepared'])
        georef_ct = len(items['georeferenced'])
        percent = 0
        if georef_ct > 0:
            percent = int((georef_ct / (unprep_ct + prep_ct + georef_ct)) * 100)

        # generate extra links and info for the user that loaded the volume
        loaded_by = {"name": "", "profile": "", "date": ""}
        if self.loaded_by is not None:
            loaded_by["name"] = self.loaded_by.username
            loaded_by["profile"] = reverse("profile_detail", args=(self.loaded_by.username, ))
            loaded_by["date"] = self.load_date.strftime("%Y-%m-%d")

        data = {
            "identifier": self.identifier,
            "title": self.__str__(),
            "year": self.year,
            "volume_no": self.volume_no,
            "status": self.status,
            "sheet_ct": {
                "total": self.sheet_ct,
                "loaded": len([i for i in self.sheets if i.doc is not None]),
            },
            "progress": {
                "unprep_ct": unprep_ct,
                "prep_ct": prep_ct,
                "georef_ct": georef_ct,
                "percent": percent,
            },
            "items": items,
            "loaded_by": loaded_by,
            "urls": self.get_urls(),
            "extent": self.extent.extent if self.extent else None,
            "locale": self.get_locale(serialized=True),
            "mosaic_preference": self.mosaic_preference,
            "sponsor": self.sponsor.username if self.sponsor else None,
            "access": self.access,
        }

        if include_session_info:
            data['sessions'] = self.get_user_activity_summary()

        return data

    def save(self, set_slug=False, *args, **kwargs):

        if set_slug or not self.slug:
            self.slug = slugify(self.title, join_char="_")

        return super(self.__class__, self).save(*args, **kwargs)


class Document(models.Model):
    """Documents are the individual source files that are directly attached to Maps.
    They represent pages in an atlas or even just a single scan of a map."""

    slug = models.SlugField(max_length=100)
    map = models.ForeignKey(
        Map,
        on_delete=models.CASCADE,
        related_name="documents"
    )
    page_number = models.CharField(max_length=10, null=True, blank=True)
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
        title = self.map.__str__()
        if self.page_number:
            title += f" {self.map.DOCUMENT_PREFIX_ABBREVIATIONS[self.map.document_page_type]}{self.page_number}"
        return title

    @cached_property
    def image_size(self):
        return get_image_size(Path(self.file.path))

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

        return super(self.__class__, self).save(*args, **kwargs)


class Region(models.Model):

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
        display_name = self.document.__str__()
        if self.division_number:
            display_name += f" [{self.division_number}]"
        return display_name

    @cached_property
    def image_size(self):
        return get_image_size(Path(self.file.path))

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

        return super(self.__class__, self).save(*args, **kwargs)


class Layer(models.Model):

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
        return self.region.__str__()

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

        return super(self.__class__, self).save(*args, **kwargs)
'''
This is a step toward moving database models from the loc_insurancemaps app into
this content app. At present, these are not Django models or even Django proxy models,
just light-weight objects that are instantiated through the Volume and related
models. This will allow the codebase to slowly evolve before actually changing any
database content and running migrations.

The eventual migration plan is this:

ohmg.loc_insurancemaps.models.Volume        --> core.models.Map
ohmg.loc_insurancemaps.models.Sheet         --> core.models.Resource

new model (idea)                            --> core.models.ItemConfigPreset
    This would allow an extraction of Sanborn-specific properties vs. generic item
    uploads. Still unclear exactly what to call this, or everything that it would have.
    Think about this more when the Map model is created, and a hard-look is made at its
    attributes.
'''

import os
import logging
from itertools import chain
from datetime import datetime
from pathlib import Path

from PIL import Image

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
)
from ohmg.core.storages import OverwriteStorage
from ohmg.core.renderers import (
    generate_document_thumbnail_content,
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
    title = models.CharField(max_length=200)
    year = models.IntegerField(blank=True, null=True)
    creator = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200)

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
        on_delete=models.PROTECT,
        related_name="sponsor_user",
    )
    loaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="loaded_by_user"
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
        from ohmg.georeference.models.resources import LayerSet, LayerSetCategory
        try:
            annoset = LayerSet.objects.get(volume=self, category__slug=cat_slug)
        except LayerSet.DoesNotExist:
            if create:
                category = LayerSetCategory.objects.get(slug=cat_slug)
                annoset = LayerSet.objects.create(
                    volume=self,
                    category=category
                )
                logger.debug(f"created new LayerSet: {self.pk} - {cat_slug}")
            else:
                annoset = None
        return annoset

    def get_layersets(self, geospatial:bool=False):
        from ohmg.georeference.models.resources import LayerSet
        sets = LayerSet.objects.filter(volume=self)
        if geospatial:
            sets = sets.filter(category__is_geospatial=True)
        return sets

    def make_sheets(self):

        from ohmg.core.importers.loc_sanborn import LOCParser
        from ohmg.loc_insurancemaps.models import Sheet

        files_to_import = self.lc_resources[0]['files']
        for fileset in files_to_import:
            parsed = LOCParser(fileset=fileset)
            sheet, created = Sheet.objects.get_or_create(
                volume=self,
                sheet_no=parsed.sheet_number,
            )
            sheet.jp2_url = parsed.jp2_url
            sheet.lc_iiif_service = parsed.iiif_service
            sheet.save()

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


class Document(models.Model):
    """Documents are the individual source files that are directly attached to Maps.
    They represent pages in an atlas or even just a single scan of a map."""

    map = models.ForeignKey(Map, on_delete=models.CASCADE)
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

    @property
    def title(self):
        title = self.map.__str__()
        if self.page_number:
            title += f" {self.map.DOCUMENT_PREFIX_ABBREVIATIONS[self.map.document_page_type]}{self.page_number}"
        return title

    def __str__(self):
        return self.title 

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
                self.file.save(f"{slugify(self.title)}.jpg", File(new_file))
            os.remove(jpg_path)

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


class Region(models.Model):

    boundary = models.PolygonField(
        null=True,
        blank=True,
    )
    document = models.ForeignKey(
        "core.Document",
        on_delete=models.CASCADE,
    )
    division_number = models.IntegerField(null=True, blank=True)
    is_map = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    file = models.FileField(
        upload_to='set_upload_location',
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
    gcp_group = models.ForeignKey(
        "georeference.GCPGroup",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        display_name = str(self.document.title)
        if self.division_number:
            display_name += f" [{self.division_number}]"
        return display_name

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
            tname = f"{name}-doc-thumb.jpg"
            self.thumbnail.save(tname, ContentFile(content))


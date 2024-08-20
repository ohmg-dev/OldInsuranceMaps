import os
import json
import logging
from itertools import chain
from datetime import datetime

from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.data import JsonLexer

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Polygon, MultiPolygon
from django.core.files import File
from django.db import transaction
from django.contrib.gis.db import models
from django.utils.safestring import mark_safe
from django.utils.functional import cached_property
from django.urls import reverse

from ohmg.georeference.models import (
    Document,
    LayerV1,
    PrepSession,
    GeorefSession,
    LayerSetCategory,
    LayerSet,
)
from ohmg.georeference.storage import OverwriteStorage
from ohmg.places.models import Place
from ohmg.core.utils import (
    get_jpg_from_jp2_url,
    STATE_CHOICES,
    STATE_ABBREV,
    MONTH_CHOICES,
)
logger = logging.getLogger(__name__)

def find_volume(item):
    """Attempt to get the volume from which a Document or Layer
    is derived. Return None if not applicable/no volume exists."""

    volume, document = None, None
    if isinstance(item, Document):
        document = item
    elif isinstance(item, LayerV1):
        document = item.get_document()

    if document is not None:
        if document.parent:
            document = document.parent
        try:
            volume = Sheet.objects.get(doc=document).volume
        except Sheet.DoesNotExist:
            volume = None
    return volume

def format_json_display(data):
    """very nice from here:
    https://www.laurencegellert.com/2018/09/django-tricks-for-processing-and-storing-json/"""

    content = json.dumps(data, indent=2)

    # format it with pygments and highlight it
    formatter = HtmlFormatter(style='colorful')

    # for some reason this isn't displaying correctly, the newlines and indents are gone.
    # tried JsonLdLexer(stripnl=False, stripall=False) so far but no luck.
    # must have to do with existing styles in GeoNode or something.
    # https://pygments.org/docs/lexers/?highlight=new%20line
    response = highlight(content, JsonLexer(stripnl=False, stripall=False), formatter)
    
    # include the style sheet
    style = "<style>" + formatter.get_style_defs() + "</style><br/>"

    return mark_safe(style + response)


class Sheet(models.Model):
    """Sheet serves mainly as a middle model between Volume and Document.
    It can store fields (like sheet number) that could conceivably be
    attached to the Document, but avoids the need for actually inheriting
    that model (and all of the signals, etc. that come along with it)."""
    doc = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True)
    volume = models.ForeignKey("Volume", on_delete=models.CASCADE)
    sheet_no = models.CharField(max_length=10, null=True, blank=True)
    lc_iiif_service = models.CharField(max_length=150, null=True, blank=True)
    jp2_url = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return f"{self.volume.__str__()} p{self.sheet_no}"

    def load_doc(self, user=None, force_reload: bool=True):

        log_prefix = f"{self.volume} p{self.sheet_no} |"
        logger.info(f"{log_prefix} start load")

        if self.jp2_url is None:
            logger.warn(f"{log_prefix} jp2_url - cancelling download")
            return

        try:
            document = Document.objects.get(title=self.__str__())
        except Document.MultipleObjectsReturned:
            logger.error(f"{self.__str__()} - multiple Documents exist. Delete one and rerun operation.")
            return
        except Document.DoesNotExist:
            document = Document.objects.create(title=self.__str__())
            document.save()

        self.doc = document
        self.save()

        if not self.doc.file:
            jpg_path = get_jpg_from_jp2_url(self.jp2_url, use_cache=not force_reload, force_convert=force_reload)
            with open(jpg_path, "rb") as new_file:
                self.doc.file.save(f"{self.doc.slug}.jpg", File(new_file))

        month = 1 if self.volume.month is None else int(self.volume.month)
        date = datetime(self.volume.year, month, 1, 12, 0)
        self.doc.date = date

        # set owner to user
        if user is None:
            user = get_user_model().objects.get(username="admin")
        self.doc.owner = user

        self.doc.status = "unprepared"
        self.doc.save()

        # self.volume.update_doc_lookup(doc)

    @property
    def real_docs(self):
        """
        This method is a necessary patch for the fact that once a
        Document has been split by the georeferencing tools, its
        children will not be associated with this Sheet.
        """
        documents = []
        if self.doc is not None:
            if self.doc.children:
                documents = self.doc.children
            else:
                documents.append(self.doc)
        return documents

    def serialize(self):
        return {
            "sheet_no": self.sheet_no,
            "sheet_name": self.__str__(),
            "doc_id": self.doc.pk,
        }

def default_ordered_layers_dict():
    return {"layers": [], "index_layers": []}

def default_sorted_layers_dict():
    return {"main": [], "key_map": [], "congested_district": [], "graphic_map_of_volumes": []}

class Volume(models.Model):

    YEAR_CHOICES = [(r,r) for r in range(1867, 1970)]
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

    identifier = models.CharField(max_length=100, primary_key=True)
    city = models.CharField(max_length=100)
    county_equivalent = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=50, choices=STATE_CHOICES)
    year = models.IntegerField(choices=YEAR_CHOICES)
    month = models.IntegerField(choices=MONTH_CHOICES, null=True, blank=True)
    volume_no = models.CharField(max_length=5, null=True, blank=True)
    lc_item = models.JSONField(default=None, null=True, blank=True)
    lc_resources = models.JSONField(default=None, null=True, blank=True)
    lc_manifest_url = models.CharField(max_length=200, null=True, blank=True,
        verbose_name="LC Manifest URL"
    )
    extra_location_tags = models.JSONField(null=True, blank=True, default=list)
    sheet_ct = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])
    loaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="loaded_by"
    )
    load_date = models.DateTimeField(null=True, blank=True)
    # DEPRECATE: marking this field for removal
    ordered_layers = models.JSONField(
        null=True,
        blank=True,
        default=default_ordered_layers_dict
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
    ## after migration to LayerSets ~4/13/24, this field is obsolete and can be removed.
    sorted_layers = models.JSONField(
        default=default_sorted_layers_dict,
    )
    ## after migration to LayerSets ~4/13/24, this field is obsolete and can be removed.
    multimask = models.JSONField(null=True, blank=True)
    locales = models.ManyToManyField(
        Place,
        blank=True,
    )
    ## after migration to LayerSets ~4/13/24, this field is obsolete and can be removed.
    mosaic_geotiff = models.FileField(
        upload_to='mosaics',
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    ## after migration to LayerSets ~4/13/24, this field is obsolete and can be removed.
    mosaic_json = models.FileField(
        upload_to='mosaics',
        null=True,
        blank=True,
        max_length=255,
        storage=OverwriteStorage(),
    )
    ## after migration to LayerSets ~4/13/24, this field is obsolete and can be removed.
    mosaic_preference = models.CharField(
        choices=(('mosaicjson', 'MosaicJSON'), ('geotiff', 'GeoTIFF')),
        default='mosaicjson',
        max_length=20,
    )
    extent = models.PolygonField(
        null=True,
        blank=True,
        srid=4326,
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
        related_name="sponsor",
    )

    def __str__(self):
        display_str = f"{self.city}, {STATE_ABBREV[self.state]} | {self.year}"
        if self.volume_no is not None:
            display_str += f" | Vol. {self.volume_no}"

        return display_str

    @cached_property
    def sheets(self):
        return Sheet.objects.filter(volume=self).order_by("sheet_no")

    @cached_property
    def prep_sessions(self):
        sessions = []
        for sheet in self.sheets:
            if sheet.doc:
                sessions = list(chain(sessions, PrepSession.objects.filter(doc=sheet.doc)))
        return sessions

    @cached_property
    def georef_sessions(self):
        sessions = []
        for doc in self.get_all_docs():
            sessions += list(chain(sessions, GeorefSession.objects.filter(doc=doc)))
        return sessions

    @property
    def gt_exists(self):
        return True if self.get_annotation_set('main-content').mosaic_geotiff else False

    @property
    def mj_exists(self):
        return True if self.get_annotation_set('main-content').mosaic_json else False

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
        main_anno = self.get_annotation_set('main-content')
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

    def lc_item_formatted(self):
        return format_json_display(self.lc_item)
    lc_item_formatted.short_description = 'LC Item'

    def lc_resources_formatted(self):
        return format_json_display(self.lc_resources)
    lc_resources_formatted.short_description = 'LC Resources'

    def document_lookup_formatted(self):
        return format_json_display(self.document_lookup)
    document_lookup_formatted.short_description = 'Document Lookup'

    def layer_lookup_formatted(self):
        return format_json_display(self.layer_lookup)
    layer_lookup_formatted.short_description = 'Layer Lookup'

    def get_annotation_set(self, cat_slug:str, create:bool=False):
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

    def get_annotation_sets(self, geospatial:bool=False):
        sets = LayerSet.objects.filter(volume=self)
        if geospatial:
            sets = sets.filter(category__is_geospatial=True)
        return sets

    def make_sheets(self):

        from ohmg.core.importers.loc_sanborn import LOCParser

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

    def load_sheet_docs(self, force_reload=False):

        self.make_sheets()
        self.update_status("initializing...")
        for sheet in self.sheets:
            if sheet.doc is None or sheet.doc.file is None or force_reload:
                sheet.load_doc(self.loaded_by, force_reload=force_reload)
        self.update_status("ready")
        self.refresh_lookups()

    def remove_sheets(self):

        for s in self.sheets:
            s.delete()

    def update_status(self, status):
        self.status = status
        self.save(update_fields=['status'])
        logger.info(f"{self.__str__()} | status: {self.status}")

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

        loc_item = f"https://loc.gov/item/{self.identifier}",
        try:
            resource_url = self.lc_item['resources'][0]['url']
            if self.sheet_ct > 1:
                resource_url += "?st=gallery"
        except IndexError:
            resource_url = loc_item

        viewer_url = ""
        if self.get_locale():
            viewer_url = reverse("viewer", args=(self.get_locale().slug,)) + f"?{self.identifier}=100"

        return {
            "loc_item": loc_item,
            "loc_resource": resource_url,
            "summary": reverse("map_summary", args=(self.identifier,)),
            "viewer": viewer_url,
        }

    def refresh_lookups(self):
        """Clean and remake document_lookup and layer_lookup fields
        for this Volume by examining the original loaded Sheets and
        re-evaluating every descendant Document and Layer.
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

        if isinstance(document, Document):
            # extreme hack, for some reason serializing the parent during testing causes a
            # failure, because of DocumentLinks not properly finding their targets.
            # DocumentLinks will be removed sooner than later, so leaving this as temp solution for now.
            serialize_parent = False if os.environ.get("TESTING") == "True" else True
            data = document.serialize(serialize_layer=False, serialize_parent=serialize_parent, include_sessions=True)
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

        self.set_extent()

    def set_extent(self):
        # calculate extent from all of the layer extents.
        # perhaps would be better to get this from the Place once that
        # those attributes have been added to those instances.

        layer_extent_polygons = []
        for lyr in self.layer_lookup.values():
            if lyr['extent']:
                poly = Polygon.from_bbox(lyr['extent'])
                layer_extent_polygons.append(poly)
        if len(layer_extent_polygons) > 0:
            multi = MultiPolygon(layer_extent_polygons)
            self.extent = Polygon.from_bbox(multi.extent)
            self.save(update_fields=['extent'])

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
                self.update_layer_lookup(k)

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

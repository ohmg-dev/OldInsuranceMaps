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
import json
import logging
from itertools import chain
from datetime import datetime

from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.data import JsonLexer

from django.conf import settings
from django.contrib.gis.db import models
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.urls import reverse

from ohmg.core.utils import (
    slugify,
    get_jpg_from_jp2_url,
    STATE_ABBREV,
    STATE_POSTAL,
)
from ohmg.core.storages import OverwriteStorage
from ohmg.core.renderers import generate_document_thumbnail_content
from ohmg.loc_insurancemaps.models import Volume
from ohmg.places.models import Place

logger = logging.getLogger(__name__)

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


class Map(object):

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
    publish_date = models.IntegerField(blank=True, null=True)
    volume_no = models.CharField(max_length=5, null=True, blank=True)
    iiif_manifest = models.JSONField(default=None, null=True, blank=True)
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
    def resources(self):
        return Resource.objects.filter(map=self).order_by("page_id")

    @cached_property
    def prep_sessions(self):
        from ohmg.georeference.models.sessions import PrepSession
        sessions = []
        for sheet in self.sheets:
            if sheet.doc:
                sessions = list(chain(sessions, PrepSession.objects.filter(doc=sheet.doc)))
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
        annoset = self.get_annotation_set('main-content')
        if annoset:
            return annoset.extent
        else:
            return None

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
    layer_lookup_formatted.short_description = 'LayerV1 Lookup'

    def get_annotation_set(self, cat_slug:str, create:bool=False):
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

    def get_annotation_sets(self, geospatial:bool=False):
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

    def load_sheet_docs(self, force_reload=False):

        self.make_sheets()
        self.update_status("initializing...")
        for sheet in self.sheets:
            if sheet.doc is None or sheet.doc.file is None or force_reload:
                sheet.load_doc(self.loaded_by)
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


class Resource(object):
    """Resources represent the individual source files that are directly attached to Maps.
    They represent pages in an atlas or even just a single scan of a map."""
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE)
    page_id = models.CharField(max_length=10, null=True, blank=True)
    file = models.FileField(
        upload_to='resources',
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
    load_date = models.DateTimeField(null=True, blank=True)

    @property
    def name(self):
        return f"{self.volume.__str__()} p{self.page_number}"

    def __str__(self):
        return self.name
    
    def download_file(self):

        log_prefix = f"{self.__str__()} |"
        logger.info(f"{log_prefix} start load")

        if not self.source_url:
            logger.warn(f"{log_prefix} no source_url - cancelling download")
            return

        if not self.file:
            jpg_path = get_jpg_from_jp2_url(self.source_url)
            with open(jpg_path, "rb") as new_file:
                self.file.save(f"{slugify(self.name)}.jpg", File(new_file))
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
            tname = f"{name}-res-thumb.jpg"
            self.thumbnail.save(tname, ContentFile(content))


class Place(object):

    PLACE_CATEGORIES = (
        ("state", "State"),
        ("county", "County"),
        ("parish", "Parish"),
        ("borough", "Borough"),
        ("census area", "Census Area"),
        {"independent city", "Independent City"},
        ("city", "City"),
        ("town", "Town"),
        ("village", "Village"),
        ("other", "Other"),
    )

    name = models.CharField(
        max_length = 200,
    )
    category = models.CharField(
        max_length=20,
        choices=PLACE_CATEGORIES,
    )
    display_name = models.CharField(
        max_length = 250,
        editable=False,
        null=True,
        blank=True,
    )
    slug = models.CharField(
        max_length = 250,
        null=True,
        blank=True,
        editable=False,
    )
    volume_count = models.IntegerField(
        default = 0,
        help_text="Number of volumes attached to this place",
    )
    volume_count_inclusive = models.IntegerField(
        default = 0,
        help_text="Number of volumes attached to this place and any of its descendants",
    )
    direct_parents = models.ManyToManyField("Place")

    def __str__(self):
        name = self.display_name if self.display_name else self.name
        return name

    @property
    def state(self):
        states = self.states
        state = None
        if len(states) == 1:
            state = states[0]
        elif len(states) > 1:
            state = states[0]
            logger.info(f"Place {self.pk} has {len(states)} states. Going with {state.slug}")
        return state

    @property
    def states(self):
        candidates = [self]
        states = []
        while candidates:
            new_candidates = []
            for p in candidates:
                if p.category == "state":
                    states.append(p)
                else:
                    for i in p.direct_parents.all():
                        new_candidates.append(i)
            candidates = new_candidates
        return list(set(states))

    def get_volumes(self):
        from ohmg.loc_insurancemaps.models import Volume
        return Volume.objects.filter(locales__id__exact=self.id).order_by("year")

    def get_state_postal(self):
        if self.state and self.state.name.lower() in STATE_POSTAL:
            return STATE_POSTAL[self.state.name.lower()]
        else:
            return None

    def get_state_abbrev(self):
        if self.state and self.state.name.lower() in STATE_ABBREV:
            return STATE_ABBREV[self.state.name.lower()]
        else:
            return None

    def get_descendants(self):
        return Place.objects.filter(direct_parents__id__exact=self.id).order_by("name")

    def get_breadcrumbs(self):
        breadcrumbs = []
        p = self
        while p.direct_parents.all().count() > 0:
            parent = p.direct_parents.all()[0]
            par_name = parent.name
            if parent.category in ("county", "parish", "borough", "census area"):
                par_name += f" {parent.get_category_display()}"
            breadcrumbs.append({"name": par_name, "slug": parent.slug})
            p = parent
        breadcrumbs.reverse()
        name = self.name
        if self.category in ("county", "parish", "borough", "census area"):
            name += f" {self.get_category_display()}"
        breadcrumbs.append({"name": name, "slug": self.slug})
        return breadcrumbs
    
    def get_select_lists(self):
        """
        Returns a dictionary with 4 levels of lists, these are used to populate
        select dropdowns. Each list has both a list of options and also a current
        selection. For example, if this Place object is Madison, WI, the returned
        dictionary would look like this:

        {
            1: {
                "selected": "united-states",
                "options": [
                    <all countries>,
                ],
            },
            2: {
                "selected": "wisconsin",
                "options": [
                    <all US states>
                ],
            },
            3: {
                "selected": "dane-county-wi",
                "options": [
                    <all counties in WI>
                ],
            },
            4: {
                "selected": "madison-wi",
                "options": [
                    <all cities in Dane County>
                ],
            },
        }

        The value --- is used to signify a non-selection in a given category,
        so for the Wisconsin Place instance, the 3rd and 4th entry above would
        have selection: "---".
        
        Note that the selected value will be a slug, while the options
        list contains dictionaries with the following key/values:
        
        "pk", "slug", "display_name", "volume_count_inclusive"
        """

        lists = {
            1: {
                "selected": "---",
                "options": [],
            },
            2: {
                "selected": "---",
                "options": [],
            },
            3: {
                "selected": "---",
                "options": [],
            },
            4: {
                "selected": "---",
                "options": [],
            },
        }

        # take the requested place, and prefill list selections based on its breadcrumbs
        for n, i in enumerate(self.get_breadcrumbs(), start=1):
            lists[n]['selected'] = i['slug']
        
        # at this point, at least a country will be selected, get its pk
        top_pk = Place.objects.get(slug=lists[1]["selected"]).pk

        # always give all of the country options
        all_lvl1 = list(Place.objects.filter(direct_parents=None).values("pk", "slug", "display_name", "volume_count_inclusive"))
        lists[1]["options"] = all_lvl1

        # set level 2 (state) options to only those in this country
        all_lvl2 = list(Place.objects.filter(direct_parents=top_pk).values("pk", "slug", "display_name", "volume_count_inclusive"))
        lists[2]["options"] = all_lvl2

        # if a state is selected, set options to all other states in the same country
        # also, set county/parish and city options for everything within the state
        if lists[2]['selected'] != "---":
            state_pk = Place.objects.get(slug=lists[2]["selected"]).pk
            all_lvl3 = list(Place.objects.filter(direct_parents=state_pk).values("pk", "slug", "display_name", "volume_count_inclusive"))
            lists[3]["options"] = all_lvl3
            lvl3_pks = [i['pk'] for i in all_lvl3]
            all_lvl4 = list(Place.objects.filter(direct_parents__in=lvl3_pks).values("pk", "slug", "display_name", "volume_count_inclusive"))
            lists[4]["options"] = all_lvl4

        # if a county/parish is selected, narrow cities to only those in the county
        if lists[3]['selected'] != "---":
            ce_pk = Place.objects.get(slug=lists[3]["selected"]).pk
            all_lvl4 = list(Place.objects.filter(direct_parents=ce_pk).values("pk", "slug", "display_name", "volume_count_inclusive"))
            lists[4]["options"] = all_lvl4

        for k, v in lists.items():
            v['options'].sort(key=lambda k : k['display_name'])

        return lists

    def get_inclusive_pks(self):
        pks = [self.pk]
        descendants = Place.objects.filter(direct_parents__id__exact=self.id)
        while descendants:
            pks += [i.pk for i in descendants]
            new_descendants = []
            for d in descendants:
                new_descendants += [i for i in Place.objects.filter(direct_parents__id__exact=d.pk)]
            descendants = new_descendants
        return pks

    def serialize(self):
        return {
            "pk": self.pk,
            "name": self.name,
            "display_name": self.display_name,
            "category": self.get_category_display(),
            "parents": [{
                "display_name": i.display_name,
                "slug": i.slug,
            } for i in self.direct_parents.all()],
            "descendants": [{
                "display_name": i.display_name,
                "slug": i.slug,
                "volume_count": i.volume_count,
                "volume_count_inclusive": i.volume_count_inclusive,
                # "has_descendant_maps": i.has_descendant_maps if self.has_descendant_maps else False,
            } for i in self.get_descendants()],
            "states": [{
                "display_name": i.display_name,
                "slug": i.slug,
            } for i in self.states],
            "slug": self.slug,
            "breadcrumbs": self.get_breadcrumbs(),
            "select_lists": self.get_select_lists(),
            "volume_count": self.volume_count,
            "volume_count_inclusive": self.volume_count_inclusive,
            "volumes": [{
                "identifier": i[0],
                "year": i[1],
                "volume_no":i[2]
            } for i in self.get_volumes().values_list("identifier", "year", "volume_no")],
        }

    def save(self, set_slug=True, *args, **kwargs):
        if set_slug is True:
            state_postal = self.get_state_postal()
            state_abbrev = self.get_state_abbrev()
            slug, display_name = "", ""
            if self.category == "state":
                slug = slugify(self.name)
                display_name = self.name
            else:
                if self.category in ["county", "parish", "borough" "census area"]:
                    slug = slugify(f"{self.name}-{self.category}")
                    display_name = f"{self.name} {self.get_category_display()}"
                else:
                    slug = slugify(self.name)
                    display_name = self.name
                if state_postal is not None:
                    slug += f"-{state_postal}"
                if state_abbrev is not None:
                    display_name += f", {state_abbrev}"
            if not slug:
                slug = slugify(self.name)
            if not display_name:
                display_name = self.name
            self.slug = slug
            self.display_name = display_name
        super(Place, self).save(*args, **kwargs)

import os
import json
import uuid
import shutil
import logging
import requests
from datetime import datetime

from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.data import JsonLexer, JsonLdLexer

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import models, transaction
from django.utils.safestring import mark_safe
from django.urls import reverse

from geonode.base.models import Region, License
from geonode.documents.models import Document
from geonode.documents.renderers import generate_thumbnail_content
from geonode.people.models import Profile

from georeference.proxy_models import DocumentProxy, LayerProxy
from georeference.utils import TKeywordManager

from .utils import LOCParser
from .enumerations import (
    STATE_CHOICES,
    STATE_ABBREV,
    MONTH_CHOICES,
)
from .renderers import convert_img_format, generate_full_thumbnail_content

logger = logging.getLogger(__name__)

def get_volume(resource_type, res_id):
    """Attempt to get the volume from which a Document or Layer
    is derived. Return None if not applicable/no volume exists."""

    volume = None
    if resource_type == "document":
        dp = DocumentProxy(res_id)
    elif resource_type == "layer":
        p = LayerProxy(res_id)
        dp = p.get_document_proxy()
    # in some cases this function gets called just before the link between
    # the Layer and the Document has been made. Return None in this case.
    if dp is not None:
        if dp.parent_doc is not None:
            doc = dp.parent_doc.get_document()
        else:
            doc = dp.get_document()

        try:
            volume = Sheet.objects.get(document=doc).volume
        except Sheet.DoesNotExist:
            pass
        except Exception as e:
            logger.error(e)

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

class FullThumbnail(models.Model):

    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="full_thumbs")

    def generate_thumbnail(self):

        if bool(self.document.doc_file) is False:
            return

        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)

        path = f"document-{self.document.uuid}-full-thumb.png"
        content = generate_full_thumbnail_content(self.document)
        self.image.save(path, ContentFile(content))

    def save(self, *args, **kwargs):
        if not self.image:
            self.generate_thumbnail()
        super(FullThumbnail, self).save(*args, **kwargs)


class Sheet(models.Model):
    """Sheet serves mainly as a middle model between Volume and Document.
    It can store fields (like sheet number) that could conceivably be
    attached to the Document, but avoids the need for actually inheriting
    that model (and all of the signals, etc. that come along with it)."""

    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    volume = models.ForeignKey("Volume", on_delete=models.CASCADE)
    sheet_no = models.CharField(max_length=10, null=True, blank=True)
    lc_iiif_service = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return f"{self.volume.__str__()} p{self.sheet_no}"

    def create_from_fileset(self, fileset, volume, user=None):

        temp_img_dir = os.path.join(settings.CACHE_DIR, "img")
        if not os.path.isdir(temp_img_dir):
            os.mkdir(temp_img_dir)

        parsed = LOCParser(fileset=fileset)

        with transaction.atomic():

            ## first, create the sheet and document and link them
            try:
                sheet = Sheet.objects.get(
                    volume=volume,
                    sheet_no=parsed.sheet_number
                )
            except Sheet.DoesNotExist:
                sheet = Sheet(
                    volume=volume,
                    sheet_no=parsed.sheet_number
                )

            doc = Document()
            doc.uuid = str(uuid.uuid4())
            doc.metadata_only = True
            doc.title = sheet.__str__()

            ## make date
            if volume.month is None:
                month = 1
            else:
                month = int(volume.month)
            doc.date = datetime(volume.year, month, 1, 12, 0)

            # set owner to user
            if user is None:
                user = Profile.objects.get(username="admin")
            doc.owner = user

            # set license
            doc.license = License.objects.get(name="Public Domain")

            # a few things need to happen only after the initial save
            doc.save()

            # set the detail_url with the same function that is used in search
            # result indexing. this must be done after the doc has been saved once.
            doc.detail_url = doc.get_absolute_url()

            # m2m regions relation also needs to happen after initial save()
            for r in volume.regions.all():
                doc.regions.add(r)

            sheet.document = doc
            sheet.save()

            ## second, download the file and set it in the Document.
            jp2_url = parsed.jp2_url
            if jp2_url is None:
                logger.warn(f"Sheet {sheet.pk}: No jp2 to download (Document {doc.pk} will be empty)")
            else:
                tmp_path = os.path.join(temp_img_dir, jp2_url.split("/")[-1])

                # basic download code: https://stackoverflow.com/a/18043472/3873885
                response = requests.get(jp2_url, stream=True)
                with open(tmp_path, 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)

                # convert the downloaded jp2 to jpeg (needed for OpenLayers static image)
                jpg_path = convert_img_format(tmp_path, format="JPEG")
                with open(jpg_path, "rb") as new_file:
                    doc.doc_file.save(os.path.basename(jpg_path), File(new_file))

                os.remove(tmp_path)
                os.remove(jpg_path)

            ## this final save will trigger the FullThumbnail creation, now that
            ## the doc has a doc_file attaches.
            doc.save()

            # manually reset the default Geonode thumbnail as well, because
            # its background creation will have failed because it is an async task
            # called from within an async task (i.e. when it's first called,
            # the document hasn't actually been saved to the db yet).
            thumbnail_content = generate_thumbnail_content(doc.doc_file.path)
            filename = f'document-{doc.uuid}-thumb.png'
            doc.save_thumbnail(filename, thumbnail_content)

        return sheet

    @property
    def real_documents(self):
        """
        This method is a necessary patch for the fact that once a
        Document has been split by the georeferencing tools it will no
        longer be properly associated with this Sheet. So a little extra
        parsing must be done to make this a reliable way to get the one
        or more documents in use for this Sheet.
        """

        doc_proxy = DocumentProxy(self.document.id)
        if len(doc_proxy.child_docs) > 0:
            return doc_proxy.child_docs
        else:
            return [doc_proxy]

    def serialize(self):
        return {
            "sheet_no": self.sheet_no,
            "sheet_name": self.__str__(),
            "doc_id": self.document.pk,
        }

def default_ordered_layers_dict():
    return {"layers": [], "index_layers": []}

class Volume(models.Model):

    YEAR_CHOICES = [(r,r) for r in range(1867, 1970)]
    STATUS_CHOICES = (
        ("not started", "not started"),
        ("initializing...", "initializing..."),
        ("started", "started"),
        ("all georeferenced", "all georeferenced"),
    )

    identifier = models.CharField(max_length=100, primary_key=True)
    city = models.CharField(max_length=100)
    county_equivalent = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=50, choices=STATE_CHOICES)
    year = models.IntegerField(choices=YEAR_CHOICES)
    month = models.CharField(max_length=10, choices=MONTH_CHOICES,
        null=True, blank=True)
    volume_no = models.CharField(max_length=5, null=True, blank=True)
    lc_item = JSONField(default=None, null=True, blank=True)
    lc_resources = JSONField(default=None, null=True, blank=True)
    lc_manifest_url = models.CharField(max_length=200, null=True, blank=True,
        verbose_name="LC Manifest URL"
    )
    regions = models.ManyToManyField(
        Region,
        null=True,
        blank=True,
    )
    extra_location_tags = JSONField(null=True, blank=True, default=list)
    sheet_ct = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])
    loaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE)
    load_date = models.DateTimeField(null=True, blank=True)
    ordered_layers = JSONField(
        null=True,
        blank=True,
        default=default_ordered_layers_dict
    )
    document_lookup = JSONField(
        null=True,
        blank=True,
        default=dict,
    )
    layer_lookup = JSONField(
        null=True,
        blank=True,
        default=dict,
    )

    def __str__(self):
        display_str = f"{self.city}, {STATE_ABBREV[self.state]} | {self.year}"
        if self.volume_no is not None:
            display_str += f" | Vol. {self.volume_no}"

        return display_str
    
    def lc_item_formatted(self):
        return format_json_display(self.lc_item)

    lc_item_formatted.short_description = 'LC Item'

    def lc_resources_formatted(self):
        return format_json_display(self.lc_resources)

    lc_resources_formatted.short_description = 'LC Resources'

    def import_sheets(self, user):

        self.update_status("initializing...")
        self.loaded_by = user
        self.load_date = datetime.now()
        self.save(update_fields=["loaded_by", "load_date"])

        try:
            sheets = []
            files_to_import = self.lc_resources[0]['files']
            for n, fileset in enumerate(files_to_import):
                logger.info(f"{self.__str__()} | importing sheet {n+1}/{len(files_to_import)}...")
                sheet = Sheet().create_from_fileset(fileset, self, user)
                sheets.append(sheet)

                # set the status once the Sheet and Document are fully created,
                # which triggers the document's addition Volume.document_lookup
                tkm = TKeywordManager()
                tkm.set_status(sheet.document, "unprepared")

        except Exception as e:
            logger.error(e)
            self.update_status("not started")

        self.update_status("started")
        return sheets

    def update_status(self, status):
        self.status = status
        self.save(update_fields=['status'])
        logger.info(f"{self.__str__()} | status: {self.status}")

    @property
    def sheets(self):
        return Sheet.objects.filter(volume=self)
    
    def get_all_documents(self):
        all_documents = []
        for sheet in self.sheets:
            all_documents += sheet.real_documents
        return all_documents

    def get_urls(self):

        # put these search result urls into Volume.serialize()
        d_facet = f"date__gte={self.year}-01-01T00:00:00.000Z"
        r_facet = f"region__name__in={self.city}"

        loc_item = f"https://loc.gov/item/{self.identifier}",
        try:
            resource_url = self.lc_item['resources'][0]['url']
            if self.sheet_ct > 1:
                resource_url += "?st=gallery"
        except IndexError:
            resource_url = loc_item
        return {
            "doc_search": f"{settings.SITEURL}documents/?{r_facet}&{d_facet}",
            "loc_item": loc_item,
            "loc_resource": resource_url,
            "summary": reverse("volume_summary", args=(self.identifier,))
        }

    def hydrate_ordered_layers(self):

        hydrated = { "layers": [], "index_layers": [] }
        for layer_id in self.ordered_layers["layers"]:
            try:
                hydrated["layers"].append(self.layer_lookup[layer_id])
            except KeyError as e:
                logger.warn(f"{self.__str__()} | layer missing from layer lookup: {layer_id}")
        for layer_id in self.ordered_layers["index_layers"]:
            try:
                hydrated["index_layers"].append(self.layer_lookup[layer_id])
            except KeyError as e:
                logger.warn(f"{self.__str__()} | layer missing from layer lookup: {layer_id}")
        return hydrated

    def populate_lookups(self):
        """Clean and remake document_lookup and layer_lookup fields
        for this Volume by examining the original loaded Sheets and
        re-evaluating every descendant Document and Layer.
        """

        if len(self.document_lookup) > 0 or len(self.layer_lookup) > 0:
            self.document_lookup = {}
            self.layer_lookup = {}
            self.save(update_fields=["document_lookup", "layer_lookup"])

        for document in self.get_all_documents():
            self.update_document_lookup(document.id, update_layer=True)

    def update_document_lookup(self, doc_id, update_layer=False):
        """Take the input document id (pk), get the serialized DocumentProxy
        content and save it back to the lookup table."""

        doc_proxy = DocumentProxy(doc_id)
        doc_json = doc_proxy.serialize()

        # hacky method for pulling out the sheet number from the doc title
        try:
            page_str = doc_proxy.title.split("|")[-1].split("p")[1]
        except IndexError:
            page_str = doc_proxy.title
        doc_json["page_str"] = page_str

        # replace default thumbnail with FullThumbnail if present
        full_thumbs = FullThumbnail.objects.filter(document_id=doc_id)
        if len(full_thumbs) > 0:
            thumb = list(full_thumbs)[0]
            doc_json['urls']['thumbnail'] = thumb.image.url

        self.document_lookup[doc_id] = doc_json
        self.save(update_fields=["document_lookup"])

        if update_layer is True:
            self.update_layer_lookup(doc_proxy=doc_proxy)

    def update_layer_lookup(self, layer_alternate=None, doc_proxy=None):
        """Pass either a layer alternate or an instance of DocumentProxy. The
        latter is specifically to allow this method to be called from within
        update_document_lookup() in the most efficient manner.

        If both are passed in, only layer_alternate will used."""

        lp = None
        if layer_alternate is not None:
            lp = LayerProxy(layer_alternate)
        elif doc_proxy is not None:
            lp = doc_proxy.get_layer_proxy()

        if lp is not None:
            layer_json = lp.serialize()
            layer_json["page_str"] = lp.title

            self.layer_lookup[lp.alternate] = layer_json
            self.save(update_fields=["layer_lookup"])

            # add layer id to ordered_layers list if its not yet there
            existing = self.ordered_layers["layers"] + self.ordered_layers["index_layers"]
            if not lp.alternate in existing:
                self.ordered_layers["layers"].append(lp.alternate)
                self.save(update_fields=["ordered_layers"])

    def sort_lookups(self):

        sorted_items = {tk: [] for tk in TKeywordManager().lookup.keys()}
        for v in self.document_lookup.values():
            if v['status'] is not None:
                sorted_items[v['status']].append(v)

        sorted_items['layers'] = list(self.layer_lookup.values())
        return sorted_items

    def serialize(self):
        """Serialize this Volume into a comprehensive JSON summary."""

        # a quick, in-place check to see if any layer thumbnails are missing,
        # and refresh that layer lookup if so.
        for k, v in self.layer_lookup.items():
            if "missing_thumb" in v["urls"]["thumbnail"]:
                self.update_layer_lookup(k)

        # now sort all of the lookups (by status) into a single set of items
        items = self.sort_lookups()

        # generate extra links and info for the user that loaded the volume
        loaded_by = {"name": "", "profile": "", "date": ""}
        if self.loaded_by is not None:
            loaded_by["name"] = self.loaded_by.username
            loaded_by["profile"] = reverse("profile_detail", args=(self.loaded_by.username, ))
            loaded_by["date"] = self.load_date.strftime("%Y-%m-%d")

        # hydrate ordered_layers
        ordered_layers = self.hydrate_ordered_layers()

        return {
            "identifier": self.identifier,
            "title": self.__str__(),
            "status": self.status,
            "sheet_ct": {
                "total": self.sheet_ct,
                "loaded": len(self.sheets),
            },
            "items": items,
            "loaded_by": loaded_by,
            "urls": self.get_urls(),
            "ordered_layers": ordered_layers,
        }

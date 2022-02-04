import os
import json
# import pytz
import time
import uuid
import shutil
import requests
from datetime import datetime

from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.data import JsonLexer, JsonLdLexer

from django.db import models, transaction
from django.db.models import signals
from django.conf import settings
from django.urls import reverse
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import Group
from django.core.files import File
from django.core.files.base import ContentFile
from django.utils.safestring import mark_safe

from geonode.base.models import Region, License, Link, ThesaurusKeyword, Thesaurus
from geonode.documents.models import DocumentResourceLink
from geonode.layers.models import Layer
from geonode.documents.models import (
    Document,
    pre_save_document,
    post_save_document,
    pre_delete_document,
)
from geonode.maps.signals import map_changed_signal
from geonode.people.models import Profile

from georeference.models import SplitDocumentLink
from georeference.proxy_models import DocumentProxy, LayerProxy
from georeference.utils import TKeywordManager

from .utils import LOCParser
from .enumerations import (
    STATE_CHOICES,
    STATE_ABBREV,
    MONTH_CHOICES,
)
from .renderers import convert_img_format, generate_full_thumbnail_content

def get_volume(resource_type, res_id):

    if resource_type == "document":
        dp = DocumentProxy(res_id)
    elif resource_type == "layer":
        p = LayerProxy(res_id)
        dp = p.get_document_proxy()
    if dp.parent_doc is not None:
        doc = dp.parent_doc.get_document()
    else:
        doc = dp.get_document()
    volume = Sheet.objects.get(document=doc).volume
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

        ## This is a tricky situation. With the atomic block, everything is saved at once
        ## which is very desirable, and causes sheets to appear on the volume summary page
        ## when they are ready (keyword set, full thumbnail made). However, within this block
        ## the action of saving the doc file seems to trigger the default geonode thumbnail
        ## creation, which forks its own background process and begins trying to find the
        ## Document immediately, causing a number of errors and retries until the document
        ## does exist. Reorganizing this would be really good, but it must be done in tandem
        ## with the collection methods that bring the documents to the Volume summary page.
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

            doc.tkeywords.add(ThesaurusKeyword.objects.get(about="unprepared"))

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
                print("no jp2 file to download, aborting document creation")

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

                try:
                    thumb = FullThumbnail.objects.get(document=doc)
                except FullThumbnail.DoesNotExist:
                    thumb = FullThumbnail(document=doc)
                    thumb.save()
            doc.save()

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
    index_layers = models.ManyToManyField(
        Layer,
        null=True,
        blank=True
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

        self.status = "initializing..."
        self.loaded_by = user
        self.load_date = datetime.now()
        self.save()

        print("importing all sheeets")

        try:
            sheets = []
            for fileset in self.lc_resources[0]['files']:
                print("importing sheet...")
                sheet = Sheet().create_from_fileset(fileset, self, user)
                sheets.append(sheet)                
        except Exception as e:
            print(e)
            self.status = "not started"
            self.save()

        self.status = "started"
        self.save()
        return sheets

    @property
    def sheets(self):
        return Sheet.objects.filter(volume=self)
    
    def get_all_documents(self):
        all_documents = []
        for sheet in self.sheets:
            all_documents += sheet.real_documents

        return all_documents

    def serialize_items(self):

        tkm = TKeywordManager()
        sorted_items = {tk: [] for tk in tkm.lookup.keys()}
        sorted_items['layers'] = []

        for doc_proxy in self.get_all_documents():
            if doc_proxy.status is None:
                continue
            try:
                thumb = FullThumbnail.objects.get(document=doc_proxy.resource)
            except FullThumbnail.DoesNotExist:
                thumb = FullThumbnail(document=doc_proxy.resource)
                thumb.save()

            doc_json = doc_proxy.serialize()

            try:
                doc_json["urls"]["thumbnail"] = thumb.image.url
            except ValueError:
                doc_json["urls"]["thumbnail"] = ""

            # hacky method for pulling out the sheet number from the doc title
            try:
                page_str = doc_proxy.title.split("|")[-1].split("p")[1]
            except IndexError:
                page_str = doc_proxy.title
            doc_json["page_str"] = page_str

            sorted_items[doc_proxy.status].append(doc_json)

            layer_proxy = doc_proxy.get_layer_proxy()
            if not layer_proxy is None:
                layer_json = layer_proxy.serialize()
                layer_json["page_str"] = page_str
                sorted_items['layers'].append(layer_json)

            continue

        return sorted_items

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

    def serialize(self):
        items = self.serialize_items()
        items_ct = sum([len(v) for v in items.values()])
        if self.loaded_by is None:
            loaded_by = {"name": "", "profile": "", "date": ""}
        else:
            loaded_by = {
                "name": self.loaded_by.username,
                "profile": reverse("profile_detail", args=(self.loaded_by.username, )),
                "date": self.load_date.strftime("%Y-%m-%d"),
            }
        index_layers = [LayerProxy(i.alternate) for i in self.index_layers.all()]
        index_layers_json = [i.serialize() for i in index_layers]
        return {
            "identifier": self.identifier,
            "title": self.__str__(),
            "status": self.status,
            "sheet_ct": {
                "total": self.sheet_ct,
                "loaded": len(self.sheets),
            },
            "items_ct": items_ct,
            "items": items,
            "loaded_by": loaded_by,
            "urls": self.get_urls(),
            "index_layers": index_layers_json,
        }

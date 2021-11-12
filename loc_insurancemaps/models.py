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

from .utils import LOCParser
from .enumerations import (
    STATE_CHOICES,
    MONTH_CHOICES,
)
from .renderers import convert_img_format, generate_full_thumbnail_content

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

        with transaction.atomic():

            parsed = LOCParser().parse_fileset(fileset)

            try:
                sheet = Sheet.objects.get(
                    volume=volume,
                    sheet_no=parsed["sheet_number"]
                )
            except Sheet.DoesNotExist:
                sheet = Sheet(
                    volume=volume,
                    sheet_no=parsed["sheet_number"]
                )
            doc = Document()

            doc.uuid = str(uuid.uuid4())

            if user is None:
                user = Profile.objects.get(username="admin")
            doc.owner = user

            jp2_url = parsed["jp2_url"]
            if jp2_url is not None:
                tmp_path = os.path.join(temp_img_dir, jp2_url.split("/")[-1])

                # basic download code: https://stackoverflow.com/a/18043472/3873885
                response = requests.get(jp2_url, stream=True)
                with open(tmp_path, 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)
                del response

                # convert the downloaded jp2 to jpeg (needed for OpenLayers static image)
                jpg_path = convert_img_format(tmp_path, format="JPEG")

                with open(jpg_path, "rb") as new_file:
                    doc.doc_file.save(os.path.basename(jpg_path), File(new_file))

                os.remove(tmp_path)
                os.remove(jpg_path)

                doc.save()

            sheet.document = doc
            sheet.sheet_no = parsed["sheet_number"]
            sheet.iiif_service = parsed["iiif_service"]
            sheet.save()

            doc.title = sheet.__str__()
            doc.date = datetime(volume.year, 1, 1)
            for r in volume.regions.all():
                doc.regions.add(r)
            # set the detail_url with the same function that is used in search
            # result indexing. this must be done after the doc has been saved once.
            doc.detail_url = doc.get_absolute_url()
            doc.save()

            doc.tkeywords.add(ThesaurusKeyword.objects.get(about="unprepared"))

            thumb = FullThumbnail(document=doc)
            thumb.save()

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

        sgt = Thesaurus.objects.get(identifier="sgt")
        sgt_keywords = ThesaurusKeyword.objects.filter(thesaurus=sgt)

        for tk in self.document.tkeywords.all():
            if tk in sgt_keywords:
                return [self.document]
        
        ## if tk is in the status dict set, then further checking needed
        links = SplitDocumentLink.objects.filter(document=self.document)
        documents = [Document.objects.get(pk=i.object_id) for i in links]
        return documents

    def to_json(self):
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

    def __str__(self):

        display_str = f"{self.city}, {self.get_state_display()} | {self.year}"
        if self.volume_no is not None:
            display_str += f" | Vol. {self.volume_no}"

        return display_str
    
    def lc_item_formatted(self):
        return format_json_display(self.lc_item)

    lc_item_formatted.short_description = 'LC Item'

    def lc_resources_formatted(self):
        return format_json_display(self.lc_resources)

    lc_resources_formatted.short_description = 'LC Resources'
    
    def create_from_lc_json(self, response):

        parsed = LOCParser().parse_item(response['item'], include_regions=True)

        with transaction.atomic():

            try:
                vol = Volume.objects.get(identifier=parsed['id'])
            except Volume.DoesNotExist:
                vol = Volume()
                vol.identifier = parsed['id']

            vol.lc_item = response['item']
            vol.lc_resources = response['resources']

            vol.city = parsed['city']
            vol.county_equivalent = parsed['county_eq']
            vol.state = parsed['state']
            vol.year = parsed['year']
            vol.month = parsed['month']
            vol.volume_no = parsed['volume_no']
            vol.extra_location_tags = parsed['extra_location_tags']

            vol.lc_manifest_url = parsed["lc_manifest_url"]

            vol.sheet_ct = parsed['sheet_ct']

            vol.save()

            for r in parsed['regions']:
                vol.regions.add(r)

        return vol

    def import_sheets(self, user):

        self.status = "initializing..."
        self.loaded_by = user
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
    
    @property
    def sheets_json(self):
        return [i.to_json() for i in self.sheets]
    
    @property
    def documents_json(self):

        sgt = Thesaurus.objects.get(identifier="sgt")
        sgt_keywords = ThesaurusKeyword.objects.filter(thesaurus=sgt)

        documents = []
        for sheet in self.sheets:
            documents += sheet.real_documents

        sorted_items = {tk.about: [] for tk in sgt_keywords}
        sorted_items['layers'] = []
        layers = []
        for document in documents:
            try:
                thumb = FullThumbnail.objects.get(document=document)
            except FullThumbnail.DoesNotExist:
                thumb = FullThumbnail(document=document)
                thumb.save()

            detail_url = reverse('document_detail', args=(document.id,))
            split_url = reverse('split_view', args=(document.id,))
            georeference_url = reverse('georeference_view', args=(document.id,))

            # hacky method for pulling out the sheet number from the doc title
            try:
                page_str = document.title.split("|")[1].split("p")[1]
            except IndexError:
                page_str = document.title

            doc_json = {
                "id": document.pk,
                "title": document.title,
                "page_str": page_str,
                "urls": {
                    "detail": detail_url,
                    "thumbnail": thumb.image.url,
                    "split": split_url,
                    "georeference": georeference_url,
                }
            }

            for tk in document.tkeywords.all():
                if tk in sgt_keywords:
                    sorted_items[tk.about].append(doc_json)

            ## must also collect layers resulting from georeferenced documents
            if "georeferenced" in [tk.about for tk in document.tkeywords.all()]:
                layer = None
                links = DocumentResourceLink.objects.filter(document=document)
                for link in links:
                    obj = link.content_type.get_object_for_this_type(pk=link.object_id)
                    if isinstance(obj, Layer):
                        layer = obj
                        break
                if layer is not None:
                    trim_url = reverse('trim_view', args=(layer.alternate,))
                    detail_url = reverse('layer_detail', args=(layer.alternate,))
                    layer_json = {
                        "id": layer.pk,
                        "title": layer.title,
                        "page_str": page_str,
                        "urls": {
                            "detail": detail_url,
                            "thumbnail": layer.thumbnail_url,
                            "georeference": georeference_url,
                            "trim": trim_url,
                        }
                    }
                    sorted_items["layers"].append(layer_json)

        return sorted_items

    def to_json(self):
        items = self.documents_json
        items_ct = sum([len(v) for v in items.values()])
        if self.loaded_by is None:
            loaded_by = ""
            loaded_by_url = ""
        else:
            loaded_by = self.loaded_by.username
            loaded_by_url = reverse("profile_detail", args=(self.loaded_by.username, ))
        return {
            "identifier": self.identifier,
            "title": self.__str__(),
            "status": self.status,
            "sheet_ct": self.sheet_ct,
            "items_ct": items_ct,
            "items": items,
            "loc_url": f"https://loc.gov/item/{self.identifier}",
            "loaded_by": loaded_by,
            "loaded_by_url": loaded_by_url,
        }

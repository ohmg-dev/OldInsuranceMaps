import os
import json
# import pytz
import time
import uuid
import shutil
import requests
# from datetime import datetime

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
from django.utils.safestring import mark_safe

from geonode.base.models import License, Link, resourcebase_post_save
from geonode.documents.models import (
    Document,
    pre_save_document,
    post_save_document,
    pre_delete_document,
)
from geonode.maps.signals import map_changed_signal
from geonode.people.models import Profile

from .utils import enumerations, parsers
from .renderers import convert_img_format
from .api import APIConnection

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

    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    volume = models.ForeignKey("Volume", on_delete=models.CASCADE)
    sheet_no = models.CharField(max_length=10, null=True, blank=True)
    lc_iiif_service = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return f"{self.volume.__str__()} p{self.sheet_no}"

    def create_from_fileset(self, fileset, volume):

        with transaction.atomic():
            sheet = Sheet()
            sheet.volume = volume

            doc = Document()

            doc.uuid = str(uuid.uuid4())
            doc.owner = Profile.objects.get(username="admin")

            jp2_url = None
            iiif_service = None
            for f in fileset:
                if f['mimetype'] == "image/jp2":
                    jp2_url = f['url']
                    filename = f['url'].split("/")[-1]
                    name, ext = os.path.splitext(filename)
                    number = name.split("-")[-1].lstrip("0")
                if 'image-services' in f['url'] and '/full/' in f['url']:
                    iiif_service = f['url'].split("/full/")[0]

            if iiif_service is not None:
                sheet.iiif_service = iiif_service

            sheet.sheet_no = number

            if jp2_url:
                tmp_path = os.path.join(settings.CACHE_DIR, "img", jp2_url.split("/")[-1])

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
            sheet.save()

            doc.title = sheet.__str__()
            # set the detail_url with the same function that is used in search
            # result indexing. this must be done after the doc has been saved once.
            doc.detail_url = doc.get_absolute_url()
            doc.save()


        return sheet


class Volume(models.Model):

    identifier = models.CharField(max_length=100, primary_key=True)
    city = models.CharField(max_length=100)
    county_equivalent = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=50, choices=enumerations.STATE_CHOICES)
    year = models.IntegerField(choices=enumerations.YEAR_CHOICES)
    month = models.CharField(max_length=10, choices=enumerations.MONTH_CHOICES,
        null=True, blank=True)
    volume_no = models.CharField(max_length=5, null=True, blank=True)
    lc_item = JSONField(default=None, null=True, blank=True)
    lc_resources = JSONField(default=None, null=True, blank=True)
    lc_manifest_url = models.CharField(max_length=200, null=True, blank=True,
        verbose_name="LC Manifest URL"
    )
    # sheets = models.ManyToManyField(Sheet, blank=True)
    sheet_ct = models.IntegerField(null=True, blank=True)

    def __str__(self):

        display_str = f"{self.city}, {self.get_state_display()} | {self.year}"
        if self.volume_no is not None:
            display_str += f" | Vol. {self.volume_no}"

        return display_str
    
    def set_lc_item_and_lc_resources(self):

        lc = APIConnection()
        data = lc.get_item(self.identifier)
        self.lc_resources = data['resources']
        self.save()
    
    def lc_item_formatted(self):
        return format_json_display(self.lc_item)

    lc_item_formatted.short_description = 'LC Item'

    def lc_resources_formatted(self):
        return format_json_display(self.lc_resources)

    lc_resources_formatted.short_description = 'LC Resources'
    
    def create_from_lc_json(self, item, dry_run=False):

        identifier = item["id"].rstrip("/").split("/")[-1]

        location_info = parsers.parse_location_info(item)
        date_info = parsers.parse_date_info(item)
        volume_no = parsers.parse_volume_number(item)

        with transaction.atomic():

            try:
                vol = Volume.objects.get(identifier=identifier)
            except Volume.DoesNotExist:
                vol = Volume()
                vol.identifier = identifier

            vol.city = location_info['city']
            vol.county_equivalent = location_info['county_equivalent']
            vol.state = location_info['state']
            vol.year = date_info['year']
            vol.month = date_info['month']
            vol.volume_no = volume_no

            vol.lc_manifest_url = f'{item["url"]}manifest.json'
            vol.lc_item = item

            if len(item["resources"]) > 0:
                vol.sheet_ct = item["resources"][0]["files"]

            if dry_run is False:
                vol.save()

        return vol
    
    def get_sheets(self, dry_run=False):

        if self.lc_resources is None:
            lc = APIConnection()
            data = lc.get_item(self.identifier)
            self.lc_resources = data['resources']
            self.save()

        for fileset in self.lc_resources[0]['files']:
            sheet = Sheet().create_from_fileset(fileset, self)

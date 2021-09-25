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

from geonode.base.models import Region, License, Link, resourcebase_post_save
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

    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    volume = models.ForeignKey("Volume", on_delete=models.CASCADE)
    sheet_no = models.CharField(max_length=10, null=True, blank=True)
    lc_iiif_service = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return f"{self.volume.__str__()} p{self.sheet_no}"

    def create_from_fileset(self, fileset, volume, fileset_info=None):

        with transaction.atomic():
            sheet = Sheet()
            sheet.volume = volume

            doc = Document()

            doc.uuid = str(uuid.uuid4())
            doc.owner = Profile.objects.get(username="admin")

            if fileset_info is None:
                fileset_info = parsers.parse_fileset(fileset)
            
            sheet.sheet_no = fileset_info["sheet_number"]
            sheet.iiif_service = fileset_info["iiif_service"]

            jp2_url = fileset_info["jp2_url"]
            if jp2_url is not None:
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
    regions = models.ManyToManyField(
        Region,
        null=True,
        blank=True,
    )
    extra_location_tags = JSONField(null=True, blank=True, default=list)
    sheet_ct = models.IntegerField(null=True, blank=True)

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
    
    def create_from_lc_json(self, item):

        identifier = parsers.parse_item_identifier(item)

        location_info = parsers.parse_location_info(item, include_regions=True)
        date_info = parsers.parse_date_info(item)
        volume_no = parsers.parse_volume_number(item)
        sheet_ct = parsers.parse_sheet_count(item)

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
            vol.extra_location_tags = location_info['extra']

            vol.lc_manifest_url = f'{item["url"]}manifest.json'
            vol.lc_item = item

            vol.sheet_ct = sheet_ct

            vol.save()

            for r in location_info['regions']:
                vol.regions.add(r)

        return vol

    def to_json(self):

        return {
            "identifier": self.identifier,
            "title": self.__str__(),
            # etc
        }
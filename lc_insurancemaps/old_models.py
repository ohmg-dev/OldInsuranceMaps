"""keeping this file around because there may be useful content related
to thumbnails, notifications, and more. but the MapScan and MapCollectionItem
models are no longer in use."""

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

## DEPRECATED, replaced by Sheet
class MapScan(Document):

    external_id = ""
    # volume = models.ForeignKey("MapCollectionItem", on_delete=models.CASCADE)
    sheet_no = models.CharField(max_length=100, null=True, blank=True)
    loc_type = models.CharField(max_length=25, null=True, blank=True)
    loc_json = JSONField(default=None, null=True, blank=True)
    is_index = models.BooleanField(default=False, null=True, blank=True)
    parent_sheet = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    iiif_service = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):

        # if not self.volume:
        #     return self.doi

        display_str = f"{self.volume.city}, {self.volume.state} | {self.volume.year}"
        if self.volume.volume_no is not None:
            display_str += f" | Vol. {self.volume.volume_no}"
        if self.sheet_no is not None:
            display_str += f" p{self.sheet_no}"

        return display_str

    def get_absolute_url(self):
        ''' this function is used by the indexing process to get the link url
        that appears in the search results '''
        return reverse('sheet_detail', args=(self.doi,))

    def create_object(self, fileset, volume):

        new_scan = MapScan()

        new_scan.uuid = str(uuid.uuid4())

        new_scan.add_volume(volume)
        new_scan.process_fileset(fileset)

        new_scan.save()

    def process_fileset(self, fileset):

        jp2_url = None
        iiif_service = None
        for f in fileset:
            if f['mimetype'] == "image/jp2":
                jp2_url = f['url']
                filename = f['url'].split("/")[-1]
                name, ext = os.path.splitext(filename)
                sheet = name.split("-")[-1].lstrip("0")
            if 'image-services' in f['url'] and '/full/' in f['url']:
                iiif_service = f['url'].split("/full/")[0]

        if iiif_service is not None:
            self.iiif_service = iiif_service

        self.sheet_no = sheet
        self.doi = name

        # set the detail_url with the same function that is used in search
        # result indexing
        self.detail_url = self.get_absolute_url()

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
                self.doc_file.save(os.path.basename(jpg_path), File(new_file))

            os.remove(tmp_path)
            os.remove(jpg_path)

        self.loc_type = "sheet"

    def add_volume(self, volume_obj):

        self.volume = volume_obj
        self.owner = self.volume.owner
        self.license = self.volume.license

## DEP[RECATED, replaced by Volume
class MapCollectionItem(Document):

    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=50, choices=enumerations.STATE_CHOICES)
    year = models.IntegerField(choices=enumerations.YEAR_CHOICES)
    month = models.CharField(max_length=10, choices=enumerations.MONTH_CHOICES,
        null=True, blank=True)
    volume_no = models.CharField(max_length=5, null=True, blank=True)
    loc_json = JSONField(default=None, null=True, blank=True)
    file_count = models.IntegerField(null=True, blank=True)
    iiif_manifest = models.CharField(max_length=200, null=True, blank=True)
    loc_type = models.CharField(max_length=25, null=True, blank=True)

    def get_absolute_url(self):
        ''' this function is used by the indexing process to get the link url
        that appears in the search results '''
        return reverse('volume_detail', args=(self.doi,))

    def __str__(self):

        display_str = f"{self.city}, {self.state} | {self.year}"
        if self.volume_no is not None:
            display_str += f" | Vol. {self.volume_no}"

        return display_str

    @property
    def display_date(self):
        if self.month is not None:
            return f"{self.month} {self.year}"
        else:
            return f"{self.year}"

    def create_from_json(self, item, owner=None, get_sheets=False):

        new_item = MapCollectionItem()

        new_item.loc_type = "volume"

        new_item.uuid = str(uuid.uuid4())

        if owner is None:
            owner = Profile.objects.get(username="admin")
        new_item.owner = owner

        # group = Group.objects.get(name="anonymous")
        # new_item.group = group

        license = License.objects.get(name="Public Domain")
        new_item.license = license

        location_info = parsers.parse_location_info(item)
        new_item.city = location_info['city']
        new_item.county = location_info['county']
        new_item.state = location_info['state']

        date_info = parsers.parse_date_info(item)
        new_item.date = date_info['datetime']
        new_item.year = date_info['year']
        new_item.month = date_info['month']

        new_item.doi = item["id"].rstrip("/").split("/")[-1]

        # set the local detail_url by reversing the path defined in urls.py
        new_item.detail_url = self.get_absolute_url()

        # set all external (LoC) url references
        new_item.doc_url = item["url"]
        new_item.iiif_manifest = f'{item["url"]}/manifest.json'

        if len(item["resources"]) > 0:
            new_item.file_count = item["resources"][0]["files"]

        # find the volume number in the publishing notes
        if "vol." in item["item"]["created_published"].lower():
            a = item["item"]["created_published"].lower().split("vol.")[1]
            b = a.lstrip(" ").split(" ")
            volume = b[0]
            # volume = pub[pub.index("vol.") + 1]
            new_item.volume_no = volume

        new_item.title = new_item.__str__()

        img_url = None
        for url in item["image_url"]:
            if ".jpg" in url and "pct:12.5" in url:
                img_url = url


        # this should be cleaned up, not sure that this image is really necessary
        # to retain, but currently it's used later for the thumbnail
        if img_url:

            cache_img_dir = os.path.join(settings.CACHE_DIR, "img")
            if not os.path.isdir(cache_img_dir):
                os.mkdir(cache_img_dir)
            down_path = os.path.join(cache_img_dir, new_item.doi + "__vol.jpg")


            # basic download code: https://stackoverflow.com/a/18043472/3873885
            response = requests.get(img_url, stream=True)
            with open(down_path, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            del response

            with open(down_path, "rb") as new_file:
                new_item.doc_file.save(os.path.basename(down_path), File(new_file))

        new_item.save()

        return new_item

    def get_all_sheets(self):

        if self.loc_json is None:
            print("ERROR: empty loc_json")
            return False

        for fileset in self.loc_json["resources"][0]['files']:

            new_scan = MapScan().create_object(fileset, self)

        return True


def _collection_thumbnail(sender, instance, created, **kwargs):

    if instance.thumbnail_url is not None:
        return

    from .tasks import create_collection_item_thumbnail
    result = create_collection_item_thumbnail.delay(object_id=instance.id)
    # Attempt to run task synchronously
    result.get()

def _map_sheet_thumbnail(sender, instance, created, **kwargs):

    if not instance.iiif_service:
        return

    from .tasks import create_map_sheet_thumbnail
    result = create_map_sheet_thumbnail.delay(object_id=instance.id)
    # Attempt to run task synchronously
    result.get()

def set_map_scan_title(sender, instance, **kwargs):

    instance.title = instance.__str__()


# not yet in use - having some issues with this error when this is hooked up:
# ---
# django.db.utils.IntegrityError: insert or update on table "lc_insurancemaps_mapscan" violates
# foreign key constraint "lc_insurancemaps_mapscan_document_ptr_id_5805d0e2_fk_documents"
# DETAIL:  Key (document_ptr_id)=(624) is not present in table "documents_document".
def delete_files(sender, instance, **kwargs):

    instance.doc_file.delete()
    Link.objects.filter(resource=instance, name='Thumbnail').delete()

signals.pre_save.connect(pre_save_document, sender=MapCollectionItem)
# signals.post_save.connect(create_collection_thumbnail, sender=MapCollectionItem)
signals.post_save.connect(_collection_thumbnail, sender=MapCollectionItem)
signals.post_save.connect(post_save_document, sender=MapCollectionItem)
signals.post_save.connect(resourcebase_post_save, sender=MapCollectionItem)
signals.pre_delete.connect(pre_delete_document, sender=MapCollectionItem)
# signals.post_delete.connect(delete_files, sender=MapCollectionItem)

signals.pre_save.connect(pre_save_document, sender=MapScan)
signals.pre_save.connect(set_map_scan_title, sender=MapScan)
signals.post_save.connect(_map_sheet_thumbnail, sender=MapScan)
signals.post_save.connect(post_save_document, sender=MapScan)
signals.post_save.connect(resourcebase_post_save, sender=MapScan)
signals.pre_delete.connect(pre_delete_document, sender=MapScan)
# signals.post_delete.connect(delete_files, sender=MapScan)

# ! pretty sure this last one doesn't need to be included here
# map_changed_signal.connect(update_documents_extent)

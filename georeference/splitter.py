import os
import logging
from copy import copy
from PIL import Image, ImageDraw, ImageFilter

from django.conf import settings
from django.core.files import File

from geonode.documents.models import Document

from .models import SplitLink, SplitSession
from .utils import (
    cut_geometry_by_lines,
    transform_coordinates,
    make_border_geometery,
)

logger = logging.getLogger(__name__)

class DocumentSplitter(object):

    def __init__(self, document=None, user=None):

        self.document = document
        self.doc_title = copy(document.title)
        self.img_file = self.document.doc_file.path
        self.border_geom = make_border_geometery(self.img_file)
        self.created_by = user
        self.session = SplitSession(document=document)
        self.divisions = []

        if os.path.isdir(settings.TEMP_DIR) is False:
            os.mkdir(settings.TEMP_DIR)
        self.temp_dir = settings.TEMP_DIR

    def generate_divisions(self, cutlines):

        self.divisions = cut_geometry_by_lines(self.border_geom, cutlines)

        return self.divisions

    def save_new_document(self, file_path):

        link_no = SplitLink.objects.filter(parent_doc=self.document).count() + 1

        fname = os.path.basename(file_path)
        new_doc = Document.objects.get(pk=self.document.pk)
        new_doc.pk = None
        new_doc.id = None
        new_doc.uuid = None
        new_doc.thumbnail_url = None
        new_doc.title = f"{self.doc_title} [{link_no}]"
        with open(file_path, "rb") as openf:
            new_doc.doc_file.save(fname, File(openf))
        new_doc.save()

        return new_doc

    def split_image(self):
        """ """

        # update the session info, now that it's about to be run
        print("splitting image...")
        self.session.divisions = self.divisions
        self.session.created_by = self.created_by
        self.session.save()

        img = Image.open(self.img_file)
        w, h = img.size

        for n, shape in enumerate(self.divisions):

            coords = transform_coordinates(shape, h)

            # future reference: this is a small rect. in the top left of the image
            # coords = [(0, 100), (50,100), (50, 0), (0, 0)]

            im_a = Image.new("L", img.size, 0)
            draw = ImageDraw.Draw(im_a)
            draw.polygon(coords, fill=255)

            im_blur = im_a.filter(ImageFilter.GaussianBlur(2))

            im_inset = img.copy()
            im_inset.putalpha(im_blur)

            im_inset_cropped = im_inset.crop(im_inset.getbbox())

            # set output file name and save file to cache
            filename = os.path.basename(self.img_file)
            ext = os.path.splitext(filename)[1]
            out_filename = filename.replace(ext, f"____{n+1}.png")
            out_path = os.path.join(self.temp_dir, out_filename)

            im_inset_cropped.save(out_path, 'PNG')

            new_doc = self.save_new_document(out_path)

            link = SplitLink.objects.create(
                parent_doc=self.document,
                child_doc=new_doc,
                session=self.session,
            )

            os.remove(out_path)

        return self.session

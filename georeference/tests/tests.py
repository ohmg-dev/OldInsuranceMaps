import io
import os
import logging
from django.conf import settings
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.documents.models import Document, DocumentResourceLink

logger = logging.getLogger(__name__)

class GeoreferenceTest(GeoNodeBaseTestSupport):

    type = 'document'
    perm_spec = {
        "users": {
            "admin": [
                "change_resourcebase",
                "change_resourcebase_permissions",
                "view_resourcebase"]},
        "groups": {}}

    def setUp(self):
        super(GeoreferenceTest, self).setUp()

        ## this is original image content that is used in geonode.documents.tests
        self.imgfile = io.BytesIO(
            b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
            b'\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')

        # here is how it can be loaded from a local file
        img_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures/img/coushatta")
        img_path = os.path.join(img_dir, "03296_1922-0001.jpg")
        with open(img_path, "rb") as openf:
            imgdata = openf.read()
        self.imgfile = imgdata

        # self.anonymous_user = get_anonymous_user()

    def test_create_document(self):
        """Tests the creation of a document with no relations"""


        f = SimpleUploadedFile(
            "03296_1922-0001.jpg",
            self.imgfile,
            'image/jpg')

        superuser = get_user_model().objects.get(pk=2)
        c = Document.objects.create(
            doc_file=f,
            owner=superuser,
            title='themap')
        c.set_default_permissions()
        self.assertEqual(Document.objects.get(pk=c.id).title, 'themap')

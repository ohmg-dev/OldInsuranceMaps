# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from geonode.documents.models import Document
from geonode.layers.models import Layer

from .splitter import Splitter
from .models import GeoreferenceSession

logger = get_task_logger(__name__)

@shared_task
def split_image_as_task(docid, cut_lines, userid=0):
    """
    This is the complete image splitting task that can be called from elsewhere.
    """
    user = get_user_model().objects.get(pk=userid)
    document = Document.objects.get(pk=docid)
    splitter = Splitter(document=document, user=user)
    splitter.generate_divisions(cut_lines)
    splitter.split_image()

@shared_task
def georeference_document_as_task(docid, userid):

    user = get_user_model().objects.get(pk=userid)
    document = Document.objects.get(pk=docid)
    gs = GeoreferenceSession.objects.create(
        document=document,
        user=user,
    )
    gs.run()

@shared_task
def trim_layer_as_task(layerid, userid):
    user = get_user_model().objects.get(pk=userid)
    layer = Layer.objects.get(pk=layerid)

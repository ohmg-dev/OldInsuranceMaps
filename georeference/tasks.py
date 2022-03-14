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

from .models import (
    SplitEvaluation,
    GeoreferenceSession,
    PrepSession,
    GeorefSession,
)

logger = get_task_logger(__name__)

@shared_task
def split_image_as_task(sessionid):
    evaluation = SplitEvaluation.objects.get(pk=sessionid)
    evaluation.run()

@shared_task
def georeference_document_as_task(sessionid):
    session = GeoreferenceSession.objects.get(pk=sessionid)
    session.run()

@shared_task
def run_preparation_session(sessionid):
    session = PrepSession.objects.get(pk=sessionid)
    session.run()

@shared_task
def run_georeference_session(sessionid):
    session = GeorefSession.objects.get(pk=sessionid)
    session.run()

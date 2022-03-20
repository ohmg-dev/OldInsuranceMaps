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

import logging

from celery import shared_task

from .celeryapp import app
from .models import (
    SessionBase,
    PrepSession,
    GeorefSession,
    TrimSession,
)

logger = logging.getLogger(__name__)

@shared_task
def run_preparation_session(sessionid):
    session = PrepSession.objects.get(pk=sessionid)
    session.run()

@shared_task
def run_georeference_session(sessionid):
    session = GeorefSession.objects.get(pk=sessionid)
    session.run()

@app.task(
    bind=True,
    queue='cleanup',
    name='georeference.tasks.delete_expired_sessions',
)
def delete_expired(self):
    SessionBase().delete_expired_sessions()
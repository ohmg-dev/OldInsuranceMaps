import json
import logging

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from ohmg.georeference.models import PrepSession, Document

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        sessions = PrepSession.objects.all()
        summary = {}

        for s in sessions:
            others = PrepSession.objects.filter(doc=s.doc)
            if others.count() > 1:
                summary[s.doc.pk] = [i.pk for i in others]

        for k, v in summary.items():
            doc = Document.objects.get(pk=k)
            print(doc)
            print(len(v), v)

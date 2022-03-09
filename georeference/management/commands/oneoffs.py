import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from georeference.proxy_models import DocumentProxy, LayerProxy
from georeference.utils import TKeywordManager
from georeference.splitter import Splitter

class Command(BaseCommand):
    help = 'Command line access point for the internal georeferencing utilities.'
    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "migrate-sessions",
            ],
            help="specify the operation to carry out",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="remove all instances of new sessions before migrating old ones",
        )

    def handle(self, *args, **options):

        if options["operation"] == "migrate-sessions":
            tkm = TKeywordManager()
            try:
                from georeference.models import (
                    SplitEvaluation,
                    GeoreferenceSession,
                    MaskSession,
                )
            except ImportError:
                exit()
            from georeference.models import (
                PrepSession,
                GeorefSession,
                TrimSession,
            )
            if options['clean'] is True:
                PrepSession.objects.all().delete()
                GeorefSession.objects.all().delete()
                TrimSession.objects.all().delete()
            for se in SplitEvaluation.objects.all():
                with transaction.atomic():
                    try:
                        ps = PrepSession.objects.create(
                            document=se.document,
                            user=se.user,
                            date_created=se.created,
                            date_run=se.created,
                        )
                        ps.data["split_needed"] = se.split_needed

                        if se.cutlines is None or len(se.cutlines) == 0:
                            ps.data["cutlines"] = []
                            ps.data["divisions"] = []
                        else:
                            ps.data["cutlines"] = se.cutlines
                            s = Splitter(image_file=ps.document.doc_file.path)
                            ps.data['divisions'] = s.generate_divisions(se.cutlines)

                        if tkm.get_status(ps.document) == "splitting":
                            ps.stage = "input"
                            ps.status = "getting user input"
                        else:
                            ps.stage = "finished"
                            ps.status = "success"
                        ps.save()
                    except Exception as e:
                        print(f"error migrating: SplitEvaluation {se.pk}")
                        raise e
            for grs in GeoreferenceSession.objects.all():
                with transaction.atomic():
                    try:
                        gs = GeorefSession.objects.create(
                            document=grs.document,
                            layer=grs.layer,
                            user=grs.user,
                            date_created=grs.created,
                            date_run=grs.created,
                        )
                        gs.data["gcps"] = grs.gcps_used
                        gs.data["epsg"] = grs.crs_epsg_used
                        gs.data["transformation"] = grs.transformation_used
                        gs.stage = "finished"
                        gs.status = "success"
                        gs.save()
                    except Exception as e:
                        print(f"error migrating: GeoreferenceSession {grs.pk}")
                        raise e
            for ms in MaskSession.objects.all():
                with transaction.atomic():
                    try:
                        ts = TrimSession.objects.create(
                            layer=ms.layer,
                            user=grs.user,
                            date_created=grs.created,
                            date_run=grs.created,
                        )
                        if ms.polygon is not None:
                            ts.data["polygon"] = json.loads(ms.polygon.geojson)
                        else:
                            ts.data["polygon"] = {}
                        ts.stage = "finished"
                        ts.status = "success"
                        ts.save()
                    except Exception as e:
                        print(f"error migrating: MaskSession {ms.pk}")
                        raise e

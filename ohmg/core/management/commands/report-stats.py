from datetime import timedelta

import humanize

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from ohmg.core.models import Map
from ohmg.georeference.models import GeorefSession


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("-i", "--identifier")
        parser.add_argument("-l", "--locale")

    def handle(self, *args, **options):
        maps = None
        if options["identifier"]:
            maps = Map.objects.filter(pk=options["identifier"])
        elif options["locale"]:
            maps = Map.objects.filter(locales__slug=options["locale"])

        def collapse_session_durations(sessions) -> list[dict]:
            print("WARNING: This needs more vetting and testing...")
            grouped_deltas = []
            for s in sessions:
                ## compare against all other deltas that have already been grouped
                is_collapsed = False
                for gd in grouped_deltas:
                    ## if the session was started before the delta start, and ends
                    ## after the delta starts, then there is definitely some overlap
                    if s.date_created < gd["start"] and s.date_run > gd["start"]:
                        ## extend the delta start back to the session start
                        gd["start"] = s.date_created
                        ## if the session ends after the delta ends, then extend the
                        ## delta end to the end of the session
                        if s.date_run > gd["end"]:
                            gd["end"] = s.date_run
                        is_collapsed = True
                    ## or, if the session started sometime within the delta,
                    ## and ended sometime after, then extend the delta to the session end
                    elif s.date_created < gd["end"] and s.date_run > gd["end"]:
                        gd["end"] = s.date_run
                        is_collapsed = True

                ## otherwise, there is no overlap, and add this session as a new delta
                if not is_collapsed:
                    grouped_deltas.append(
                        {
                            "start": s.date_created,
                            "end": s.date_run,
                        }
                    )

            return grouped_deltas

        for m in maps:
            print(m)
            # docs = m.documents.all()
            # lyrs = m.layers.all()
            # prep_s = PrepSession.objects.filter(doc2__in=m.documents.all())
            georef_all = GeorefSession.objects.filter(lyr2__in=m.layers.all())

            for user_id in set(georef_all.values_list("user", flat=True)):
                user = get_user_model().objects.get(pk=user_id)
                print("\n" + user.username)
                georef_s = georef_all.filter(lyr2__in=m.layers.all(), user=user)
                print(f"georef sessions: {georef_s.count()}")
                g_delts = collapse_session_durations(georef_s)
                uncollapsed_elapsed = timedelta(
                    seconds=sum([i.user_input_duration for i in georef_s if i.user_input_duration])
                )
                print(f"uncollapsed elapsed: {uncollapsed_elapsed}")
                true_elapsed = sum([i["end"] - i["start"] for i in g_delts], timedelta())
                print(f"true elapsed: {true_elapsed}")
                layer_ct = len(set(georef_s.values_list("lyr2", flat=True)))
                print(f"layers: {layer_ct}")
                print(f"time per layer: {humanize.precisedelta(true_elapsed.seconds / layer_ct)}")

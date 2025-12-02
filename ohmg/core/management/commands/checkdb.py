import copy

from django.core.management.base import BaseCommand
from django.db.models import Q

from ohmg.core.models import Document, Layer, LayerSet
from ohmg.core.utils.cli import confirm_continue
from ohmg.georeference.models import GeorefSession, PrepSession, SessionLock


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "multimasks",
                "sessions",
            ],
            help="Choose what check to run.",
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Run a fix on the check (actions taken depend on the check).",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Verbose print statements.",
        )

    def handle(self, *args, **options):
        verbose = options["verbose"]

        def fix_layer_slug(slug, valid_slugs):
            """Return the input slug if it's valid, or a fixed one if it can
            be figured out. Return None if no fix can be found."""

            if (ct := valid_slugs.count(slug)) == 1:
                return slug
            elif ct == 0:
                # handle the shreveport 1963 volume with a bad date in the slugs
                if valid_slugs.count((slug1 := slug.replace("1415", "1963"))) == 1:
                    return slug1
                elif valid_slugs.count((slug1a := slug1 + "0")) == 1:
                    return slug1a
                elif valid_slugs.count((slug1b := slug1.replace("_p_", "_p0_"))) == 1:
                    return slug1b
                # handle New Orleans volume with wrong date in slug
                elif valid_slugs.count((slug2 := slug.replace("1895", "1896"))) == 1:
                    return slug2
                elif valid_slugs.count((slug2a := slug2 + "0")) == 1:
                    return slug2a
                elif valid_slugs.count((slug2b := slug2.replace("_p_", "_p0_"))) == 1:
                    return slug2b
                # handle the new addition of 0 to the end of unnamed pages
                elif valid_slugs.count((slug3 := slug + "0")) == 1:
                    return slug3
                # handle the new addition of 0 to the end of unnamed pages that have been split
                elif valid_slugs.count((slug4 := slug.replace("_p_", "_p0_"))) == 1:
                    return slug4
            else:
                return None

        if options["operation"] == "multimasks":
            valid_slugs = list(Layer.objects.all().values_list("slug", flat=True))
            layersets = LayerSet.objects.exclude(multimask=None).order_by("map_id")
            to_save = set()
            errors = []
            for ls in layersets:
                new_mm = copy.deepcopy(ls.multimask)
                for k, v in ls.multimask.items():
                    newslug = fix_layer_slug(k, valid_slugs)
                    if not newslug:
                        errors.append(f"ERROR: {k}")
                    elif newslug != k:
                        print(f"{k} -> {newslug}")
                        new_mm[newslug] = new_mm.pop(k)
                        new_mm[newslug]["properties"] = {"layer": newslug}
                        to_save.add(ls)
                ls.multimask = new_mm

            for e in errors:
                print(e)
            print(f"{len(errors)} layer slugs have errors")

            print(f"{len(to_save)} multimasks to fix")
            if options["fix"]:
                for ls in to_save:
                    print(f"saving {ls}")
                    ls.save()

        if options["operation"] == "sessions":
            print("\nchecking PrepSessions...")
            s = PrepSession.objects.filter(doc2__isnull=True)
            print(f"{s.count()} missing doc2")
            if s.count() > 0 and verbose:
                for i in s:
                    print(f"-- {i}")
            s = PrepSession.objects.filter(Q(reg2__isnull=False) | Q(lyr2__isnull=False))
            print(f"{s.count()} have reg2 or lyr2")
            if s.count() > 0 and verbose:
                for i in s:
                    print(f"-- {i}")
            s = PrepSession.objects.filter(map__isnull=True)
            print(f"{s.count()} missing map")
            if s.count() > 0 and verbose:
                for i in s:
                    print(f"-- {i}")
            split = PrepSession.objects.filter(data__split_needed=True)
            print(f"{split.count()} split prepsessions")
            for i in split:
                if i.doc2 and i.doc2.regions.count() < 2 and verbose:
                    print(f"-- {i}: document {i.doc2} is split but only has 1 region attached")
            nosplit = PrepSession.objects.filter(data__split_needed=False)
            print(f"{nosplit.count()} no split prepsessions")
            dupe_ct = 0
            for i in nosplit:
                if i.doc2 and i.doc2.regions.count() > 1:
                    dupe_ct += 1
                    if verbose:
                        print(
                            f"-- {i}: document {i.doc2} has multiple regions (should just have one)"
                        )
                        print(f"   {i.doc2.regions.all()}")
            print(f"{dupe_ct} no split prepsessions have documents with multiple regions")
            mp = 0
            for d in Document.objects.all():
                if PrepSession.objects.filter(doc2=d).count() > 1:
                    mp += 1
                    if verbose:
                        print(f"document {d} has multiple prepsessions")
            print(f"{mp} documents have multiple prepsessions")

            print("\nchecking GeorefSessions...")
            s = GeorefSession.objects.filter(doc2__isnull=False)
            print(f"{s.count()} have doc2")
            if s.count() > 0 and verbose:
                for i in s:
                    print(f"-- {i}")
            s = GeorefSession.objects.filter(reg2__isnull=True)
            print(f"{s.count()} missing reg2")
            if s.count() > 0 and verbose:
                for i in s:
                    print(f"-- {i}")
            s = GeorefSession.objects.filter(lyr2__isnull=True)
            print(f"{s.count()} missing lyr2")
            if s.count() > 0 and (verbose or confirm_continue("print details?")):
                for i in s:
                    print(f"-- {i}")

            print("\nchecking SessionLocks...")
            locks = SessionLock.objects.all()
            print(f"{locks.count()} current locks")

import os
import copy
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.test.client import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware

from ohmg.core.models import Layer
from ohmg.georeference.models import LayerSet

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "multimasks",
            ],
            help="Choose what check to run."
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Run a fix on the check (actions taken depend on the check).",
        )

    def handle(self, *args, **options):

        def fix_layer_slug(slug, valid_slugs):
            """ Return the input slug if it's valid, or a fixed one if it can
            be figured out. Return None if no fix can be found. """

            if (ct := valid_slugs.count(slug))  == 1:
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

        if options['operation'] == "multimasks":
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
                        new_mm[newslug]['properties'] = {'layer': newslug}
                        to_save.add(ls)
                ls.multimask = new_mm

            for e in errors:
                print(e)
            print(f"{len(errors)} layer slugs have errors")

            print(f"{len(to_save)} multimasks to fix")
            if options['fix']:
                for ls in to_save:
                    print(f"saving {ls}")
                    ls.save()

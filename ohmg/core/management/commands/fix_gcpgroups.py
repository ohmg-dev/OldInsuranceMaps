
from django.core.management.base import BaseCommand

from ohmg.georeference.models import GCPGroup
from ohmg.core.models import (
    Map,
    Document,
    Region,
    Layer,
)


class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        unmatched_docs = []
        matching_reg = []
        for g in GCPGroup.objects.all():
            if not g.doc:
                if not g.region:
                    print("missing doc:", g)
            else:
                doc_slug = g.doc.slug
                if doc_slug.endswith("p"):
                    doc_slug2 = doc_slug + "0"
                else:
                    doc_slug2 = doc_slug.replace("p_", "p0_")
                # handle the incorrect year on the new orleans vol.
                doc_slug3 = doc_slug2.replace("1895", "1896")
                # handle the incorrect year on the shreveport vol.
                doc_slug4 = doc_slug2.replace("1415", "1963")
                reg = None
                if Region.objects.filter(slug=doc_slug).exists():
                    reg = Region.objects.get(slug=doc_slug)
                elif Region.objects.filter(slug=doc_slug2).exists():
                    reg = Region.objects.get(slug=doc_slug2)
                elif Region.objects.filter(slug=doc_slug3).exists():
                    reg = Region.objects.get(slug=doc_slug3)
                elif Region.objects.filter(slug=doc_slug4).exists():
                    reg = Region.objects.get(slug=doc_slug4)
                else:
                    unmatched_docs.append(g.doc)
                if reg:
                    matching_reg.append(reg)
                    reg.gcp_group = g
                    reg.save(skip_map_lookup_update=True)

        print(f"docs attached to GCPGroups not matched to a Region ({len(unmatched_docs)}):")
        for i in unmatched_docs:
            print(i, i.pk)

        georef_reg = Region.objects.filter(georeferenced=True)
        matched_ids = [i.pk for i in matching_reg]
        missing_reg = georef_reg.exclude(pk__in=matched_ids)
        print(f"georeffed regions without gcpgroups: {missing_reg.count()}:")
        for i in missing_reg:
            print(i, i.pk)

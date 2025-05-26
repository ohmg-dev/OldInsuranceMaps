import csv
import logging
from django.db import models, transaction
from django.contrib.gis.geos import Polygon

from ohmg.core.utils import slugify
from ohmg.core.utils import (
    STATE_ABBREV,
    STATE_POSTAL,
)

logger = logging.getLogger(__name__)


class Place(models.Model):
    PLACE_CATEGORIES = (
        ("state", "State"),
        ("county", "County"),
        ("parish", "Parish"),
        ("borough", "Borough"),
        ("census area", "Census Area"),
        {"independent city", "Independent City"},
        ("city", "City"),
        ("town", "Town"),
        ("village", "Village"),
        ("other", "Other"),
    )

    name = models.CharField(
        max_length=200,
    )
    category = models.CharField(
        max_length=20,
        choices=PLACE_CATEGORIES,
    )
    display_name = models.CharField(
        max_length=250,
        editable=False,
        null=True,
        blank=True,
    )
    slug = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        editable=False,
    )
    volume_count = models.IntegerField(
        default=0,
        help_text="Number of volumes attached to this place",
    )
    volume_count_inclusive = models.IntegerField(
        default=0,
        help_text="Number of volumes attached to this place and any of its descendants",
    )
    direct_parents = models.ManyToManyField("Place")

    def __str__(self):
        return self.display_name

    @property
    def state(self):
        states = self.states
        state = None
        if len(states) == 1:
            state = states[0]
        elif len(states) > 1:
            state = states[0]
            logger.info(f"Place {self.pk} has {len(states)} states. Going with {state.slug}")
        return state

    @property
    def states(self):
        candidates = [self]
        states = []
        while candidates:
            new_candidates = []
            for p in candidates:
                if p.category == "state":
                    states.append(p)
                else:
                    for i in p.direct_parents.all():
                        new_candidates.append(i)
            candidates = new_candidates
        return list(set(states))

    def get_state_postal(self):
        if self.state and self.state.name.lower() in STATE_POSTAL:
            return STATE_POSTAL[self.state.name.lower()]
        else:
            return None

    def get_state_abbrev(self):
        if self.state and self.state.name.lower() in STATE_ABBREV:
            return STATE_ABBREV[self.state.name.lower()]
        else:
            return None

    def get_descendants(self):
        return Place.objects.filter(direct_parents__id__exact=self.id).order_by("name")

    def get_breadcrumbs(self):
        breadcrumbs = []
        p = self
        while p.direct_parents.all().count() > 0:
            parent = p.direct_parents.all()[0]
            par_name = parent.name
            if parent.category in ("county", "parish", "borough", "census area"):
                par_name += f" {parent.get_category_display()}"
            breadcrumbs.append({"name": par_name, "slug": parent.slug})
            p = parent
        breadcrumbs.reverse()
        name = self.name
        if self.category in ("county", "parish", "borough", "census area"):
            name += f" {self.get_category_display()}"
        breadcrumbs.append({"name": name, "slug": self.slug})
        return breadcrumbs

    def get_select_lists(self):
        """
        Returns a dictionary with 4 levels of lists, these are used to populate
        select dropdowns. Each list has both a list of options and also a current
        selection. For example, if this Place object is Madison, WI, the returned
        dictionary would look like this:

        {
            1: {
                "selected": "united-states",
                "options": [
                    <all countries>,
                ],
            },
            2: {
                "selected": "wisconsin",
                "options": [
                    <all US states>
                ],
            },
            3: {
                "selected": "dane-county-wi",
                "options": [
                    <all counties in WI>
                ],
            },
            4: {
                "selected": "madison-wi",
                "options": [
                    <all cities in Dane County>
                ],
            },
        }

        The value --- is used to signify a non-selection in a given category,
        so for the Wisconsin Place instance, the 3rd and 4th entry above would
        have selection: "---".

        Note that the selected value will be a slug, while the options
        list contains dictionaries with the following key/values:

        "pk", "slug", "display_name", "volume_count_inclusive"
        """

        lists = {
            1: {
                "selected": "---",
                "options": [],
            },
            2: {
                "selected": "---",
                "options": [],
            },
            3: {
                "selected": "---",
                "options": [],
            },
            4: {
                "selected": "---",
                "options": [],
            },
        }

        # take the requested place, and prefill list selections based on its breadcrumbs
        for n, i in enumerate(self.get_breadcrumbs(), start=1):
            lists[n]["selected"] = i["slug"]

        # at this point, at least a country will be selected, get its pk
        top_pk = Place.objects.get(slug=lists[1]["selected"]).pk

        # always give all of the country options
        all_lvl1 = list(
            Place.objects.filter(direct_parents=None).values(
                "pk", "slug", "display_name", "volume_count_inclusive"
            )
        )
        lists[1]["options"] = all_lvl1

        # set level 2 (state) options to only those in this country
        all_lvl2 = list(
            Place.objects.filter(direct_parents=top_pk).values(
                "pk", "slug", "display_name", "volume_count_inclusive"
            )
        )
        lists[2]["options"] = all_lvl2

        # if a state is selected, set options to all other states in the same country
        # also, set county/parish and city options for everything within the state
        if lists[2]["selected"] != "---":
            state_pk = Place.objects.get(slug=lists[2]["selected"]).pk
            all_lvl3 = list(
                Place.objects.filter(direct_parents=state_pk, volume_count_inclusive__gt=0).values(
                    "pk", "slug", "display_name", "volume_count_inclusive"
                )
            )
            lists[3]["options"] = all_lvl3
            lvl3_pks = [i["pk"] for i in all_lvl3]
            all_lvl4 = list(
                Place.objects.filter(
                    direct_parents__in=lvl3_pks, volume_count_inclusive__gt=0
                ).values("pk", "slug", "display_name", "volume_count_inclusive")
            )
            lists[4]["options"] = all_lvl4

        # if a county/parish is selected, narrow cities to only those in the county
        if lists[3]["selected"] != "---":
            ce_pk = Place.objects.get(slug=lists[3]["selected"]).pk
            all_lvl4 = list(
                Place.objects.filter(direct_parents=ce_pk, volume_count_inclusive__gt=0).values(
                    "pk", "slug", "display_name", "volume_count_inclusive"
                )
            )
            lists[4]["options"] = all_lvl4

        for k, v in lists.items():
            v["options"].sort(key=lambda k: k["display_name"])

        return lists

    def get_inclusive_pks(self):
        pks = [self.pk]
        descendants = Place.objects.filter(direct_parents__id__exact=self.id)
        while descendants:
            pks += [i.pk for i in descendants]
            new_descendants = []
            for d in descendants:
                new_descendants += [i for i in Place.objects.filter(direct_parents__id__exact=d.pk)]
            descendants = new_descendants
        return pks

    def serialize(self):
        """TO DEPRECATE: remove this once the Map model schema has been implemented, that's
        the only place it is used."""
        return {
            "pk": self.pk,
            "name": self.name,
            "display_name": self.display_name,
            "category": self.get_category_display(),
            "parents": [
                {
                    "display_name": i.display_name,
                    "slug": i.slug,
                }
                for i in self.direct_parents.all()
            ],
            "descendants": [
                {
                    "display_name": i.display_name,
                    "slug": i.slug,
                    "volume_count": i.volume_count,
                    "volume_count_inclusive": i.volume_count_inclusive,
                    # "has_descendant_maps": i.has_descendant_maps if self.has_descendant_maps else False,
                }
                for i in self.get_descendants()
            ],
            "states": [
                {
                    "display_name": i.display_name,
                    "slug": i.slug,
                }
                for i in self.states
            ],
            "slug": self.slug,
            "breadcrumbs": self.get_breadcrumbs(),
            "select_lists": self.get_select_lists(),
            "volume_count": self.volume_count,
            "volume_count_inclusive": self.volume_count_inclusive,
            "volumes": [
                {"identifier": i[0], "year": i[1], "volume_no": i[2]}
                for i in self.map_set.all()
                .order_by("year", "title")
                .values_list("identifier", "year", "volume_number")
            ],
        }

    def get_center(self):
        coords = [-90, 30]
        for map in self.map_set.all().order_by("year"):
            if ls := map.get_layerset("main-content"):
                if ls.extent:
                    coords = Polygon().from_bbox(ls.extent).centroid.coords
                    break
        return coords

    def save(self, set_slug=True, *args, **kwargs):
        if set_slug is True:
            state_postal = self.get_state_postal()
            state_abbrev = self.get_state_abbrev()
            slug, display_name = "", ""
            if self.category == "state":
                slug = slugify(self.name)
                display_name = self.name
            else:
                if self.category in ["county", "parish", "borough" "census area"]:
                    slug = slugify(f"{self.name}-{self.category}")
                    display_name = f"{self.name} {self.get_category_display()}"
                else:
                    slug = slugify(self.name)
                    display_name = self.name
                if state_postal is not None:
                    slug += f"-{state_postal}"
                if state_abbrev is not None:
                    display_name += f", {state_abbrev}"
            if not slug:
                slug = slugify(self.name)
            if not display_name:
                display_name = self.name
            self.slug = slug
            self.display_name = display_name

        super(Place, self).save(*args, **kwargs)

    def bulk_load_from_csv(self, filepath):
        with open(filepath, "r") as op:
            reader = csv.DictReader(op)
            with transaction.atomic():
                for n, row in enumerate(reader, start=1):
                    parents = row.pop("direct_parents")
                    if n % 100 == 0:
                        print(n)
                    p = Place.objects.create(**row)
                    if parents:
                        for parent in parents.split(","):
                            p.direct_parents.add(parent)
                    p.save(set_slug=True)

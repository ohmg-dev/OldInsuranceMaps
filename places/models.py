import logging
from django.db import models

from georeference.utils import slugify
from loc_insurancemaps.enumerations import (
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
        max_length = 200,
    )
    category = models.CharField(
        max_length=20,
        choices=PLACE_CATEGORIES,
    )
    display_name = models.CharField(
        max_length = 250,
        editable=False,
        null=True,
        blank=True,
    )
    slug = models.CharField(
        max_length = 250,
        null=True,
        blank=True,
        editable=False,
    )
    volume_count = models.IntegerField(
        default = 0,
        help_text="Number of volumes attached to this place",
    )
    volume_count_inclusive = models.IntegerField(
        default = 0,
        help_text="Number of volumes attached to this place and any of its descendants",
    )
    direct_parents = models.ManyToManyField("Place")

    def __str__(self):
        name = self.display_name if self.display_name else self.name
        return name

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

    def get_volumes(self):
        from loc_insurancemaps.models import Volume
        # return Volume.objects.filter(locale=self).order_by("year")
        return Volume.objects.filter(identifier="empty")

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

    def serialize(self):
        return {
            "pk": self.pk,
            "name": self.name,
            "display_name": self.display_name,
            "category": self.get_category_display(),
            "parents": [{
                "display_name": i.display_name,
                "slug": i.slug,
            } for i in self.direct_parents.all()],
            "descendants": [{
                "display_name": i.display_name,
                "slug": i.slug,
                "volume_count": i.volume_count,
                "volume_count_inclusive": i.volume_count_inclusive,
                # "has_descendant_maps": i.has_descendant_maps if self.has_descendant_maps else False,
            } for i in self.get_descendants()],
            "states": [{
                "display_name": i.display_name,
                "slug": i.slug,
            } for i in self.states],
            "slug": self.slug,
            "breadcrumbs": self.get_breadcrumbs(),
            "volume_count": self.volume_count,
            "volume_count_inclusive": self.volume_count_inclusive,
            "volumes": [{
                "identifier": i[0],
                "year": i[1],
                "volume_no":i[2]
            } for i in self.get_volumes().values_list("identifier", "year", "volume_no")],
        }

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


from django.contrib.gis.db import models
from django.forms import ValidationError
from markdownx.models import MarkdownxField

from ohmg.core.utils import slugify


class Navbar(models.Model):
    image_url = models.CharField(
        max_length=200,
        help_text="Relative or absolute url to logo image for left-hand icon.",
        default="/static/img/colored-full-linework.png",
    )
    left_side = models.JSONField()

    def save(self, *args, **kwargs):
        if not self.pk and Navbar.objects.exists():
            # if you don't check for the existence of self.pk, you'll get
            # an error when updating the current instance as well
            raise ValidationError("There can be only one Navbar instance")
        return super(Navbar, self).save(*args, **kwargs)


class Page(models.Model):
    title = models.CharField(
        max_length=200,
        help_text="Title will be slugified and must not conflict with "
        "other Pages or Places. Place slugs are formatted as "
        "follows: 'united-states', 'orleans-parish-la', and "
        "'new-orleans-la'.",
    )
    slug = models.CharField(max_length=200, null=True, blank=True)
    content = MarkdownxField()
    extra_head = models.CharField(max_length=600, null=True, blank=True)
    published = models.BooleanField(default=False)
    render_as_html = models.BooleanField(default=False)
    date_modified = models.DateTimeField(auto_now=True)
    date_published = models.DateTimeField(auto_now_add=True)
    show_date_modified = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        return super(Page, self).save(*args, **kwargs)


class Partner(models.Model):
    name = models.CharField(max_length=200)
    logo = models.FileField(
        upload_to="partner-logos",
        null=True,
        blank=True,
        max_length=255,
    )
    url = models.CharField(max_length=400, null=True, blank=True)
    description = MarkdownxField(null=True, blank=True)
    sortorder = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    def serialize(self):
        return {
            "name": self.name,
            "logo_url": self.logo.url if self.logo else "",
            "link": self.url,
            "description": self.description,
            "sortorder": self.sortorder,
        }

    def save(self, *args, **kwargs):
        if not self.sortorder:
            if not self.pk:
                self.sortorder = Partner.objects.all().count() + 1
            else:
                self.sortorder = self.pk
        return super(Partner, self).save(*args, **kwargs)

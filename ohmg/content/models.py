from django.contrib.gis.db import models

from markdownx.models import MarkdownxField

from ohmg.core.utils import slugify


class Page(models.Model):

    title = models.CharField(
        max_length=200,
        help_text="Title will be slugified and must not conflict with "\
            "other Pages or Places. Place slugs are formatted as "\
            "follows: 'united-states', 'orleans-parish-la', and "\
            "'new-orleans-la'."
    )
    slug = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )
    content = MarkdownxField()
    published = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        return super(Page, self).save(*args, **kwargs)

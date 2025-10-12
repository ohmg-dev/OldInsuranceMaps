import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage


def get_file_url(obj, attr_name: str = "file"):
    f = getattr(obj, attr_name)
    if f is None or (not f.name):
        return ""

    ## with S3 storage FileField will return an absolute url
    if settings.ENABLE_S3_STORAGE:
        url = f.url
    ## this is true during local development
    elif settings.MODE == "DEV":
        url = f"{settings.LOCAL_MEDIA_HOST.rstrip('/')}{f.url}"
    ## this is true in prod without S3 storage enabled
    else:
        url = f"{settings.SITEURL.rstrip('/')}{f.url}"

    return url


class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, **kwargs):
        """Returns a filename that's free on the target storage system, and
        available for new content to be written to.

        Found at http://djangosnippets.org/snippets/976/

        This file storage solves overwrite on upload problem. Another
        proposed solution was to override the save method on the model
        like so (from https://code.djangoproject.com/ticket/11663):

        def save(self, *args, **kwargs):
            try:
                this = MyModelName.objects.get(id=self.id)
                if this.MyImageFieldName != self.MyImageFieldName:
                    this.MyImageFieldName.delete()
            except: pass
            super(MyModelName, self).save(*args, **kwargs)
        """
        # If the filename already exists, remove it as if it was a true file system
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name

from geonode.thumbs.background import BaseThumbBackground

class NoThumbnailBackground(BaseThumbBackground):
    """
    Generates an empty background for thumbnails. In app settings, use
    THUMBNAIL_BACKGROUND = { "class": "loc_insurancemaps.background.NoThumbnailBackground" }
    """
    def fetch(self, *args, **kwargs):
        return None

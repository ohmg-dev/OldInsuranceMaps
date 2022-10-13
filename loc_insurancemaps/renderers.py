from io import BytesIO
from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None

def generate_full_thumbnail_content(document):

    # size = (200, 200)
    image_path = document.doc_file.path
    full_image = Image.open(image_path)
    # img = ImageOps.fit(img, size, Image.ANTIALIAS)
    width, height = full_image.size
    # only resize if one of the dimensions is larger than 200
    if width > 200 or height > 200:
        biggest_dim = max([width, height])
        ratio = 200/biggest_dim
        new_width, new_height = int(ratio*width), int(ratio*height)
        new_size = (new_width, new_height)
        image = ImageOps.fit(full_image, new_size, Image.ANTIALIAS)
    else:
        image = full_image

    output = BytesIO()
    image.save(output, format='PNG')
    content = output.getvalue()
    output.close()

    return content

def generate_layer_geotiff_thumbnail(layer):

    from django.conf import settings
    from geonode.layers.models import LayerFile
    from geonode.thumbs.thumbnails import _generate_thumbnail_name

    # find geotiff file path for layer
    lf = LayerFile.objects.filter(upload_session=layer.upload_session)
    if len(lf) > 1:
        print(f"too many files for this layer: {layer.alternate}")
        return None
    if len(lf) == 0:
        print(f"no file for this layer: {layer.alternate}")
        return None

    # generate blank thumbnail canvas, off-white background (geonode standard)
    size = (settings.THUMBNAIL_SIZE["width"], settings.THUMBNAIL_SIZE["height"])
    background = Image.new("RGB", size, (250, 250, 250))

    # open full image and reduce to thumbnail
    img = Image.open(lf[0].file.path)
    img.thumbnail(size)

    # paste onto background with horizontal/vertical centering
    paste_x, paste_y = 0, 0
    if img.size[0] != size[0]:
        paste_x = int((size[0] - img.size[0]) / 2)
    if img.size[1] != size[1]:
        paste_y = int((size[1] - img.size[1]) / 2)
    background.paste(img, (paste_x, paste_y), img)

    # write to bytes
    output = BytesIO()
    background.save(output, format='PNG')
    content = output.getvalue()
    output.close()

    name = _generate_thumbnail_name(layer)
    layer.save_thumbnail(name, image=content)

    del img
    del background

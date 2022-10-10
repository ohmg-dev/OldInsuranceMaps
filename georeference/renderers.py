import os
from io import BytesIO
from PIL import Image, ImageOps

from django.conf import settings

Image.MAX_IMAGE_PIXELS = None

def generate_document_thumbnail_content(image_file_path):

    full_image = Image.open(image_file_path)
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

    del image

    return content

def generate_layer_thumbnail_content(image_file_path):

    # generate blank thumbnail canvas, off-white background (geonode standard)
    size = settings.DEFAULT_THUMBNAIL_SIZE
    background = Image.new("RGB", size, (250, 250, 250))

    # open full image and reduce to thumbnail
    img = Image.open(image_file_path)
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

    del img
    del background

    return content

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps
from osgeo import gdal

from django.conf import settings

Image.MAX_IMAGE_PIXELS = None

def generate_document_thumbnail_content(image_file_path):

    full_image = Image.open(image_file_path)
    width, height = full_image.size
    # only resize if one of the dimensions is larger than 200
    if width > settings.DEFAULT_MAX_THUMBNAIL_DIMENSION or height > settings.DEFAULT_MAX_THUMBNAIL_DIMENSION:
        biggest_dim = max([width, height])
        ratio = settings.DEFAULT_MAX_THUMBNAIL_DIMENSION/biggest_dim
        new_width, new_height = int(ratio*width), int(ratio*height)
        new_size = (new_width, new_height)
        if 0 in new_size:
            return b''
        image = ImageOps.fit(full_image, new_size, Image.ANTIALIAS)
    else:
        image = full_image

    output = BytesIO()
    image.save(output, format='JPEG')
    content = output.getvalue()
    output.close()

    del image

    return content

def generate_layer_thumbnail_content(image_file_path):

    # generate blank thumbnail canvas, off-white background (geonode strategy)
    size = settings.DEFAULT_THUMBNAIL_SIZE
    background_color = (255, 255, 255)
    background = Image.new("RGB", size, background_color)

    # open full image and reduce to thumbnail
    img = Image.open(image_file_path)
    img.thumbnail(size)

    # convert to RGB if necessary, this will turn the transparent areas black
    if img.mode == 'RGBA':
        img = img.convert('RGB')

    # iterate all pixels, turn true black to white, i.e. transparent
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            if img.getpixel((x,y)) == (0, 0, 0):
                img.putpixel((x,y), background_color)

    # paste onto background with horizontal/vertical centering
    paste_x, paste_y = 0, 0
    if img.size[0] != size[0]:
        paste_x = int((size[0] - img.size[0]) / 2)
    if img.size[1] != size[1]:
        paste_y = int((size[1] - img.size[1]) / 2)
    background.paste(img, (paste_x, paste_y))

    # write to bytes
    output = BytesIO()
    background.save(output, format='JPEG')
    content = output.getvalue()
    output.close()

    del img
    del background

    return content

def convert_img_to_pyramidal_tiff(input_image):

    in_path = Path(input_image)

    print(in_path)
    out_path = Path(settings.TEMP_DIR, in_path.stem + ".tif")

    print(out_path)

    to = gdal.TranslateOptions(
        # format="GTiff",
        format="COG",
        # maskBand="mask",
        creationOptions=[
            # 'COMPRESS=DEFLATE',
            # 'PREDICTOR=2',
            # 'COMPRESS=LZW',
            # 'PREDICTOR=YES',
            'COMPRESS=JPEG',
            'QUALITY=100',
            # 'TILED=YES',
            # 'BLOCKXSIZE=512',
            # 'BLOCKYSIZE=512',
            # "PHOTOMETRIC=YCBCR",
        ],
        resampleAlg="nearest"
    )
    gdal.Translate(out_path, input_image, options=to)

    return out_path

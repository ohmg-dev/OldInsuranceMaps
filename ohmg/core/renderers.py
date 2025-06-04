from io import BytesIO
from pathlib import Path
import logging
import subprocess

from PIL import Image, ImageOps
from osgeo import gdal, osr

from django.conf import settings
from django.db.models import FileField

Image.MAX_IMAGE_PIXELS = None

gdal.UseExceptions()

logger = logging.getLogger(__name__)


def get_extent_from_file(file_path: Path):
    """Credit: https://gis.stackexchange.com/a/201320/28414"""

    if not file_path.is_file():
        return None
    src = gdal.Open(str(file_path))
    ulx, xres, xskew, uly, yskew, yres = src.GetGeoTransform()
    lrx = ulx + (src.RasterXSize * xres)
    lry = uly + (src.RasterYSize * yres)

    src = None
    del src

    webMerc = osr.SpatialReference()
    webMerc.ImportFromEPSG(3857)
    wgs84 = osr.SpatialReference()
    wgs84.ImportFromEPSG(4326)
    transform = osr.CoordinateTransformation(webMerc, wgs84)

    ul = transform.TransformPoint(ulx, uly)
    lr = transform.TransformPoint(lrx, lry)

    return [ul[1], lr[0], lr[1], ul[0]]


def get_image_size(file: FileField):
    size = None
    with file.open("rb") as f:
        try:
            img = Image.open(f)
            size = img.size
            img.close()
        except Exception as e:
            logger.warning(f"error opening file {f}: {e}")
    return size


def generate_document_thumbnail_content(file: FileField):
    with file.open("rb") as f:
        full_image = Image.open(f)
        width, height = full_image.size
        # only resize if one of the dimensions is larger than 200
        if (
            width > settings.DEFAULT_MAX_THUMBNAIL_DIMENSION
            or height > settings.DEFAULT_MAX_THUMBNAIL_DIMENSION
        ):
            biggest_dim = max([width, height])
            ratio = settings.DEFAULT_MAX_THUMBNAIL_DIMENSION / biggest_dim
            new_width, new_height = int(ratio * width), int(ratio * height)
            new_size = (new_width, new_height)
            if 0 in new_size:
                return b""
            image = ImageOps.fit(full_image, new_size, Image.ANTIALIAS)
        else:
            image = full_image

        output = BytesIO()
        image.save(output, format="JPEG")
        content = output.getvalue()
        output.close()

        del image

    return content


def generate_layer_thumbnail_content(file: FileField):
    # generate blank thumbnail canvas, off-white background (geonode strategy)
    size = settings.DEFAULT_THUMBNAIL_SIZE
    background_color = (255, 255, 255)
    background = Image.new("RGB", size, background_color)

    with file.open("rb") as f:
        # open full image and reduce to thumbnail
        img = Image.open(f)
        img.thumbnail(size)

        # convert to RGB if necessary, this will turn the transparent areas black
        if img.mode == "RGBA":
            img = img.convert("RGB")

        # iterate all pixels, turn true black to white, i.e. transparent
        for y in range(img.size[1]):
            for x in range(img.size[0]):
                if img.getpixel((x, y)) == (0, 0, 0):
                    img.putpixel((x, y), background_color)

        # paste onto background with horizontal/vertical centering
        paste_x, paste_y = 0, 0
        if img.size[0] != size[0]:
            paste_x = int((size[0] - img.size[0]) / 2)
        if img.size[1] != size[1]:
            paste_y = int((size[1] - img.size[1]) / 2)
        background.paste(img, (paste_x, paste_y))

        # write to bytes
        output = BytesIO()
        background.save(output, format="JPEG")
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
            "COMPRESS=JPEG",
            "QUALITY=100",
            # 'TILED=YES',
            # 'BLOCKXSIZE=512',
            # 'BLOCKYSIZE=512',
            # "PHOTOMETRIC=YCBCR",
        ],
        resampleAlg="nearest",
    )
    gdal.Translate(out_path, input_image, options=to)

    return out_path


def convert_pdf_to_jpg(input_path: Path):
    if not subprocess.getstatusoutput("pdftoppm --help")[0] == 0:
        logger.warning("pdftoppm is not available, PDF file cannot be converted")
        return None

    output_path = input_path.with_suffix(".jpg")
    cmd = ["pdftoppm", str(input_path), "-jpeg", str(output_path), "-singlefile"]
    subprocess.run(cmd)

    return output_path

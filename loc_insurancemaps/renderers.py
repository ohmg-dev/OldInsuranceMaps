import os
from io import BytesIO
from PIL import Image, ImageOps

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

def convert_img_format(input_img, format="JPEG"):

    ext_map = {"PNG":".png", "JPEG":".jpg", "TIFF": ".tif"}
    ext = os.path.splitext(input_img)[1]

    outpath = input_img.replace(ext, ext_map[format])

    img = Image.open(input_img)
    img.save(outpath, format=format)

    return outpath

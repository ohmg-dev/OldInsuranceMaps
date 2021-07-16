# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import os
from io import BytesIO
import requests
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageFont

def generate_collection_item_thumbnail_content(image_path, size=(150, 180), number=None):
    """Generate custom thumbnail content for a collection item that shows
    the number of files associated with the item.
    """

    file_ct = str(number)
    font_path = "/home/adam/Octavian/Fonts/Adobe Fan Heiti Std B/Adobe Fan Heiti Std B.ttf"

    image = Image.open(image_path)
    source_width, source_height = image.size
    target_width, target_height = size

    if source_width != target_width or source_width != target_height:
        image = ImageOps.fit(image, size, Image.ANTIALIAS)

    # if there is no number of files then just save a simple thumbnail
    if number is None:
        out_image = image

    # otherwise add image editing to print the number on the image
    else:

        # figure out a lot of measurements
        if len(file_ct) == 1:
            box_width = 36
        elif len(file_ct) == 2:
            box_width = 72
        elif len(file_ct) == 3:
            box_width = 106

        side_margin = int((target_width-box_width)/2)
        x0, y0 = 0 + side_margin, int(target_height/2) - 30
        x1, y1 = target_width - side_margin, int(target_height/2) + 30
        coords = [x0, y0, x1, y1]

        font = ImageFont.truetype(font_path, y1-y0)

        # create an alpha layer and add it to the image
        alpha = Image.new("L", size, 255)
        image.putalpha(alpha)

        # create a new layer and draw a rectagle on it
        im_rect = Image.new("RGBA", size, (255,255,255,0))
        d2 = ImageDraw.Draw(im_rect)
        d2.rectangle(coords, fill=(255,255,255,150))

        # blur the edges of the rectangle
        im_blur = im_rect.filter(ImageFilter.GaussianBlur(3))

        # add text to the rectagle drawing
        d3 = ImageDraw.Draw(im_blur)
        d3.text((coords[0], coords[1]), str(number), font=font, fill=(50,50,50))

        # combine the original image with the drawn rectagle and text
        out_image = Image.alpha_composite(image, im_blur)

    # save to temp bytes and return the content
    output = BytesIO()
    out_image.save(output, format='PNG')
    content = output.getvalue()
    output.close()

    return content

def get_image_content_from_url(url):

    response = requests.get(url)
    content = BytesIO(response.content).getvalue()

    return content

def convert_img_format(input_img, format="JPEG"):

    ext_map = {"PNG":".png", "JPEG":".jpg", "TIFF": ".tif"}
    ext = os.path.splitext(input_img)[1]

    outpath = input_img.replace(ext, ext_map[format])

    img = Image.open(input_img)
    img.save(outpath, format=format)

    return outpath

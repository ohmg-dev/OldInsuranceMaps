import os
from PIL import Image, ImageDraw, ImageFont


# working from this guide for now
# https://haptik.ai/tech/putting-text-on-image-using-python/

def make_thumbnail():

    img_dir = os.path.join("lc_insurancemaps", "utils", "thumbs")
    image = Image.open(os.path.join(img_dir, "background.png"))

    # initialise the drawing context with
    # the image object as background

    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype('/home/adam/Octavian/Fonts/Adobe Fan Heiti Std B/Adobe Fan Heiti Std B.ttf', size=45)

    # starting position of the message

    (x, y) = (50, 50)
    message = "this volume has"
    color = 'rgb(0, 0, 0)' # black color

    # draw the message on the background

    draw.text((x, y), message, fill=color, font=font)
    (x, y) = (150, 150)
    name = 'Adam!'
    color = 'rgb(255, 255, 255)' # white color
    draw.text((x, y), name, fill=color, font=font)

    # save the edited image

    image.save(os.path.join(img_dir, 'greeting_card.png'))

if __name__ == "__main__":
    make_thumbnail()

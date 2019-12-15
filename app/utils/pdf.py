import base64

from PIL import Image
from wand.image import Image
import os
import io


def extract_first_page(blob):
    pdf = Image(blob=blob, resolution=200)

    image = Image(
        width=pdf.width,
        height=pdf.height
    )

    image.composite(
        pdf.sequence[0],
        top=0,
        left=0
    )

    return image.make_blob('png')

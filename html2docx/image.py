import base64
import binascii
import http
import io
import pathlib
import time
import urllib.error
import urllib.request
from typing import Dict, Optional, cast

from docx.image.exceptions import UnrecognizedImageError
from docx.image.image import Image
from docx.shared import Inches

# The usable size is the space inside the default template margins.
# In LibreOffice, the maximum height for an image is capped to USABLE_HEIGHT.
USABLE_HEIGHT = Inches(8.1)
USABLE_WIDTH = Inches(5.8)
DEFAULT_DPI = 72

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MiB

RFC_2397_BASE64 = ";base64"


def make_image(data: Optional[bytes]) -> io.BytesIO:
    image_buffer = None
    if data:
        image_buffer = io.BytesIO(data)
        try:
            Image.from_blob(image_buffer.getbuffer())
        except UnrecognizedImageError:
            image_buffer = None

    if not image_buffer:
        broken_img_path = pathlib.Path(__file__).parent / "image-broken.png"
        image_buffer = io.BytesIO(broken_img_path.read_bytes())

    return image_buffer


def load_external_image(src: str) -> Optional[bytes]:
    data = None
    retry = 3
    while retry and not data:
        try:
            with urllib.request.urlopen(src) as response:
                size = response.getheader("Content-Length")
                if size and int(size) > MAX_IMAGE_SIZE:
                    break
                # Read up to MAX_IMAGE_SIZE when response does not contain
                # the Content-Length header. The extra byte avoids an extra read to
                # check whether the EOF was reached.
                data = cast(bytes, response.read(MAX_IMAGE_SIZE + 1))
        except (ValueError, http.client.HTTPException, urllib.error.HTTPError):
            # ValueError: Invalid URL or non-integer Content-Length.
            # HTTPException: Server does not speak HTTP properly.
            # HTTPError: Server could not perform request.
            retry = 0
        except urllib.error.URLError:
            # URLError: Transient network error, e.g. DNS request failed.
            retry -= 1
            if retry:
                time.sleep(1)
        else:
            if len(data) <= MAX_IMAGE_SIZE:
                return data
    return None


def load_inline_image(src: str) -> Optional[bytes]:
    image_data = None
    header_data = src.split(RFC_2397_BASE64 + ",", maxsplit=1)
    if len(header_data) == 2:
        data = header_data[1]
        try:
            image_data = base64.b64decode(data, validate=True)
        except (binascii.Error, ValueError):
            # binascii.Error: Character outside of base64 set.
            # ValueError: Character outside of ASCII.
            pass
    return image_data


def load_image(src: str) -> io.BytesIO:
    image_bytes = (
        load_inline_image(src) if src.startswith("data:") else load_external_image(src)
    )
    return make_image(image_bytes)


def image_size(
    image_buffer: io.BytesIO,
    width_px: Optional[int] = None,
    height_px: Optional[int] = None,
) -> Dict[str, int]:
    """
    Compute width and height to feed python-docx so that image is contained in the page
    and respects width_px and height_px.

    Return:
        Empty: No resize
        Single dimension (width or height): image ratio is expected to be maintained
        Two dimensions (width and height): image should be resized to dimensions
    """
    image = Image.from_blob(image_buffer.getbuffer())

    # Normalize image size to inches.
    # - Without a specified pixel size, images are their actual pixel size, so that
    #   images of the same pixel size appear the same size in the document, regardless
    #   of their resolution.
    # - With a specified pixel size, images should take the specified size, regardless
    #   of their resolution.
    if height_px is None:
        height = image.px_height / image.vert_dpi
    else:
        height = height_px / DEFAULT_DPI
    if width_px is None:
        width = image.px_width / image.horz_dpi
    else:
        width = width_px / DEFAULT_DPI

    height = Inches(height)
    width = Inches(width)

    size = {}
    if width > USABLE_WIDTH:
        new_height = round(image.px_height / (image.px_width / USABLE_WIDTH))
        if new_height > USABLE_HEIGHT:
            size["height"] = USABLE_HEIGHT
        else:
            size["width"] = USABLE_WIDTH
    elif height > USABLE_HEIGHT:
        new_width = round(image.px_width / (image.px_height / USABLE_HEIGHT))
        if new_width > USABLE_WIDTH:
            size["width"] = USABLE_WIDTH
        else:
            size["height"] = USABLE_HEIGHT
    else:
        if width_px is not None:
            size["width"] = width
        if height_px is not None:
            size["height"] = height
    return size

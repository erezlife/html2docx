import http
import io
import pathlib
import time
import urllib.error
import urllib.request

from docx.image.exceptions import UnrecognizedImageError
from docx.image.image import Image

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MiB


def load_image(src: str) -> io.BytesIO:
    image_buffer = None
    retry = 3
    while retry and not image_buffer:
        try:
            with urllib.request.urlopen(src) as response:
                size = response.getheader("Content-Length")
                if size and int(size) > MAX_IMAGE_SIZE:
                    break
                # Read up to MAX_IMAGE_SIZE when response does not contain
                # the Content-Length header. The extra byte avoids an extra read to
                # check whether the EOF was reached.
                data = response.read(MAX_IMAGE_SIZE + 1)
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
                image_buffer = io.BytesIO(data)

    if image_buffer:
        try:
            Image.from_blob(image_buffer.getbuffer())
        except UnrecognizedImageError:
            image_buffer = None

    if not image_buffer:
        broken_img_path = pathlib.Path(__file__).parent / "image-broken.png"
        image_buffer = io.BytesIO(broken_img_path.read_bytes())

    return image_buffer

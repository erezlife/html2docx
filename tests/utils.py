import pathlib
from io import BytesIO

from PIL import Image

from html2docx.image import DEFAULT_DPI

TEST_DIR = pathlib.Path(__file__).parent.resolve(strict=True)
PROJECT_DIR = TEST_DIR.parent


def generate_image(width: int, height: int, dpi=(DEFAULT_DPI, DEFAULT_DPI)) -> BytesIO:
    data = BytesIO()
    with Image.new("L", (width, height)) as image:
        image.save(data, format="png", dpi=dpi)
    return data

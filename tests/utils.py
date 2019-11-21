import pathlib
from io import BytesIO

from PIL import Image

TEST_DIR = pathlib.Path(__file__).parent.resolve(strict=True)
PROJECT_DIR = TEST_DIR.parent
DPI = 72


def generate_image(width: int, height: int, dpi=(DPI, DPI)) -> BytesIO:
    data = BytesIO()
    with Image.new("L", (width, height)) as image:
        image.save(data, format="png", dpi=dpi)
    return data

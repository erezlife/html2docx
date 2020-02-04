from math import ceil

from docx.shared import Inches

from html2docx.image import DEFAULT_DPI, USABLE_HEIGHT, USABLE_WIDTH, image_size

from .utils import PROJECT_DIR, generate_image

broken_image = PROJECT_DIR / "html2docx" / "image-broken.png"
broken_image_bytes = broken_image.read_bytes()


def inches_to_px(inches: int, dpi: int = DEFAULT_DPI) -> int:
    return ceil(inches / Inches(1) * dpi)


def px_to_inches(px: int, dpi: int = DEFAULT_DPI) -> int:
    return ceil(px * Inches(1) / dpi)


def test_one_px():
    image = generate_image(width=1, height=1)
    size = image_size(image, 1, 1)
    side = px_to_inches(1)
    assert size == {"width": side, "height": side}


def test_upscale():
    image = generate_image(width=1, height=1)
    size = image_size(image, width_px=2, height_px=2)
    side = px_to_inches(2)
    assert size == {"width": side, "height": side}


def test_downscale():
    image = generate_image(width=2, height=2)
    size = image_size(image, width_px=1, height_px=1)
    side = px_to_inches(1)
    assert size == {"width": side, "height": side}


def test_image_larger_than_usable_width():
    image = generate_image(width=inches_to_px(USABLE_WIDTH) + 1, height=1)
    size = image_size(image)
    assert size == {"width": USABLE_WIDTH}


def test_image_taller_than_usable_height():
    image = generate_image(width=1, height=inches_to_px(USABLE_HEIGHT) + 1)
    size = image_size(image)
    assert size == {"height": USABLE_HEIGHT}


def test_size_larger_than_usable_width():
    image = generate_image(width=100, height=1)
    max_width_px = inches_to_px(USABLE_WIDTH) + 1
    size = image_size(image, width_px=max_width_px)
    assert size == {"width": USABLE_WIDTH}


def test_size_taller_than_usable_height():
    image = generate_image(width=1, height=100)
    max_height_px = inches_to_px(USABLE_HEIGHT) + 1
    size = image_size(image, height_px=max_height_px)
    assert size == {"height": USABLE_HEIGHT}


def test_resize_exceeds_width():
    image = generate_image(width=1, height=1)
    size = image_size(image, height_px=inches_to_px(USABLE_HEIGHT))
    assert size == {"width": USABLE_WIDTH}


def test_resize_exceeds_height():
    image = generate_image(width=1, height=2)
    size = image_size(image, width_px=inches_to_px(USABLE_WIDTH))
    assert size == {"height": USABLE_HEIGHT}


def test_no_pixel_size_uses_dpi_width():
    width_px = inches_to_px(USABLE_WIDTH, 300)
    image = generate_image(width=width_px, height=1, dpi=(300, 300))
    size = image_size(image)
    assert size == {}


def test_no_pixel_size_uses_dpi_height():
    height_px = inches_to_px(USABLE_HEIGHT, 300)
    image = generate_image(width=1, height=height_px, dpi=(300, 300))
    size = image_size(image)
    assert size == {}


def test_pixel_size_specified_ignores_dpi_width():
    width_px = inches_to_px(Inches(1))
    image = generate_image(width=width_px, height=1, dpi=(300, 300))
    size = image_size(image, width_px=width_px)
    assert size == {"width": Inches(1)}


def test_pixel_size_specified_ignores_dpi_height():
    height_px = inches_to_px(Inches(1))
    image = generate_image(width=1, height=height_px, dpi=(300, 300))
    size = image_size(image, height_px=height_px)
    assert size == {"height": Inches(1)}

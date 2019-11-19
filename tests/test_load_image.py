import urllib.error
import urllib.request
from unittest import mock

from html2docx.image import load_image

from .utils import PROJECT_DIR, TEST_DIR

broken_image = PROJECT_DIR / "html2docx" / "image-broken.png"
broken_image_bytes = broken_image.read_bytes()


def test_basic(image_server):
    image_data = load_image(image_server.base_url + "1x1.png")
    expected = TEST_DIR / "data" / "1x1.png"
    assert image_data.getbuffer() == expected.read_bytes()


def test_non_image(image_server):
    image_data = load_image(image_server.base_url)
    assert image_data.getbuffer() == broken_image_bytes


def test_bad_url():
    image_data = load_image("bad")
    assert image_data.getbuffer() == broken_image_bytes


def test_transient_network_error_retries():
    url = "https://transient.network.issue.com/image.png"
    with mock.patch(
        "html2docx.image.urllib.request.urlopen",
        autospec=True,
        side_effect=urllib.error.URLError(
            reason="[Errno -2] Name or service not known"
        ),
    ) as url_mock:
        with mock.patch("html2docx.image.time.sleep", autospec=True) as time_mock:
            image_data = load_image(url)
            assert time_mock.mock_calls == [mock.call(1)] * 2
        assert url_mock.call_args_list == [mock.call(url)] * 3
    assert image_data.getbuffer() == broken_image_bytes


def test_404(image_server):
    image_data = load_image(image_server.base_url + "nonexistent")
    assert image_data.getbuffer() == broken_image_bytes
    assert image_server.httpd.request_count == 1


def test_bad_server(bad_server):
    image_data = load_image(bad_server.base_url)
    assert image_data.getbuffer() == broken_image_bytes
    assert bad_server.httpd.request_count == 1


def test_bad_content_length(bad_content_length_server):
    image_data = load_image(bad_content_length_server.base_url)
    assert image_data.getbuffer() == broken_image_bytes
    assert bad_content_length_server.httpd.request_count == 1

import http.server
import os
import sys
import threading

import pytest

from .utils import TEST_DIR


class CountingHTTPServer(http.server.HTTPServer):
    request_count = 0

    def finish_request(self, *args, **kwargs):
        self.request_count += 1
        return super().finish_request(*args, **kwargs)


class HttpServerThread(threading.Thread):
    def __init__(self, handler):
        super().__init__()
        self.is_ready = threading.Event()
        self.handler = handler
        self.error = None

    def run(self):
        try:
            self.httpd = CountingHTTPServer(("localhost", 0), self.handler)
            port = self.httpd.server_address[1]
            self.base_url = f"http://localhost:{port}/"
            self.is_ready.set()
            self.httpd.serve_forever(poll_interval=0.01)
        except Exception as e:
            self.error = e
            self.is_ready.set()

    def terminate(self):
        if hasattr(self, "httpd"):
            self.httpd.shutdown()
            self.httpd.server_close()
        self.join()


class ImageHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        if sys.version_info >= (3, 9):
            kwargs["directory"] = TEST_DIR / "images"
        elif sys.version_info >= (3, 7):
            kwargs["directory"] = os.fspath(TEST_DIR / "images")
        super().__init__(*args, **kwargs)

    def translate_path(self, path):
        if sys.version_info < (3, 7):
            cwd = os.getcwd()
            try:
                os.chdir(TEST_DIR / "images")
                return super().translate_path(path)
            finally:
                os.chdir(cwd)
        return super().translate_path(path)


def http_server_thread(handler):
    server_thread = HttpServerThread(handler)
    server_thread.daemon = True
    server_thread.start()
    server_thread.is_ready.wait()
    yield server_thread
    try:
        if server_thread.error:
            raise server_thread.error
    finally:
        server_thread.terminate()


@pytest.fixture(scope="function")
def image_server():
    """
    Start a HTTP server serving test images.
    """
    yield from http_server_thread(ImageHandler)


class BadContentHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.close_connection = True


@pytest.fixture(scope="function")
def bad_server():
    yield from http_server_thread(BadContentHandler)


class BadContentLengthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(http.HTTPStatus.OK)
        self.send_header("Content-Length", "invalid")
        self.end_headers()


@pytest.fixture(scope="function")
def bad_content_length_server():
    yield from http_server_thread(BadContentLengthHandler)

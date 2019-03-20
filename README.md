# html2docx

html2docx converts valid HTML input to docx output. The project is distributed
under the MIT license.

## Installing

To install, use pip:

```
$ pip install html2docx
```

## Usage

```py
from html2docx import html2docx

with open("my.html") as fp:
    html = fp.read()

# html2docx() returns an io.BytesIO() object. The HTML must be valid.
buf = html2docx(html, title="My Document")

with open("my.docx", "wb") as fp:
    fp.write(buf.getvalue())
```

## Testing

To run the test suite, use tox:

```
$ tox
```

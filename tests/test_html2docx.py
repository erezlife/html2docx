import json
import pathlib

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
import pytest

from html2docx import html2docx


def generate_testdata():
    datadir = pathlib.Path(__file__).parent.joinpath("data")
    for html_path in datadir.glob("*.html"):
        spec_path = datadir.joinpath(f"{html_path.stem}.json")
        yield html_path, spec_path


@pytest.mark.parametrize("html_path,spec_path", generate_testdata())
def test_html2docx(html_path, spec_path):
    title = html_path.name
    with html_path.open() as fp:
        html = fp.read()
    with spec_path.open() as fp:
        spec = json.load(fp)

    buf = html2docx(html, title=title)
    doc = docx.Document(buf)

    assert doc.core_properties.title == title
    assert len(doc.paragraphs) == len(spec)
    for p, p_spec in zip(doc.paragraphs, spec):
        assert p.text == p_spec["text"]
        assert p.style.name == p_spec.get("style", "Normal")

        runs_spec = p_spec["runs"]
        assert len(p.runs) == len(runs_spec)
        for run, run_spec in zip(p.runs, runs_spec):
            assert run.text == run_spec["text"]
            for attr in ("bold", "italic", "underline", "subscript", "superscript"):
                msg = f"Wrong {attr} for text '{run.text}' in {html_path}"
                assert getattr(run.font, attr) is run_spec.get(attr), msg


def test_para_align_left():
    html = "<p style=\"text-align: left;\">Left aligned.</p>"
    buf = html2docx(html, title="Title")
    doc = docx.Document(buf)
    p = doc.paragraphs[0]
    assert p.alignment == WD_ALIGN_PARAGRAPH.LEFT, "Left alignment not set."


def test_para_align_right():
    html = "<p style=\"text-align: right;\">Right aligned.</p>"
    buf = html2docx(html, title="Title")
    doc = docx.Document(buf)
    p = doc.paragraphs[0]
    assert p.alignment == WD_ALIGN_PARAGRAPH.RIGHT, "Right alignment not set."


def test_para_align_center():
    html = "<p style=\"text-align: center;\">Center aligned.</p>"
    buf = html2docx(html, title="Title")
    doc = docx.Document(buf)
    p = doc.paragraphs[0]
    assert p.alignment == WD_ALIGN_PARAGRAPH.CENTER, "Center alignment not set."


def test_para_align_justify():
    html = "<p style=\"text-align: justify;\">Justify aligned.</p>"
    buf = html2docx(html, title="Title")
    doc = docx.Document(buf)
    p = doc.paragraphs[0]
    assert p.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY, "Justify alignment not set."


def test_para_left_indent():
    html = "<p style=\"padding-left: 40px;\">Left indent.</p>"
    buf = html2docx(html, title="Title")
    doc = docx.Document(buf)
    p = doc.paragraphs[0]
    assert p.paragraph_format.left_indent == Pt(40), "Indent not set"


def test_blockquote():
    html = "<blockquote>This is a block quote.</blockquote>"
    buf = html2docx(html, title="Title")
    doc = docx.Document(buf)
    p = doc.paragraphs[0]
    assert p.style.name == "Quote", "Quote style not set."


def test_code():
    html = "<p><code>value = get_value(arg)</code></p>"
    buf = html2docx(html, title="Title")
    doc = docx.Document(buf)
    p = doc.paragraphs[0]
    r = p.runs[0]
    assert r.font.name == "Mono", "Mono font not set."

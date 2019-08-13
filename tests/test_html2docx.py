import json
import pathlib

import docx
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
            for attr in ("bold", "italic", "underline"):
                msg = f"Wrong {attr} for text '{run.text}' in {html_path}"
                assert getattr(run.font, attr) is run_spec.get(attr, False), msg

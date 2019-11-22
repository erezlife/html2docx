import json
import pathlib

import docx
import pytest

from html2docx import html2docx

TEST_DIR = pathlib.Path(__file__).parent.resolve(strict=True)
PROJECT_DIR = TEST_DIR.parent


def generate_testdata():
    datadir = TEST_DIR / "data"
    for html_path in datadir.glob("*.html"):
        spec_path = html_path.with_suffix(".json")
        yield html_path, spec_path


@pytest.mark.parametrize("html_path,spec_path", generate_testdata())
def test_html2docx(html_path, spec_path):
    html_rel_path = html_path.relative_to(PROJECT_DIR)

    title = html_path.name
    html = html_path.read_text()
    with spec_path.open() as fp:
        spec = json.load(fp)

    buf = html2docx(html, title=title)
    doc = docx.Document(buf)

    assert doc.core_properties.title == title
    assert len(doc.paragraphs) == len(spec)
    for p, p_spec in zip(doc.paragraphs, spec):
        assert p.text == p_spec["text"]
        assert p.style.name == p_spec.get("style", "Normal")
        if p.alignment:
            assert int(p.alignment) == p_spec["alignment"]

        runs_spec = p_spec["runs"]
        assert len(p.runs) == len(runs_spec)
        for run, run_spec in zip(p.runs, runs_spec):
            assert run.text == run_spec["text"]
            for attr in (
                "bold",
                "italic",
                "strike",
                "subscript",
                "superscript",
                "underline",
            ):
                msg = f"Wrong {attr} for text '{run.text}' in {html_rel_path}"
                assert getattr(run.font, attr) is run_spec.get(attr), msg

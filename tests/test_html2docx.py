import json
from typing import Union

import docx
import pytest
from docx.document import Document
from docx.oxml import CT_P, CT_Tbl
from docx.shared import Pt
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph

from html2docx import html2docx

from .utils import PROJECT_DIR, TEST_DIR

FONT_ATTRS = [
    "bold",
    "italic",
    "name",
    "strike",
    "subscript",
    "superscript",
    "underline",
]


def generate_testdata():
    datadir = TEST_DIR / "data"
    for html_path in datadir.glob("*.html"):
        spec_path = html_path.with_suffix(".json")
        yield html_path, spec_path


def get_document_children(element: Union[Document, _Cell]):
    if isinstance(element, Document):
        parent_element = element.element.body
    elif isinstance(element, _Cell):
        parent_element = element._tc
    else:
        raise Exception("Received an item that does not have children.")
    for child in parent_element.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, element)
        elif isinstance(child, CT_Tbl):
            yield Table(child, element)


def assert_paragraph_comply_with_spec(
    p: Paragraph, p_spec: dict, html_rel_path: str, spec_rel_path: str
):
    assert p.text == p_spec["text"]
    assert p.style.name == p_spec.get("style", "Normal")
    if p_spec.get("alignment") is not None:
        assert p.alignment == p_spec["alignment"]
    else:
        assert p.alignment is None
    if p_spec.get("left_indent"):
        assert p.paragraph_format.left_indent == Pt(p_spec["left_indent"])
    else:
        assert p.paragraph_format.left_indent is None

    runs_spec = p_spec["runs"]
    assert len(p.runs) == len(runs_spec)
    for run, run_spec in zip(p.runs, runs_spec):
        assert run.text == run_spec.pop("text")
        shapes_spec = run_spec.pop("shapes", None)
        unknown = set(run_spec).difference(FONT_ATTRS)
        assert not unknown, "Unknown attributes in {}: {}".format(
            spec_rel_path, ", ".join(unknown)
        )
        for attr in FONT_ATTRS:
            msg = f"Wrong {attr} for text '{run.text}' in {html_rel_path}"
            assert getattr(run.font, attr) == run_spec.get(attr), msg
        if shapes_spec:
            shapes = run.part.inline_shapes
            assert len(shapes) == len(shapes_spec)
            for shape, shape_spec in zip(shapes, shapes_spec):
                assert shape.type == shape_spec["type"]
                assert shape.width == shape_spec["width"]
                assert shape.height == shape_spec["height"]


def assert_table_comply_with_spec(
    t: Table, t_spec: dict, html_rel_path: str, spec_rel_path: str
):
    assert "table" in t_spec
    assert len(t.rows) == len(t_spec["table"])
    for (row, row_spec) in zip(t.rows, t_spec["table"]):
        assert len(t.columns) == len(row_spec)
        for (cell, cell_spec) in zip(row.cells, row_spec):
            assert_element_comply_with_spec(
                cell, cell_spec["cell"], html_rel_path, spec_rel_path
            )


def assert_element_comply_with_spec(
    element: Union[Document, _Cell], spec: dict, html_rel_path: str, spec_rel_path: str
):
    children = list(get_document_children(element))
    assert len(children) == len(spec)
    for child, child_spec in zip(children, spec):
        if isinstance(child, Paragraph):
            assert_paragraph_comply_with_spec(
                child, child_spec, html_rel_path, spec_rel_path
            )
        if isinstance(child, Table):
            assert_table_comply_with_spec(
                child, child_spec, html_rel_path, spec_rel_path
            )


@pytest.mark.parametrize("html_path,spec_path", generate_testdata())
def test_html2docx(html_path, spec_path):
    html_rel_path = html_path.relative_to(PROJECT_DIR)
    spec_rel_path = spec_path.relative_to(PROJECT_DIR)

    title = html_path.name
    html = html_path.read_text()
    with spec_path.open() as fp:
        spec = json.load(fp)

    buf = html2docx(html, title=title)
    doc = docx.Document(buf)

    assert doc.core_properties.title == title
    assert_element_comply_with_spec(doc, spec, html_rel_path, spec_rel_path)

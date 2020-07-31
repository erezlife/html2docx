import os

import docx

from html2docx import html2docx

from .utils import TEST_DIR


def test_table():
    html_path = os.path.join(TEST_DIR, "table.html")
    html = open(html_path).read()
    buf = html2docx(html, title="table")

    doc = docx.Document(buf)

    assert len(doc.tables) == 1
    table = doc.tables[0]

    assert len(table.rows) == 3
    assert len(table.columns) == 2

    contents = [
        ("column1", "column2"),
        ("1", "2"),
        ("3", "4"),
    ]

    for r, row in enumerate(contents):
        for c, text in enumerate(row):
            assert table.cell(r, c).text == text

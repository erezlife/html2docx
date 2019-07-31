"""Parser for converting HTML to DOCX

Accept input from a source like TinyMCE generated HTML. The
source HTML may be preprocessed to limit tags and attributes.
The input HTML must be valid with all closing tags (except
for `br` tag).

This module assumes a few conventions:

- Block elements: `h1` to `h6`, `p`, `ol`, `ul`.
- Any text inside a block element (`div`, `blockquote`, `pre`) that is
  not inside a `p` element will have its own `p` element created
  for it. The block element itself is not represented in the
  resulting document.
"""

from html.parser import HTMLParser
from io import BytesIO
from typing import Dict, List, Tuple
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt


PT_WHITESPACE = re.compile(r"\s+")
PT_VALPX = re.compile(r"^\d+px$")


def get_attrs(attrs: List) -> List:
    args = []
    for attr in attrs:
        if attr == ("style", "text-decoration: underline;"):
            args.append("underline")
        elif attr == ("style", "text-decoration: line-through;"):
            args.append("strike")
    return args


def get_p_style(a: str) -> Dict:
    """Split a MIME type formatted text into a dictionary

    >>> get_p_style("param1: Value 1; param2: value two;")
    {'param1': 'Value 1', 'param2': 'value two'}
    """
    return dict((t.strip() for t in i.split(":")) for i in a.split(";") if i)


class HTML2Docx(HTMLParser):
    ALIGNMENTS = {
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
        "right": WD_ALIGN_PARAGRAPH.RIGHT,
        "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
    }

    def __init__(self, title: str):
        super().__init__()
        self.doc = Document()
        self.doc.core_properties.title = title

        self.font_name = None
        self.style = None
        self.pre = False
        self.p = None
        self.r = None
        self.list_styles = []
        self.attrs = []
        self.href = ""

    def _add_p(self, attrs=()) -> None:
        style = self.list_styles and self.list_styles[-1] or self.style
        self.p = self.doc.add_paragraph(style=style)
        p_stype = get_p_style(dict(attrs).get("style", ""))
        if p_stype.get("text-align"):
            self.p.alignment = self.ALIGNMENTS[p_stype["text-align"]]
        if re.match(PT_VALPX, p_stype.get("padding-left", "")):
            padding = int(p_stype["padding-left"][:-2])
            self.p.paragraph_format.left_indent = Pt(padding)
        self.r = None
        self.attrs = []

    def _add_r(self, attrs=None) -> None:
        if self.p is None:
            self._add_p()
        if attrs is not None:
            self.attrs.append(attrs)
        self.r = self.p.add_run()
        self.r.font.name = self.font_name
        for style in (a for s in self.attrs for a in s):
            setattr(self.r.font, style, True)

    def _curb_r(self) -> None:
        self.attrs = self.attrs[:-1]
        self.r = None

    def _ensure_r(self) -> None:
        if self.r is None:
            self._add_r()

    def _add_list_style(self, name: str) -> None:
        level = min(len(self.list_styles) + 1, 3)
        suffix = level > 1 and f" {level}" or ""
        self.list_styles.append(f"{name}{suffix}")
        self.p = None
        self.r = None

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        if tag == "a":
            self.href = dict(attrs).get("href")
            self._add_r([])
        elif tag in ("b", "strong"):
            self._add_r(["bold"])
        elif tag == "blockquote":
            self.style = "Quote"
        elif tag == "br":
            self._ensure_r()
            self.r.add_break()
        elif tag == "code":
            self.font_name = "Mono"
        elif tag in ("em", "i"):
            self._add_r(["italic"])
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[-1])
            self.p = self.doc.add_heading(level=level)
        elif tag == "ol":
            self._add_list_style("List Number")
        elif tag == "p":
            self._add_p(attrs=attrs)
        elif tag == "pre":
            self.pre = True
            self._add_p()
        elif tag == "span":
            run_attrs = get_attrs(attrs)
            self._add_r(run_attrs)
        elif tag == "sub":
            self._add_r(["subscript"])
        elif tag == "sup":
            self._add_r(["superscript"])
        elif tag == "u":
            self._add_r(["underline"])
        elif tag == "ul":
            self._add_list_style("List Bullet")

    def handle_data(self, data: str) -> None:
        if not data.strip() and self.p is None:  # whitespace between tags
            return
        self._ensure_r()
        if not self.pre:
            data = re.sub(PT_WHITESPACE, " ", data)
        self.r.add_text(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("a", "b", "em", "i", "span", "strong", "sub", "sup", "u"):
            if tag == "a" and self.href:
                self.r.add_text(f" [{self.href}]")
                self.href = ""
            self._curb_r()
        elif tag == "blockquote":
            self.style = None
        elif tag == "code":
            self.font_name = None
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6", "li", "ol", "p", "pre", "ul"):
            self.p = None
            self.r = None
            self.attrs = []
            if tag in ("ol", "ul"):
                self.list_styles = self.list_styles[:-1]
            elif tag == "pre":
                self.pre = False


def html2docx(content: str, title: str) -> BytesIO:
    """Convert valid HTML content to a docx document and return it as a
    io.BytesIO() object.
    """
    parser = HTML2Docx(title)
    parser.feed(content)

    buf = BytesIO()
    parser.doc.save(buf)
    return buf

import re
from html.parser import HTMLParser
from typing import Iterator, List, Optional, Tuple

from docx import Document
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from tinycss2 import parse_declaration_list
from tinycss2.ast import IdentToken

WHITESPACE_RE = re.compile(r"\s+")


def attr_to_css(attr: Tuple[str, Optional[str]]) -> Iterator[Tuple[str, str]]:
    name, value = attr
    if name == "style":
        for declaration in parse_declaration_list(value):
            for value in declaration.value:
                if isinstance(value, IdentToken):
                    yield declaration.lower_name, value.lower_value


def html_attrs_to_font_style(attrs: List[Tuple[str, Optional[str]]]) -> List[str]:
    """Return Font style names based on tag style attributes

    :param attrs:
        a list of attribute name plus attribute value tuples.
    :returns:
        a list of style names to be applied to Run Font property
    """
    styles = []
    for attr in attrs:
        for style in attr_to_css(attr):
            if style == ("text-decoration", "underline"):
                styles.append("underline")
            elif style == ("text-decoration", "line-through"):
                styles.append("strike")
    return styles


class HTML2Docx(HTMLParser):
    def __init__(self, title: str):
        super().__init__()
        self.doc = Document()
        self.doc.core_properties.title = title
        self.list_style: List[str] = []
        self.href = ""
        self._reset()

    def _reset(self) -> None:
        self.p: Optional[Paragraph] = None
        self.r: Optional[Run] = None

        # Formatting options
        self.pre = False
        self.attrs: List[List[str]] = []
        self.collapse_space = True

    def finish_p(self) -> None:
        if self.r is not None:
            self.r.text = self.r.text.rstrip()
        self._reset()

    def init_run(self, attrs: List[str]) -> None:
        self.attrs.append(attrs)
        if attrs:
            self.r = None

    def finish_run(self) -> None:
        attrs = self.attrs.pop()
        if attrs:
            self.r = None

    def add_text(self, data: str) -> None:
        if self.p is None:
            style = self.list_style[-1] if self.list_style else None
            self.p = self.doc.add_paragraph(style=style)
        if self.r is None:
            self.r = self.p.add_run()
            for attrs in self.attrs:
                for run_style in attrs:
                    setattr(self.r.font, run_style, True)
        self.r.add_text(data)

    def add_list_style(self, name: str) -> None:
        self.finish_p()
        # The template included by python-docx only has 3 list styles.
        level = min(len(self.list_style) + 1, 3)
        suffix = f" {level}" if level > 1 else ""
        self.list_style.append(f"{name}{suffix}")

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag == "a":
            self.href = str(next((val for name, val in attrs if name == "href"), ""))
            self.init_run([])
        elif tag in ["b", "strong"]:
            self.init_run(["bold"])
        elif tag == "br":
            if self.r:
                self.r.add_break()
        elif tag in ["em", "i"]:
            self.init_run(["italic"])
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag[-1])
            self.p = self.doc.add_heading(level=level)
        elif tag == "ol":
            self.add_list_style("List Number")
        elif tag == "pre":
            self.pre = True
        elif tag == "span":
            span_attrs = html_attrs_to_font_style(attrs)
            self.init_run(span_attrs)
        elif tag == "sub":
            self.init_run(["subscript"])
        elif tag == "sup":
            self.init_run(["superscript"])
        elif tag == "u":
            self.init_run(["underline"])
        elif tag == "ul":
            self.add_list_style("List Bullet")

    def handle_data(self, data: str) -> None:
        if not self.pre:
            data = re.sub(WHITESPACE_RE, " ", data)
        if self.collapse_space:
            data = data.lstrip()
        if data:
            if self.href:
                if data.endswith(" "):
                    data += self.href + " "
                else:
                    data += " " + self.href
                self.href = ""
            self.collapse_space = data.endswith(" ")
            self.add_text(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in ["a", "b", "em", "i", "span", "strong", "sub", "sup", "u"]:
            self.finish_run()
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6", "li", "ol", "p", "pre", "ul"]:
            self.finish_p()
            if tag in ["ol", "ul"]:
                del self.list_style[-1]
            elif tag == "pre":
                self.pre = False

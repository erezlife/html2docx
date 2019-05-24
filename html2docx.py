import io
import re
from html.parser import HTMLParser
from typing import List, Tuple

from docx import Document
from docx.text.paragraph import Paragraph

WHITESPACE_RE = re.compile(r"\s+")


class HTML2Docx(HTMLParser):
    header_re = re.compile(r"^h[1-6]$")

    def __init__(self, title: str):
        super().__init__()
        self.doc = Document()
        self.doc.core_properties.title = title

        self.p: Paragraph = None
        self.runs: List[Run] = []
        self.list_style: List[str] = []
        self.bold = 0
        self.italic = 0
        self.underline = 0
        self.extra_data = ""

    def feed(self, data: str) -> None:
        super().feed(data)
        self.finish()

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        if tag in ["p", "div"]:
            self.finish()
            self.p = self.doc.add_paragraph()
        elif tag == "br":
            self.out("\n", strip_whitespace=False)
        elif self.header_re.match(tag):
            self.finish()
            level = int(tag[-1])
            self.p = self.doc.add_heading(level=level)
        elif tag == "a":
            href = next((val for name, val in attrs if name == "href"), "")
            if href:
                self.extra_data = " " + href
        elif tag == "ul":
            self.add_list_style("List Bullet")
        elif tag == "ol":
            self.add_list_style("List Number")
        elif tag == "li":
            self.p = self.doc.add_paragraph(style=self.list_style[-1])
        elif tag in ["b", "strong"]:
            self.bold += 1
        elif tag in ["i", "em"]:
            self.italic += 1
        elif tag == "u":
            self.underline += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ["p", "div", "li"] or self.header_re.match(tag):
            self.finish()
            self.p = None
        elif tag == "a":
            self.extra_data = ""
        elif tag in ["ul", "ol"]:
            self.list_style.pop()
        elif tag in ["b", "strong"]:
            self.bold -= 1
        elif tag in ["i", "em"]:
            self.italic -= 1
        elif tag == "u":
            self.underline -= 1

    def handle_data(self, data: str) -> None:
        if self.p or data.strip():
            self.out(data)

    def out(self, data: str, strip_whitespace: bool = True) -> None:
        if not self.p:
            self.p = self.doc.add_paragraph()

        if self.extra_data:
            data += self.extra_data

        run = Run(
            data,
            bold=bool(self.bold),
            italic=bool(self.italic),
            underline=bool(self.underline),
            strip_whitespace=strip_whitespace,
        )
        self.runs.append(run)

    def finish(self) -> None:
        """Collapse white space across runs."""
        prev_run = None
        for run in self.runs:
            if run.strip_whitespace:
                run.text = WHITESPACE_RE.sub(" ", run.text.strip())
                if prev_run and prev_run.strip_whitespace:
                    if prev_run.needs_space_suffix:
                        prev_run.text += " "
                    elif run.text and run.needs_space_prefix:
                        run.text = " " + run.text
            prev_run = run

        for run in self.runs:
            if run.text:
                doc_run = self.p.add_run(run.text)
                doc_run.bold = run.bold
                doc_run.italic = run.italic
                doc_run.underline = run.underline

        self.p = None
        self.runs = []

    def add_list_style(self, style: str) -> None:
        self.finish()
        if self.list_style:
            # The template included by python-docx only has 3 list styles.
            level = min(len(self.list_style) + 1, 3)
            style = f"{style} {level}"
        self.list_style.append(style)


class Run:
    def __init__(
        self,
        text: str,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strip_whitespace: bool = True,
    ):
        self.text = text
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.strip_whitespace = strip_whitespace

        self.needs_space_prefix = bool(WHITESPACE_RE.match(text[0]))
        self.needs_space_suffix = bool(WHITESPACE_RE.match(text[-1]))


def html2docx(content: str, title: str) -> io.BytesIO:
    """Convert valid HTML content to a docx document and return it as a
    io.BytesIO() object.

    """
    parser = HTML2Docx(title)
    parser.feed(content)

    buf = io.BytesIO()
    parser.doc.save(buf)
    return buf

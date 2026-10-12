#!/usr/bin/env python3
"""Extracts the text of a transcript saved in .docx format.

Usage:
    python3 docx2txt.py <file.docx> [<output.txt>]

Without an output file the text goes to stdout (UTF-8). Standard library only:
nothing to install. Reads the body of the document (paragraphs, table cells,
line breaks) and, if present, the comments of the document, which are appended
in a separate section because they can contain notes useful for reading.
"""
import sys
import zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _paragraphs(xml_bytes):
    """Returns the non-empty paragraphs of a WordprocessingML XML part."""
    root = ET.fromstring(xml_bytes)
    out = []
    for p in root.iter(W + "p"):
        pieces = []
        for node in p.iter():
            if node.tag == W + "t" and node.text:
                pieces.append(node.text)
            elif node.tag == W + "tab":
                pieces.append("\t")
            elif node.tag in (W + "br", W + "cr"):
                pieces.append("\n")
        text = "".join(pieces).strip()
        if text:
            out.append(text)
    return out


def extract(docx_path):
    """Returns (body_paragraphs, comment_paragraphs)."""
    with zipfile.ZipFile(docx_path) as z:
        names = set(z.namelist())
        if "word/document.xml" not in names:
            raise ValueError("The file does not contain word/document.xml: it is not a valid .docx")
        body = _paragraphs(z.read("word/document.xml"))
        comments = _paragraphs(z.read("word/comments.xml")) if "word/comments.xml" in names else []
    return body, comments


def to_text(body, comments):
    text = "\n".join(body)
    if comments:
        text += "\n\n--- COMMENTS OF THE DOCUMENT ---\n" + "\n".join(comments)
    return text + "\n"


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 2
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    body, comments = extract(argv[1])
    text = to_text(body, comments)
    if len(argv) >= 3:
        with open(argv[2], "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        dest = argv[2]
    else:
        sys.stdout.write(text)
        dest = "stdout"
    print(
        f"[docx2txt] paragraphs: {len(body)} | characters: {sum(len(p) for p in body)}"
        f" | comments: {len(comments)} | output: {dest}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

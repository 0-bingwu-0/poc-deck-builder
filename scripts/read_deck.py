#!/usr/bin/env python3
"""Print the text of a PowerPoint file, slide by slide, with speaker notes.

Usage:
    python3 scripts/read_deck.py references/past-deck.pptx

For reading past decks, decks to review, and PowerPoint files in a POC's
materials. Text in shapes and tables comes out in order; pictures show as
[Picture: alt text]. Charts and the pictures themselves aren't read. Uses only
the Python standard library.
"""
import posixpath
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def relationships(z, part):
    """Id -> (type, part name) for one part."""
    folder, name = posixpath.split(part)
    path = posixpath.join(folder, "_rels", name + ".rels")
    if path not in z.namelist():
        return {}
    out = {}
    for rel in ET.fromstring(z.read(path)).iter(PKG + "Relationship"):
        target = posixpath.normpath(posixpath.join(folder, rel.get("Target")))
        out[rel.get("Id")] = (rel.get("Type").rsplit("/", 1)[-1], target)
    return out


def paragraphs(element):
    for p in element.iter(A + "p"):
        text = "".join(t.text or "" for t in p.iter(A + "t")).strip()
        if text:
            yield text


def slide_lines(root):
    lines = []
    for el in root.iter():
        if el.tag == P + "sp":
            ph = el.find(f"{P}nvSpPr/{P}nvPr/{P}ph")
            kind = ph.get("type") if ph is not None else None
            if kind in ("sldNum", "dt", "ftr"):
                continue
            texts = list(paragraphs(el))
            if kind in ("title", "ctrTitle") and texts:
                texts = ["**" + " ".join(texts) + "**"]
            lines += texts
        elif el.tag == A + "tr":
            cells = [" ".join(paragraphs(tc)) for tc in el.findall(A + "tc")]
            lines.append("| " + " | ".join(cells) + " |")
        elif el.tag == P + "pic":
            props = el.find(f"{P}nvPicPr/{P}cNvPr")
            descr = props.get("descr") if props is not None else ""
            lines.append(f"[Picture: {descr}]" if descr else "[Picture]")
    return lines


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 scripts/read_deck.py <file.pptx>")
    path = Path(sys.argv[1])
    if not path.is_file():
        sys.exit(f"Not found: {path}")
    with zipfile.ZipFile(path) as z:
        pres = ET.fromstring(z.read("ppt/presentation.xml"))
        rels = relationships(z, "ppt/presentation.xml")
        ids = pres.find(P + "sldIdLst")
        slides = [rels[s.get(R + "id")][1] for s in ids] if ids is not None else []
        for n, part in enumerate(slides, 1):
            print(f"## Slide {n}\n")
            for line in slide_lines(ET.fromstring(z.read(part))):
                print(line)
            for kind, target in relationships(z, part).values():
                if kind == "notesSlide":
                    notes = ET.fromstring(z.read(target))
                    for sp in notes.iter(P + "sp"):
                        ph = sp.find(f"{P}nvSpPr/{P}nvPr/{P}ph")
                        if ph is not None and ph.get("type") == "body":
                            text = " ".join(paragraphs(sp))
                            if text:
                                print(f"\nNotes: {text}")
            print()


if __name__ == "__main__":
    main()

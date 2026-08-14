#!/usr/bin/env python3
"""Does the text fit? Measure the render. Do not estimate it.

python-pptx will write more text than a box can show, and say nothing. PowerPoint reveals it on
the screen, which is where everyone else finds out.

The obvious way to check is arithmetic: font size times line spacing times number of lines. That
way is a trap, and this file exists because the trap was walked into from both sides on the same
deck. A constant of 1.42 under-estimated CJK line pitch and let a slide's body cross into the
footer. Measuring the render gave 24.0 pt for 15 pt type — 1.60. Raising the constant to 1.62 then
**refused about 290 passages that rendered perfectly well**. An estimator tuned away from one
failure walks straight into the other, and the same trap was hit again five months later from a
different direction: sizing a block at font x 1.06 without accounting for the roughly 1.2 leading
PowerPoint adds on top, so a 21-line list computed to 4.1 in and needed 5.1.

None of that arithmetic is necessary. **The render already knows.** `pdftotext -bbox` gives every
line's rectangle in points, and the .pptx gives every shape's rectangle. Two comparisons:

    OFF_SLIDE   a line's bottom crosses into the reserved band at the foot of the page, or past it
    CARD        a line's bottom passes the bottom of the filled block it is sitting in

WHY THERE IS NO ESTIMATOR IN HERE AS A FALLBACK
    Because two backends that nobody asserts agree are not a safety net; they are a second opinion
    with no tiebreaker, and the softer one gets believed. If the PDF is missing this exits 2 — it
    could not run — rather than 0. A check that reports "fine" when it did not look is worse than
    no check, because it is quoted.

SHIPPING A PDF IS NOT AN EXTRA STEP
    Validation in this skill already requires a PDF export (it is half of the Mac-compatibility
    check, and the portable fallback for a venue without your fonts). This reads the file you were
    going to produce anyway.

    LibreOffice: `soffice --headless --convert-to pdf deck.pptx`.

Stdlib only, plus `pdftotext` (poppler) on PATH.

Usage:
    check_text_overflow.py deck.pptx --pdf deck.pdf [--json out.json] [--strict]

Exit: 0 clean (or findings without --strict), 1 findings with --strict, 2 could not measure.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

DETECTOR = "check_text_overflow"

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"

EMU_PER_INCH = 914400
PT_PER_INCH = 72.0

# A few points of descender slack inside a block. Below this a "finding" is a font's tail, not text
# leaving its box.
CARD_TOL_PT = 5.0

# What counts as a block text is expected to stay inside. Bars, rules and hairlines are not blocks,
# and treating them as such turns every divider into a container with text overflowing it.
MIN_CARD_W_IN = 2.0
MIN_CARD_H_IN = 0.9


@dataclass
class Finding:
    detector: str
    verdict: str
    slide: Optional[int]
    summary: str
    evidence: List[str] = field(default_factory=list)


class CannotMeasure(Exception):
    """Raised when the answer would have to be guessed. Never downgraded to a pass."""


def run_pdftotext(pdf: Path) -> str:
    if not shutil.which("pdftotext"):
        raise CannotMeasure(
            "pdftotext is not on PATH. It ships with poppler (macOS: brew install poppler; "
            "Debian/Ubuntu: apt install poppler-utils).")
    try:
        return subprocess.run(["pdftotext", "-bbox", str(pdf), "-"],
                              capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as exc:
        raise CannotMeasure(f"pdftotext could not read {pdf} ({exc})") from exc


def parse_bbox(xml: str) -> Dict[int, List[Tuple[float, float, float, float, str]]]:
    """{page: [(x0, y0, x1, y1, text)]} in points, y measured from the top of the page."""
    pages: Dict[int, List[Tuple[float, float, float, float, str]]] = {}
    cur = 0
    for m in re.finditer(r'<page width="([\d.]+)" height="([\d.]+)">|'
                         r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">'
                         r'(.*?)</line>', xml, re.S):
        if m.group(1):
            cur += 1
            pages[cur] = []
        elif cur:
            txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(7))).strip()
            pages[cur].append((float(m.group(3)), float(m.group(4)),
                               float(m.group(5)), float(m.group(6)), txt))
    return pages


def deck_geometry(pptx: Path) -> Tuple[float, float, Dict[int, List[Tuple[float, ...]]]]:
    """-> (slide width pt, slide height pt, {slide: [block rectangles in pt]}).

    A block is a filled autoshape big enough to be a card. Shapes that carry `<a:spAutoFit/>` are
    skipped: there the declared height is a floor PowerPoint recomputes, so text below it is the
    shape growing, not text escaping.
    """
    blocks: Dict[int, List[Tuple[float, ...]]] = {}
    with zipfile.ZipFile(pptx) as z:
        pres = ET.fromstring(z.read("ppt/presentation.xml"))
        sz = pres.find(f"{P}sldSz")
        w_emu = int(sz.get("cx")) if sz is not None else 12192000
        h_emu = int(sz.get("cy")) if sz is not None else 6858000

        names = sorted(
            (n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
            key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[1]).group(1)),
        )
        for i, n in enumerate(names, start=1):
            root = ET.fromstring(z.read(n))
            tree = root.find(f".//{P}cSld/{P}spTree")
            rects: List[Tuple[float, ...]] = []
            if tree is not None:
                for sp in tree.iter(f"{P}sp"):
                    spPr = sp.find(f"{P}spPr")
                    if spPr is None or spPr.find(f"{A}solidFill") is None:
                        continue
                    if sp.find(f".//{A}spAutoFit") is not None:
                        continue
                    xfrm = spPr.find(f"{A}xfrm")
                    if xfrm is None:
                        continue
                    off, ext = xfrm.find(f"{A}off"), xfrm.find(f"{A}ext")
                    if off is None or ext is None:
                        continue
                    x, y = int(off.get("x", 0)), int(off.get("y", 0))
                    cx, cy = int(ext.get("cx", 0)), int(ext.get("cy", 0))
                    if cx / EMU_PER_INCH < MIN_CARD_W_IN or cy / EMU_PER_INCH < MIN_CARD_H_IN:
                        continue
                    s = PT_PER_INCH / EMU_PER_INCH
                    rects.append((x * s, y * s, (x + cx) * s, (y + cy) * s))
            blocks[i] = rects
    return w_emu / EMU_PER_INCH * PT_PER_INCH, h_emu / EMU_PER_INCH * PT_PER_INCH, blocks


_PAGE_NUMBER = re.compile(r"^\s*\d{1,3}\s*(?:[/|]\s*\d{1,3}\s*)?$")


def audit(pptx: Path, bbox_xml: str, reserve_in: float) -> List[Finding]:
    _w_pt, h_pt, blocks = deck_geometry(pptx)
    pages = parse_bbox(bbox_xml)

    if len(pages) != len(blocks):
        raise CannotMeasure(
            f"the PDF has {len(pages)} page(s) and the deck has {len(blocks)} slide(s). "
            "Page N has to be slide N for this comparison to mean anything — export the slides "
            "themselves, not a handout or a notes-pages layout.")

    safe_bottom = h_pt - reserve_in * PT_PER_INCH
    out: List[Finding] = []
    for pg, lines in sorted(pages.items()):
        for x0, y0, x1, y1, txt in lines:
            if not txt or _PAGE_NUMBER.match(txt):
                continue
            if y1 > safe_bottom:
                out.append(Finding(
                    DETECTOR, "OFF_SLIDE", pg,
                    f"Slide {pg}: a line ends {(y1 - safe_bottom) / PT_PER_INCH:.2f} in into the "
                    f"reserved band at the foot of the slide.",
                    [f"measured bottom {y1 / PT_PER_INCH:.2f} in of a "
                     f"{h_pt / PT_PER_INCH:.2f} in slide — {txt[:44]!r}"],
                ))
                continue
            for cx0, cy0, cx1, cy1 in blocks.get(pg, []):
                inside_x = x0 >= cx0 - 6 and x1 <= cx1 + 6
                starts_in = cy0 - 6 <= y0 <= cy1
                if inside_x and starts_in and y1 > cy1 + CARD_TOL_PT:
                    out.append(Finding(
                        DETECTOR, "CARD", pg,
                        f"Slide {pg}: a line ends "
                        f"{(y1 - cy1) / PT_PER_INCH:.2f} in below the block it sits in.",
                        [f"measured bottom {y1 / PT_PER_INCH:.2f} in, block bottom "
                         f"{cy1 / PT_PER_INCH:.2f} in — {txt[:44]!r}"],
                    ))
                    break
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("deck", type=Path, help="the .pptx")
    ap.add_argument("--pdf", type=Path, help="the rendered PDF of that same deck (required)")
    ap.add_argument("--bbox-xml", type=Path,
                    help="a recorded `pdftotext -bbox` output to use instead of running it. "
                         "Same measurement, same parser, supplied from a file — this is how the "
                         "challenge card stays deterministic without poppler.")
    ap.add_argument("--bottom-reserve-in", type=float, default=0.10,
                    help="band at the foot of the slide text must not enter (default 0.10 in)")
    ap.add_argument("--json", type=Path)
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()

    if not a.deck.is_file():
        print(f"cannot read {a.deck}", file=sys.stderr)
        return 2
    if a.pdf is None and a.bbox_xml is None:
        print("this check measures the render, so it needs --pdf: the deck exported to PDF "
              "(soffice --headless --convert-to pdf deck.pptx). Without it there is nothing to "
              "measure, and guessing from line-height constants is the failure this replaced.",
              file=sys.stderr)
        return 2
    for p in (a.pdf, a.bbox_xml):
        if p is not None and not p.is_file():
            print(f"cannot read {p}", file=sys.stderr)
            return 2

    try:
        xml = a.bbox_xml.read_text(encoding="utf-8") if a.bbox_xml else run_pdftotext(a.pdf)
        findings = audit(a.deck, xml, a.bottom_reserve_in)
    except CannotMeasure as exc:
        print(f"could not measure: {exc}", file=sys.stderr)
        return 2
    except (zipfile.BadZipFile, ET.ParseError, KeyError) as exc:
        print(f"{a.deck} is not a readable .pptx ({exc})", file=sys.stderr)
        return 2

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(
            {"detector": DETECTOR, "deck": str(a.deck),
             "measured_from": str(a.bbox_xml or a.pdf),
             "findings": [f.__dict__ for f in findings]},
            indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not findings:
        print("OK: measured the render; no line leaves its block or the slide.")
        return 0

    print(f"{len(findings)} overflow(s), measured\n")
    for f in findings:
        print(f"  [{f.verdict}] (slide {f.slide})")
        print(f"      {f.summary}")
        for e in f.evidence:
            print(f"      - {e}")
        print()
    return 1 if a.strict else 0


if __name__ == "__main__":
    sys.exit(main())

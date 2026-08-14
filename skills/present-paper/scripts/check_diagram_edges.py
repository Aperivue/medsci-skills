#!/usr/bin/env python3
"""A box drawn on the canvas edge does not look clipped on the slide. It looks like a missing line.

This skill's highest-yield rule is that diagrams are drawn as code and inserted as images. The cost
of that rule is a second coordinate system: the drawing is correct in the figure's units and wrong
at the figure's boundary, where a stroke placed exactly on the edge is half-cut by the render. On
the slide the reader does not see a clipped box. They see a box whose right side is missing, and
they wonder what it means.

    DIAGRAM_EDGE_CLIP   ink within a few pixels of the image border.

The reason this is a check and not a note in a style guide is what happened the day it was first
written. A reader had found one clipped diagram by eye — "the right-hand line of the box on slide 33
is cut" — and the guard written that same afternoon immediately found a second one, on a different
slide, that nobody had noticed. This defect is caught one instance at a time by people and all at
once by arithmetic.

The fix is upstream, in the drawing: keep an explicit inner margin so nothing is laid out against
the boundary, and save with `bbox_inches="tight"` plus a pad. Cropping the PNG afterwards does not
help — the stroke is already half gone.

FULL-BLEED IMAGES ARE NOT CLIPPED DIAGRAMS
    A photograph, or a diagram deliberately framed to its border, has ink along all four edges by
    construction. Reporting those would make this fire on every screenshot in the deck. So an image
    whose four borders are essentially solid is left alone; the signature of a clip is ink touching
    some edges and not others, or touching one edge partially.

Needs Pillow and numpy (both arrive with python-pptx, which this skill already requires).

Usage:
    check_diagram_edges.py IMAGE_OR_DIR [...] [--margin-px 3] [--json out.json] [--strict]

Exit: 0 clean (or findings without --strict), 1 findings with --strict, 2 nothing readable.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

DETECTOR = "check_diagram_edges"

SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}

# An edge this saturated is a design decision, not a casualty. Applied to all four at once.
BLEED_FRACTION = 0.90


@dataclass
class Finding:
    detector: str
    verdict: str
    slide: Optional[int]
    summary: str
    evidence: List[str] = field(default_factory=list)


def edge_ink(path: Path, margin: int) -> Dict[str, float]:
    """Fraction of each border strip that carries ink. Empty dict if the image cannot be read."""
    from PIL import Image  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    with Image.open(path) as im:
        a = np.asarray(im.convert("RGBA"))
    if a.size == 0:
        return {}
    alpha = a[..., 3]
    # A transparent background states where the drawing is. An opaque one does not, so fall back to
    # "darker than near-white", which is what a stroke on a white figure is.
    ink = alpha > 8 if alpha.min() < 255 else a[..., :3].sum(-1) < 720
    m = max(1, margin)
    return {
        "top": float(ink[:m, :].mean()),
        "bottom": float(ink[-m:, :].mean()),
        "left": float(ink[:, :m].mean()),
        "right": float(ink[:, -m:].mean()),
    }


def audit(images: List[Path], margin: int) -> List[Finding]:
    out: List[Finding] = []
    for p in images:
        frac = edge_ink(p, margin)
        if not frac:
            continue
        if all(v >= BLEED_FRACTION for v in frac.values()):
            continue  # full-bleed by construction
        touched = {k: v for k, v in frac.items() if v > 0}
        if not touched:
            continue
        where = ", ".join(f"{k} ({v * 100:.0f}% of the strip)"
                          for k, v in sorted(touched.items(), key=lambda kv: -kv[1]))
        out.append(Finding(
            DETECTOR, "DIAGRAM_EDGE_CLIP", None,
            f"{p.name}: ink reaches the image border on {len(touched)} side(s) — {where}.",
            [f"Checked the outer {margin} px.",
             "On the slide this reads as a box with a side missing, not as a cropped picture. Add "
             "an inner margin in the drawing and save with bbox_inches='tight' and a pad; "
             "re-cropping the PNG cannot restore a stroke that is already half gone."],
        ))
    return out


def expand(paths: List[Path]) -> List[Path]:
    out: List[Path] = []
    for p in paths:
        if p.is_dir():
            out += sorted(q for q in p.rglob("*") if q.suffix.lower() in SUFFIXES)
        elif p.is_file() and p.suffix.lower() in SUFFIXES:
            out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("images", nargs="+", type=Path, help="image files, or directories of them")
    ap.add_argument("--margin-px", type=int, default=3,
                    help="how close to the border counts as touching it (default 3)")
    ap.add_argument("--json", type=Path)
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()

    files = expand(a.images)
    if not files:
        print("no readable images in the given paths", file=sys.stderr)
        return 2

    try:
        findings = audit(files, a.margin_px)
    except ImportError as exc:
        print(f"needs Pillow and numpy ({exc})", file=sys.stderr)
        return 2

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(
            {"detector": DETECTOR, "images": [str(f) for f in files],
             "findings": [f.__dict__ for f in findings]},
            indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not findings:
        print(f"OK: {len(files)} image(s) keep their ink off the border.")
        return 0

    print(f"{len(findings)} of {len(files)} image(s) touch their own border\n")
    for f in findings:
        print(f"  [{f.verdict}]")
        print(f"      {f.summary}")
        for e in f.evidence:
            print(f"      - {e}")
        print()
    return 1 if a.strict else 0


if __name__ == "__main__":
    sys.exit(main())

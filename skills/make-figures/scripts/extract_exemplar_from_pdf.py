#!/usr/bin/env python3
r"""extract_exemplar_from_pdf.py — Extract a figure region from a PDF page to
build the exemplar reference set used by the make-figures Critic Loop.

Renders a single PDF page at 300 DPI (configurable), optionally crops a
sub-region, and writes the PNG + a YAML metadata sidecar + a _why.md stub
into references/exemplar_diagrams/{type}/.

Example:
    python extract_exemplar_from_pdf.py \
        --pdf /Users/eugene/Zotero/storage/ABCD/Yan2017.pdf \
        --page 3 \
        --type stard \
        --label Yan2017_STARD \
        --doi 10.1148/radiol.2017170371 \
        --crop 0.05,0.1,0.95,0.6 \
        --dpi 300
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

DEFAULT_EXEMPLAR_DIR = Path(__file__).resolve().parent.parent / "references" / "exemplar_diagrams"
VALID_TYPES = {"stard", "consort", "prisma", "pipeline", "roc", "forest", "km", "other"}


def render_page(pdf_path: Path, page_num: int, dpi: int, crop: Optional[tuple] = None) -> bytes:
    doc = fitz.open(pdf_path)
    try:
        if page_num < 1 or page_num > doc.page_count:
            raise ValueError(f"Page {page_num} out of range (1-{doc.page_count})")
        page = doc[page_num - 1]
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        if crop:
            rect = page.rect
            x0, y0, x1, y1 = crop
            clip = fitz.Rect(
                rect.x0 + rect.width * x0,
                rect.y0 + rect.height * y0,
                rect.x0 + rect.width * x1,
                rect.y0 + rect.height * y1,
            )
            pix = page.get_pixmap(matrix=matrix, clip=clip, alpha=False)
        else:
            pix = page.get_pixmap(matrix=matrix, alpha=False)
        return pix.tobytes("png")
    finally:
        doc.close()


def parse_crop(s: str) -> tuple:
    parts = [float(p.strip()) for p in s.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("crop must be 'x0,y0,x1,y1' as fractions 0.0–1.0")
    for v in parts:
        if not 0.0 <= v <= 1.0:
            raise argparse.ArgumentTypeError(f"crop fraction {v} out of range 0.0–1.0")
    if parts[0] >= parts[2] or parts[1] >= parts[3]:
        raise argparse.ArgumentTypeError("crop x0<x1 and y0<y1 required")
    return tuple(parts)


def write_metadata(meta_path: Path, **fields) -> None:
    lines = ["# Exemplar metadata (YAML)"]
    for k, v in fields.items():
        if v is None:
            continue
        if isinstance(v, str):
            lines.append(f'{k}: "{v}"')
        elif isinstance(v, (list, tuple)):
            lines.append(f"{k}: {list(v)}")
        else:
            lines.append(f"{k}: {v}")
    meta_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_why_stub(why_path: Path, label: str, figure_type: str) -> None:
    if why_path.exists():
        return  # don't clobber existing notes
    why_path.write_text(
        f"""# Why this exemplar is good — {label} ({figure_type})

<!-- 50–100 words on why this figure is a quality anchor. Fill in during curation. -->

Hierarchy / structure:

Whitespace & balance:

Typography (font size, weight, alignment):

Emphasis (which elements are visually strongest, why):

Color usage:

Weaknesses (if any — nothing is perfect):
""",
        encoding="utf-8",
    )


def extract_one(
    pdf: Path,
    page: int,
    figure_type: str,
    label: str,
    doi: Optional[str],
    crop: Optional[tuple],
    dpi: int,
    exemplar_dir: Path,
) -> Path:
    if figure_type not in VALID_TYPES:
        raise ValueError(f"type must be one of {sorted(VALID_TYPES)}, got {figure_type}")
    target_dir = exemplar_dir / figure_type
    target_dir.mkdir(parents=True, exist_ok=True)

    png_bytes = render_page(pdf, page, dpi, crop)
    safe_label = label.replace("/", "_").replace(" ", "_")
    png_path = target_dir / f"{safe_label}.png"
    meta_path = target_dir / f"{safe_label}.meta.yaml"
    why_path = target_dir / f"{safe_label}_why.md"

    png_path.write_bytes(png_bytes)
    write_metadata(
        meta_path,
        label=label,
        figure_type=figure_type,
        source_pdf=str(pdf),
        page=page,
        crop=list(crop) if crop else None,
        dpi=dpi,
        doi=doi,
    )
    write_why_stub(why_path, label, figure_type)

    return png_path


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pdf", required=True, type=Path, help="Path to source PDF")
    p.add_argument("--page", required=True, type=int, help="1-based page number")
    p.add_argument("--type", dest="figure_type", required=True, choices=sorted(VALID_TYPES),
                   help="Exemplar category (subdirectory under exemplar_diagrams/)")
    p.add_argument("--label", required=True, help="Short label, used as filename stem (e.g., Yan2017_STARD)")
    p.add_argument("--doi", default=None, help="DOI of source paper (for attribution)")
    p.add_argument("--crop", default=None, type=parse_crop,
                   help="Optional crop as 'x0,y0,x1,y1' fractions 0.0–1.0")
    p.add_argument("--dpi", type=int, default=300, help="Render DPI (default: 300)")
    p.add_argument("--exemplar-dir", type=Path, default=DEFAULT_EXEMPLAR_DIR,
                   help="Base exemplar directory (default: references/exemplar_diagrams/)")
    args = p.parse_args()

    if not args.pdf.exists():
        print(f"ERROR: PDF not found at {args.pdf}", file=sys.stderr)
        return 2

    try:
        out = extract_one(
            pdf=args.pdf,
            page=args.page,
            figure_type=args.figure_type,
            label=args.label,
            doi=args.doi,
            crop=args.crop,
            dpi=args.dpi,
            exemplar_dir=args.exemplar_dir,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Extracted: {out}")
    print(f"Metadata:  {out.with_suffix('')}.meta.yaml")
    print(f"Why stub:  {out.with_name(out.stem + '_why.md')}")
    print("\nNext: open the _why.md and add a 50–100 word note on why this figure is a quality anchor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

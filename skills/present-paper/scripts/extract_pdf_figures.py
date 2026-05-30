#!/usr/bin/env python3
"""Extract figures from PDF pages via pdftoppm + PIL crop (normalized box coords).

Two usage modes:

1. **CLI single-crop**: extract one or more figures from specific pages of a PDF
   using normalized (0–1) crop boxes.

       extract_pdf_figures.py paper.pdf \\
           --page 5 --crop 0.10,0.05,0.95,0.55 --out fig01.png

       extract_pdf_figures.py paper.pdf \\
           --pages 5,6 \\
           --crops "0.10,0.05,0.95,0.55;0.05,0.05,0.95,0.50" \\
           --out fig01.png,fig02.png

2. **YAML config batch**: extract many figures across multiple PDFs declaratively.

       extract_pdf_figures.py --config figures.yaml --out-dir extracted/

   YAML schema:

       dpi: 250                          # default 250; override per item with item.dpi
       pdf_dir: /abs/path/to/pdfs/       # optional base path resolved per item.pdf
       items:
         - name: fig01_concept_overview
           pdf: 01_paper.pdf             # joined with pdf_dir if relative
           page: 4                       # 1-indexed
           crop: [0.06, 0.08, 0.97, 0.52]  # [left, top, right, bottom] normalized
           caption: "Conceptual overview (Author YYYY Fig 1)"  # optional, only logged

Requires: pdftoppm (poppler-utils — `brew install poppler`), Pillow.
Optional: PyYAML for --config mode (`pip install pyyaml`).

Cross-references:
  - /present-paper Phase 3 (Slides & Notes)
  - references/slide_visual_styles/nature_lancet.md §5 (figure handling)
  - ~/.claude/rules/pptx-mac-compatibility.md §7 (Inches EMU pitfall)
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image
except ImportError:
    sys.stderr.write("ERROR: Pillow is required. Install: pip install Pillow\n")
    raise


def _parse_crop(s: str) -> tuple[float, float, float, float]:
    """Parse 'l,t,r,b' string into normalized box tuple. Validates 0 <= l<r <=1, t<b."""
    parts = s.split(",")
    if len(parts) != 4:
        raise ValueError(f"crop must be 4 comma-separated floats, got: {s!r}")
    l, t, r, b = (float(x) for x in parts)
    for label, v in (("left", l), ("top", t), ("right", r), ("bottom", b)):
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"crop {label}={v} not in [0,1]")
    if not (l < r and t < b):
        raise ValueError(f"crop must satisfy left<right and top<bottom; got {s!r}")
    return (l, t, r, b)


def _render_page(pdf: Path, page: int, dpi: int, tmp_dir: Path) -> Path:
    """Render a single PDF page to PNG using pdftoppm; return resulting file path."""
    if not pdf.exists():
        raise FileNotFoundError(f"PDF not found: {pdf}")
    out_prefix = tmp_dir / f"page_{page}"
    cmd = [
        "pdftoppm",
        "-png",
        "-r", str(dpi),
        "-f", str(page),
        "-l", str(page),
        str(pdf),
        str(out_prefix),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"pdftoppm failed for {pdf.name} page {page}:\n{proc.stderr.strip()}"
        )
    # pdftoppm writes "<prefix>-<padded_page>.png" — width varies with total pages.
    matches = sorted(tmp_dir.glob(f"page_{page}-*.png"))
    if not matches:
        raise RuntimeError(
            f"pdftoppm produced no output for {pdf.name} page {page} "
            f"(expected page_{page}-*.png in {tmp_dir})"
        )
    return matches[0]


def _crop_image(src: Path, box: tuple[float, float, float, float], dst: Path) -> tuple[int, int]:
    """Crop src image by normalized box and save to dst. Returns (w, h) of cropped image."""
    img = Image.open(src)
    W, H = img.size
    l, t, r, b = box
    cropped = img.crop((int(W * l), int(H * t), int(W * r), int(H * b)))
    dst.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(dst, "PNG", optimize=True)
    return cropped.size


def extract_one(pdf: Path, page: int, crop: tuple[float, float, float, float],
                out: Path, dpi: int = 250) -> Path:
    """Single-figure extraction. Returns the output path."""
    with tempfile.TemporaryDirectory() as td:
        page_png = _render_page(pdf, page, dpi, Path(td))
        w, h = _crop_image(page_png, crop, out)
        print(f"OK  {out.name:50s}  ({w}x{h})  {pdf.name} page {page}")
    return out


def extract_batch(items: Iterable[dict], out_dir: Path, default_dpi: int = 250,
                   pdf_dir: Path | None = None) -> list[Path]:
    """Batch extraction from YAML config. Caches rendered pages per (pdf, page, dpi).

    Each item dict accepts:
      name (str, required): output filename stem (.png appended)
      pdf  (str, required): PDF path (joined with pdf_dir if relative)
      page (int, required): 1-indexed PDF page number
      crop (list[float], required): [left, top, right, bottom] normalized
      dpi  (int, optional): override default_dpi
      caption (str, optional): logged only
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[Path] = []
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        cache: dict[tuple[str, int, int], Path] = {}
        for item in items:
            try:
                name = item["name"]
                pdf_str = item["pdf"]
                page = int(item["page"])
                crop = tuple(float(x) for x in item["crop"])
                if len(crop) != 4:
                    raise ValueError("crop must have 4 elements")
                dpi = int(item.get("dpi", default_dpi))
            except (KeyError, ValueError, TypeError) as e:
                print(f"SKIP item {item!r}: {e}")
                continue

            pdf = Path(pdf_str)
            if pdf_dir is not None and not pdf.is_absolute():
                pdf = pdf_dir / pdf

            cache_key = (str(pdf), page, dpi)
            if cache_key not in cache:
                try:
                    cache[cache_key] = _render_page(pdf, page, dpi, td_path)
                except (FileNotFoundError, RuntimeError) as e:
                    print(f"SKIP {name}: {e}")
                    continue

            dst = out_dir / f"{name}.png"
            try:
                w, h = _crop_image(cache[cache_key], crop, dst)
            except ValueError as e:
                print(f"SKIP {name}: {e}")
                continue

            caption = item.get("caption", "")
            tail = f"  {caption}" if caption else ""
            print(f"OK  {dst.name:50s}  ({w}x{h})  {pdf.name} page {page}{tail}")
            results.append(dst)

    print(f"\nTotal: {len(results)} figures in {out_dir}")
    return results


def _cli() -> int:
    p = argparse.ArgumentParser(
        description="Extract figures from PDF pages (pdftoppm + PIL crop).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("pdf", nargs="?", help="PDF input (single-crop mode); omit for --config mode")
    p.add_argument("--page", type=int, help="single-crop: 1-indexed page number")
    p.add_argument("--pages", help="single-crop: comma-separated pages (paired with --crops)")
    p.add_argument("--crop", help="single-crop: 'l,t,r,b' normalized box")
    p.add_argument("--crops", help="single-crop: ';'-separated 'l,t,r,b' boxes paired with --pages")
    p.add_argument("--out", help="single-crop: output path (or comma-separated paths)")
    p.add_argument("--out-dir", help="batch mode: output directory")
    p.add_argument("--dpi", type=int, default=250, help="render DPI (default 250)")
    p.add_argument("--config", help="batch mode: YAML config path")
    args = p.parse_args()

    # Batch (YAML) mode
    if args.config:
        try:
            import yaml  # type: ignore
        except ImportError:
            sys.stderr.write("ERROR: --config requires PyYAML. Install: pip install pyyaml\n")
            return 2
        cfg_path = Path(args.config)
        if not cfg_path.exists():
            sys.stderr.write(f"ERROR: config not found: {cfg_path}\n")
            return 2
        cfg = yaml.safe_load(cfg_path.read_text()) or {}
        items = cfg.get("items", [])
        out_dir = Path(args.out_dir or cfg.get("out_dir", "extracted"))
        dpi = int(args.dpi if args.dpi != 250 else cfg.get("dpi", 250))
        pdf_dir = cfg.get("pdf_dir")
        pdf_dir = Path(pdf_dir) if pdf_dir else None
        extract_batch(items, out_dir, default_dpi=dpi, pdf_dir=pdf_dir)
        return 0

    # Single-crop mode (single or paired)
    if not args.pdf:
        p.error("pdf positional argument required for single-crop mode (or use --config)")
    pdf = Path(args.pdf)

    if args.crops or args.pages:
        if not (args.crops and args.pages and args.out):
            p.error("--pages, --crops, and --out must all be set together")
        pages = [int(x) for x in args.pages.split(",")]
        crops = [_parse_crop(c) for c in args.crops.split(";")]
        outs = [Path(o.strip()) for o in args.out.split(",")]
        if not (len(pages) == len(crops) == len(outs)):
            p.error(
                f"counts mismatch: {len(pages)} pages, {len(crops)} crops, {len(outs)} outs"
            )
        for pg, cb, op in zip(pages, crops, outs):
            extract_one(pdf, pg, cb, op, dpi=args.dpi)
        return 0

    if not (args.page is not None and args.crop and args.out):
        p.error("single crop requires --page, --crop, --out")
    box = _parse_crop(args.crop)
    extract_one(pdf, args.page, box, Path(args.out), dpi=args.dpi)
    return 0


if __name__ == "__main__":
    sys.exit(_cli())

#!/usr/bin/env python3
"""Export a figure to a portal-ready TIFF — LZW-compressed, RGBA→RGB white-flattened.

Why this exists. Two submission-portal facts collide on figure upload:

  1. Some portals accept only a fixed raster set and NOT PNG. Springer Nature's SNAPP,
     for one, takes `.jpeg` / `.tiff` / `.eps` — a PNG has to be converted on the spot.
  2. A portal caps figure size (JACC: Asia rejects a figure over 25 MB). A raw,
     uncompressed 600-dpi RGBA TIFF blows straight past that; the *same* image saved
     LZW-compressed with the alpha channel flattened away is a fraction of the size and
     pixel-identical.

The naive conversion also introduces a print defect: a TIFF that keeps an alpha channel
renders the transparent regions BLACK on many print/production pipelines. Flattening the
alpha onto a white background (the paper) is what a human does by hand in Photoshop; this
does it deterministically and then PROVES the result is pixel-identical to that flatten
before it hands you the file.

What it does:
  * opens the input raster (any PIL-readable format — PNG, TIFF, BMP, …);
  * if it carries alpha/transparency (RGBA / LA / palette-with-transparency), composites
    it onto a solid background (white by default) to get RGB; a plain RGB/L image is kept;
  * saves TIFF with LZW compression (lossless), preserving dpi;
  * VERIFIES the output by independently re-flattening the source and comparing bytes —
    refuses (exit 1) if the produced TIFF is not pixel-identical to the expected flatten;
  * reports the before/after byte size and, with --max-mb, refuses an output that still
    exceeds the portal cap (so the failure surfaces here, not at the upload button).

This is a figure PRODUCER (like render_core_figures.py), not a manuscript detector. It
requires Pillow — the same runtime dependency every raster figure helper in this skill
already has — and does nothing over the network.

Usage:
  export_portal_tiff.py --in figure.png                    # -> figure.tiff (white bg, LZW)
  export_portal_tiff.py --in fig.png --out fig.tiff --max-mb 25
  export_portal_tiff.py --in fig.png --background 255,255,255 --dpi 600

Exit codes: 0 success (verified), 1 verification mismatch / over the --max-mb cap,
2 input/usage error (missing file, unreadable image, Pillow absent).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# A palette image can carry per-pixel transparency via a `transparency` info key.
ALPHA_MODES = ("RGBA", "LA", "PA", "La")


def _load_pillow():
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        sys.stderr.write(
            "ERROR: Pillow is required (pip install Pillow) — the same dependency the "
            "other raster figure helpers in /make-figures use.\n")
        sys.exit(2)
    from PIL import Image
    return Image


def _has_alpha(img) -> bool:
    """True if the image carries per-pixel transparency that a flatten must resolve."""
    if img.mode in ALPHA_MODES:
        return True
    # A palette (P) or grayscale image can still declare a transparent colour.
    return "transparency" in img.info


def flatten_to_rgb(img, background):
    """Return an RGB copy with any alpha composited onto `background` (an (R,G,B) tuple).
    A plain RGB/grayscale image (no transparency) is converted straight to RGB. This is the
    single definition of the flatten, used both to produce the output and to verify it."""
    if not _has_alpha(img):
        return img.convert("RGB")
    rgba = img.convert("RGBA")
    Image = _load_pillow()
    bg = Image.new("RGB", rgba.size, background)
    bg.paste(rgba, mask=rgba.split()[-1])  # last band is alpha
    return bg


def _parse_bg(s: str):
    parts = s.split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("background must be R,G,B (e.g. 255,255,255)")
    try:
        vals = tuple(int(p) for p in parts)
    except ValueError:
        raise argparse.ArgumentTypeError("background components must be integers 0-255")
    if not all(0 <= v <= 255 for v in vals):
        raise argparse.ArgumentTypeError("background components must be 0-255")
    return vals


def export(in_path: Path, out_path: Path, background, dpi, max_mb):
    Image = _load_pillow()
    try:
        src = Image.open(in_path)
        src.load()
    except Exception as e:  # noqa: BLE001 — PIL raises a variety of decode errors
        sys.stderr.write(f"ERROR: could not open image {in_path}: {e}\n")
        sys.exit(2)

    expected = flatten_to_rgb(src, background)

    save_kwargs = {"format": "TIFF", "compression": "tiff_lzw"}
    src_dpi = dpi or src.info.get("dpi")
    if src_dpi:
        save_kwargs["dpi"] = tuple(src_dpi) if not isinstance(src_dpi, (int, float)) else (src_dpi, src_dpi)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    expected.save(out_path, **save_kwargs)

    # Verify: reopen the produced TIFF and require it to be pixel-identical to the flatten,
    # LZW-compressed, and alpha-free. A silent decode surprise fails here, not at upload.
    with Image.open(out_path) as produced:
        produced.load()
        compression = produced.tag_v2.get(259) if hasattr(produced, "tag_v2") else None
        prod_rgb = produced.convert("RGB")
        identical = prod_rgb.tobytes() == expected.tobytes()

    problems = []
    if compression != 5:  # TIFF Compression tag: 5 == LZW
        problems.append(f"output is not LZW-compressed (Compression tag={compression}, expected 5)")
    if not identical:
        problems.append("output TIFF is NOT pixel-identical to the white-flattened source")

    in_mb = in_path.stat().st_size / (1024 * 1024)
    out_mb = out_path.stat().st_size / (1024 * 1024)
    if max_mb is not None and out_mb > max_mb:
        problems.append(f"output is {out_mb:.1f} MB, over the --max-mb {max_mb} portal cap")

    print("=" * 52)
    print(" Portal TIFF export")
    print("=" * 52)
    print(f"  in:          {in_path}  ({in_mb:.2f} MB, mode {src.mode})")
    print(f"  out:         {out_path}  ({out_mb:.2f} MB, mode RGB, LZW)")
    print(f"  flattened:   {'alpha composited onto ' + str(background) if _has_alpha(src) else 'no alpha (RGB kept)'}")
    print(f"  pixel-check: {'identical to source flatten' if identical else 'MISMATCH'}")
    if problems:
        print("\nFAIL: " + "; ".join(problems))
        return 1
    print("\nOK: portal-ready TIFF (LZW, RGB, pixel-identical to source).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Export a figure to a portal-ready TIFF (LZW, RGBA→RGB white-flatten).")
    ap.add_argument("--in", dest="inp", required=True, help="input raster image (PNG/TIFF/…)")
    ap.add_argument("--out", default=None, help="output .tiff (default: input stem + .tiff)")
    ap.add_argument("--background", type=_parse_bg, default=(255, 255, 255),
                    help="RGB fill for transparent regions (default 255,255,255 = white)")
    ap.add_argument("--dpi", type=int, default=None, help="override dpi (default: keep source dpi)")
    ap.add_argument("--max-mb", type=float, default=None,
                    help="refuse (exit 1) if the output still exceeds this many MB (e.g. 25 for a portal cap)")
    args = ap.parse_args()

    in_path = Path(args.inp)
    if not in_path.is_file():
        sys.stderr.write(f"ERROR: input not found: {in_path}\n")
        return 2
    out_path = Path(args.out) if args.out else in_path.with_suffix(".tiff")
    return export(in_path, out_path, args.background, args.dpi, args.max_mb)


if __name__ == "__main__":
    sys.exit(main())

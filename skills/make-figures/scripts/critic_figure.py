#!/usr/bin/env python3
"""critic_figure.py — Quantitative checks for make-figures skill output.

Part of the medsci-skills Critic Loop (Phase 1). This script runs deterministic
checks that do NOT require a language model:

  - DPI and physical dimensions vs. journal specification
  - Dominant-color analysis against the Wong colorblind-safe palette
  - OCR text extraction for minimum font-size estimation and
    optional coverage comparison against a source-text file

The qualitative side of the Critic Loop (layout balance, hierarchy,
readability, exemplar comparison) is handled by the Claude session afterward
using the rubrics in references/critic_rubrics/.

Usage:
    python critic_figure.py figures/fig1_stard.png \
        --type stard --spec-min-dpi 600 --spec-width-in 7.0 \
        --source-text figures/fig1_stard.txt \
        --out figures/fig1_stard.critique.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from PIL import Image

WONG_PALETTE: dict[str, tuple[int, int, int]] = {
    "black":          (0, 0, 0),
    "orange":         (230, 159, 0),
    "sky_blue":       (86, 180, 233),
    "bluish_green":   (0, 158, 115),
    "yellow":         (240, 228, 66),
    "blue":           (0, 114, 178),
    "vermillion":     (213, 94, 0),
    "reddish_purple": (204, 121, 167),
}
NEUTRAL_TOLERANCE = 25
PALETTE_DISTANCE_THRESHOLD = 60
DOMINANT_COLOR_TOP_N = 12
DOMINANT_COLOR_MIN_FRACTION = 0.002
OUT_OF_PALETTE_TOLERANCE = 0.15
MIN_READABLE_PX = 14


def color_distance(c1, c2) -> float:
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5


def classify_color(rgb) -> str:
    r, g, b = rgb
    if max(r, g, b) - min(r, g, b) < NEUTRAL_TOLERANCE:
        return "neutral"
    best_name, best_dist = None, float("inf")
    for name, palette_rgb in WONG_PALETTE.items():
        d = color_distance(rgb, palette_rgb)
        if d < best_dist:
            best_name, best_dist = name, d
    if best_dist < PALETTE_DISTANCE_THRESHOLD:
        return f"wong:{best_name}"
    return "out_of_palette"


def check_palette(img: Image.Image) -> dict:
    rgb_img = img.convert("RGB")
    total = rgb_img.size[0] * rgb_img.size[1]
    quant = rgb_img.quantize(colors=64).convert("RGB")
    pixels = quant.getcolors(maxcolors=64 * 64)
    if not pixels:
        return {"passed": None, "note": "too many colors to quantize"}

    dominant = []
    out_frac = 0.0
    for count, rgb in sorted(pixels, key=lambda x: -x[0])[:DOMINANT_COLOR_TOP_N]:
        fraction = count / total
        if fraction < DOMINANT_COLOR_MIN_FRACTION:
            continue
        label = classify_color(rgb)
        dominant.append({"rgb": list(rgb), "fraction": round(fraction, 4), "class": label})
        if label == "out_of_palette":
            out_frac += fraction

    return {
        "passed": out_frac < OUT_OF_PALETTE_TOLERANCE,
        "out_of_palette_fraction": round(out_frac, 4),
        "tolerance": OUT_OF_PALETTE_TOLERANCE,
        "dominant_colors": dominant,
    }


def check_dimensions(img: Image.Image, spec: dict) -> dict:
    w_px, h_px = img.size
    dpi = img.info.get("dpi", (None, None))
    dpi_x = dpi[0] if dpi and dpi[0] else None
    dpi_y = dpi[1] if dpi and dpi[1] else None
    result = {
        "width_px": w_px,
        "height_px": h_px,
        "dpi_x": dpi_x,
        "dpi_y": dpi_y,
    }
    min_dpi = spec.get("min_dpi")
    width_in = spec.get("width_in")
    if min_dpi and dpi_x:
        result["dpi_meets_spec"] = dpi_x >= min_dpi
        result["required_dpi"] = min_dpi
    if width_in and dpi_x:
        actual_width_in = w_px / dpi_x
        result["width_in"] = round(actual_width_in, 2)
        result["width_matches_spec"] = abs(actual_width_in - width_in) < 0.3
        result["required_width_in"] = width_in
    return result


def check_ocr(image_path: Path, source_text: Optional[str] = None) -> dict:
    try:
        import pytesseract
    except ImportError:
        return {"passed": None, "note": "pytesseract not installed; install with `pip install pytesseract` (tesseract binary already at /opt/homebrew/bin/tesseract)"}
    try:
        data = pytesseract.image_to_data(
            str(image_path), output_type=pytesseract.Output.DICT
        )
    except Exception as exc:
        return {"passed": None, "note": f"tesseract failed: {exc}"}

    words = []
    heights = []
    for i, word in enumerate(data.get("text", [])):
        if not word.strip():
            continue
        conf_raw = data["conf"][i]
        try:
            conf = int(conf_raw)
        except (TypeError, ValueError):
            conf = -1
        if conf < 50:
            continue
        words.append(word.strip())
        heights.append(data["height"][i])

    result: dict = {
        "word_count": len(words),
    }
    if heights:
        heights_sorted = sorted(heights)
        result["median_word_height_px"] = heights_sorted[len(heights_sorted) // 2]
        result["min_word_height_px"] = min(heights)
        result["min_readable_threshold_px"] = MIN_READABLE_PX

    if source_text:
        source_words = {w.lower().strip(".,:;()[]") for w in source_text.split() if len(w) > 2}
        ocr_words = {w.lower().strip(".,:;()[]") for w in words if len(w) > 2}
        missing = sorted(source_words - ocr_words)
        result["missing_source_words"] = missing[:20]
        result["missing_source_word_count"] = len(missing)
        result["source_word_coverage"] = round(
            len(source_words & ocr_words) / max(1, len(source_words)), 2
        )
    return result


def critique(
    image_path: Path,
    figure_type: Optional[str] = None,
    journal: Optional[str] = None,
    source_text: Optional[str] = None,
    spec: Optional[dict] = None,
) -> dict:
    img = Image.open(image_path)
    spec = spec or {}
    checks = {
        "dimensions": check_dimensions(img, spec),
        "palette": check_palette(img),
        "ocr": check_ocr(image_path, source_text=source_text),
    }

    flags = []
    dim = checks["dimensions"]
    if dim.get("dpi_meets_spec") is False:
        flags.append(
            f"DPI below journal spec ({dim.get('dpi_x')} < {dim.get('required_dpi')})"
        )
    if dim.get("width_matches_spec") is False:
        flags.append(
            f"Width deviates from journal spec ({dim.get('width_in')} in vs {dim.get('required_width_in')} in)"
        )
    pal = checks["palette"]
    if pal.get("passed") is False:
        flags.append(
            f"{pal['out_of_palette_fraction'] * 100:.1f}% pixels outside Wong palette (tolerance {OUT_OF_PALETTE_TOLERANCE * 100:.0f}%)"
        )
    ocr = checks["ocr"]
    min_h = ocr.get("min_word_height_px")
    if min_h and min_h < MIN_READABLE_PX:
        flags.append(f"Smallest OCR text only {min_h}px tall (<{MIN_READABLE_PX}px threshold)")
    if ocr.get("missing_source_word_count") and ocr["missing_source_word_count"] > 3:
        flags.append(
            f"{ocr['missing_source_word_count']} source words not detected by OCR (possible cropping/truncation)"
        )

    return {
        "image": str(image_path),
        "figure_type": figure_type,
        "journal": journal,
        "checks": checks,
        "flags": flags,
        "summary": "PASS" if not flags else f"{len(flags)} issue(s) flagged",
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Quantitative figure critic (medsci-skills Critic Loop, Phase 1).")
    p.add_argument("image", help="Path to generated figure (PNG)")
    p.add_argument(
        "--type", dest="figure_type",
        choices=[
            "stard", "consort", "prisma", "pipeline",
            "roc", "forest", "km", "calibration",
            "bland_altman", "confusion_matrix",
            "visual_abstract", "other",
        ],
    )
    p.add_argument("--journal", help="Journal key (e.g., radiology, radiology_ai, eur_radiol)")
    p.add_argument("--source-text", help="Path to text file with expected source strings for OCR coverage check")
    p.add_argument("--spec-width-in", type=float, help="Expected figure width in inches (per figure_specs.md)")
    p.add_argument("--spec-min-dpi", type=int, help="Minimum DPI (600 for line art, 300 for halftone)")
    p.add_argument("--out", default=None, help="Path to JSON report (default: {image}.critique.json)")
    args = p.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"ERROR: {image_path} not found", file=sys.stderr)
        return 2

    source_text = None
    if args.source_text:
        source_path = Path(args.source_text)
        if not source_path.exists():
            print(f"WARN: source text {source_path} not found; skipping OCR coverage check", file=sys.stderr)
        else:
            source_text = source_path.read_text(encoding="utf-8", errors="ignore")

    report = critique(
        image_path,
        figure_type=args.figure_type,
        journal=args.journal,
        source_text=source_text,
        spec={"width_in": args.spec_width_in, "min_dpi": args.spec_min_dpi},
    )
    out_path = Path(args.out) if args.out else image_path.with_suffix(image_path.suffix + ".critique.json")
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print(json.dumps({"summary": report["summary"], "flags": report["flags"]}, indent=2, ensure_ascii=False))
    print(f"\nFull report: {out_path}", file=sys.stderr)
    return 0 if not report["flags"] else 1


if __name__ == "__main__":
    sys.exit(main())

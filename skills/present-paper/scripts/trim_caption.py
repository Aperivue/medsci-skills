#!/usr/bin/env python3
"""Auto-trim journal figure PNGs to keep only the figure body.

Removes:
- Top running-head / journal title bar
- Bottom figure caption text ("FIGURE 1. ...")
- Surrounding whitespace

Strategy: horizontal-projection segmentation. Find whitespace bands, score
each non-white segment by (height * density), pick the largest as the figure.
Then trim left/right whitespace. Short white runs (< MIN_GAP_ROWS) inside a
figure (panel gaps) are tolerated so multi-panel figures are kept intact.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

DARK_THRESHOLD = 235  # pixel value below this counts as "dark/content"
WHITE_ROW_FRAC = 0.005  # row is "white" if <0.5% of its pixels are dark
WHITE_COL_FRAC = 0.005
MIN_GAP_ROWS = 5  # ≥ this many consecutive white rows splits segments
PAD = 6  # final padding around the kept block

# Edge trim heuristics
TOP_TEXT_MAX_FRAC = 0.18  # "top band" if segment.end is within top 18%
TOP_TEXT_MAX_PX = 150  # journal headers can be a thin colored bar (~80–140 px)
BOTTOM_TEXT_MIN_FRAC = 0.78  # "bottom region" if segment.start is in bottom 22%
BOTTOM_TEXT_MAX_PX = 260  # caption blocks can be multi-line — allow taller
MIN_GAP_BEFORE_CAPTION = 18  # require a clear visual gap before declaring caption
MIN_GAP_AFTER_HEADER = 30  # journal-header band followed by larger gap


def find_caption_top(
    row_density: np.ndarray,
    top: int,
    bottom: int,
    width: int,
    min_text_lines: int = 3,
    text_line_h_range=(11, 40),
    gap_h_range=(3, 20),
) -> int | None:
    """Detect a caption text block inside [top, bottom] anchored at the bottom.

    Caption signature: ≥ min_text_lines consecutive narrow dark runs (each
    ``text_line_h_range`` px tall) separated by narrow white gaps (each
    ``gap_h_range`` px tall). Return the row index where the caption starts,
    or None if no caption-like block is found in the bottom region.
    """
    threshold = width * 0.015
    rel = row_density[top : bottom + 1]
    is_dark = (rel > threshold).astype(np.uint8)
    n = len(is_dark)
    if n < 30:
        return None
    runs = []  # (start, end, is_dark)
    i = 0
    while i < n:
        state = int(is_dark[i])
        j = i
        while j < n and int(is_dark[j]) == state:
            j += 1
        runs.append((i, j - 1, bool(state)))
        i = j

    # Walk runs from the end, build a contiguous "text block" from the bottom.
    caption_start_rel = None
    text_lines = 0
    for idx in range(len(runs) - 1, -1, -1):
        rs, re, dark_flag = runs[idx]
        rh = re - rs + 1
        if dark_flag:
            if text_line_h_range[0] <= rh <= text_line_h_range[1]:
                text_lines += 1
                caption_start_rel = rs
            else:
                # too tall/short to be a text line — stop block growth
                break
        else:
            if rh > gap_h_range[1]:
                # big white gap — end of caption block
                break
            if rh < gap_h_range[0]:
                # too tight, unusual; still allow
                pass
    if text_lines >= min_text_lines and caption_start_rel is not None:
        return top + caption_start_rel
    return None


def find_segments(profile: np.ndarray, threshold: float, min_gap: int):
    """Split a 1D density profile into (start, end) inclusive segments.

    Segments are separated by ≥min_gap consecutive points below threshold.
    Short white runs inside a segment are tolerated.
    """
    is_white = profile < threshold
    segments = []
    n = len(profile)
    i = 0
    while i < n:
        while i < n and is_white[i]:
            i += 1
        if i >= n:
            break
        start = i
        last_dark = i
        while i < n:
            if not is_white[i]:
                last_dark = i
                i += 1
                continue
            run_start = i
            while i < n and is_white[i]:
                i += 1
            run_len = i - run_start
            if run_len >= min_gap:
                break
        segments.append((start, last_dark))
    return segments


def score_segment(profile: np.ndarray, seg, width: int):
    s, e = seg
    height = e - s + 1
    if height < 4:
        return 0.0
    density = profile[s : e + 1].mean() / width
    return height * (density + 0.005)


def trim_one(src: Path, dst: Path) -> dict:
    pil = Image.open(src).convert("RGB")
    img = np.array(pil)  # HxWx3 uint8
    h, w = img.shape[:2]
    gray = np.array(pil.convert("L"))

    dark = (gray < DARK_THRESHOLD).astype(np.uint8)
    row_density = dark.sum(axis=1).astype(np.float32)
    row_threshold = w * WHITE_ROW_FRAC

    segments = find_segments(row_density, row_threshold, MIN_GAP_ROWS)
    trimmed_top = 0
    trimmed_bottom = 0

    # Trim text-like bands at the top edge (e.g., journal running head).
    # A top segment is a header candidate if it sits in the top region AND
    # any of: short height, sparse density (header bar), or clear gap below.
    while len(segments) >= 1:
        s, e = segments[0]
        h_seg = e - s + 1
        if e >= h * TOP_TEXT_MAX_FRAC:
            break
        gap_after = (segments[1][0] - e - 1) if len(segments) >= 2 else 0
        seg_d_top = float((row_density[s : e + 1] / w).mean()) if e > s else 0.0
        is_short = h_seg <= TOP_TEXT_MAX_PX
        is_sparse = seg_d_top < 0.25
        has_gap = gap_after >= MIN_GAP_AFTER_HEADER
        if is_short and (is_sparse or has_gap):
            segments.pop(0)
            trimmed_top += 1
        else:
            break

    # Trim text-like caption bands at the bottom edge.
    # A bottom segment is a caption candidate if any of:
    #   (a) clear visual gap above (≥ MIN_GAP_BEFORE_CAPTION)
    #   (b) short height (< 90 px) AND sparse density (< 0.30) — i.e., one
    #       line of small text well below the figure body
    # AND it sits in the bottom region (start > BOTTOM_TEXT_MIN_FRAC * h).
    def seg_density(s, e):
        return float((row_density[s : e + 1] / w).mean())

    while len(segments) >= 2:
        s, e = segments[-1]
        prev_e = segments[-2][1]
        gap = s - prev_e - 1
        h_seg = e - s + 1
        is_at_bottom = s > h * BOTTOM_TEXT_MIN_FRAC
        is_short_enough = h_seg <= BOTTOM_TEXT_MAX_PX
        has_gap = gap >= MIN_GAP_BEFORE_CAPTION
        is_thin_text = h_seg < 90 and seg_density(s, e) < 0.30
        if is_at_bottom and is_short_enough and (has_gap or is_thin_text):
            segments.pop()
            trimmed_bottom += 1
        else:
            break

    caption_cut = False
    if not segments:
        ys, xs = np.where(dark > 0)
        if len(ys) == 0:
            dst.write_bytes(src.read_bytes())
            return {"file": src.name, "method": "passthrough",
                    "in_wh": (w, h), "crop_xywh": (0, 0, w, h),
                    "segments_found": 0, "trimmed": (0, 0)}
        top, bottom = int(ys.min()), int(ys.max())
        left, right = int(xs.min()), int(xs.max())
        method = "fallback-bbox"
    else:
        # Union of remaining segments = figure body
        top = segments[0][0]
        bottom = segments[-1][1]
        # Sub-trim: detect a caption text-block fused inside the anchor.
        cap_top = find_caption_top(row_density, top, bottom, w)
        if cap_top is not None and cap_top > top + (bottom - top) * 0.4:
            bottom = cap_top - 1
            caption_cut = True
        strip = dark[top : bottom + 1, :]
        col_density = strip.sum(axis=0).astype(np.float32)
        col_thr = strip.shape[0] * WHITE_COL_FRAC
        non_white_cols = np.where(col_density >= col_thr)[0]
        if len(non_white_cols) == 0:
            left, right = 0, w - 1
        else:
            left = int(non_white_cols[0])
            right = int(non_white_cols[-1])
        method = "edge-trim+cap" if caption_cut else "edge-trim"

    top = max(0, top - PAD)
    bottom = min(h - 1, bottom + PAD)
    left = max(0, left - PAD)
    right = min(w - 1, right + PAD)

    cropped = img[top : bottom + 1, left : right + 1]
    Image.fromarray(cropped).save(dst, format="PNG", optimize=True)
    return {
        "file": src.name,
        "method": method,
        "in_wh": (w, h),
        "crop_xywh": (left, top, right - left + 1, bottom - top + 1),
        "segments_found": len(segments),
        "trimmed": (trimmed_top, trimmed_bottom),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pngs = sorted(in_dir.glob("*.png"))
    if not pngs:
        print(f"no PNGs in {in_dir}", file=sys.stderr)
        sys.exit(1)

    for p in pngs:
        info = trim_one(p, out_dir / p.name)
        x, y, cw, ch = info["crop_xywh"]
        iw, ih = info["in_wh"]
        pct_w = cw / iw * 100
        pct_h = ch / ih * 100
        tt, tb = info.get("trimmed", (0, 0))
        print(
            f"{p.name:50s}  {iw}x{ih} -> {cw}x{ch}  "
            f"({pct_w:.0f}% w, {pct_h:.0f}% h)  segs={info['segments_found']}  "
            f"trim=top{tt}/bot{tb}  [{info['method']}]"
        )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Scientific-symbol + CJK glyph-coverage scanner for xelatex PDF builds.

xelatex can finish successfully with missing glyphs (warnings may be in the log).
Academic markdown routinely
carries glyphs a default Latin font misses: transition arrows (→ ↑ ↓ ↔), math
operators (− ≤ ≥ ± √ ∪ × ≈ ≠), stats Greek (κ μ σ β χ), bullets/marks (• ★ ✓),
and CJK. This scans the SOURCE markdown, groups the risky non-ASCII glyphs it
finds by class, and (when a font file + fonttools are available) reports which are
genuinely absent from the font's cmap. The DOCX is authoritative; the PDF is a
convenience copy, so the goal is to surface a likely silent drop before it ships.

NOT an integrity detector — named `scan_glyph_coverage.py` (not check_/detect_/
derive_) so the catalog glob does not count it; it is a render-time QA helper.

INPUT
  markdown   one or more .md files (positional).
  --font     optional path to the .ttf/.otf/.ttc/.otc that will render the body; with
             `fonttools` installed, glyphs absent from its cmap are reported as
             MISSING (the real coverage check). Without it, the scan is advisory
             (presence by class — verify your mainfont/CJKmainfont covers them).
  --font-index  required zero-based face index for a collection; one face is
                checked, never the union of different faces' glyphs.

OUTPUT
  stdout report and, with --json, an artifact:
    {files, classes{name:[chars]}, font_checked, font_check, missing_in_font[], summary}
  Exit 1 (with --strict) when risky glyphs are present AND no font verified them,
  or when --font is given and any glyph is genuinely missing from it.

Stdlib-only core (re/json/argparse/unicodedata); fonttools optional. Exit codes:
0 clean/advisory-ok, 1 risky-uncovered (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
import unicodedata
from pathlib import Path

# Risky glyph classes (codepoint ranges / explicit points) that a default Latin
# font (Helvetica/Times) commonly misses and xelatex drops silently.
CLASSES = {
    "arrows": [(0x2190, 0x21FF)],
    "math_operators": [(0x2212, 0x2212), (0x2264, 0x2265), (0x00B1, 0x00B1),
                       (0x221A, 0x221A), (0x222A, 0x222A), (0x00D7, 0x00D7),
                       (0x2248, 0x2248), (0x2260, 0x2260), (0x2211, 0x2211),
                       (0x220F, 0x220F), (0x2265, 0x2265), (0x2243, 0x2243)],
    "greek_stats": [(0x0370, 0x03FF)],
    "marks_bullets": [(0x2605, 0x2606), (0x2713, 0x2714), (0x2022, 0x2022),
                      (0x2020, 0x2021), (0x00A7, 0x00A7)],
    "cjk": [(0x3040, 0x30FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF),
            (0xAC00, 0xD7A3), (0xF900, 0xFAFF)],
}


def _classify(ch: str) -> str | None:
    cp = ord(ch)
    if cp < 0x80:
        return None
    for name, ranges in CLASSES.items():
        for lo, hi in ranges:
            if lo <= cp <= hi:
                return name
    return None


def scan(paths: list[Path]) -> dict:
    classes: dict[str, dict[str, int]] = {}
    all_chars: set[str] = set()
    for p in paths:
        if not p.is_file():
            sys.stderr.write(f"ERROR: file not found: {p}\n")
            sys.exit(2)
        for ch in p.read_text(encoding="utf-8"):
            cls = _classify(ch)
            if cls:
                classes.setdefault(cls, {}).setdefault(ch, 0)
                classes[cls][ch] += 1
                all_chars.add(ch)
    return {"classes": classes, "chars": sorted(all_chars)}


def check_font(chars: list[str], font_path: Path, font_index: int | None = None) -> dict:
    """Inspect one face's preferred Unicode cmap; an unavailable check is explicit.

    Cmap coverage does not establish shaping, fallback-font selection, or whether
    the renderer used this font. Inspect the rendered PDF separately.
    """
    result = {"status": "unavailable", "reason": None, "face_index": font_index,
              "face_name": None, "n_faces": None, "missing": []}
    try:
        from fontTools.ttLib import TTFont  # type: ignore
    except ImportError:
        return dict(result, reason="fonttools_unavailable")
    try:
        with font_path.open("rb") as source:
            header = source.read(12)
        collection = header[:4] == b"ttcf"
        n_faces = struct.unpack(">I", header[8:12])[0] if collection else 1
        result["n_faces"] = n_faces
        if collection and font_index is None:
            return dict(result, reason="face_selection_required")
        face_index = 0 if font_index is None else font_index
        if not 0 <= face_index < n_faces:
            return dict(result, reason="font_index_out_of_range")
        result["face_index"] = face_index
        with TTFont(str(font_path), fontNumber=face_index, lazy=True) as font:
            cmap = font.getBestCmap()
            if cmap is None:
                return dict(result, reason="unicode_cmap_unavailable")
            if "name" in font:
                result["face_name"] = (font["name"].getDebugName(6)
                                       or font["name"].getDebugName(4))
            missing = [c for c in chars if cmap.get(ord(c), ".notdef") == ".notdef"]
    except FileNotFoundError:
        return dict(result, reason="font_not_found")
    except Exception:
        return dict(result, reason="font_unreadable")
    return dict(result, status="checked", missing=missing)


def font_missing(chars: list[str], font_path: Path,
                 font_index: int | None = None) -> tuple[list[str], bool]:
    """Compatibility wrapper returning (missing_chars, checked)."""
    result = check_font(chars, font_path, font_index)
    return result["missing"], result["status"] == "checked"


def main() -> int:
    ap = argparse.ArgumentParser(description="Scientific-symbol + CJK glyph-coverage scanner.")
    ap.add_argument("markdown", nargs="+", help="markdown file(s) to scan")
    ap.add_argument("--font", help="font file (.ttf/.otf/.ttc/.otc); fonttools required for cmap check")
    ap.add_argument("--font-index", type=int, help="zero-based face index (required for collections)")
    ap.add_argument("--json", help="write JSON artifact")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if risky glyphs are present and unverified, or genuinely missing from --font")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    if args.font_index is not None and (not args.font or args.font_index < 0):
        ap.error("--font-index requires --font and a nonnegative integer")

    res = scan([Path(m) for m in args.markdown])
    classes = res["classes"]
    font_check = {"status": "not_requested", "reason": "no_font_supplied",
                  "face_index": None, "face_name": None, "n_faces": None, "missing": []}
    if args.font:
        font_check = check_font(res["chars"], Path(args.font), args.font_index)
    missing = font_check.pop("missing")
    checked = font_check["status"] == "checked"
    if args.font and not checked:
        sys.stderr.write(f"WARN: font_checked=false: {font_check['reason']}\n")
        if font_check["reason"] == "face_selection_required":
            sys.stderr.write(f"Select --font-index 0..{font_check['n_faces'] - 1} "
                             "to match the face used by the renderer.\n")

    n_risky = sum(sum(d.values()) for d in classes.values())
    out = {
        "files": args.markdown,
        "classes": {k: sorted(v) for k, v in classes.items()},
        "font_checked": checked,
        "font_check": font_check,
        "missing_in_font": sorted(missing),
        "summary": {"n_risky_glyphs": n_risky, "n_classes": len(classes),
                    "n_missing_in_font": len(missing)},
    }

    if not args.quiet:
        print("=" * 41)
        print(" Glyph Coverage (xelatex silent-drop scan)")
        print("=" * 41)
        for cls, chars in out["classes"].items():
            names = ", ".join(f"{c} (U+{ord(c):04X} {unicodedata.name(c, '?')[:24]})" for c in chars[:8])
            print(f"  {cls}: {names}{' …' if len(chars) > 8 else ''}")
        if not classes:
            print("  (no risky non-ASCII glyphs found)")
        if checked:
            print(f"\nfont face {font_check['face_index']}: {font_check['face_name'] or '(unnamed)'}")
            print(f"\nfont cmap checked: {len(missing)} glyph(s) MISSING from the font"
                  + (f": {' '.join(missing)}" if missing else ""))
        elif classes:
            print("\nADVISORY: risky glyphs present; verify mainfont/CJKmainfont cover them "
                  "(pass --font with fonttools for a real cmap check). DOCX is authoritative.")
        if not checked:
            print(f"\nfont_checked=false ({font_check['reason']})")

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(out, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"wrote {args.json}")

    if args.strict:
        if checked:
            return 1 if missing else 0
        return 1 if n_risky else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())

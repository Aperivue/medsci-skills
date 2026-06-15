#!/usr/bin/env python3
"""Scientific-symbol + CJK glyph-coverage scanner for xelatex PDF builds.

xelatex **silently drops** a character the chosen font does not cover — the PDF
renders with the glyph simply missing, no error. Academic markdown routinely
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
  --font     optional path to the .ttf/.otf that will render the body; with
             `fonttools` installed, glyphs absent from its cmap are reported as
             MISSING (the real coverage check). Without it, the scan is advisory
             (presence by class — verify your mainfont/CJKmainfont covers them).

OUTPUT
  stdout report and, with --json, an artifact:
    {files, classes{name:[chars]}, missing_in_font[], summary}
  Exit 1 (with --strict) when risky glyphs are present AND no font verified them,
  or when --font is given and any glyph is genuinely missing from it.

Stdlib-only core (re/json/argparse/unicodedata); fonttools optional. Exit codes:
0 clean/advisory-ok, 1 risky-uncovered (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
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


def font_missing(chars: list[str], font_path: Path) -> tuple[list[str], bool]:
    """Return (missing_chars, checked). checked=False if fonttools/font unavailable."""
    try:
        from fontTools.ttLib import TTFont  # type: ignore
    except Exception:
        return [], False
    if not font_path.is_file():
        sys.stderr.write(f"WARN: --font not found: {font_path}\n")
        return [], False
    try:
        font = TTFont(str(font_path))
        cmap = set()
        for t in font["cmap"].tables:
            cmap.update(t.cmap.keys())
    except Exception as e:
        sys.stderr.write(f"WARN: could not read font cmap: {e}\n")
        return [], False
    return [c for c in chars if ord(c) not in cmap], True


def main() -> int:
    ap = argparse.ArgumentParser(description="Scientific-symbol + CJK glyph-coverage scanner.")
    ap.add_argument("markdown", nargs="+", help="markdown file(s) to scan")
    ap.add_argument("--font", help="path to body font (.ttf/.otf) — checks real cmap if fonttools present")
    ap.add_argument("--json", help="write JSON artifact")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if risky glyphs are present and unverified, or genuinely missing from --font")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    res = scan([Path(m) for m in args.markdown])
    classes = res["classes"]
    missing, checked = ([], False)
    if args.font:
        missing, checked = font_missing(res["chars"], Path(args.font))

    n_risky = sum(sum(d.values()) for d in classes.values())
    out = {
        "files": args.markdown,
        "classes": {k: sorted(v) for k, v in classes.items()},
        "font_checked": checked,
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
            print(f"\nfont cmap checked: {len(missing)} glyph(s) MISSING from the font"
                  + (f": {' '.join(missing)}" if missing else ""))
        elif classes:
            print("\nADVISORY: risky glyphs present; verify mainfont/CJKmainfont cover them "
                  "(pass --font with fonttools for a real cmap check). DOCX is authoritative.")

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

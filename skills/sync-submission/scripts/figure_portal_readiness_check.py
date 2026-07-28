#!/usr/bin/env python3
"""Figure portal-readiness gate — catch an over-cap or wrong-format figure BEFORE upload.

Two portal facts bounce a figure at the upload button, after a long submission session:

  * a size cap — JACC: Asia rejects a figure over 25 MB, which a raw uncompressed
    600-dpi RGBA TIFF sails straight past;
  * a format allowlist — Springer Nature's SNAPP accepts only `.tiff` / `.jpeg` / `.eps`
    and REJECTS the `.png` a figure was rendered as.

Both are deterministic from the file on disk — a byte size and an extension — so they can be
caught at pre-flight instead of at the portal. This is the DETECTION half; the fix is to
regenerate the figure with `/make-figures export_portal_tiff.py` (LZW + RGBA→RGB flatten).

This is a stdlib pre-flight sub-check (like scope_drift_check.py / cover_letter_drift_check.py),
not a manuscript-integrity detector — its filename intentionally avoids the `check_`/`detect_`
prefix so it is not counted in the MedSci-Audit detector suite.

Verdicts:
  FIGURE_OVERSIZE (Major)         a figure file exceeds --max-mb (default 25).
  FIGURE_FORMAT_REJECTED (Major)  a figure's extension is not in the portal's --accept set.
                                  Only evaluated when --accept is given (a portal-specific
                                  allowlist, e.g. `--accept tiff --accept jpeg --accept eps`
                                  for SNAPP); without it, format is not judged.

INPUT
  --figures-dir DIR   directory of figure files (scanned recursively for image extensions).
  --accept EXT ...    portal-accepted extensions (repeatable; dot optional; tif==tiff, jpg==jpeg).
  --max-mb N          size cap in MB (default 25; a figure strictly over this is flagged).

OUTPUT (--out PATH)
  {"detector": "figure_portal_readiness_check", "scanned", "findings":
     [{path, kind, size_mb, ext, label, severity}], "summary", "submission_safe"}

Stdlib-only. Exit codes: 0 clean, 1 finding, 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Files treated as figures. A portal-field .txt or a manuscript .md is not a figure.
IMAGE_EXTS = {".png", ".tif", ".tiff", ".jpg", ".jpeg", ".eps", ".pdf", ".gif", ".bmp", ".svg"}
MB = 1024 * 1024


def _norm_ext(e: str) -> str:
    """Lowercase, strip a leading dot, and canonicalize tif->tiff / jpg->jpeg."""
    e = e.lower().lstrip(".")
    return {"tif": "tiff", "jpg": "jpeg"}.get(e, e)


def analyze(figures_dir: str, accept, max_mb: float) -> dict:
    d = Path(figures_dir)
    if not d.is_dir():
        sys.stderr.write(f"ERROR: --figures-dir not a directory: {figures_dir}\n")
        sys.exit(2)
    accept_set = {_norm_ext(a) for a in accept} if accept else None
    findings: list[dict] = []
    scanned = 0
    for p in sorted(d.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in IMAGE_EXTS:
            continue
        scanned += 1
        size_mb = p.stat().st_size / MB
        ext = _norm_ext(p.suffix)
        if size_mb > max_mb:
            findings.append({
                "path": str(p), "kind": "FIGURE_OVERSIZE", "size_mb": round(size_mb, 2),
                "ext": ext, "severity": "Major",
                "label": (f"{size_mb:.1f} MB exceeds the {max_mb:g} MB portal cap — re-export "
                          f"LZW-compressed / flattened (make-figures export_portal_tiff.py)"),
            })
        if accept_set is not None and ext not in accept_set:
            findings.append({
                "path": str(p), "kind": "FIGURE_FORMAT_REJECTED", "size_mb": round(size_mb, 2),
                "ext": ext, "severity": "Major",
                "label": (f".{p.suffix.lstrip('.')} is not accepted by this portal "
                          f"(accepts: {', '.join(sorted(accept_set))}) — convert before upload"),
            })
    return {
        "scanned": {"figures": scanned},
        "findings": findings,
        "summary": {"oversize": sum(1 for f in findings if f["kind"] == "FIGURE_OVERSIZE"),
                    "format_rejected": sum(1 for f in findings if f["kind"] == "FIGURE_FORMAT_REJECTED")},
        "submission_safe": not findings,
    }


def render(result: dict) -> str:
    lines = ["| Figure | Size (MB) | Kind | Detail |", "|---|---|---|---|"]
    for f in result["findings"]:
        lines.append(f"| {Path(f['path']).name} | {f['size_mb']} | {f['kind']} | {f['label']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | — | every figure is under the cap and in an accepted format |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Figure portal-readiness gate (size + accepted format).")
    ap.add_argument("--figures-dir", required=True, help="directory of figure files (scanned recursively)")
    ap.add_argument("--accept", action="append", default=[], metavar="EXT",
                    help="portal-accepted extension (repeatable; dot optional). Omit to skip the format check.")
    ap.add_argument("--max-mb", type=float, default=25.0, help="size cap in MB (default 25)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.figures_dir, args.accept, args.max_mb)

    if not args.quiet:
        print("=" * 44)
        print(" Figure Portal Readiness")
        print("=" * 44)
        print(render(result))
        print()
        s = result["summary"]
        n = s["oversize"] + s["format_rejected"]
        if n:
            print(f"NOT PORTAL-READY: {s['oversize']} over-cap, {s['format_rejected']} wrong-format "
                  f"figure(s). Re-export before upload.")
        else:
            print(f"OK: {result['scanned']['figures']} figure(s) are portal-ready.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps({"detector": "figure_portal_readiness_check", **result}, indent=2, ensure_ascii=False),
            encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if result["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())

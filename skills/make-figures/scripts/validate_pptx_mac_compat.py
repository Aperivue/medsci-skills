#!/usr/bin/env python3
"""Validate a .pptx for Mac PowerPoint compatibility.

Detects four classes of defect that PowerPoint Mac renders differently
from PowerPoint Windows / Keynote / LibreOffice and that PDF export
alone does not catch:

1. TIFF images embedded in ppt/media/ — Mac PowerPoint silently drops them.
2. <a:sp3d> 3-D bevel inside text rPr — Mac renders as red outline that
   does not appear in PDF or on Windows.
3. docProps/app.xml count mismatch with actual slide count — triggers a
   "PowerPoint found a problem" recovery dialog on first open.
4. <a:srcRect> values exceeding 100000 (1/1000-percent) — image is
   over-cropped (sometimes 99 % cut off) only on Mac.

Reference rule: ~/.claude/rules/pptx-mac-compatibility.md.

Usage:
    python validate_pptx_mac_compat.py path/to/deck.pptx
    python validate_pptx_mac_compat.py deck.pptx --json out.json
    python validate_pptx_mac_compat.py deck.pptx --strict   # exit 1 on any FAIL

Exit codes:
    0 — all checks PASS
    1 — at least one FAIL (only with --strict; otherwise still 0 with WARN)
    2 — input invalid (file missing, not a zip, etc.)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path


SP3D_RE = re.compile(r"<a:sp3d\b", re.IGNORECASE)
SRC_RECT_RE = re.compile(
    r'<a:srcRect\b[^/>]*?(?:l|t|r|b)="(\d+)"', re.IGNORECASE
)
APP_XML_SLIDES_RE = re.compile(r"<Slides>(\d+)</Slides>", re.IGNORECASE)
APP_XML_VECTOR_SIZE_RE = re.compile(
    r'<vt:vector\b[^>]*?size="(\d+)"', re.IGNORECASE
)


def _check_tiff(zf: zipfile.ZipFile) -> list[str]:
    found = [
        name
        for name in zf.namelist()
        if name.lower().startswith("ppt/media/")
        and name.lower().endswith((".tif", ".tiff"))
    ]
    return found


def _check_sp3d(zf: zipfile.ZipFile) -> list[tuple[str, int]]:
    hits: list[tuple[str, int]] = []
    for name in zf.namelist():
        if not (name.startswith("ppt/slides/") and name.endswith(".xml")):
            continue
        try:
            text = zf.read(name).decode("utf-8", errors="replace")
        except Exception:
            continue
        count = len(SP3D_RE.findall(text))
        if count > 0:
            hits.append((name, count))
    return hits


def _check_app_xml(zf: zipfile.ZipFile) -> dict:
    result = {"present": False, "declared_slides": None, "actual_slides": None,
              "vector_size_max": None, "mismatch": False}
    actual = sum(
        1
        for n in zf.namelist()
        if n.startswith("ppt/slides/slide") and n.endswith(".xml")
    )
    result["actual_slides"] = actual
    try:
        app = zf.read("docProps/app.xml").decode("utf-8", errors="replace")
    except KeyError:
        return result
    result["present"] = True
    m = APP_XML_SLIDES_RE.search(app)
    if m:
        declared = int(m.group(1))
        result["declared_slides"] = declared
        if declared != actual:
            result["mismatch"] = True
    sizes = [int(s) for s in APP_XML_VECTOR_SIZE_RE.findall(app)]
    if sizes:
        result["vector_size_max"] = max(sizes)
    return result


def _check_src_rect(zf: zipfile.ZipFile) -> list[tuple[str, int]]:
    """Return [(slide_path, max_value)] for any srcRect value > 100000.

    srcRect uses 1/1000-percent units; legitimate values are 0–100000.
    Anything above 100000 indicates a unit-conversion bug (e.g., a
    percent-to-1/1000-percent miscalculation) and produces severe over-crop
    on Mac PowerPoint.
    """
    hits: list[tuple[str, int]] = []
    for name in zf.namelist():
        if not (name.startswith("ppt/slides/") and name.endswith(".xml")):
            continue
        try:
            text = zf.read(name).decode("utf-8", errors="replace")
        except Exception:
            continue
        values = [int(v) for v in SRC_RECT_RE.findall(text)]
        bad = [v for v in values if v > 100000]
        if bad:
            hits.append((name, max(bad)))
    return hits


def validate(pptx_path: Path) -> dict:
    if not pptx_path.exists():
        return {"ok": False, "error": f"file not found: {pptx_path}"}
    if not zipfile.is_zipfile(pptx_path):
        return {"ok": False, "error": f"not a zip / pptx: {pptx_path}"}

    with zipfile.ZipFile(pptx_path) as zf:
        tiffs = _check_tiff(zf)
        sp3d = _check_sp3d(zf)
        app = _check_app_xml(zf)
        srcrect = _check_src_rect(zf)

    findings: list[dict] = []

    if tiffs:
        findings.append({
            "id": "TIFF",
            "severity": "FAIL",
            "message": f"{len(tiffs)} TIFF image(s) embedded; Mac PowerPoint will silently drop these.",
            "files": tiffs,
            "fix": "Convert each to PNG (`sips -s format png in.tif --out out.png` on macOS) and update _rels/*.rels to reference the new .png filenames.",
        })

    if sp3d:
        total = sum(c for _, c in sp3d)
        findings.append({
            "id": "SP3D",
            "severity": "FAIL",
            "message": f"<a:sp3d> 3-D bevel found in {len(sp3d)} slide(s) ({total} occurrence(s)); renders as red outline on Mac PowerPoint and is invisible in PDF export.",
            "files": [{"slide": n, "count": c} for n, c in sp3d],
            "fix": "Strip <a:sp3d>...</a:sp3d> blocks via regex in each slide XML. Verify on Mac PowerPoint after fix.",
        })

    if app["present"] and app["mismatch"]:
        findings.append({
            "id": "APP_XML_COUNT",
            "severity": "FAIL",
            "message": f"docProps/app.xml declares <Slides>{app['declared_slides']}</Slides> but the package contains {app['actual_slides']} slide XML files; PowerPoint Mac will show a 'recover file' dialog on first open.",
            "fix": "Update <Slides>, <HeadingPairs>, and <TitlesOfParts> in docProps/app.xml to match the actual slide count.",
        })
    elif not app["present"]:
        findings.append({
            "id": "APP_XML_MISSING",
            "severity": "WARN",
            "message": "docProps/app.xml not found in package; PowerPoint Mac may show a recovery dialog or open with broken metadata.",
            "fix": "Re-export the deck from PowerPoint (which writes app.xml) or generate one programmatically.",
        })

    if srcrect:
        findings.append({
            "id": "SRC_RECT_OVERFLOW",
            "severity": "FAIL",
            "message": f"<a:srcRect> values >100000 (1/1000-percent maximum) found in {len(srcrect)} slide(s); image will be over-cropped on Mac PowerPoint (often >99 % cut off).",
            "files": [{"slide": n, "max_value": v} for n, v in srcrect],
            "fix": "Recompute srcRect: percentages stay 0–100; 1/1000-percent units stay 0–100000. Compare to original .pptx srcRect values if a build script regressed.",
        })

    fail_count = sum(1 for f in findings if f["severity"] == "FAIL")
    warn_count = sum(1 for f in findings if f["severity"] == "WARN")

    return {
        "ok": fail_count == 0,
        "file": str(pptx_path),
        "summary": {
            "fail": fail_count,
            "warn": warn_count,
            "slides": app["actual_slides"],
        },
        "findings": findings,
    }


def _format_human(report: dict) -> str:
    if not report.get("ok") and "error" in report:
        return f"ERROR: {report['error']}"
    lines = [f"PPTX Mac compatibility check — {report['file']}"]
    s = report["summary"]
    lines.append(f"  slides={s['slides']}  fail={s['fail']}  warn={s['warn']}")
    if not report["findings"]:
        lines.append("  ✓ All four checks PASS (TIFF, sp3d, app.xml count, srcRect).")
        return "\n".join(lines)
    for f in report["findings"]:
        lines.append(f"  [{f['severity']}] {f['id']}: {f['message']}")
        lines.append(f"        fix: {f['fix']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pptx", help="path to .pptx")
    ap.add_argument("--json", help="write JSON report to this path")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any FAIL (default exits 0 with WARN)")
    args = ap.parse_args(argv)

    report = validate(Path(args.pptx))
    if not report.get("ok") and "error" in report:
        print(_format_human(report), file=sys.stderr)
        return 2

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2))
    print(_format_human(report))

    if args.strict and not report["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Backbone-article full-text readiness gate for /write-paper (issues #4, #8).

`/write-paper` Phase 0 records a *backbone article* (`project.yaml::backbone_article`)
whose structure the draft follows. Retrieval and PDF->Markdown conversion exist
(`/lit-sync` Phase 2.7, `/fulltext-retrieval` `pdf_to_md.py`), but nothing forces
the backbone's **full text** to be extracted *before* drafting — so the model can
scaffold Methods/Results from an abstract alone, which is exactly what the
backbone is supposed to prevent.

This is a pre-draft **workflow prerequisite**, not a manuscript-integrity
detector (it inspects the source material, not the manuscript), so it is
deliberately named `gate_*` and is not part of the MedSci-Audit detector count.

It answers one question: is the backbone article's extracted full text present
and substantial (more than an abstract)?

  * BACKBONE_FULLTEXT_MISSING (major) — no extracted Markdown found for the
    backbone article; drafting would proceed from the abstract only.
  * BACKBONE_FULLTEXT_THIN (major) — an extracted file exists but is below the
    full-text size floor (likely an abstract/landing page, not the article).
  * BACKBONE_UNDECLARED (warn) — no backbone article is declared; Phase 0 should
    record one before drafting (cannot gate what is not declared).

Resolution order for the backbone's extracted text:
  1. an explicit `--fulltext PATH` (authoritative);
  2. a `<citekey>.md` in any `--fulltext-dir`;
  3. any `*.md` in a `--fulltext-dir` whose text contains the backbone DOI
     (resolved from `--refs`) or the citekey.

Usage:
    gate_backbone_fulltext.py --project project.yaml --refs manuscript/_src/refs.bib \
        --fulltext-dir pdfs/ [--fulltext pdfs/backbone.md] [--min-bytes 3000] [--strict]

Exit 0 = ready (or only a warning), 1 = a major verdict under --strict, 2 = usage.
Requires PyYAML for --project (a CI dependency); refs.bib parsed with stdlib.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_MIN_BYTES = 3000  # a real article body is well above this; an abstract is below


def load_backbone_from_project(project: Path) -> str | None:
    try:
        import yaml
    except Exception:  # pragma: no cover
        # stdlib fallback: grep the key
        for line in project.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"\s*backbone_article\s*:\s*(.+?)\s*$", line)
            if m:
                return m.group(1).strip().strip("'\"") or None
        return None
    data = yaml.safe_load(project.read_text(encoding="utf-8", errors="replace")) or {}
    val = data.get("backbone_article")
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None


def doi_for_citekey(refs: Path, citekey: str) -> str | None:
    """Minimal .bib scan: find the entry for citekey and return its doi field."""
    if not refs or not refs.is_file():
        return None
    text = refs.read_text(encoding="utf-8", errors="replace")
    # locate "@type{citekey," then read until the next "@" at line start
    m = re.search(r"@\w+\s*\{\s*" + re.escape(citekey) + r"\s*,", text)
    if not m:
        return None
    tail = text[m.end():]
    nxt = re.search(r"\n@\w+\s*\{", tail)
    entry = tail[: nxt.start()] if nxt else tail
    d = re.search(r"doi\s*=\s*[{\"]\s*([^}\"]+?)\s*[}\"]", entry, re.IGNORECASE)
    return d.group(1).strip() if d else None


def find_fulltext(citekey: str, doi: str | None, dirs: list[Path]) -> Path | None:
    """Locate an extracted-markdown file for the backbone article."""
    doi_l = doi.lower() if doi else None
    for d in dirs:
        if not d.is_dir():
            continue
        direct = d / f"{citekey}.md"
        if direct.is_file():
            return direct
    for d in dirs:
        if not d.is_dir():
            continue
        for md in sorted(d.rglob("*.md")):
            try:
                head = md.read_text(encoding="utf-8", errors="replace")[:20000].lower()
            except OSError:
                continue
            if citekey.lower() in head or (doi_l and doi_l in head):
                return md
    return None


def build_report(project: Path | None, backbone_cli: list[str], refs: Path | None,
                 fulltext: Path | None, fulltext_dirs: list[Path], min_bytes: int) -> dict:
    findings: list[dict] = []
    backbones = list(backbone_cli)
    if not backbones and project and project.is_file():
        b = load_backbone_from_project(project)
        if b:
            backbones = [b]

    if not backbones:
        findings.append({
            "verdict": "BACKBONE_UNDECLARED", "severity": "warn",
            "message": "No backbone article declared (project.yaml::backbone_article). "
                       "Phase 0 should record one before drafting.",
        })
        return {"backbones": [], "findings": findings, "ready": False}

    for citekey in backbones:
        doi = doi_for_citekey(refs, citekey) if refs else None
        path = fulltext if (fulltext and fulltext.is_file() and len(backbones) == 1) else None
        if path is None:
            path = find_fulltext(citekey, doi, fulltext_dirs)
        if path is None:
            findings.append({
                "verdict": "BACKBONE_FULLTEXT_MISSING", "severity": "major", "backbone": citekey,
                "doi": doi,
                "message": f"No extracted full-text Markdown found for backbone '{citekey}'. "
                           "Retrieve + convert it (/lit-sync Phase 2.7 or /fulltext-retrieval "
                           "pdf_to_md.py) before drafting.",
            })
            continue
        size = path.stat().st_size
        if size < min_bytes:
            findings.append({
                "verdict": "BACKBONE_FULLTEXT_THIN", "severity": "major", "backbone": citekey,
                "path": str(path), "bytes": size,
                "message": f"Backbone full text '{path}' is {size} bytes (< {min_bytes}); "
                           "looks like an abstract/landing page, not the article body.",
            })
    ready = not any(f["severity"] == "major" for f in findings)
    return {"backbones": backbones, "findings": findings, "ready": ready}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, help="project.yaml (read backbone_article)")
    ap.add_argument("--backbone", action="append", default=[], help="backbone citekey (overrides project). Repeatable.")
    ap.add_argument("--refs", type=Path, help="refs.bib to resolve citekey -> DOI")
    ap.add_argument("--fulltext", type=Path, help="explicit path to the backbone's extracted markdown")
    ap.add_argument("--fulltext-dir", action="append", default=[], type=Path, help="dir(s) of extracted .md. Repeatable.")
    ap.add_argument("--min-bytes", type=int, default=DEFAULT_MIN_BYTES, help=f"full-text size floor (default {DEFAULT_MIN_BYTES})")
    ap.add_argument("--out", type=Path, help="write JSON report here")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any major verdict fires")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if not args.project and not args.backbone:
        print("error: pass --project or at least one --backbone", file=sys.stderr)
        return 2

    report = build_report(args.project, args.backbone, args.refs, args.fulltext,
                          args.fulltext_dir, args.min_bytes)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.quiet:
        if report["ready"] and not report["findings"]:
            print(f"OK: backbone full text present for {report['backbones']}.")
        else:
            for f in report["findings"]:
                print(f"  [{f['severity'].upper()}] {f['verdict']}: {f['message']}")

    if args.strict and any(f["severity"] == "major" for f in report["findings"]):
        print("\nBACKBONE_FULLTEXT_NOT_READY: extract the backbone article's full text before drafting.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

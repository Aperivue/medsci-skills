#!/usr/bin/env python3
"""Supplement assembler + structural validator (cohort/SR supplements).

Cohort and SR/MA supplements are a directory of per-section `S{N}_*.md` files +
an `00_index.md`, hand-concatenated into `_combined.md` and re-rendered. Adding
and extending sections across revisions desynchronizes the set: a declared `S{N}`
with no file (or a file with no index row), a duplicate `S{N}`, or a skipped
sub-section number after an insert (`S6.3` then `S6.5`, no `S6.4`). This script
validates that structure and rebuilds `_combined.md` in index order so the
assembly is reproducible rather than hand-maintained.

NOT an integrity detector — deliberately named `assemble_supplement.py` (not
check_/detect_/derive_) so the catalog glob does not count it. It is a build/QA
helper, run before a submission package is frozen.

INPUTS
  --dir         supplement directory holding `S{N}_*.md` (or `supplement_S{N}_*`/
                `suppl_S{N}_*`) section files and an index (`00_index.md` by
                default; override with --index).
  --index       index filename within --dir (default 00_index.md).
  --manuscript  optional manuscript .md; cross-checks which `Supplementary
                (Table|Figure|Material|Methods…) N` / `S{N}` are cited in the body
                (coverage: uncited sections + body callouts with no section file).
  --out         optional path to write the rebuilt `_combined.md` (index order).

OUTPUT
  stdout report and, with --json, a JSON artifact:
    {dir, declared[], present[], problems[{kind, detail}], coverage{...}, summary}
  problem kinds: INDEX_WITHOUT_FILE, FILE_WITHOUT_INDEX, DUPLICATE_SECTION,
  SUBSECTION_GAP, CALLOUT_WITHOUT_SECTION, SECTION_UNCITED.
  Exit 1 (with --strict) when any STRUCTURAL problem exists (the first four kinds;
  coverage findings are advisory and never fail --strict).

Stdlib-only (re / json / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 structural problem(s) with --strict, 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FILE_RE = re.compile(r"^(?:supplement_|suppl_)?S(\d+)(?:[_.]|$)", re.IGNORECASE)
# Top-level S-number tokens in the index (S1, S2 …), not sub-sections (S6.3).
INDEX_TOKEN_RE = re.compile(r"\bS(\d+)\b(?!\.\d)")
# Sub-section headings inside a file: "## S6.3 …", "### **S6.4** …".
SUBSEC_RE = re.compile(r"^#{1,4}\s*\*{0,2}\s*S(\d+)\.(\d+)\b", re.IGNORECASE | re.MULTILINE)
STRUCTURAL = {"INDEX_WITHOUT_FILE", "FILE_WITHOUT_INDEX", "DUPLICATE_SECTION", "SUBSECTION_GAP"}
# Body callouts: "Supplementary Table S3", "Supplementary Methods 2", "Table S3", "§S3", "(S3)".
CALLOUT_RE = re.compile(
    r"(?:Supplementary\s+(?:Table|Figure|Material|Methods|Appendix|Note|Data|File)s?\s*|"
    r"(?:Table|Figure|Fig\.?)\s+|§\s*|\(\s*)S(\d+)\b", re.IGNORECASE)


def scan_files(d: Path) -> dict:
    """Map S-number -> [filenames] for section files (excludes the index/_combined)."""
    out: dict[int, list[str]] = {}
    for p in sorted(d.glob("*.md")):
        if p.name.startswith("00_") or p.name.startswith("_combined"):
            continue
        m = FILE_RE.match(p.name)
        if m:
            out.setdefault(int(m.group(1)), []).append(p.name)
    return out


def declared_order(index_text: str) -> list[int]:
    """S-numbers in the order they first appear in the index."""
    seen, order = set(), []
    for m in INDEX_TOKEN_RE.finditer(index_text):
        n = int(m.group(1))
        if n not in seen:
            seen.add(n)
            order.append(n)
    return order


def subsection_gaps(text: str, n: int) -> list[str]:
    subs = sorted({int(b) for a, b in SUBSEC_RE.findall(text) if int(a) == n})
    if len(subs) < 2:
        return []
    gaps = [s for s in range(subs[0], subs[-1] + 1) if s not in subs]
    return [f"S{n}.{g}" for g in gaps]


def analyze(d: Path, index_name: str, manuscript: Path | None, out_path: Path | None) -> dict:
    if not d.is_dir():
        sys.stderr.write(f"ERROR: --dir not found: {d}\n")
        sys.exit(2)
    index_path = d / index_name
    if not index_path.is_file():
        sys.stderr.write(f"ERROR: index not found: {index_path}\n")
        sys.exit(2)
    index_text = index_path.read_text(encoding="utf-8")
    declared = declared_order(index_text)
    files = scan_files(d)
    present = sorted(files)

    problems = []
    for n in declared:
        if n not in files:
            problems.append({"kind": "INDEX_WITHOUT_FILE",
                             "detail": f"index declares S{n} but no S{n}_*.md file exists"})
    for n in present:
        if n not in declared:
            problems.append({"kind": "FILE_WITHOUT_INDEX",
                             "detail": f"file(s) {files[n]} present for S{n} but the index does not list it"})
        if len(files[n]) > 1:
            problems.append({"kind": "DUPLICATE_SECTION",
                             "detail": f"S{n} has {len(files[n])} files: {files[n]}"})
    for n in present:
        text = (d / files[n][0]).read_text(encoding="utf-8")
        for g in subsection_gaps(text, n):
            problems.append({"kind": "SUBSECTION_GAP",
                             "detail": f"{files[n][0]}: sub-section {g} is missing (numbering gap after an insert)"})

    coverage = {}
    if manuscript is not None:
        if not manuscript.is_file():
            sys.stderr.write(f"ERROR: --manuscript not found: {manuscript}\n")
            sys.exit(2)
        body = manuscript.read_text(encoding="utf-8")
        cited = sorted({int(m.group(1)) for m in CALLOUT_RE.finditer(body)})
        uncited = [n for n in present if n not in cited]
        callout_no_section = [n for n in cited if n not in files]
        coverage = {"cited": cited, "uncited_sections": uncited,
                    "callout_without_section": callout_no_section}
        for n in callout_no_section:
            problems.append({"kind": "CALLOUT_WITHOUT_SECTION",
                             "detail": f"body cites Supplementary S{n} but no S{n}_*.md section exists"})
        for n in uncited:
            problems.append({"kind": "SECTION_UNCITED",
                             "detail": f"S{n} section file exists but is never cited in the manuscript body"})

    rebuilt = None
    if out_path is not None:
        parts = []
        for n in declared:
            if n in files:
                parts.append((d / files[n][0]).read_text(encoding="utf-8").rstrip())
        rebuilt = "\n\n---\n\n".join(parts) + "\n"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rebuilt, encoding="utf-8")

    n_structural = sum(1 for p in problems if p["kind"] in STRUCTURAL)
    return {
        "dir": str(d),
        "declared": declared,
        "present": present,
        "problems": problems,
        "coverage": coverage,
        "rebuilt_to": str(out_path) if out_path else None,
        "summary": {"n_problems": len(problems), "n_structural": n_structural,
                    "verdict": "STRUCTURAL_PROBLEM" if n_structural else "OK"},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Supplement assembler + structural validator.")
    ap.add_argument("--dir", required=True, help="supplement directory")
    ap.add_argument("--index", default="00_index.md", help="index filename (default 00_index.md)")
    ap.add_argument("--manuscript", help="manuscript .md for callout coverage")
    ap.add_argument("--out", help="write rebuilt _combined.md to this path (index order)")
    ap.add_argument("--json", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any structural problem")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout report")
    args = ap.parse_args()

    result = analyze(Path(args.dir), args.index,
                     Path(args.manuscript) if args.manuscript else None,
                     Path(args.out) if args.out else None)

    if not args.quiet:
        print("=" * 41)
        print(" Supplement Assembly / Structure")
        print("=" * 41)
        print(f"declared (index): {result['declared']}")
        print(f"present (files):  {result['present']}")
        for p in result["problems"]:
            print(f"  [{p['kind']}] {p['detail']}")
        if result["rebuilt_to"]:
            print(f"rebuilt _combined → {result['rebuilt_to']}")
        s = result["summary"]
        print(f"\n{'STRUCTURAL PROBLEM: ' + str(s['n_structural']) if s['n_structural'] else 'OK: supplement structure consistent.'}")

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"wrote {args.json}")

    return 1 if (args.strict and result["summary"]["n_structural"]) else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""PRISMA flow 5-way consistency checker (DI-6).

Validates PRISMA flow numbers across five surfaces against a YAML single
source of truth. Substitutes drift control described in
`skills/meta-analysis/references/data_integrity_checklist.md` DI-6.

Usage:
    python3 scripts/prisma_5way_consistency.py --ssot prisma.yaml \\
        [--project-root <path>] [--json]

SSOT schema (YAML):
    databases:
      pubmed: 1234
      embase: 567
      cochrane: 89
    deduplication:
      after_dedup: 1500
    screening:
      title_abstract_excluded: 1400
      full_text_assessed: 100
      full_text_excluded: 85
    included:
      k: 15
    exclusion_reasons:
      wrong_population: 30
      wrong_intervention: 25
      wrong_outcome: 20
      wrong_study_design: 10
    surfaces:
      search_csv_glob: "1_Search/*.csv"
      # Surfaces may be either a bare path (requires ALL numbers) or a
      # mapping with `path` + `require` keys. `require` accepts a list of
      # dotted keys ("databases.pubmed", "deduplication.after_dedup",
      # "included.k") or glob-like patterns ("databases.*", "screening.*").
      screening_md:
        path: "2_Screening/prisma_flow_final.md"
        require: ["databases.*", "deduplication.after_dedup", "screening.*", "included.k"]
      methods_md:
        path: "7_Manuscript/methods.md"
        require: ["deduplication.after_dedup", "included.k"]
      results_md: "7_Manuscript/results.md"
      figure_caption: "5_Figures/_captions.md"

Exit codes: 0 all-consistent, 1 mismatch, 2 bad args / missing ssot.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


def load_ssot(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return yaml.safe_load(f)


def count_csv_rows(csv_glob: str, project_root: Path) -> int:
    total = 0
    for p in glob.glob(str(project_root / csv_glob)):
        with open(p) as f:
            n = sum(1 for _ in f) - 1
            total += max(n, 0)
    return total


def find_numbers_in_file(path: Path, expected: dict[str, int]) -> dict[str, bool]:
    if not path.exists():
        return {k: False for k in expected}
    text = path.read_text()
    hits: dict[str, bool] = {}
    for key, val in expected.items():
        pattern = rf"(?<!\d){val}(?!\d)"
        hits[key] = bool(re.search(pattern, text))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description="PRISMA 5-way consistency checker")
    ap.add_argument("--ssot", required=True, help="YAML single source of truth")
    ap.add_argument("--project-root", default=".", help="Project root (default: cwd)")
    ap.add_argument("--json", action="store_true", help="Emit JSON report")
    args = ap.parse_args()

    ssot_path = Path(args.ssot)
    if not ssot_path.exists():
        print(f"ERROR: SSOT not found: {ssot_path}", file=sys.stderr)
        return 2

    project_root = Path(args.project_root).resolve()
    ssot = load_ssot(ssot_path)

    # Flatten to dotted keys → int.
    all_numbers: dict[str, int] = {}
    for section in ("databases", "screening", "exclusion_reasons"):
        for k, v in (ssot.get(section) or {}).items():
            all_numbers[f"{section}.{k}"] = int(v)
    if "deduplication" in ssot:
        all_numbers["deduplication.after_dedup"] = int(ssot["deduplication"]["after_dedup"])
    if "included" in ssot:
        all_numbers["included.k"] = int(ssot["included"]["k"])

    def resolve_require(patterns: list[str] | None) -> dict[str, int]:
        if patterns is None:
            return dict(all_numbers)
        resolved: dict[str, int] = {}
        for pat in patterns:
            if pat.endswith(".*"):
                prefix = pat[:-2] + "."
                resolved.update({k: v for k, v in all_numbers.items() if k.startswith(prefix)})
            elif pat in all_numbers:
                resolved[pat] = all_numbers[pat]
        return resolved

    surfaces = ssot.get("surfaces") or {}
    report: dict[str, Any] = {"ssot": str(ssot_path), "surfaces": {}, "mismatches": []}

    csv_glob = surfaces.get("search_csv_glob")
    db_total = sum(v for k, v in all_numbers.items() if k.startswith("databases."))
    if csv_glob:
        csv_rows = count_csv_rows(csv_glob, project_root)
        ok = csv_rows == db_total
        report["surfaces"]["search_csv"] = {"expected": db_total, "found": csv_rows, "ok": ok}
        if not ok:
            report["mismatches"].append(
                f"search_csv: expected {db_total} rows across {csv_glob}, found {csv_rows}"
            )

    for surface_key in ("screening_md", "methods_md", "results_md", "figure_caption"):
        entry = surfaces.get(surface_key)
        if not entry:
            continue
        if isinstance(entry, str):
            rel, require = entry, None
        else:
            rel = entry.get("path")
            require = entry.get("require")
            if not rel:
                continue
        path = project_root / rel
        expected = resolve_require(require)
        hits = find_numbers_in_file(path, expected)
        missing = sorted(k for k, present in hits.items() if not present)
        report["surfaces"][surface_key] = {
            "path": str(path),
            "exists": path.exists(),
            "required": sorted(expected),
            "missing_numbers": missing,
        }
        if not path.exists():
            report["mismatches"].append(f"{surface_key}: file not found ({path})")
        elif missing:
            report["mismatches"].append(
                f"{surface_key}: missing {len(missing)} SSOT number(s): {', '.join(missing)}"
            )

    report["consistent"] = not report["mismatches"]

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"PRISMA 5-way consistency: {'PASS' if report['consistent'] else 'FAIL'}")
        print(f"  SSOT: {ssot_path}")
        for surface, info in report["surfaces"].items():
            status = "OK" if not info.get("missing_numbers") and info.get("exists", True) and info.get("ok", True) else "FAIL"
            print(f"  [{status}] {surface}: {info}")
        if report["mismatches"]:
            print("\nMismatches:")
            for m in report["mismatches"]:
                print(f"  - {m}")

    return 0 if report["consistent"] else 1


if __name__ == "__main__":
    sys.exit(main())

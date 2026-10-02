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

Optional SSOT keys used only by the flow-identity checks:
    screening.reports_not_retrieved   reports sought but not retrieved
    included.reports                  reports of included studies, when one
                                      study has several reports (else k is used)

What is checked
  1. Flow identities on the SSOT itself (each only when its keys are present):
       sum(databases)              >= after_dedup
       after_dedup - title_abstract_excluded [- reports_not_retrieved]
                                    = full_text_assessed
       full_text_assessed - full_text_excluded = included.reports or included.k
       sum(exclusion_reasons)       = full_text_excluded
  2. search_csv: CSV *records* (csv module; a quoted multi-line abstract is one
     record) across the glob = sum(databases).
  3. Each Markdown surface contains each required number AS A COUNT: not a
     decimal fragment ("3.12"), not part of a larger number ("1,500" for 500),
     not followed by a unit ("12 months", "12-month", "12%"), and not a table /
     figure / citation number ("Table 12", "[12]"). "1,500" matches 1500.
     This is still presence, not proof that the sentence states that count.

Exit codes: 0 all-consistent, 1 mismatch, 2 bad args / missing ssot.
"""

from __future__ import annotations

import argparse
import csv
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
    """Count CSV records (not physical lines): a quoted field may span lines."""
    total = 0
    for p in glob.glob(str(project_root / csv_glob)):
        with open(p, encoding="utf-8-sig", newline="") as f:
            rows = [r for r in csv.reader(f) if any(c.strip() for c in r)]
        total += max(len(rows) - 1, 0)
    return total


# A number followed by one of these is a measurement, not a PRISMA count.
_UNIT_RE = (
    r"(?:%|percent\b|per\s*cent\b|"
    r"(?:-\s*|\s+)?(?:months?|mo|years?|yrs?|y|weeks?|wks?|days?|d|hours?|hrs?|h|"
    r"minutes?|mins?|seconds?|s|mg|kg|g|mcg|µg|ml|mL|l|L|cm|mm|m|kDa|Gy|mmHg|bpm|"
    r"years?-old|year-old|fold|times)\b)"
)
# A number preceded by one of these labels something else (a table, a citation).
_LABEL_BEFORE_RE = re.compile(
    r"(?:\b(?:table|tables|figure|figures|fig\.?|supplementary|appendix|item|items|"
    r"ref\.?|refs\.?|reference|references|version|v)\s*|\[[\d,\s\u2013-]*|\^)$",
    re.IGNORECASE,
)


def _count_pattern(val: int) -> re.Pattern:
    forms = [str(val)]
    if abs(val) >= 1000:
        forms.append(f"{val:,}")
    alts = "|".join(re.escape(f) for f in sorted(forms, key=len, reverse=True))
    return re.compile(
        rf"(?<![\d.,])(?:{alts})(?!\d)(?!\.\d)(?!,\d{{3}})(?!\s*{_UNIT_RE})",
        re.IGNORECASE,
    )


def number_present_as_count(text: str, val: int) -> bool:
    for m in _count_pattern(val).finditer(text):
        if _LABEL_BEFORE_RE.search(text[max(0, m.start() - 20):m.start()]):
            continue
        return True
    return False


def find_numbers_in_file(path: Path, expected: dict[str, int]) -> dict[str, bool]:
    if not path.exists():
        return {k: False for k in expected}
    text = path.read_text(encoding="utf-8")
    return {key: number_present_as_count(text, val) for key, val in expected.items()}


def flow_identity_checks(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    """PRISMA flow arithmetic on the SSOT. Each identity is evaluated only when
    every key it needs is present."""
    dbs = ssot.get("databases") or {}
    dedup = (ssot.get("deduplication") or {}).get("after_dedup")
    scr = ssot.get("screening") or {}
    inc = ssot.get("included") or {}
    reasons = ssot.get("exclusion_reasons") or {}
    ta_ex = scr.get("title_abstract_excluded")
    assessed = scr.get("full_text_assessed")
    ft_ex = scr.get("full_text_excluded")
    not_retrieved = int(scr.get("reports_not_retrieved") or 0)
    k_reports = inc.get("reports", inc.get("k"))
    out: list[dict[str, Any]] = []

    def add(name: str, ok: bool, lhs: int, rhs: int) -> None:
        out.append({"identity": name, "ok": ok, "lhs": lhs, "rhs": rhs})

    if dbs and dedup is not None:
        tot = sum(int(v) for v in dbs.values())
        add("sum(databases) >= deduplication.after_dedup", tot >= int(dedup), tot, int(dedup))
    if None not in (dedup, ta_ex, assessed):
        lhs = int(dedup) - int(ta_ex) - not_retrieved
        name = "after_dedup - title_abstract_excluded"
        if not_retrieved:
            name += " - reports_not_retrieved"
        add(name + " = full_text_assessed", lhs == int(assessed), lhs, int(assessed))
    if None not in (assessed, ft_ex, k_reports):
        lhs = int(assessed) - int(ft_ex)
        target = "included.reports" if "reports" in inc else "included.k"
        add(f"full_text_assessed - full_text_excluded = {target}", lhs == int(k_reports), lhs, int(k_reports))
    if reasons and ft_ex is not None:
        tot = sum(int(v) for v in reasons.values())
        add("sum(exclusion_reasons) = full_text_excluded", tot == int(ft_ex), tot, int(ft_ex))
    return out


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

    report["flow_identities"] = flow_identity_checks(ssot)
    for chk in report["flow_identities"]:
        if not chk["ok"]:
            report["mismatches"].append(
                f"flow: {chk['identity']} fails ({chk['lhs']} vs {chk['rhs']})"
            )

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
        for chk in report["flow_identities"]:
            print(f"  [{'OK' if chk['ok'] else 'FAIL'}] flow: {chk['identity']} ({chk['lhs']} vs {chk['rhs']})")
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

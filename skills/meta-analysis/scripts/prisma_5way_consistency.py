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
    screening.other_methods_assessed  reports from other methods (citation
                                      searching, registers, experts) assessed
                                      at full text without passing through
                                      deduplication / title-abstract screening
                                      (PRISMA 2020 two-column flow)
    included.reports                  reports of included studies, when one
                                      study has several reports (else k is used)
  Declare a key as 0 when it does not apply; that makes the identity strict.

What is checked
  1. Flow identities on the SSOT itself (each only when its keys are present):
       sum(databases)              >= after_dedup
       after_dedup - title_abstract_excluded - reports_not_retrieved
         + other_methods_assessed   = full_text_assessed
       full_text_assessed - full_text_excluded = included.reports or included.k
       sum(exclusion_reasons)       = full_text_excluded
     An identity whose gap could be explained by an optional key the SSOT does
     not declare is reported NOT_ASSESSED (not a failure, not a pass):
       - left side < full_text_assessed and other_methods_assessed absent;
       - left side > full_text_assessed and reports_not_retrieved absent;
       - assessed - excluded > k and included.reports absent (one study may
         have several reports). assessed - excluded < k is always a failure.
  2. search_csv: CSV *records* (csv module; a quoted multi-line abstract is one
     record) across the glob = sum(databases).
  3. Each Markdown surface contains each required number AS A COUNT: not a
     decimal fragment ("3.12"), not part of a larger number ("1,500" for 500),
     not followed by a unit ("12 months", "12-month", "12%"), and not a table /
     figure / citation number ("Table 12", "[12]"). "1,500" matches 1500.
     The unit test looks only along the same line (a following Markdown
     bullet "- Years ..." is not a unit) and accepts "-", en and em dashes.
     This is still presence, not proof that the sentence states that count.

Exit codes: 0 all-consistent (NOT_ASSESSED identities do not fail the run),
1 mismatch, 2 bad args / missing ssot / non-numeric SSOT count.
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


class SSOTError(ValueError):
    """A count in the SSOT is not a whole number."""


def as_count(value: Any, key: str) -> int:
    if isinstance(value, bool):
        raise SSOTError(f"{key}: expected a whole number, got {value!r}")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and re.fullmatch(r"\s*\d+\s*", value):
        return int(value)
    raise SSOTError(f"{key}: expected a whole number, got {value!r}")


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
# "[^\S\r\n]" is any whitespace except a line break (so a non-breaking space
# from a Word/pandoc conversion still joins "12" to "months", but the next
# bullet's "- Years" on a new line does not).
_HSPACE = r"[^\S\r\n]"
# Multi-letter units: case-insensitive, end at a word boundary.
_LONG_UNITS = (
    r"(?:months?|years?-old|year-old|years?|yrs?|weeks?|wks?|days?|hours?|hrs?|"
    r"minutes?|mins?|seconds?|mg|kg|mcg|µg|ml|cm|mm|kDa|Gy|mmHg|bpm|fold|times)\b"
)
# One- and two-letter units are lower case (plus "L" for litre) and count only
# when the token ends there: not followed by a letter or digit, by "-" or "."
# then a letter or digit, or by ". " then a lower-case word. Otherwise
# "12 D-dimer", "12 G-tube", "12 S-ketamine", "12 H. pylori", "12 Y-90",
# "12 L-dopa", "12 m-Health" and "G-CSF" would read as measurements and hide
# the count they state.
_SHORT_UNITS = (
    r"(?-i:mo|y|d|h|s|m|g|l|L)"
    r"(?![\w])(?![-.\u2013\u2014]\w)(?!\.[^\S\r\n]+[a-z])"
)
_UNIT_RE = (
    rf"(?:%|percent\b|per{_HSPACE}*cent\b|"
    rf"(?:[-\u2013\u2014]{_HSPACE}*|{_HSPACE}+)?(?:{_LONG_UNITS}|{_SHORT_UNITS}))"
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
        rf"(?<![\d.,])(?:{alts})(?!\d)(?!\.\d)(?!,\d{{3}})(?!{_HSPACE}*{_UNIT_RE})",
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
    every key it needs is present. status is OK, FAIL or NOT_ASSESSED; ok is
    True / False / None accordingly."""
    dbs = ssot.get("databases") or {}
    dedup_sec = ssot.get("deduplication") or {}
    scr = ssot.get("screening") or {}
    inc = ssot.get("included") or {}
    reasons = ssot.get("exclusion_reasons") or {}

    def opt(sec: dict, sec_name: str, key: str) -> int | None:
        v = sec.get(key)
        return None if v is None else as_count(v, f"{sec_name}.{key}")

    dedup = opt(dedup_sec, "deduplication", "after_dedup")
    ta_ex = opt(scr, "screening", "title_abstract_excluded")
    assessed = opt(scr, "screening", "full_text_assessed")
    ft_ex = opt(scr, "screening", "full_text_excluded")
    not_retrieved = opt(scr, "screening", "reports_not_retrieved")
    other_methods = opt(scr, "screening", "other_methods_assessed")
    k = opt(inc, "included", "k")
    reports = opt(inc, "included", "reports")
    out: list[dict[str, Any]] = []

    def add(name: str, status: str, lhs: int, rhs: int, note: str = "") -> None:
        ok = {"OK": True, "FAIL": False}.get(status)
        row = {"identity": name, "status": status, "ok": ok, "lhs": lhs, "rhs": rhs}
        if note:
            row["note"] = note
        out.append(row)

    def strict(lhs: int, rhs: int) -> str:
        return "OK" if lhs == rhs else "FAIL"

    if dbs and dedup is not None:
        tot = sum(as_count(v, f"databases.{n}") for n, v in dbs.items())
        add("sum(databases) >= deduplication.after_dedup",
            "OK" if tot >= dedup else "FAIL", tot, dedup)
    if None not in (dedup, ta_ex, assessed):
        lhs = dedup - ta_ex - (not_retrieved or 0) + (other_methods or 0)
        name = "after_dedup - title_abstract_excluded"
        if not_retrieved is not None:
            name += " - reports_not_retrieved"
        if other_methods is not None:
            name += " + other_methods_assessed"
        name += " = full_text_assessed"
        status, note = strict(lhs, assessed), ""
        if lhs < assessed and other_methods is None:
            status = "NOT_ASSESSED"
            note = ("full_text_assessed exceeds the database path by "
                    f"{assessed - lhs}; declare screening.other_methods_assessed "
                    "(0 if none) to assess this identity")
        elif lhs > assessed and not_retrieved is None:
            status = "NOT_ASSESSED"
            note = ("database path exceeds full_text_assessed by "
                    f"{lhs - assessed}; declare screening.reports_not_retrieved "
                    "(0 if none) to assess this identity")
        add(name, status, lhs, assessed, note)
    k_reports = reports if reports is not None else k
    if None not in (assessed, ft_ex, k_reports):
        lhs = assessed - ft_ex
        target = "included.reports" if reports is not None else "included.k"
        status, note = strict(lhs, k_reports), ""
        if reports is None and lhs > k_reports:
            status = "NOT_ASSESSED"
            note = (f"{lhs} reports vs {k_reports} studies; declare "
                    "included.reports (reports of included studies) to assess "
                    "this identity")
        add(f"full_text_assessed - full_text_excluded = {target}", status, lhs, k_reports, note)
    if reasons and ft_ex is not None:
        tot = sum(as_count(v, f"exclusion_reasons.{n}") for n, v in reasons.items())
        add("sum(exclusion_reasons) = full_text_excluded", strict(tot, ft_ex), tot, ft_ex)
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
    if not isinstance(ssot, dict):
        print(f"ERROR: SSOT is not a YAML mapping: {ssot_path}", file=sys.stderr)
        return 2

    # Flatten to dotted keys → int.
    all_numbers: dict[str, int] = {}
    try:
        for section in ("databases", "screening", "exclusion_reasons"):
            for k, v in (ssot.get(section) or {}).items():
                all_numbers[f"{section}.{k}"] = as_count(v, f"{section}.{k}")
        if "deduplication" in ssot:
            all_numbers["deduplication.after_dedup"] = as_count(
                (ssot["deduplication"] or {}).get("after_dedup"), "deduplication.after_dedup")
        if "included" in ssot:
            all_numbers["included.k"] = as_count(
                (ssot["included"] or {}).get("k"), "included.k")
        flow = flow_identity_checks(ssot)
    except (SSOTError, AttributeError) as exc:
        print(f"ERROR: bad SSOT {ssot_path}: {exc}", file=sys.stderr)
        return 2

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

    report["flow_identities"] = flow
    for chk in report["flow_identities"]:
        if chk["status"] == "FAIL":
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
            extra = f" - {chk['note']}" if chk.get("note") else ""
            print(f"  [{chk['status']}] flow: {chk['identity']} ({chk['lhs']} vs {chk['rhs']}){extra}")
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

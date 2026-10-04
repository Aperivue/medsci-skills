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
    deduplication.other_sources_before_dedup
                                      records from other sources (citation
                                      searching, registers) added BEFORE
                                      deduplication (PRISMA 2009 layout)
    included.reports                  reports of included studies. Declare it
                                      to make assessed - excluded strict; without
                                      it a mismatch with k is NOT_ASSESSED (one
                                      study may have several reports, and one
                                      report several studies, e.g. DTA cohorts)
  Declare a key as 0 when it does not apply; that makes the identity strict.
  Like every screening.* key, a declared key is also a number a bare-path
  surface (one without `require`) must contain; list `require` explicitly on
  surfaces that do not state it.

Optional PRISMA 2020 report-level section (flow identities only; these keys
are NOT surface numbers, and an SSOT without the section is reported exactly
as before). Unknown keys in it are an input error (exit 2):
  The counts are the databases/registers column of the PRISMA 2020 diagram,
  except reports_included and studies_included, which are the review totals
  (both columns, and the previous version of an updated review).
    prisma2020:
      records_screened: 700         # after_dedup minus records removed before
                                    # screening (automation tools, other)
      reports_sought: 80            # reports sought for retrieval
      reports_not_retrieved: 5
      reports_assessed: 75          # reports assessed for eligibility
      reports_excluded: 60
      reports_excluded_reasons: {wrong_population: 35, wrong_outcome: 25}
      reports_included: 15          # reports of included studies (total)
      other_reports_included: 0     # of those, reports from other methods
                                    # (citation searching, websites, ...) or
                                    # from the previous version of the review
      studies_included: 12          # studies included in review
  Identities (each listed only when one of its prisma2020 keys is declared;
  one with an undeclared term is NOT_ASSESSED, naming the term):
       records_screened - screening.title_abstract_excluded = reports_sought
         (with records_screened undeclared, after_dedup is used instead and a
         mismatch is NOT_ASSESSED: records removed before screening)
       reports_sought - reports_not_retrieved = reports_assessed
       reports_assessed - reports_excluded + other_reports_included
         = reports_included
         (with other_reports_included undeclared, a reports_included above
         assessed - excluded is NOT_ASSESSED, below it a FAIL)
       sum(reports_excluded_reasons, else exclusion_reasons) = reports_excluded
         (a sum above reports_excluded is NOT_ASSESSED, below it a FAIL)
       studies_included <= reports_included
         (more studies than reports is NOT_ASSESSED, as for included.reports)
  A declared identity that does not hold is a FAIL (exit 1).

What is checked
  1. Flow identities on the SSOT itself (each only when its keys are present):
       sum(databases) + other_sources_before_dedup >= after_dedup
       full_text_assessed - full_text_excluded = included.reports
         (or = included.k when included.reports is absent; see below)
       included.reports             >= included.k
       sum(exclusion_reasons)       = full_text_excluded
     An identity whose gap could be explained by an optional key the SSOT does
     not declare is reported NOT_ASSESSED (not a failure, not a pass):
       - sum(databases) < after_dedup and other_sources_before_dedup absent;
       - assessed - excluded != k and included.reports absent: one study may
         have several reports (> k), and one report may contribute several
         studies -- DTA cohorts / 2x2 tables, or an updated review's studies
         from the previous version (< k). Declared, the identity is strict;
       - included.reports < included.k (a report may hold several studies);
       - sum(exclusion_reasons) > full_text_excluded (several reasons may be
         recorded per report). A smaller sum is a failure.
     after_dedup -> full_text_assessed is NOT checked: the SSOT has no key for
     records removed before screening (automation tools, other reasons), so a
     correct PRISMA 2020 flow cannot be told from a wrong one.
  2. search_csv: CSV *records* (csv module; a quoted multi-line abstract is one
     record) across the glob = sum(databases).
  3. Each Markdown surface: a required number that does not occur at all is a
     FAIL (it cannot be stated there). A number that does occur is only
     PRESENT: prose cannot be parsed into "this is the count of included
     studies" ("12 months", "Table 12" and "12 studies" all contain 12), so the
     surface is reported NOT_ASSESSED, never OK. Read those sentences yourself.
     "1,500" is accepted as an occurrence of 1500.

Exit codes: 0 no mismatch (verdict PASS, or NOT_ASSESSED when a flow identity
or a prose surface could not be assessed -- the report lists each one),
1 mismatch, 2 bad args / missing ssot / non-numeric SSOT count,
3 --strict and something was NOT_ASSESSED.
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


def number_present(text: str, val: int) -> bool:
    """True when `val` occurs as a digit run in `text` (the boundary main always
    used: not preceded or followed by another digit), or in its thousands-
    separated form ("1,500" for 1500). This is PRESENCE only. Whether that
    occurrence is the PRISMA count ("12 studies") or something else ("12
    months", "Table 12") is not decided here -- no prose heuristic can decide it
    reliably -- so a present number is reported NOT_ASSESSED, never OK."""
    forms = [str(val)]
    if abs(val) >= 1000:
        forms.append(f"{val:,}")
    alts = "|".join(re.escape(f) for f in sorted(forms, key=len, reverse=True))
    return re.search(rf"(?<!\d)(?:{alts})(?!\d)", text) is not None


def find_numbers_in_file(path: Path, expected: dict[str, int]) -> dict[str, bool]:
    if not path.exists():
        return {k: False for k in expected}
    text = path.read_text(encoding="utf-8")
    return {key: number_present(text, val) for key, val in expected.items()}


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
    assessed = opt(scr, "screening", "full_text_assessed")
    ft_ex = opt(scr, "screening", "full_text_excluded")
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

    other_before = opt(dedup_sec, "deduplication", "other_sources_before_dedup")
    if dbs and dedup is not None:
        tot = sum(as_count(v, f"databases.{n}") for n, v in dbs.items())
        name = "sum(databases)"
        if other_before is not None:
            tot += other_before
            name += " + other_sources_before_dedup"
        name += " >= deduplication.after_dedup"
        status, note = ("OK" if tot >= dedup else "FAIL"), ""
        if tot < dedup and other_before is None:
            # PRISMA 2009 flows add records from other sources before
            # deduplication; they can outnumber the duplicates removed.
            status = "NOT_ASSESSED"
            note = ("after_dedup exceeds the database records by "
                    f"{dedup - tot}; declare "
                    "deduplication.other_sources_before_dedup (0 if none) "
                    "to assess this identity")
        add(name, status, tot, dedup, note)
    if None not in (assessed, ft_ex) and (reports is not None or k is not None):
        lhs = assessed - ft_ex
        if reports is not None:
            # Strict only when the SSOT declares how many reports were included.
            add("full_text_assessed - full_text_excluded = included.reports",
                strict(lhs, reports), lhs, reports)
        elif k is not None:
            # Without included.reports the SSOT cannot tell reports from
            # studies: one study may have several reports (lhs > k), and one
            # report may contribute several studies -- cohorts or 2x2 tables in
            # a DTA review, or studies carried over from a previous version of
            # an updated review (lhs < k). Never a failure here.
            status, note = "OK", ""
            if lhs != k:
                status = "NOT_ASSESSED"
                note = (f"{lhs} reports (assessed - excluded) vs {k} studies; "
                        "declare included.reports (reports of included studies) "
                        "to assess this identity")
            add("full_text_assessed - full_text_excluded = included.k", status, lhs, k, note)
    if reports is not None and k is not None:
        # Reports normally outnumber studies, but a report can contribute
        # several studies (DTA cohorts / 2x2 tables), so the input cannot tell
        # an error from that design: NOT_ASSESSED, never FAIL.
        status, note = "OK", ""
        if reports < k:
            status = "NOT_ASSESSED"
            note = (f"{k - reports} more studies than reports; correct if one report "
                    "contributes several studies (e.g. DTA cohorts), otherwise check "
                    "included.reports and included.k")
        add("included.reports >= included.k", status, reports, k, note)
    if reasons and ft_ex is not None:
        tot = sum(as_count(v, f"exclusion_reasons.{n}") for n, v in reasons.items())
        status, note = strict(tot, ft_ex), ""
        if tot > ft_ex:
            # Several reasons may be recorded per excluded report; only a sum
            # SMALLER than full_text_excluded proves a report has no reason.
            status = "NOT_ASSESSED"
            note = (f"reasons sum to {tot - ft_ex} more than full_text_excluded; "
                    "expected only if some reports list several reasons")
        add("sum(exclusion_reasons) = full_text_excluded", status, tot, ft_ex, note)
    out.extend(prisma2020_checks(ssot, dedup))
    return out


# Optional PRISMA 2020 report-level keys (section `prisma2020:`). Read only by
# the flow identities below; they are not surface numbers.
PRISMA2020_COUNT_KEYS = (
    "records_screened", "reports_sought", "reports_not_retrieved",
    "reports_assessed", "reports_excluded", "reports_included", "studies_included",
    "other_reports_included",
)
PRISMA2020_KEYS = PRISMA2020_COUNT_KEYS + ("reports_excluded_reasons",)


def prisma2020_checks(ssot: dict[str, Any], dedup: int | None) -> list[dict[str, Any]]:
    """Report-level PRISMA 2020 identities. Returns [] when the SSOT has no
    `prisma2020` section, so an SSOT without it is reported exactly as before.
    An identity is listed only when at least one of its prisma2020 keys is
    declared; one with an undeclared term is NOT_ASSESSED, naming that term."""
    sec = ssot.get("prisma2020")
    if sec is None:
        return []
    if not isinstance(sec, dict):
        raise SSOTError(f"prisma2020: expected a mapping, got {type(sec).__name__}")
    unknown = sorted(str(k) for k in sec if k not in PRISMA2020_KEYS)
    if unknown:
        raise SSOTError(f"prisma2020: unknown key(s) {', '.join(unknown)} "
                        f"(allowed: {', '.join(PRISMA2020_KEYS)})")
    p = {k: (None if sec.get(k) is None else as_count(sec[k], f"prisma2020.{k}"))
         for k in PRISMA2020_COUNT_KEYS}
    reasons_raw = sec.get("reports_excluded_reasons")
    if reasons_raw is not None and not isinstance(reasons_raw, dict):
        raise SSOTError("prisma2020.reports_excluded_reasons: expected a mapping of "
                        "reason -> count")
    scr = ssot.get("screening") or {}
    ta_raw = scr.get("title_abstract_excluded")
    ta_ex = None if ta_raw is None else as_count(ta_raw, "screening.title_abstract_excluded")
    out: list[dict[str, Any]] = []

    def row(name: str, status: str, lhs: int | None, rhs: int | None, note: str = "") -> None:
        r = {"identity": name, "status": status, "ok": {"OK": True, "FAIL": False}.get(status),
             "lhs": lhs, "rhs": rhs}
        if note:
            r["note"] = note
        out.append(r)

    def undeclared(name: str, missing: list[str]) -> None:
        row(name, "NOT_ASSESSED", None, None,
            f"undeclared: {', '.join(missing)}; declare it (0 if none) to assess this identity")

    # 1. records screened - title/abstract excluded = reports sought.
    if p["reports_sought"] is not None or p["records_screened"] is not None:
        if p["records_screened"] is not None:
            base, base_name, strict_base = p["records_screened"], "prisma2020.records_screened", True
        else:
            base, base_name, strict_base = dedup, "deduplication.after_dedup", False
        name = (f"{base_name} - screening.title_abstract_excluded "
                "= prisma2020.reports_sought")
        missing = [n for n, v in ((base_name, base),
                                  ("screening.title_abstract_excluded", ta_ex),
                                  ("prisma2020.reports_sought", p["reports_sought"]))
                   if v is None]
        if missing:
            undeclared(name, missing)
        else:
            lhs = base - ta_ex
            if lhs == p["reports_sought"]:
                row(name, "OK", lhs, p["reports_sought"])
            elif strict_base:
                row(name, "FAIL", lhs, p["reports_sought"])
            else:
                # Records removed before screening (automation tools, other
                # reasons) sit between after_dedup and screening; the SSOT
                # cannot tell them from an error unless records_screened is set.
                row(name, "NOT_ASSESSED", lhs, p["reports_sought"],
                    "after_dedup may include records removed before screening; declare "
                    "prisma2020.records_screened to assess this identity")

    def strict_identity(name: str, terms: list[tuple[str, int | None]], compute) -> None:
        missing = [n for n, v in terms if v is None]
        if missing:
            undeclared(name, missing)
            return
        lhs, rhs = compute()
        row(name, "OK" if lhs == rhs else "FAIL", lhs, rhs)

    # 2. reports sought - not retrieved = reports assessed.
    t2 = [("prisma2020.reports_sought", p["reports_sought"]),
          ("prisma2020.reports_not_retrieved", p["reports_not_retrieved"]),
          ("prisma2020.reports_assessed", p["reports_assessed"])]
    if any(v is not None for _, v in t2):
        strict_identity("prisma2020.reports_sought - prisma2020.reports_not_retrieved "
                        "= prisma2020.reports_assessed", t2,
                        lambda: (p["reports_sought"] - p["reports_not_retrieved"],
                                 p["reports_assessed"]))

    # 3. reports assessed - reports excluded (+ other methods) = reports included.
    # reports_included is the review total; reports found by other methods
    # (citation searching, websites) or carried over from a previous version
    # are added below the databases/registers column, so without
    # other_reports_included only a total SMALLER than assessed - excluded is
    # certain to be wrong.
    other = p["other_reports_included"]
    t3 = [("prisma2020.reports_assessed", p["reports_assessed"]),
          ("prisma2020.reports_excluded", p["reports_excluded"]),
          ("prisma2020.reports_included", p["reports_included"])]
    if any(v is not None for _, v in t3) or other is not None:
        name = "prisma2020.reports_assessed - prisma2020.reports_excluded"
        if other is not None:
            name += " + prisma2020.other_reports_included"
        name += " = prisma2020.reports_included"
        missing = [n for n, v in t3 if v is None]
        if missing:
            undeclared(name, missing)
        else:
            lhs = p["reports_assessed"] - p["reports_excluded"] + (other or 0)
            rhs = p["reports_included"]
            if lhs == rhs:
                row(name, "OK", lhs, rhs)
            elif other is not None or rhs < lhs:
                row(name, "FAIL", lhs, rhs)
            else:
                row(name, "NOT_ASSESSED", lhs, rhs,
                    f"reports_included exceeds assessed - excluded by {rhs - lhs}; "
                    "expected if reports came from other methods or a previous version. "
                    "Declare prisma2020.other_reports_included (0 if none) to assess "
                    "this identity")

    # 4. sum(reasons) = reports excluded. Reasons come from
    # prisma2020.reports_excluded_reasons, else from exclusion_reasons.
    if p["reports_excluded"] is not None or reasons_raw is not None:
        if reasons_raw is not None:
            reasons, rname = reasons_raw, "prisma2020.reports_excluded_reasons"
        else:
            reasons, rname = ssot.get("exclusion_reasons") or None, "exclusion_reasons"
        name = f"sum({rname}) = prisma2020.reports_excluded"
        missing = ([] if reasons is not None else [rname]) + (
            [] if p["reports_excluded"] is not None else ["prisma2020.reports_excluded"])
        if missing:
            undeclared(name, missing)
        else:
            tot = sum(as_count(v, f"{rname}.{n}") for n, v in reasons.items())
            ex = p["reports_excluded"]
            if tot == ex:
                row(name, "OK", tot, ex)
            elif tot < ex:
                row(name, "FAIL", tot, ex)
            else:
                # Several reasons may be recorded per excluded report.
                row(name, "NOT_ASSESSED", tot, ex,
                    f"reasons sum to {tot - ex} more than reports_excluded; "
                    "expected only if some reports list several reasons")

    # 5. studies included <= reports included.
    t5 = [("prisma2020.studies_included", p["studies_included"]),
          ("prisma2020.reports_included", p["reports_included"])]
    if any(v is not None for _, v in t5):
        name = "prisma2020.studies_included <= prisma2020.reports_included"
        missing = [n for n, v in t5 if v is None]
        if missing:
            undeclared(name, missing)
        elif p["studies_included"] <= p["reports_included"]:
            row(name, "OK", p["studies_included"], p["reports_included"])
        else:
            # Same reasoning as included.reports >= included.k: one report can
            # contribute several studies (DTA cohorts / 2x2 tables).
            row(name, "NOT_ASSESSED", p["studies_included"], p["reports_included"],
                f"{p['studies_included'] - p['reports_included']} more studies than "
                "reports; correct if one report contributes several studies (e.g. DTA "
                "cohorts), otherwise check both counts")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="PRISMA 5-way consistency checker")
    ap.add_argument("--ssot", required=True, help="YAML single source of truth")
    ap.add_argument("--project-root", default=".", help="Project root (default: cwd)")
    ap.add_argument("--json", action="store_true", help="Emit JSON report")
    ap.add_argument("--strict", action="store_true",
                    help="Exit 3 when any check is NOT_ASSESSED (prose surface or flow identity)")
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
    report["not_assessed"] = []
    for chk in report["flow_identities"]:
        if chk["status"] == "FAIL":
            report["mismatches"].append(
                f"flow: {chk['identity']} fails ({chk['lhs']} vs {chk['rhs']})"
            )
        elif chk["status"] == "NOT_ASSESSED":
            report["not_assessed"].append(f"flow: {chk['identity']}")

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
        present = sorted(k for k, hit in hits.items() if hit)
        if not path.exists() or missing:
            status = "FAIL"
        elif present:
            status = "NOT_ASSESSED"
        else:
            status = "OK"  # nothing required on this surface
        report["surfaces"][surface_key] = {
            "path": str(path),
            "exists": path.exists(),
            "required": sorted(expected),
            "missing_numbers": missing,
            # Present somewhere in the prose; NOT verified to be stated as that count.
            "present_not_verified_as_count": present,
            "status": status,
        }
        if not path.exists():
            report["mismatches"].append(f"{surface_key}: file not found ({path})")
        elif missing:
            report["mismatches"].append(
                f"{surface_key}: missing {len(missing)} SSOT number(s): {', '.join(missing)}"
            )
        if path.exists() and present:
            report["not_assessed"].append(
                f"{surface_key}: {len(present)} number(s) present in prose but not verified "
                f"as the PRISMA count: {', '.join(present)}"
            )

    report["consistent"] = not report["mismatches"]
    if report["mismatches"]:
        report["verdict"] = "FAIL"
    elif report["not_assessed"]:
        report["verdict"] = "NOT_ASSESSED"
    else:
        report["verdict"] = "PASS"

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"PRISMA 5-way consistency: {report['verdict']}")
        print(f"  SSOT: {ssot_path}")
        for chk in report["flow_identities"]:
            extra = f" - {chk['note']}" if chk.get("note") else ""
            vals = ("not computed" if chk["lhs"] is None
                    else f"{chk['lhs']} vs {chk['rhs']}")
            print(f"  [{chk['status']}] flow: {chk['identity']} ({vals}){extra}")
        for surface, info in report["surfaces"].items():
            status = info.get("status") or ("OK" if info.get("ok", True) else "FAIL")
            print(f"  [{status}] {surface}: {info}")
        if report["mismatches"]:
            print("\nMismatches:")
            for m in report["mismatches"]:
                print(f"  - {m}")
        if report["not_assessed"]:
            print("\nNot assessed (no mismatch found, but not verified either):")
            for m in report["not_assessed"]:
                print(f"  - {m}")

    if not report["consistent"]:
        return 1
    if args.strict and report["not_assessed"]:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())

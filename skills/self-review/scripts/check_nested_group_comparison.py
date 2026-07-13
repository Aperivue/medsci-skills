#!/usr/bin/env python3
"""check_nested_group_comparison.py — flag a baseline/characteristics table that
reports a P value comparing an analysed subset against the parent cohort that
contains it.

When authors answer a selection-bias comment with a "representativeness" table,
they routinely compare the analysed subset (n=33) with the "full cohort" (n=132)
that *includes* those 33 patients, and print P values from it. The two groups are
nested, so the two-group test is not merely uninformative — it is invalid. The
informative contrast is subset vs remainder (n=99). This is deterministic: the
column headers announce the two n's and their labels verbatim.

Fires when a table has (a) two column headers each carrying an ``n = N``, (b) one
header labelled subset/sub-cohort/correlated/analysed/surgical/pathology and the
other labelled full/total/overall/entire/whole cohort, and (c) a P-value column.
Also on prose of the form "compared … between the … subset and the … cohort".

Stdlib-only. Reads the manuscript, never writes it.

Usage:
  python3 check_nested_group_comparison.py --manuscript paper.md [--strict] [--quiet] [--json]
Exit: 0 clean; with --strict, 1 on any NESTED_GROUP_TEST; 2 on input/usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict

HEADER_N_RE = re.compile(r"\bn\s*=\s*([0-9][0-9,]*)", re.I)
SUBSET_RE = re.compile(r"\b(subset|sub-?cohort|correlated|analy[sz]ed|surgical|patholog\w*|resected|with .*patholog)", re.I)
FULL_RE = re.compile(r"\b(full|total|overall|entire|whole)\b", re.I)
REMAINDER_RE = re.compile(r"\b(remainder|remaining|rest of|excluded|non-)", re.I)
PVAL_HEADER_RE = re.compile(r"^\s*\*?\s*[Pp]\s*(?:[- ]?value)?\s*\*?\s*$")
PVAL_HEADER_CONTAINS = re.compile(r"\bp[- ]?value\b", re.I)
SEP_RE = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")
PROSE_RE = re.compile(
    r"compar\w+\b[^.]*\bbetween\b[^.]*\b(subset|sub-?cohort|analy[sz]ed[^.]*?)\b[^.]*\b(full|entire|total|whole)\s+cohort",
    re.I)


@dataclass
class Finding:
    kind: str
    severity: str
    line: int
    detail: str


@dataclass
class Report:
    source: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def n_flag(self) -> int:
        return sum(1 for f in self.findings if f.kind == "NESTED_GROUP_TEST")

    @property
    def verdict(self) -> str:
        return "NESTED COMPARISON FOUND" if self.n_flag else "OK"


def _split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _tables(text: str):
    lines = text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        if "|" in lines[i] and i + 1 < n and SEP_RE.match(lines[i + 1]) and "-" in lines[i + 1]:
            yield _split_row(lines[i]), i + 1
            i += 2
        else:
            i += 1


def audit(text: str, source: str) -> Report:
    rep = Report(source=source)
    for header, lineno in _tables(text):
        n_cols = [(j, h, int(m.group(1).replace(",", "")))
                  for j, h in enumerate(header) if (m := HEADER_N_RE.search(h))]
        if len(n_cols) < 2:
            continue
        has_p = any(PVAL_HEADER_RE.match(h) or PVAL_HEADER_CONTAINS.search(h) for h in header)
        if not has_p:
            continue
        subset_cols = [(j, h, nv) for j, h, nv in n_cols if SUBSET_RE.search(h)]
        full_cols = [(j, h, nv) for j, h, nv in n_cols
                     if FULL_RE.search(h) and not REMAINDER_RE.search(h)]
        if subset_cols and full_cols:
            s = min(subset_cols, key=lambda c: c[2])
            f = max(full_cols, key=lambda c: c[2])
            if s[2] < f[2]:  # subset smaller than the cohort that names it
                rep.findings.append(Finding(
                    "NESTED_GROUP_TEST", "MAJOR", lineno,
                    f"P-value table compares subset '{s[1]}' (n={s[2]}) against "
                    f"'{f[1]}' (n={f[2]}) that contains it — nested groups; the valid "
                    f"contrast is subset vs remainder (n={f[2] - s[2]})"))
    for m in PROSE_RE.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        rep.findings.append(Finding(
            "NESTED_GROUP_TEST", "MAJOR", line,
            f"prose compares a subset against the full cohort that contains it: "
            f"\"{m.group(0)[:90]}…\""))
    return rep


def format_report(rep: Report, color: bool) -> str:
    tag = {"OK": "\033[92m", "NESTED COMPARISON FOUND": "\033[91m"}.get(rep.verdict, "") if color else ""
    end = "\033[0m" if color else ""
    out = [f"{tag}== {rep.verdict} =={end}  {rep.source}", f"nested_comparisons={rep.n_flag}"]
    if not rep.findings:
        out.append("no subset-vs-parent-cohort P-value comparison detected.")
        return "\n".join(out)
    for f in sorted(rep.findings, key=lambda x: (x.line, x.detail)):
        out.append(f"[{f.severity}] {f.kind} L{f.line}  {f.detail}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any NESTED_GROUP_TEST")
    ap.add_argument("--quiet", action="store_true", help="suppress the report; exit code only")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a text report")
    args = ap.parse_args(argv)
    try:
        text = open(args.manuscript, encoding="utf-8").read()
    except OSError as e:
        print(f"error: cannot read manuscript: {e}", file=sys.stderr)
        return 2
    rep = audit(text, args.manuscript)
    if not args.quiet:
        if args.json:
            print(json.dumps({"detector": "check_nested_group_comparison", "source": rep.source, "verdict": rep.verdict,
                              "findings": [asdict(f) for f in rep.findings]},
                             ensure_ascii=False, indent=2))
        else:
            print(format_report(rep, color=sys.stdout.isatty()))
    return 1 if (args.strict and rep.n_flag) else 0


if __name__ == "__main__":
    raise SystemExit(main())

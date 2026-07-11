#!/usr/bin/env python3
"""check_table_percentages.py — recompute every ``n (p%)`` table cell against its
own column denominator and flag a printed percentage that does not match the count.

The cheapest, highest-precision arithmetic check a reviewer can run: a
characteristics table printing ``79 (63%)`` and ``53 (37%)`` under a denominator of
132 is simply wrong (59.8% / 40.2%), needs no judgement or domain knowledge, and
routinely survives multiple review rounds because it was on the page from the
first submission. This detector parses GFM pipe tables from a manuscript, recovers
each column's denominator, and recomputes ``100·n/denominator`` for every count/
percentage cell.

Percentage-column detection (so ``mean (SD)`` cells never fire): a column is
treated as percentages only when a cell carries an explicit ``%`` OR its
parenthetical values (each ≤ 100) sum to ~100 — a percentage partition. Standard
deviations do not sum to 100 and carry no ``%``, so they are skipped.

Denominator recovery, in order: a ``n = N`` in the column header; a Total/Overall
row's count; or the column's own counts summing (a partition). A column with no
recoverable denominator emits ``PERCENT_DENOM_UNKNOWN`` (informational only).

Stdlib-only. Reads the manuscript, never writes it.

Usage:
  python3 check_table_percentages.py --manuscript paper.md
  python3 check_table_percentages.py --manuscript paper.md --strict --quiet
  python3 check_table_percentages.py --manuscript paper.md --tol 0.5 --json
Exit: 0 clean; with --strict, 1 on any PERCENT_MISMATCH; 2 on input/usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict

DEFAULT_TOL = 0.5  # percentage points

CELL_RE = re.compile(r"^\s*([0-9][0-9,]*)\s*\(\s*([0-9]+(?:\.[0-9]+)?)\s*(%?)\s*\)\s*$")
HEADER_N_RE = re.compile(r"\bn\s*=\s*([0-9][0-9,]*)", re.I)
TOTAL_LABEL_RE = re.compile(r"^\s*(total|overall|all|entire cohort|full cohort|whole cohort)\b", re.I)
SEP_RE = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")


@dataclass
class Finding:
    kind: str            # PERCENT_MISMATCH / PERCENT_DENOM_UNKNOWN
    severity: str        # MAJOR / INFO
    table_line: int      # 1-indexed line of the table header
    cell: str
    detail: str


@dataclass
class Report:
    source: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def n_mismatch(self) -> int:
        return sum(1 for f in self.findings if f.kind == "PERCENT_MISMATCH")

    @property
    def verdict(self) -> str:
        return "MISMATCH FOUND" if self.n_mismatch else "OK"


def _split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _parse_tables(text: str):
    """Yield (header_cells, data_rows, header_line_no) for each GFM pipe table."""
    lines = text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        if "|" in lines[i] and i + 1 < n and SEP_RE.match(lines[i + 1]) and "-" in lines[i + 1]:
            header = _split_row(lines[i])
            rows, j = [], i + 2
            while j < n and "|" in lines[j] and lines[j].strip():
                rows.append(_split_row(lines[j]))
                j += 1
            yield header, rows, i + 1
            i = j
        else:
            i += 1


def _cell_count_pct(cell: str):
    m = CELL_RE.match(cell)
    if not m:
        return None
    count = int(m.group(1).replace(",", ""))
    pct = float(m.group(2))
    has_pct = m.group(3) == "%"
    return count, pct, has_pct


def audit(text: str, source: str, tol: float = DEFAULT_TOL) -> Report:
    rep = Report(source=source)
    for header, rows, lineno in _parse_tables(text):
        ncols = len(header)
        data_rows = [r for r in rows if r and not TOTAL_LABEL_RE.match(r[0])]
        total_rows = [r for r in rows if r and TOTAL_LABEL_RE.match(r[0])]

        for col in range(1, ncols):  # col 0 is the row label
            # gather count/pct cells in this column
            parsed = []
            for r in data_rows:
                if col < len(r):
                    cp = _cell_count_pct(r[col])
                    if cp:
                        parsed.append((r[0], r[col], *cp))  # label, raw, count, pct, has_pct
            if not parsed:
                continue

            # is this a percentage column?
            has_pct = any(p[4] for p in parsed)
            le100 = [p[3] for p in parsed if p[3] <= 100]
            is_partition = len(le100) >= 2 and 98.0 <= sum(le100) <= 102.0
            if not (has_pct or is_partition):
                continue  # e.g. mean (SD): no %, SDs don't sum to 100

            # recover denominator
            denom = None
            src = ""
            if col < len(header):
                hm = HEADER_N_RE.search(header[col])
                if hm:
                    denom, src = int(hm.group(1).replace(",", "")), "header n="
            if denom is None:
                for tr in total_rows:
                    if col < len(tr):
                        tc = CELL_RE.match(tr[col]) or re.match(r"^\s*([0-9][0-9,]*)\s*$", tr[col])
                        if tc:
                            denom, src = int(tc.group(1).replace(",", "")), "Total row"
                            break
            if denom is None:
                denom, src = sum(p[2] for p in parsed), "column count-sum"

            if not denom:
                rep.findings.append(Finding("PERCENT_DENOM_UNKNOWN", "INFO", lineno,
                                            f"column {col}", "percentage column with no recoverable denominator"))
                continue

            for label, raw, count, pct, _hp in parsed:
                if count > denom:
                    continue  # not a proportion of this denominator
                recomputed = 100.0 * count / denom
                if abs(recomputed - pct) > tol:
                    rep.findings.append(Finding(
                        "PERCENT_MISMATCH", "MAJOR", lineno, f"{label}: {raw}",
                        f"printed {pct:g}% but {count}/{denom} ({src}) = {recomputed:.1f}% "
                        f"(Δ{abs(recomputed - pct):.1f}pp)"))
    return rep


def format_report(rep: Report, color: bool) -> str:
    tag = {"OK": "\033[92m", "MISMATCH FOUND": "\033[91m"}.get(rep.verdict, "") if color else ""
    end = "\033[0m" if color else ""
    lines = [f"{tag}== {rep.verdict} =={end}  {rep.source}",
             f"mismatches={rep.n_mismatch} findings={len(rep.findings)}"]
    if not rep.findings:
        lines.append("all n (%) cells reconcile with their column denominators.")
        return "\n".join(lines)
    for f in sorted(rep.findings, key=lambda x: (x.kind != "PERCENT_MISMATCH", x.table_line, x.cell)):
        lines.append(f"[{f.severity:<5}] {f.kind:<22} L{f.table_line}  {f.detail}")
        lines.append(f"        cell> {f.cell}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text with GFM tables")
    ap.add_argument("--tol", type=float, default=DEFAULT_TOL,
                    help=f"flag threshold in percentage points (default {DEFAULT_TOL})")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any PERCENT_MISMATCH")
    ap.add_argument("--quiet", action="store_true", help="suppress the report; exit code only")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a text report")
    ap.add_argument("--out", help="write the JSON artifact to this path")
    args = ap.parse_args(argv)

    try:
        text = open(args.manuscript, encoding="utf-8").read()
    except OSError as e:
        print(f"error: cannot read manuscript: {e}", file=sys.stderr)
        return 2

    rep = audit(text, source=args.manuscript, tol=args.tol)
    payload = {"source": rep.source, "verdict": rep.verdict,
               "n_mismatch": rep.n_mismatch, "findings": [asdict(f) for f in rep.findings]}
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)

    if not args.quiet:
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json
              else format_report(rep, color=sys.stdout.isatty()))

    return 1 if (args.strict and rep.n_mismatch) else 0


if __name__ == "__main__":
    raise SystemExit(main())

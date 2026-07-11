#!/usr/bin/env python3
"""check_reported_p_from_counts.py — recompute each 2x2 table row's P value from its
own integer counts and flag a reported P that reproduces under no standard test.

A baseline table comparing two groups prints a count per group and a P value per
row. That P is fully determined by the four cell counts, yet a wrong one (e.g. a
reported ``p<0.001`` whose true value is ~0.06) routinely survives review because
no one recomputes it. This detector rebuilds the 2x2 table for every count row,
recomputes Fisher's exact test and Pearson's chi-square (with and without Yates'
correction) in pure stdlib, *calibrates* which family the manuscript used on the
rows that reproduce, and flags any row whose reported P differs by more than one
order of magnitude under **every** family.

Guards: continuous rows (mean ± SD, median [IQR]) are skipped; at least two count
rows are required so the family can be calibrated; a single-row table never fires.

Stdlib-only (math.comb / math.erfc). Reads the manuscript, never writes it.

Usage:
  python3 check_reported_p_from_counts.py --manuscript paper.md [--strict] [--quiet] [--json]
Exit: 0 clean; with --strict, 1 on any P_NOT_REPRODUCIBLE; 2 on input/usage error.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, field, asdict

SEP_RE = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")
HEADER_N_RE = re.compile(r"\bn\s*=\s*([0-9][0-9,]*)", re.I)
PVAL_HEADER_RE = re.compile(r"^\s*\*?\s*[Pp]\s*(?:[- ]?value)?\s*\*?\s*$")
PVAL_HEADER_CONTAINS = re.compile(r"\bp[- ]?value\b", re.I)
COUNT_CELL_RE = re.compile(r"^\s*(\d[\d,]*)\s*(?:\(|$)")          # integer count, optionally "count (pct)"
PVAL_CELL_RE = re.compile(r"^\s*([<=]?)\s*(0?\.\d+|\d+(?:\.\d+)?)\s*$")
FAMILIES = ("Fisher exact", "Pearson chi-square (Yates)", "Pearson chi-square (uncorrected)")


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
        return sum(1 for f in self.findings if f.kind == "P_NOT_REPRODUCIBLE")

    @property
    def verdict(self) -> str:
        return "NON-REPRODUCIBLE P" if self.n_flag else "OK"


def _split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _fisher(a: int, b: int, c: int, d: int) -> float:
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d
    if 0 in (r1, r2, c1, b + d):
        return 1.0
    denom = math.comb(n, c1)
    lo, hi = max(0, c1 - r2), min(r1, c1)
    p_obs = math.comb(r1, a) * math.comb(r2, c1 - a) / denom
    tol = p_obs * (1 + 1e-7)
    total = sum(math.comb(r1, k) * math.comb(r2, c1 - k) / denom
                for k in range(lo, hi + 1)
                if math.comb(r1, k) * math.comb(r2, c1 - k) / denom <= tol)
    return min(1.0, total)


def _chi2(a: int, b: int, c: int, d: int, yates: bool) -> float:
    n = a + b + c + d
    r1, r2, c1, c2 = a + b, c + d, a + c, b + d
    if 0 in (r1, r2, c1, c2):
        return 1.0
    num = abs(a * d - b * c)
    if yates:
        num = max(0.0, num - n / 2)
    chi2 = n * num * num / (r1 * r2 * c1 * c2)
    return math.erfc(math.sqrt(chi2 / 2))  # 1 df


def _pvals(a: int, b: int, c: int, d: int) -> tuple[float, float, float]:
    return _fisher(a, b, c, d), _chi2(a, b, c, d, True), _chi2(a, b, c, d, False)


def _order_gap(rep_op: str, rep_val: float, comp: float) -> float:
    """log10 gap between reported and computed; for '<' bounds, only a computed
    value ABOVE the bound counts (a computed below the claimed upper bound is fine)."""
    if comp <= 0 or rep_val <= 0:
        return 0.0
    if rep_op == "<":
        return max(0.0, math.log10(comp) - math.log10(rep_val))
    return abs(math.log10(comp) - math.log10(rep_val))


def audit(text: str, source: str) -> Report:
    rep = Report(source=source)
    lines = text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        if not ("|" in lines[i] and i + 1 < n and SEP_RE.match(lines[i + 1]) and "-" in lines[i + 1]):
            i += 1
            continue
        header = _split_row(lines[i])
        lineno0 = i + 1
        group_cols = [j for j, h in enumerate(header) if HEADER_N_RE.search(h)]
        p_col = next((j for j, h in enumerate(header)
                      if PVAL_HEADER_RE.match(h) or PVAL_HEADER_CONTAINS.search(h)), None)
        # gather rows
        rows = []
        j = i + 2
        while j < n and "|" in lines[j] and lines[j].strip():
            rows.append((_split_row(lines[j]), j + 1))
            j += 1
        i = j
        if len(group_cols) < 2 or p_col is None:
            continue
        g1, g2 = group_cols[0], group_cols[1]
        n1 = int(HEADER_N_RE.search(header[g1]).group(1).replace(",", ""))
        n2 = int(HEADER_N_RE.search(header[g2]).group(1).replace(",", ""))

        parsed = []
        for cells, ln in rows:
            if max(g1, g2, p_col) >= len(cells):
                continue
            m1, m2 = COUNT_CELL_RE.match(cells[g1]), COUNT_CELL_RE.match(cells[g2])
            pm = PVAL_CELL_RE.match(cells[p_col])
            if not (m1 and m2 and pm):
                continue  # continuous row (mean±SD / IQR) or no P
            a, c = int(m1.group(1).replace(",", "")), int(m2.group(1).replace(",", ""))
            if a > n1 or c > n2:
                continue
            b, d = n1 - a, n2 - c
            parsed.append((cells[0], ln, a, b, c, d, pm.group(1) or "=", float(pm.group(2))))

        if len(parsed) < 2:
            continue  # cannot calibrate the family on a single row

        # calibrate: which family reproduces the most rows to <= 1e-3 (op '=')?
        computed = [(_pvals(a, b, c, d)) for _, _, a, b, c, d, _, _ in parsed]
        repro = [0, 0, 0]
        for (lbl, ln, a, b, c, d, op, val), pv in zip(parsed, computed):
            if op == "=":
                for k in range(3):
                    if abs(pv[k] - val) <= 1e-3:
                        repro[k] += 1
        fam_idx = max(range(3), key=lambda k: repro[k]) if any(repro) else 2

        for (lbl, ln, a, b, c, d, op, val), pv in zip(parsed, computed):
            gaps = [_order_gap(op, val, pv[k]) for k in range(3)]
            if min(gaps) > 1.0:  # differs by >1 order under EVERY family
                closest = min(range(3), key=lambda k: gaps[k])
                rep.findings.append(Finding(
                    "P_NOT_REPRODUCIBLE", "MAJOR", ln,
                    f"row '{lbl}' ({a}/{a+b} vs {c}/{c+d}) reports P{op}{val:g}, but recomputes to "
                    f"Fisher {pv[0]:.3g} / Yates {pv[1]:.3g} / uncorrected {pv[2]:.3g} "
                    f"(closest {FAMILIES[closest]}; table family ≈ {FAMILIES[fam_idx]})"))
    return rep


def format_report(rep: Report, color: bool) -> str:
    tag = {"OK": "\033[92m", "NON-REPRODUCIBLE P": "\033[91m"}.get(rep.verdict, "") if color else ""
    end = "\033[0m" if color else ""
    out = [f"{tag}== {rep.verdict} =={end}  {rep.source}", f"non_reproducible={rep.n_flag}"]
    if not rep.findings:
        out.append("every reported P reproduces from its counts under a standard test.")
        return "\n".join(out)
    for f in sorted(rep.findings, key=lambda x: (x.line, x.detail)):
        out.append(f"[{f.severity}] {f.kind} L{f.line}  {f.detail}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any P_NOT_REPRODUCIBLE")
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
            print(json.dumps({"source": rep.source, "verdict": rep.verdict,
                              "findings": [asdict(f) for f in rep.findings]},
                             ensure_ascii=False, indent=2))
        else:
            print(format_report(rep, color=sys.stdout.isatty()))
    return 1 if (args.strict and rep.n_flag) else 0


if __name__ == "__main__":
    raise SystemExit(main())

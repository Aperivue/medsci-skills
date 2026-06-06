#!/usr/bin/env python3
"""Confounding-completeness gate for observational studies (self-review Phase 2.5e).

The highest-yield observational reviewer finding is also the most mechanical: a
covariate that was *measured*, is *imbalanced across exposure groups* in the
baseline table, and is *absent from the adjustment set* is residual confounding
by a measured variable. A single-pass prose review misses it because the
manuscript text is internally consistent; only a join of the exposure-stratified
Table 1 against the Methods adjustment set exposes it. This script is that join
(probe O1 of observational_confounding.md), backported from the panel so the
deterministic finding lands without a multi-agent pass.

INPUTS
  --table1   exposure-stratified baseline table, CSV. One row per covariate.
             Needs a covariate-name column and a p-value (or SMD) column. Column
             names are auto-detected (case-insensitive); override with
             --name-col / --p-col / --smd-col. A file named like
             `table1_by_<exposure>.csv` is the convention.
  --adjusted adjustment-set variables. Either a path to a file (one variable per
             line, or a Methods paragraph the script greps after "adjusted for")
             or a comma-separated list passed inline with --adjusted-list.

OUTPUT
  A reconciliation table (stdout) and, with --out, a JSON artifact:
    {covariate, imbalance_p / smd, in_adjustment_set, verdict}
  verdict UNADJUSTED_IMBALANCED is the Major candidate. Exit 1 (with --strict)
  when any UNADJUSTED_IMBALANCED row exists.

Matching the adjustment set to Table-1 covariate labels is fuzzy (a table row
"Smoking, pack-years" vs an adjustment token "smoking"), so the match is a
normalized-substring test in both directions; review the reconciliation table
rather than trusting the count blindly.

Stdlib-only (csv / json / re / argparse). Exit codes: 0 clean (or report-only),
1 unadjusted-imbalanced rows found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# --- column auto-detection -------------------------------------------------

NAME_HINTS = ("covariate", "variable", "characteristic", "feature", "name", "")
P_HINTS = ("p_value", "pvalue", "p-value", "p val", "p", "pr")
SMD_HINTS = ("smd", "std_diff", "standardized", "std. mean", "std mean")

P_THRESHOLD = 0.05
SMD_THRESHOLD = 0.10

# Header / summary rows that are not covariates (sample-size lines, group totals,
# trend-p rows). Matched on the whole normalized label, not a substring, so a real
# covariate like "Total cholesterol" is not swallowed by "total".
def _is_skip_row(cov: str) -> bool:
    c = _norm(cov)
    if c in ("", "total", "overall", "n", "no", "number"):
        return True
    if re.match(r"^n\s*[=:]", cov.strip().lower()):     # "N = ...", "n: ..."
        return True
    if "p for trend" in c or "p trend" in c or "for trend" in c:
        return True
    return False


def _norm(s: str) -> str:
    """Lowercase, drop punctuation/units, collapse whitespace for fuzzy match."""
    s = s.lower()
    s = re.sub(r"\(.*?\)", " ", s)            # drop "(mg/dL)", "(%)"
    s = re.sub(r"[^a-z0-9 ]+", " ", s)        # punctuation -> space
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _pick_col(header: list[str], hints: tuple[str, ...], override: str | None) -> int | None:
    if override:
        for i, h in enumerate(header):
            if _norm(h) == _norm(override):
                return i
        sys.stderr.write(f"ERROR: column '{override}' not found in header {header}\n")
        return None
    norm = [_norm(h) for h in header]
    # exact-ish first
    for hint in hints:
        h = _norm(hint)
        for i, col in enumerate(norm):
            if col == h and h:
                return i
    # then substring
    for hint in hints:
        h = _norm(hint)
        for i, col in enumerate(norm):
            if h and h in col:
                return i
    return None


def _parse_p(raw: str) -> float | None:
    """Parse a p-value cell: '0.001', '<0.001', 'p<0.01', '0.03*', 'NS'."""
    if raw is None:
        return None
    s = raw.strip().lower()
    if not s or s in ("ns", "na", "n/a", "-", "."):
        return 1.0 if s == "ns" else None
    m = re.search(r"<\s*(0?\.[0-9]+|[0-9]+\.?[0-9]*)", s)   # "<0.001", "p<.01"
    if m:
        try:                                   # report just under the stated bound
            return max(float(m.group(1)) - 1e-6, 0.0)
        except ValueError:
            return None
    m = re.search(r"0?\.[0-9]+|[0-9]+\.?[0-9]*", s)
    if m:
        try:
            return float(m.group(0))
        except ValueError:
            return None
    return None


def _parse_float(raw: str) -> float | None:
    if raw is None:
        return None
    m = re.search(r"-?[0-9]*\.?[0-9]+", raw.strip())
    return float(m.group(0)) if m else None


# --- adjustment set --------------------------------------------------------

def load_adjustment_set(path: str | None, inline: str | None) -> list[str]:
    if inline:
        return [t.strip() for t in inline.split(",") if t.strip()]
    if not path:
        return []
    p = Path(path)
    if not p.is_file():
        sys.stderr.write(f"ERROR: adjustment file not found: {path}\n")
        sys.exit(2)
    text = p.read_text(encoding="utf-8")
    # If the file is a Methods paragraph, grep the "adjusted for ..." clause.
    m = re.search(r"adjust(?:ed|ing)?\s+for\s+(.+?)(?:\.|;|\n\n|$)", text, re.I | re.S)
    if m:
        clause = m.group(1)
        parts = re.split(r",| and | as well as ", clause)
        return [p2.strip() for p2 in parts if p2.strip()]
    # Otherwise treat as one variable per line.
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]


def in_adjustment_set(cov: str, adj_norm: list[str]) -> bool:
    c = _norm(cov)
    if not c:
        return False
    for a in adj_norm:
        if not a:
            continue
        if a in c or c in a:
            return True
        # token overlap on the leading word (smoking ~ "smoking, pack-years")
        if c.split(" ")[0] == a.split(" ")[0] and len(c.split(" ")[0]) >= 3:
            return True
    return False


# --- core ------------------------------------------------------------------

def analyze(table1: str, adj: list[str], name_col, p_col, smd_col) -> dict:
    p = Path(table1)
    if not p.is_file():
        sys.stderr.write(f"ERROR: table1 not found: {table1}\n")
        sys.exit(2)
    with p.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = [r for r in reader if any(c.strip() for c in r)]
    if len(rows) < 2:
        sys.stderr.write("ERROR: table1 has no data rows\n")
        sys.exit(2)
    header = rows[0]
    ni = _pick_col(header, NAME_HINTS, name_col)
    pi = _pick_col(header, P_HINTS, p_col)
    si = _pick_col(header, SMD_HINTS, smd_col)
    if ni is None:
        ni = 0
    if pi is None and si is None:
        sys.stderr.write("ERROR: could not locate a p-value or SMD column; pass --p-col/--smd-col\n")
        sys.exit(2)

    adj_norm = [_norm(a) for a in adj]
    findings = []
    for r in rows[1:]:
        if ni >= len(r):
            continue
        cov = r[ni].strip()
        if _is_skip_row(cov):
            continue
        pval = _parse_p(r[pi]) if (pi is not None and pi < len(r)) else None
        smd = _parse_float(r[si]) if (si is not None and si < len(r)) else None
        imbalanced = (pval is not None and pval < P_THRESHOLD) or \
                     (smd is not None and abs(smd) >= SMD_THRESHOLD)
        if not imbalanced:
            continue
        adjusted = in_adjustment_set(cov, adj_norm)
        findings.append({
            "covariate": cov,
            "imbalance_p": pval,
            "smd": smd,
            "in_adjustment_set": adjusted,
            "verdict": "ADJUSTED" if adjusted else "UNADJUSTED_IMBALANCED",
        })

    unadjusted = [f for f in findings if f["verdict"] == "UNADJUSTED_IMBALANCED"]
    return {
        "table1": str(p),
        "adjustment_set": adj,
        "thresholds": {"p": P_THRESHOLD, "smd": SMD_THRESHOLD},
        "n_imbalanced": len(findings),
        "n_unadjusted_imbalanced": len(unadjusted),
        "findings": findings,
        "verdict": "MAJOR_CANDIDATE" if unadjusted else "OK",
        "suggested_fix": (
            "Report an extended-adjustment sensitivity model adding the "
            "unadjusted imbalanced covariates; keep the original model primary "
            "only if the extended model agrees."
        ) if unadjusted else None,
    }


def render_table(result: dict) -> str:
    lines = [
        "| Covariate | Imbalance p | SMD | In adjustment set? | Verdict |",
        "|---|---|---|---|---|",
    ]
    for f in result["findings"]:
        p = "—" if f["imbalance_p"] is None else f"{f['imbalance_p']:.4g}"
        s = "—" if f["smd"] is None else f"{f['smd']:.3g}"
        mark = "✗ Major" if f["verdict"] == "UNADJUSTED_IMBALANCED" else "✓"
        lines.append(
            f"| {f['covariate']} | {p} | {s} | "
            f"{'yes' if f['in_adjustment_set'] else 'NO'} | {mark} |"
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Observational confounding-completeness gate (O1).")
    ap.add_argument("--table1", required=True, help="exposure-stratified Table 1 CSV")
    ap.add_argument("--adjusted", help="adjustment-set file (var-per-line or Methods paragraph)")
    ap.add_argument("--adjusted-list", help="comma-separated adjustment variables (inline)")
    ap.add_argument("--name-col", help="override covariate-name column header")
    ap.add_argument("--p-col", help="override p-value column header")
    ap.add_argument("--smd-col", help="override SMD column header")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if unadjusted-imbalanced rows exist")
    args = ap.parse_args()

    adj = load_adjustment_set(args.adjusted, args.adjusted_list)
    if not adj:
        sys.stderr.write("WARN: empty adjustment set — every imbalanced covariate will flag.\n")

    result = analyze(args.table1, adj, args.name_col, args.p_col, args.smd_col)

    print("=" * 41)
    print(" Confounding Completeness (Phase 2.5e / O1)")
    print("=" * 41)
    print(f"adjustment set: {', '.join(adj) if adj else '(none)'}")
    print(render_table(result))
    print()
    if result["n_unadjusted_imbalanced"]:
        print(f"MAJOR candidate: {result['n_unadjusted_imbalanced']} imbalanced covariate(s) "
              f"absent from the adjustment set.")
        print(f"Fix: {result['suggested_fix']}")
    else:
        print("OK: no measured-but-unadjusted imbalanced covariate.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["n_unadjusted_imbalanced"]) else 0


if __name__ == "__main__":
    sys.exit(main())

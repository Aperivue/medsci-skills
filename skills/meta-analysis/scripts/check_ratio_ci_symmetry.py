#!/usr/bin/env python3
"""Ratio-CI plausibility gate for an extraction CSV (meta-analysis Phase 6).

A ratio measure (OR, RR, HR, IRR) is pooled on the log scale, and the standard
error the pooling code uses is usually back-derived from the transcribed CI:
SE = (log(upper) - log(lower)) / (2 z). A transcription slip in one bound
(3.96 for 2.96) passes every type check and silently changes that study's
weight. This gate reads the printed numbers and reports two things.

Claims
  RATIO_CI_IMPOSSIBLE (Major)  a printed value is negative, or no values within
      printed-decimal rounding satisfy lower <= estimate <= upper. Certain from
      the input: no real ratio CI can look like that.
  RATIO_CI_ASYMMETRIC (Minor)  a Wald CI for a ratio is symmetric about the
      estimate on the log scale. Even after allowing every printed value to move
      within its rounding interval, the CI is still asymmetric by more than 10%
      of its log half-width. Verify the transcription; a profile-likelihood,
      exact or bootstrap CI can legitimately be asymmetric (declare it in
      ci_method and the row is not checked for symmetry).
  RATIO_CI_ASYMMETRY_NOT_ASSESSED (Minor)  the symmetry check could not run on a
      row (a printed bound or estimate of 0, or a zero-width interval).

Symmetry statistic. With arms a_u = log(u) - log(e) and a_l = log(e) - log(l),
and log half-width h = (log(u) - log(l)) / 2, the relative asymmetry is
    r = |a_u - a_l| / h = |log(u) + log(l) - 2 log(e)| / h.
A value printed with d decimals is taken to lie in [x - 0.5*10^-d, x + 0.5*10^-d].
N = log(u) + log(l) - 2 log(e) is monotone in each value, so its range over the
rounding box is exact; if that range contains 0, the row is consistent with a
symmetric CI. Otherwise the gate takes the smallest |N| over the box and divides
it by the LARGEST h over the box: a lower bound on r for every value set within
rounding. It flags only when that lower bound exceeds 0.10, so rounding alone
never fires the claim.

INPUT  --extraction FILE  (.csv, or .tsv/.tab for tab-separated; UTF-8)
  Required columns (case-insensitive): study, measure, estimate, lower, upper.
  Optional: ci_level (percent, 50 to <100, default 95; a fraction such as
  0.95 is an input error), ci_method.
  Rows whose measure is not exactly OR / RR / HR / IRR (case-insensitive) are
  skipped; the final line and summary.skipped_measures name those labels, so
  a ratio written another way ("aOR", "Odds ratio") is visible, not silent.
  On a ratio row, estimate / lower / upper must be plain decimals ("1.35");
  a blank or non-numeric value is an input error naming the row and column.
  ci_method containing "profile", "exact" or "bootstrap" skips the symmetry
  check for that row, with no claim.

OUTPUT (--out path)
  {"detector": "check_ratio_ci_symmetry", "extraction", "rows": [{row, study,
   measure, estimate, lower, upper, ci_level, ci_method, se_log,
   asymmetry_lower_bound, symmetry}], "claims": [{verdict, severity, row,
   study, detail}], "summary": {n_rows, n_ratio_rows, n_skipped_measure,
   skipped_measures, n_symmetry_checked, n_major, n_minor, verdict}}
  se_log is the SE on the log scale back-derived from the printed CI with
  z = the standard-normal quantile for ci_level; null when a bound is <= 0 or
  upper <= lower.

Verdict: MAJOR_CANDIDATE when a Major claim fired; NOT_ASSESSED when the file
has no ratio-measure row; otherwise OK (Minor claims are counted).

Exit codes: 0 run completed (report-only, or --strict with no Major claim);
1 --strict and a Major claim; 2 input/usage error (missing file or column,
bad value, unwritable --out), or --strict with NOT_ASSESSED.

Stdlib only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from statistics import NormalDist

DETECTOR = "check_ratio_ci_symmetry"
RATIO_MEASURES = {"OR", "RR", "HR", "IRR"}
REQUIRED = ("study", "measure", "estimate", "lower", "upper")
OPTIONAL = ("ci_level", "ci_method")
ASYMMETRIC_METHOD_RE = re.compile(r"profile|exact|bootstrap", re.I)
# Relative asymmetry (|a_u - a_l| / h) above which a row is flagged, applied to
# a lower bound over the rounding box (see the module docstring).
ASYMMETRY_TOLERANCE = 0.10
DECIMAL_RE = re.compile(r"^[+-]?(?:\d+(?:\.(\d*))?|\.(\d+))$")


class InputError(ValueError):
    pass


def parse_printed(raw: str, where: str) -> tuple[float, float]:
    """Return (value, half rounding step) of a printed decimal."""
    s = (raw or "").strip()
    m = DECIMAL_RE.match(s)
    if not m:
        raise InputError(f"{where}: expected a plain decimal number, got {raw!r}")
    decimals = len(m.group(1) or m.group(2) or "")
    value = float(s)
    if not math.isfinite(value):
        raise InputError(f"{where}: number out of range, got {raw!r}")
    return value, 0.5 * 10.0 ** (-decimals)


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    delimiter = "\t" if path.suffix.lower() in {".tsv", ".tab"} else ","
    try:
        with path.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.reader(fh, delimiter=delimiter)
            header = next(reader, None)
            if header is None:
                raise InputError(f"{path}: empty file (no header row)")
            names = [h.strip().lower() for h in header]
            seen: set[str] = set()
            for n in names:
                if n and n in seen:
                    raise InputError(f"{path}: duplicate column {n!r}")
                seen.add(n)
            missing = [c for c in REQUIRED if c not in seen]
            if missing:
                raise InputError(f"{path}: missing required column(s): {', '.join(missing)}")
            rows = []
            for cells in reader:
                if not any(c.strip() for c in cells):
                    continue
                rows.append({n: (cells[i].strip() if i < len(cells) else "")
                             for i, n in enumerate(names) if n})
    except UnicodeDecodeError as exc:
        raise InputError(f"{path}: not UTF-8 ({exc})") from exc
    except csv.Error as exc:
        raise InputError(f"{path}: malformed CSV ({exc})") from exc
    return names, rows


def ci_z(raw: str, where: str) -> tuple[float, float]:
    s = (raw or "").strip().rstrip("%").strip()
    if not s:
        return 95.0, NormalDist().inv_cdf(0.975)
    try:
        level = float(s)
    except ValueError:
        raise InputError(f"{where}: ci_level must be a percentage, got {raw!r}") from None
    if not (math.isfinite(level) and 50.0 <= level < 100.0):
        raise InputError(f"{where}: ci_level must be a percentage from 50 to below 100 "
                         f"(write 95, not 0.95), got {raw!r}")
    return level, NormalDist().inv_cdf(1.0 - (1.0 - level / 100.0) / 2.0)


def asymmetry_lower_bound(e: tuple[float, float], lo: tuple[float, float],
                          up: tuple[float, float]) -> float | None:
    """Lower bound on |log u + log l - 2 log e| / h over the rounding box, or
    None when the box reaches a value <= 0 or a zero-width interval."""
    e_lo, e_hi = e[0] - e[1], e[0] + e[1]
    l_lo, l_hi = lo[0] - lo[1], lo[0] + lo[1]
    u_lo, u_hi = up[0] - up[1], up[0] + up[1]
    if min(e_lo, l_lo, u_lo) <= 0.0:
        return None
    h_max = (math.log(u_hi) - math.log(l_lo)) / 2.0
    if h_max <= 0.0:
        return None
    n_min = math.log(u_lo) + math.log(l_lo) - 2.0 * math.log(e_hi)
    n_max = math.log(u_hi) + math.log(l_hi) - 2.0 * math.log(e_lo)
    if n_min <= 0.0 <= n_max:
        return 0.0
    return min(abs(n_min), abs(n_max)) / h_max


def analyze(path: Path) -> dict:
    _, rows = read_rows(path)
    out_rows: list[dict] = []
    claims: list[dict] = []
    n_skipped = 0
    skipped_labels: set[str] = set()
    n_sym = 0
    for i, r in enumerate(rows, start=2):  # row 1 is the header
        measure = r.get("measure", "").strip().upper()
        if measure not in RATIO_MEASURES:
            n_skipped += 1
            skipped_labels.add(r.get("measure", "").strip() or "<blank>")
            continue
        study = r.get("study", "")
        where = f"row {i}"
        e = parse_printed(r.get("estimate", ""), f"{where} column estimate")
        lo = parse_printed(r.get("lower", ""), f"{where} column lower")
        up = parse_printed(r.get("upper", ""), f"{where} column upper")
        level, z = ci_z(r.get("ci_level", ""), f"{where} column ci_level")
        method = r.get("ci_method", "")
        se = None
        if lo[0] > 0 and up[0] > lo[0]:
            se = (math.log(up[0]) - math.log(lo[0])) / (2.0 * z)
        rec = {"row": i, "study": study, "measure": measure, "estimate": e[0],
               "lower": lo[0], "upper": up[0], "ci_level": level, "ci_method": method,
               "se_log": se, "asymmetry_lower_bound": None, "symmetry": None}
        out_rows.append(rec)

        negative = [n for n, v in (("estimate", e), ("lower", lo), ("upper", up)) if v[0] < 0]
        order_bad = (lo[0] - lo[1] > e[0] + e[1]) or (e[0] - e[1] > up[0] + up[1])
        if negative or order_bad:
            why = (f"negative printed value ({', '.join(negative)})" if negative
                   else "lower <= estimate <= upper fails even within printed rounding")
            claims.append({
                "verdict": "RATIO_CI_IMPOSSIBLE", "severity": "Major", "row": i,
                "study": study,
                "detail": (f"{measure} {r.get('estimate')} ({r.get('lower')}, {r.get('upper')}): "
                           f"{why}; a ratio and its CI are positive and the CI contains the "
                           "estimate. Re-extract this row from the source."),
            })
            rec["symmetry"] = "IMPOSSIBLE"
            continue
        if ASYMMETRIC_METHOD_RE.search(method):
            rec["symmetry"] = "SKIPPED_DECLARED_METHOD"
            continue
        bound = asymmetry_lower_bound(e, lo, up)
        if bound is None:
            rec["symmetry"] = "NOT_ASSESSED"
            claims.append({
                "verdict": "RATIO_CI_ASYMMETRY_NOT_ASSESSED", "severity": "Minor", "row": i,
                "study": study,
                "detail": (f"{measure} {r.get('estimate')} ({r.get('lower')}, {r.get('upper')}): "
                           "a value within rounding is 0 or the interval has no width, so "
                           "log-scale symmetry could not be checked; print more decimals."),
            })
            continue
        n_sym += 1
        rec["asymmetry_lower_bound"] = round(bound, 6)
        if bound > ASYMMETRY_TOLERANCE:
            rec["symmetry"] = "ASYMMETRIC"
            claims.append({
                "verdict": "RATIO_CI_ASYMMETRIC", "severity": "Minor", "row": i,
                "study": study,
                "detail": (f"{measure} {r.get('estimate')} ({r.get('lower')}, {r.get('upper')}): "
                           f"on the log scale the CI is asymmetric about the estimate by at "
                           f"least {bound:.0%} of its half-width after allowing for rounding. "
                           "Verify the transcription; profile-likelihood/exact CIs can be "
                           "asymmetric (declare ci_method to skip this check)."),
            })
        else:
            rec["symmetry"] = "OK"
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    if n_major:
        verdict = "MAJOR_CANDIDATE"
    elif not out_rows:
        verdict = "NOT_ASSESSED"
    else:
        verdict = "OK"
    return {
        "extraction": str(path),
        "rows": out_rows,
        "claims": claims,
        "summary": {
            "n_rows": len(rows),
            "n_ratio_rows": len(out_rows),
            "n_skipped_measure": n_skipped,
            "skipped_measures": sorted(skipped_labels),
            "n_symmetry_checked": n_sym,
            "n_major": n_major,
            "n_minor": len(claims) - n_major,
            "verdict": verdict,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Ratio-CI plausibility and log-scale symmetry gate.")
    ap.add_argument("--extraction", required=True, help="extraction CSV/TSV")
    ap.add_argument("--out", help="write the JSON artifact to this path")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 on a Major claim, 2 when nothing could be assessed")
    ap.add_argument("--quiet", action="store_true", help="suppress the stdout table")
    args = ap.parse_args()

    path = Path(args.extraction)
    if not path.is_file():
        sys.stderr.write(f"ERROR: extraction file not found: {path}\n")
        return 2
    try:
        result = analyze(path)
    except InputError as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 2

    s = result["summary"]
    if not args.quiet:
        print("| Row | Study | Verdict | Severity | Detail |")
        print("|---|---|---|---|---|")
        for c in result["claims"]:
            print(f"| {c['row']} | {c['study']} | {c['verdict']} | {c['severity']} | {c['detail']} |")
        if not result["claims"]:
            print("| - | - | (none) | - | no claim fired |")
        print()
        if s["n_skipped_measure"]:
            print(f"Skipped {s['n_skipped_measure']} row(s) whose measure is not "
                  f"OR/RR/HR/IRR: {', '.join(s['skipped_measures'])}.")
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} impossible ratio CI(s); "
                  f"{s['n_minor']} Minor.")
        elif s["verdict"] == "NOT_ASSESSED":
            print("NOT ASSESSED: no row with measure OR/RR/HR/IRR was found; "
                  "fill the measure column.")
        elif s["n_minor"]:
            print(f"No Major issue: {s['n_minor']} Minor (asymmetric or unchecked ratio CI).")
        else:
            print(f"OK: {s['n_ratio_rows']} ratio CI(s) are possible and "
                  f"{s['n_symmetry_checked']} are log-symmetric within rounding.")
    if args.out:
        try:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(
                json.dumps({"detector": DETECTOR, **result}, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8")
        except OSError as exc:
            sys.stderr.write(f"ERROR: cannot write --out {args.out}: {exc}\n")
            return 2
    if args.strict and s["n_major"]:
        return 1
    if args.strict and s["verdict"] == "NOT_ASSESSED":
        sys.stderr.write("ERROR: --strict and no ratio-measure row was found\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

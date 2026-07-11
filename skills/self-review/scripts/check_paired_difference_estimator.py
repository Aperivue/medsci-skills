#!/usr/bin/env python3
"""check_paired_difference_estimator.py — sanity-check a reported "median paired
difference" against the achievable value set, its interval, and its named estimator.

Reader/Likert studies routinely bolt an effect size onto a revision to answer an
uncertainty comment, and the estimator is left undefined. The tells are
deterministic: the median of an odd number of integer paired differences is one of
the integer differences, so a reported non-integer median (e.g. 0.5) is impossible
and signals a Hodges–Lehmann pseudomedian mislabelled as a median; a "95% CI" whose
bounds are equal (0.5–0.5) is degenerate; and an effect size + CI with no estimator
or interval method named cannot be reproduced.

Checks:
  MEDIAN_PARITY    n odd ∧ integer scale ∧ reported median difference non-integer
                   (if scores are means of R raters, the step is 1/R — still flag a
                   value that is not a multiple of 1/R). Suppressed when the value is
                   labelled a Hodges–Lehmann pseudomedian.
  DEGENERATE_CI    a reported interval whose lower bound equals its upper bound.
  ESTIMATOR_UNNAMED a median-difference effect size + CI while no estimator / interval
                   method (Hodges–Lehmann, pseudomedian, bootstrap, Wilcoxon, exact,
                   sign test) is named anywhere in the manuscript.

Stdlib-only. Reads the manuscript, never writes it.

Usage:
  python3 check_paired_difference_estimator.py --manuscript paper.md [--strict] [--quiet] [--json]
Exit: 0 clean; with --strict, 1 on any MAJOR finding; 2 on input/usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict

MEDIAN_DIFF_RE = re.compile(
    r"(?<!pseudo)\b(?:paired\s+)?median\s+(?:paired\s+)?difference\b[^.\n]{0,40}?\b(\d+(?:\.\d+)?)", re.I)
N_RE = re.compile(r"\b(\d+)\s+paired\b|\bn\s*=\s*(\d+)\b", re.I)
SCALE_RE = re.compile(r"\b(\d+)-point\b|\bLikert\b", re.I)
RATERS_RE = re.compile(r"\b(?:mean|average[d]?)\b[^.\n]{0,30}?\b(\d+)\s+raters?\b", re.I)
CI_RE = re.compile(r"95\s*%\s*CI[:\s]*\(?\s*(-?\d+(?:\.\d+)?)\s*(?:[–\-−]|to)\s*(-?\d+(?:\.\d+)?)", re.I)
ESTIMATOR_RE = re.compile(r"\b(hodges[-–\s]?lehmann|pseudomedian|bootstrap|wilcoxon|exact\s+(?:test|confidence)|sign\s+test)\b", re.I)


@dataclass
class Finding:
    kind: str
    severity: str
    detail: str


@dataclass
class Report:
    source: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def n_flag(self) -> int:
        return sum(1 for f in self.findings if f.severity == "MAJOR")

    @property
    def verdict(self) -> str:
        return "ESTIMATOR PROBLEM" if self.n_flag else "OK"


def _is_multiple(value: float, step: float) -> bool:
    q = value / step
    return abs(q - round(q)) < 1e-9


def audit(text: str, source: str) -> Report:
    rep = Report(source=source)
    estimator_named = bool(ESTIMATOR_RE.search(text))

    n_m = N_RE.search(text)
    n_val = int(next(g for g in (n_m.groups() if n_m else ()) if g)) if n_m else None
    scale_m = SCALE_RE.search(text)
    integer_scale = bool(scale_m)
    raters_m = RATERS_RE.search(text)
    step = 1.0 / int(raters_m.group(1)) if raters_m else 1.0

    for m in MEDIAN_DIFF_RE.finditer(text):
        # is this occurrence a mislabel guarded by a nearby pseudomedian/HL tag?
        window = text[max(0, m.start() - 20):m.end()]
        if re.search(r"pseudomedian|hodges", window, re.I):
            continue
        value = float(m.group(1))
        if n_val is not None and n_val % 2 == 1 and integer_scale and not _is_multiple(value, step):
            rep.findings.append(Finding(
                "MEDIAN_PARITY", "MAJOR",
                f"reported median paired difference {value:g} is not achievable: the median of "
                f"n={n_val} (odd) integer differences must be an integer"
                + (f" (or a multiple of 1/{int(raters_m.group(1))})" if raters_m else "")
                + " — likely a Hodges–Lehmann pseudomedian mislabelled as a median"))

    for m in CI_RE.finditer(text):
        lo, hi = float(m.group(1)), float(m.group(2))
        if lo == hi:
            rep.findings.append(Finding(
                "DEGENERATE_CI", "MAJOR",
                f"reported 95% CI has equal bounds ({m.group(1)}–{m.group(2)}) — zero width"))

    if MEDIAN_DIFF_RE.search(text) and CI_RE.search(text) and not estimator_named:
        rep.findings.append(Finding(
            "ESTIMATOR_UNNAMED", "MAJOR",
            "a median-difference effect size with a CI is reported but no estimator / interval "
            "method (Hodges–Lehmann, pseudomedian, bootstrap, Wilcoxon, exact, sign test) is named"))
    return rep


def format_report(rep: Report, color: bool) -> str:
    tag = {"OK": "\033[92m", "ESTIMATOR PROBLEM": "\033[91m"}.get(rep.verdict, "") if color else ""
    end = "\033[0m" if color else ""
    out = [f"{tag}== {rep.verdict} =={end}  {rep.source}", f"problems={rep.n_flag}"]
    if not rep.findings:
        out.append("median-difference estimator, interval, and value set are consistent.")
        return "\n".join(out)
    for f in sorted(rep.findings, key=lambda x: (x.kind, x.detail)):
        out.append(f"[{f.severity}] {f.kind}  {f.detail}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any MAJOR finding")
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

#!/usr/bin/env python3
"""check_dta_denominators.py — cross-check diagnostic-accuracy sensitivity /
specificity denominators against the reference-standard category counts in the
characteristics table.

Sensitivity is a/(a+c) over the disease-positive patients; specificity is d/(b+d)
over the disease-negative patients. Those denominators must equal the reference-
standard positive / negative counts printed in the characteristics table. When
they disagree while the grand total still matches (e.g. table 14/19, Results
15/18, both summing to 33), a totals check passes and the split-level error — which
sits under an Abstract headline — survives multiple review rounds. This detector
recovers both category counts and both denominators and asserts equality per
category, refusing to accept grand-total agreement as passing.

Also `STAGE_ROWSUM`: a staging-confusion breakdown must satisfy
correctly-staged + over-staged + under-staged == n.

Runs on FIRST submissions, not only revisions — the source incident had both
numbers on the page from submission one.

Stdlib-only. Reads the manuscript, never writes it.

Usage:
  python3 check_dta_denominators.py --manuscript paper.md [--strict] [--quiet] [--json]
Exit: 0 clean; with --strict, 1 on any mismatch; 2 on input/usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict

SEP_RE = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")
NEG_LABEL_RE = re.compile(r"\b(p?N\s*0|node[- ]negative|disease[- ](?:free|negative)|absent|benign|non-?malignant)\b", re.I)
POS_LABEL_RE = re.compile(r"\b(p?N\s*[1-9]|node[- ]positive|disease[- ]positive|present|malignant|metasta\w+)\b", re.I)
# "sensitivity ... 13/18" or "13 of 18"; bounded gap so it does not cross a
# sentence boundary but tolerates a decimal percentage (e.g. "72.2% (13/18)").
SENS_RE = re.compile(r"sensitivit\w*[^\n]{0,40}?\b(\d+)\s*(?:/|of)\s*(\d+)", re.I)
SPEC_RE = re.compile(r"specificit\w*[^\n]{0,40}?\b(\d+)\s*(?:/|of)\s*(\d+)", re.I)
CORRECT_RE = re.compile(r"correctl\w*[^.\n]*?\b(\d+)", re.I)
OVER_RE = re.compile(r"over[- ]?stag\w*[^.\n]*?\b(\d+)", re.I)
UNDER_RE = re.compile(r"under[- ]?stag\w*[^.\n]*?\b(\d+)", re.I)
STAGE_N_RE = re.compile(r"\b(?:in|of|among)\s+(\d+)\s+(?:patients|exams|cases|lesions)\b", re.I)


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
        return "DENOMINATOR MISMATCH" if self.n_flag else "OK"


def _split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _reference_counts(text: str):
    """Return (neg_total, pos_total) summed over reference-standard rows, or None."""
    neg = pos = 0
    seen = False
    lines = text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        if "|" in lines[i] and i + 1 < n and SEP_RE.match(lines[i + 1]) and "-" in lines[i + 1]:
            j = i + 2
            while j < n and "|" in lines[j] and lines[j].strip():
                cells = _split_row(lines[j])
                if cells:
                    label = cells[0]
                    cm = re.search(r"\b(\d[\d,]*)\b", " ".join(cells[1:]))
                    if cm:
                        cnt = int(cm.group(1).replace(",", ""))
                        if NEG_LABEL_RE.search(label):
                            neg += cnt; seen = True
                        elif POS_LABEL_RE.search(label):
                            pos += cnt; seen = True
                j += 1
            i = j
        else:
            i += 1
    return (neg, pos) if seen else None


def audit(text: str, source: str) -> Report:
    rep = Report(source=source)
    ref = _reference_counts(text)
    sens = SENS_RE.search(text)
    spec = SPEC_RE.search(text)

    if ref and (sens or spec):
        neg_ct, pos_ct = ref
        sens_denom = int(sens.group(2)) if sens else None
        spec_denom = int(spec.group(2)) if spec else None
        if sens_denom is not None and pos_ct and sens_denom != pos_ct:
            rep.findings.append(Finding(
                "DTA_DENOMINATOR_MISMATCH", "MAJOR",
                f"sensitivity denominator {sens_denom} (disease-positive) ≠ reference-standard "
                f"positive count {pos_ct} from the characteristics table"))
        if spec_denom is not None and neg_ct and spec_denom != neg_ct:
            rep.findings.append(Finding(
                "DTA_DENOMINATOR_MISMATCH", "MAJOR",
                f"specificity denominator {spec_denom} (disease-negative) ≠ reference-standard "
                f"negative count {neg_ct} from the characteristics table"))
        # note when the grand totals still agree — that is what hides it
        if rep.n_flag and sens_denom and spec_denom and neg_ct + pos_ct == sens_denom + spec_denom:
            rep.findings.append(Finding(
                "GRAND_TOTAL_AGREES", "INFO",
                f"grand totals agree ({neg_ct}+{pos_ct} = {sens_denom}+{spec_denom} = "
                f"{neg_ct + pos_ct}), so a totals-only check passes — the split-level "
                f"mismatch is the defect"))

    c, o, u = CORRECT_RE.search(text), OVER_RE.search(text), UNDER_RE.search(text)
    sn = STAGE_N_RE.search(text)
    if c and o and u and sn:
        s = int(c.group(1)) + int(o.group(1)) + int(u.group(1))
        tot = int(sn.group(1))
        if s != tot:
            rep.findings.append(Finding(
                "STAGE_ROWSUM", "MAJOR",
                f"correctly {c.group(1)} + over {o.group(1)} + under {u.group(1)} = {s} ≠ n={tot}"))
    return rep


def format_report(rep: Report, color: bool) -> str:
    tag = {"OK": "\033[92m", "DENOMINATOR MISMATCH": "\033[91m"}.get(rep.verdict, "") if color else ""
    end = "\033[0m" if color else ""
    out = [f"{tag}== {rep.verdict} =={end}  {rep.source}", f"mismatches={rep.n_flag}"]
    if not rep.findings:
        out.append("sens/spec denominators reconcile with the reference-standard category counts.")
        return "\n".join(out)
    for f in sorted(rep.findings, key=lambda x: (x.severity != "MAJOR", x.kind, x.detail)):
        out.append(f"[{f.severity:<5}] {f.kind}  {f.detail}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any mismatch")
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

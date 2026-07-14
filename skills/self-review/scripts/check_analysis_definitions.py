#!/usr/bin/env python3
"""check_analysis_definitions.py — every analysis reported in Results must be
defined in Methods. A model with no outcome variable is not complex; it is
incomplete.

Twenty-four detectors in this skill ask whether a number is *correct*. None asks
whether the analysis that produced it was ever *defined*. This one does.

The failure it catches is not "the statistics are too advanced". It is a Cox model
whose dependent variable is never stated, and a calibration analysis whose
reference standard is, in a reviewer's words, "not defined anywhere". Both were
asked for twice in the rejection that motivated this gate, alongside "this section
is largely incomprehensible in its current form".

Load is the *cause*, not the crime. The same reviewer wrote: "too many analyses
have been performed and reported, resulting in a manuscript with multiple tables
and a lengthy Results section. This appears to have contributed to omissions of
critical information in the Materials and Methods section." A second reviewer, on
the same manuscript, listed the sensitivity analyses as a *strength*. So the count
is reported here as context (`ANALYSIS_LOAD`, informational) and never as a
verdict: a detector that punished the strength and missed the defect would be
worse than none.

Fires on:
  MODEL_NOT_IN_METHODS        a model reported in Results that Methods never
                              describes at all.
  MODEL_OUTCOME_UNDEFINED     a model described in Methods with no outcome /
                              dependent variable (and, for time-to-event, no time
                              variable) named anywhere near it.
  REFERENCE_STANDARD_UNDEFINED
                              discrimination (C-index / AUC) or calibration is
                              reported, but Methods names no reference standard or
                              observed outcome to score against.
  TIER_LABEL_UNDEFINED        a tier/group label (T1–T4, Group A, Class 2) carries
                              results but Methods never states its defining
                              criterion.
  ANALYSIS_LOAD               informational: distinct analyses + tables. Context
                              for the above, never a verdict on its own.

Stdlib-only. Reads the manuscript, never writes it.

Usage:
  python3 check_analysis_definitions.py --manuscript paper.md [--strict] [--quiet] [--json]
Exit: 0 clean; with --strict, 1 on any MAJOR finding; 2 on input/usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict

METHODS_RE = re.compile(
    r"^#{1,4}\s*\**\s*(?:\d+\.?\s*)?(?:materials?\s+and\s+methods?|methods?|"
    r"patients?\s+and\s+methods?)\b", re.I | re.M)
RESULTS_RE = re.compile(r"^#{1,4}\s*\**\s*(?:\d+\.?\s*)?results?\b", re.I | re.M)
DISCUSSION_RE = re.compile(r"^#{1,4}\s*\**\s*(?:\d+\.?\s*)?discussion\b", re.I | re.M)

# Model families a reader must be told the outcome of.
MODELS = {
    "Cox proportional-hazards": r"\bCox\b(?:[^.]{0,40}?\b(?:model|regression|hazard))?",
    "Fine–Gray subdistribution": r"\bFine[-–—\s]?Gray\b|\bsubdistribution\s+hazard\b",
    "logistic regression": r"\blogistic\s+regression\b",
    "Poisson / negative-binomial": r"\b(?:Poisson|negative[-\s]binomial)\s+(?:model|regression)\b",
    "linear / mixed model": r"\b(?:linear\s+mixed|mixed[-\s]effects)\s+model\b",
}

# Methods must say what the model predicts.
OUTCOME_DECL_RE = re.compile(
    r"\b(?:"
    r"outcome\s+(?:was|were|is|variable|of\s+interest)|"
    r"dependent\s+variable|"
    r"event\s+of\s+interest|"
    r"(?:primary|secondary)\s+(?:endpoint|outcome)\s+(?:was|were|is)|"
    r"time[-\s]to[-\s]\w+|"
    r"time\s+(?:variable|scale|origin)|"
    r"modell?ed\s+(?:the\s+)?(?:time\s+to|risk\s+of|hazard\s+of|odds\s+of)|"
    r"the\s+outcome\s+for\s+(?:the|this)|"
    r"failure\s+time|"
    r"censor\w+\s+at"
    r")\b", re.I)

# Discrimination / calibration need something to be scored against.
PERF_RE = re.compile(
    r"\b(?:C[-\s]?index|c[-\s]?statistic|Harrell'?s?\s+C|Uno'?s?\s+C|"
    r"AUROC|AUC\b|discrimination|calibration|Brier\s+score|"
    r"calibration\s+(?:slope|plot|curve))\b", re.I)
REFSTD_DECL_RE = re.compile(
    r"\b(?:"
    r"reference\s+standard|ground\s+truth|gold\s+standard|"
    r"observed\s+(?:outcome|event|risk|proportion)s?|"
    r"predicted\s+(?:versus|vs\.?|against)\s+observed|"
    r"against\s+the\s+observed|"
    r"compared\s+with\s+(?:the\s+)?observed"
    r")\b", re.I)

TIER_LABEL_RE = re.compile(r"\b([TC][1-9]|Group\s+[A-D]|Class\s+[1-4]|Tier\s+[1-4])\b")
# A tier is defined when its label sits next to a criterion: "T1 (≥15 mm)", "T1 = ...",
# "T1 was defined as", "T1 (6–9 mm)".
TIER_DEF_TMPL = (r"{lab}\s*(?:\(|,|:|=|\bwas\s+defined\b|\bwere\s+defined\b|\bdenote|\brefer)"
                 r"[^.\n]{{0,60}}?(?:[<>≥≤]|\d|\bmm\b|\bcm\b|defined)")

SENS_RE = re.compile(
    r"\b(?:sensitivity\s+analys[ie]s|subgroup\s+analys[ie]s|landmark\s+analys[ie]s|"
    r"competing[-\s]risk\w*|robustness\s+(?:check|analys[ie]s)|"
    r"meta[-\s]regression|leave[-\s]one[-\s]out|E[-\s]value)\b", re.I)
TABLE_RE = re.compile(r"^\s*\**\s*Table\s+\d+\b", re.I | re.M)


@dataclass
class Finding:
    kind: str
    severity: str
    line: int
    detail: str


@dataclass
class Report:
    source: str
    load: dict = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)

    @property
    def n_major(self) -> int:
        return sum(1 for f in self.findings if f.severity == "MAJOR")

    @property
    def verdict(self) -> str:
        return "UNDEFINED ANALYSES" if self.n_major else "OK"


def _sections(text: str) -> tuple[str, str]:
    """Return (methods, results). Empty strings when a heading is absent."""
    m = METHODS_RE.search(text)
    r = RESULTS_RE.search(text)
    d = DISCUSSION_RE.search(text)
    methods = text[m.end(): r.start()] if m and r and r.start() > m.start() else (
        text[m.end():] if m else "")
    if r:
        results = text[r.end(): d.start()] if d and d.start() > r.start() else text[r.end():]
    else:
        results = ""
    return methods, results


def _line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def audit(text: str, source: str) -> Report:
    rep = Report(source=source)
    methods, results = _sections(text)
    if not methods or not results:
        rep.findings.append(Finding(
            "SECTIONS_NOT_FOUND", "MINOR", 1,
            "could not locate both a Methods and a Results heading; "
            "the definition cross-check needs both"))
        return rep

    m_off = text.index(methods) if methods else 0

    # --- models -----------------------------------------------------------
    for label, pat in MODELS.items():
        rx = re.compile(pat, re.I)
        in_results = rx.search(results)
        m_hits = list(rx.finditer(methods))
        if in_results and not m_hits:
            rep.findings.append(Finding(
                "MODEL_NOT_IN_METHODS", "MAJOR",
                _line_of(text, text.index(results) + in_results.start()),
                f"a {label} model carries results but Methods never describes it"))
            continue
        if not m_hits:
            continue
        # Does *any* mention of this model in Methods sit near an outcome declaration?
        defined = any(
            OUTCOME_DECL_RE.search(methods[max(0, h.start() - 400): h.end() + 400])
            for h in m_hits)
        if not defined:
            rep.findings.append(Finding(
                "MODEL_OUTCOME_UNDEFINED", "MAJOR",
                _line_of(text, m_off + m_hits[0].start()),
                f"a {label} model is specified with no outcome / dependent variable "
                f"named near it — state the event and, for time-to-event, the time "
                f"variable and the censoring rule"))

    # --- discrimination / calibration -------------------------------------
    perf_hit = PERF_RE.search(results) or PERF_RE.search(methods)
    if perf_hit and not REFSTD_DECL_RE.search(methods):
        where = results if PERF_RE.search(results) else methods
        base = text.index(where)
        rep.findings.append(Finding(
            "REFERENCE_STANDARD_UNDEFINED", "MAJOR",
            _line_of(text, base + PERF_RE.search(where).start()),
            "discrimination and/or calibration are reported, but Methods names no "
            "reference standard or observed outcome to score the predictions against"))

    # --- tier labels -------------------------------------------------------
    used = {m.group(1) for m in TIER_LABEL_RE.finditer(results)}
    for lab in sorted(used):
        rx = re.compile(TIER_DEF_TMPL.format(lab=re.escape(lab)), re.I)
        if not rx.search(methods):
            first = TIER_LABEL_RE.search(results)
            rep.findings.append(Finding(
                "TIER_LABEL_UNDEFINED", "MINOR",
                _line_of(text, text.index(results) + (first.start() if first else 0)),
                f"'{lab}' carries results but Methods never states its defining "
                f"criterion — give the range or rule, and prefer the criterion itself "
                f"over an invented label"))

    # --- load (context only, never a verdict) ------------------------------
    n_models = sum(1 for pat in MODELS.values()
                   if re.search(pat, methods + results, re.I))
    n_sens = len({m.group(0).lower() for m in SENS_RE.finditer(methods + results)})
    n_tables = len(TABLE_RE.findall(text))
    rep.load = {"model_families": n_models, "auxiliary_analyses": n_sens, "tables": n_tables}
    rep.findings.append(Finding(
        "ANALYSIS_LOAD", "INFO", 0,
        f"{n_models} model famil{'y' if n_models == 1 else 'ies'}, {n_sens} auxiliary "
        f"analys{'is' if n_sens == 1 else 'es'}, {n_tables} table{'' if n_tables == 1 else 's'}. "
        f"Load is context, not a verdict — but it is what crowds the Methods until "
        f"definitions fall out. If the checks above fired, look here first."))
    return rep


def format_report(rep: Report, color: bool) -> str:
    tag = {"OK": "\033[92m", "UNDEFINED ANALYSES": "\033[91m"}.get(rep.verdict, "") if color else ""
    end = "\033[0m" if color else ""
    out = [f"{tag}== {rep.verdict} =={end}  {rep.source}"]
    if rep.load:
        out.append(f"load: models={rep.load['model_families']} "
                   f"auxiliary={rep.load['auxiliary_analyses']} tables={rep.load['tables']}")
    majors = [f for f in rep.findings if f.severity != "INFO"]
    if not majors:
        out.append("every reported analysis names its outcome and its reference standard.")
    for f in sorted(rep.findings, key=lambda x: (x.severity == "INFO", x.line, x.kind)):
        out.append(f"[{f.severity}] {f.kind} L{f.line}  {f.detail}")
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
            print(json.dumps({"detector": "check_analysis_definitions",
                              "source": rep.source, "verdict": rep.verdict,
                              "load": rep.load,
                              "findings": [asdict(f) for f in rep.findings]},
                             ensure_ascii=False, indent=2))
        else:
            print(format_report(rep, color=sys.stdout.isatty()))
    return 1 if (args.strict and rep.n_major) else 0


if __name__ == "__main__":
    raise SystemExit(main())

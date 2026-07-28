#!/usr/bin/env python3
"""check_review_request_types.py — audit a *reviewer's own draft* for the kind of
request it makes, not the manuscript it reviews.

Every other detector in this repo audits the manuscript. This one audits the
review. Sort each ask into two kinds:

  Disclosure  — "show what the study already knows and has not printed."
                (the analysis unit; a CI you already computed; the n per stratum;
                the reading order.) It costs the authors nothing and *surfaces*
                errors.

  Computation — "produce a number that does not yet exist."
                (test this difference; bootstrap a CI; propagate these rates.)
                It creates a **new, unreviewed error surface**, produced under
                revision deadline by authors who will not re-check it, and
                accepted next round by a reviewer who reads its existence as
                compliance.

`/peer-review` Phase 3 already states this rule in prose, and Phase 6 already
lists it as a checkbox. Prose did not bind: in the first live review after the
rule shipped, a draft went out with four unjustified computation requests and
passed every neighbouring gate (word count, em-dash density, forbidden words,
attitude markers) because those are scripts and this one was a sentence. Hence
this file.

Fires on:
  COMPUTATION_UNJUSTIFIED  a computation request with no stated reason the
                           manuscript's existing tables cannot answer it. Phase 3
                           requires that justification; otherwise reword the ask
                           as disclosure or drop it.
  COMPUTATION_HEAVY        more computation requests than --max-computation.
  NEW_DATA_REQUESTED       an ask requiring data that does not exist (a second
                           reader, re-segmentation, a new cohort). Strictly worse
                           than computation: it cannot be satisfied in revision.
  NESTED_P_REQUESTED       an ask for a P value comparing an analysed subset with
                           the parent cohort that contains it. The groups are
                           nested, so the test is invalid — never *request* the
                           table `check_nested_group_comparison.py` exists to flag.
  ESTIMATOR_UNNAMED        an effect size / interval requested without naming the
                           estimator, which the authors will resolve by guessing.

Deliberately high-precision, not high-recall: a detector that never falsely
accuses a disclosure request is worth more than one that catches every
computation. It cannot know whether a number already exists in the manuscript, so
it gates on the request's own verbs.

Stdlib-only. Reads the review draft, never writes it.

Usage:
  python3 check_review_request_types.py --review draft.md [--max-computation N]
                                        [--strict] [--quiet] [--json]
Exit: 0 clean; with --strict, 1 on any MAJOR finding; 2 on input/usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict

# An "ask" is a bullet or a numbered item. A review draft's requests live there.
ASK_RE = re.compile(r"^\s{0,3}(?:[-*+]|\d{1,2}[.)])\s+(.*\S)\s*$")

# --- request classes -------------------------------------------------------
# High-precision only. Bare "model" / "test" / "estimate" are excluded: they
# appear in disclosure asks ("whether the model is released", "the index test").
COMPUTE_RE = re.compile(
    r"\b(?:"
    r"re-?comput\w*|comput\w+|re-?calculat\w*|calculat\w+|"
    r"re-?deriv\w*|deriv\w+|propagat\w+|bootstrap\w*|"
    r"re-?run|rerun|re-?analys\w+|re-?analyz\w+|reanalys\w+|reanalyz\w+|"
    r"re-?fit\b|fit\s+(?:a|the)\b|model(?:l?ing|\s+(?:the|percentiles|these))|"
    r"simulat\w+|imput\w+|re-?weight\w*|inverse[- ]probability|"
    r"cross-?tabulat\w+|"
    r"sensitivity\s+analys\w+|subgroup\s+analys\w+|"
    r"(?:additional|further|new)\s+analys\w+|"
    r"(?:perform|conduct|carry\s+out)\s+(?:an?|the)\s+\w+|"
    r"test\s+(?:whether|this|that|for\s+a|the\s+difference)|"
    r"statistical\s+test|significance\s+test|"
    r"[Pp][- ]values?\b|interaction\s+test|effect\s+size|"
    r"GAMLSS|\bLMS\b|E-values?"
    r")\b", re.I)

NEW_DATA_RE = re.compile(
    r"\b(?:"
    r"(?:a\s+)?second\s+(?:reader|rater|observer)|two\s+(?:readers|raters|observers)|"
    r"independently\s+(?:label|re-?read|re-?assess|score|rate)|"
    r"re-?read|re-?assess|re-?segment\w*|re-?annotat\w*|adjudicat\w+|"
    r"recruit\w*|prospectively\s+collect|collect\s+(?:new|additional)|"
    r"repeat\s+the\s+validation|external\s+(?:validation\s+)?cohort"
    r")\b", re.I)

# Phase 3 requires: "an explicit justification that the existing tables cannot
# answer the question". Feasibility ("this is cheap") is NOT that justification.
JUSTIFY_RE = re.compile(
    r"(?:"
    r"cannot\s+(?:be\s+)?(?:answer|deriv|recover|obtain|read|tell)\w*|"
    r"can\s+not\s+(?:be\s+)?\w+|"
    r"not\s+(?:derivable|recoverable|answerable|reported\s+anywhere|shown\s+anywhere)|"
    r"hard\s+to\s+deriv\w*|"
    r"(?:existing|present|current|reported|published)\s+tables?\s+(?:cannot|do\s+not|does\s+not|will\s+not)|"
    r"no(?:ne\s+of\s+the)?\s+(?:existing\s+)?tables?\s+(?:cannot|do\s+not|show|report|answer)|"
    r"nothing\s+in\s+the\s+(?:manuscript|paper|tables?)|"
    r"I\s+raise\s+this\s+because"
    r")", re.I)

NESTED_P_RE = re.compile(
    r"(?=.*\b(?:[Pp][- ]values?|test|compar\w+)\b)"
    r"(?=.*\b(?:subset|sub-?cohort|analy[sz]ed\s+(?:subset|group))\b)"
    r"(?=.*\b(?:full|entire|whole|parent|total)\s+cohort\b)", re.I)

# A reviewer who *declines* the invalid test is doing the right thing. Do not
# flag the ask that says so.
NESTED_ACK_RE = re.compile(
    r"(?:without\s+(?:a\s+)?(?:significance\s+)?test|no\s+[Pp][- ]values?|"
    r"groups?\s+(?:are|is)\s+nested|nested\s+groups?|"
    r"subset\s+vs\.?\s+(?:the\s+)?remainder)", re.I)

# "without a significance test", "I am not asking you to repeat the validation",
# "rather than modelling" — the ask is *declining* the work, not requesting it.
NEGATOR_RE = re.compile(
    r"\b(?:without|not|no|never|rather\s+than|instead\s+of|avoid|refrain\s+from)"
    r"\b[\s\w,'-]{0,24}$", re.I)

# A bullet that merely *describes* a defect is not a request. "bootstrap intervals
# are reported for the median only" states a fact; "Bootstrap the percentiles" asks
# for work. Only an ask carrying a request cue is classified at all — the detector
# would rather miss an implied ask than accuse a plain observation.
REQUEST_CUE_RE = re.compile(
    r"^(?:please\s+)?(?:also\s+)?(?:"
    r"report|state|clarify|confirm|give|add|provide|specify|list|name|indicate|"
    r"describe|explain|justify|show|include|present|discuss|address|acknowledge|"
    r"reconcile|temper|soften|update|correct|remove|move|replace|relabel|"
    r"consider|extend|have|repeat|drop|split|separate|"
    r"re-?deriv\w*|re-?comput\w*|recalculat\w*|calculat\w+|comput\w+|propagat\w+|"
    r"bootstrap|model|fit|run|perform|conduct|test|simulat\w+|imput\w+|pool"
    r")\b"
    r"|\b(?:please|should|could you|would you|we ask|it would help|"
    r"I (?:would )?(?:suggest|ask|request|recommend))\b", re.I)


def _unnegated(pat: re.Pattern, ask: str) -> bool:
    """True iff at least one match of `pat` is not preceded by a negator."""
    return any(not NEGATOR_RE.search(ask[: m.start()]) for m in pat.finditer(ask))

EFFECT_ASK_RE = re.compile(
    r"\b(?:effect\s+size|confidence\s+intervals?|\bCIs?\b|"
    r"(?:median|mean|paired)\s+difference)\b", re.I)
ESTIMATOR_NAMED_RE = re.compile(
    r"\b(?:Hodges[-–\s]?Lehmann|pseudomedian|Wilcoxon|Mann[-–\s]?Whitney|"
    r"Clopper[-–\s]?Pearson|Wilson|Fisher|Cohen'?s?\s*d|Hedges|Cliff'?s?\s*delta|"
    r"BCa|percentile\s+bootstrap|Agresti[-–\s]?Coull|Newcombe|DeLong)\b", re.I)


@dataclass
class Finding:
    kind: str
    severity: str
    line: int
    detail: str


@dataclass
class Report:
    source: str
    asks: int = 0
    disclosure: int = 0
    computation: int = 0
    new_data: int = 0
    descriptive: int = 0
    findings: list[Finding] = field(default_factory=list)

    @property
    def n_major(self) -> int:
        return sum(1 for f in self.findings if f.severity == "MAJOR")

    @property
    def verdict(self) -> str:
        return "REQUEST-TYPE VIOLATIONS" if self.n_major else "OK"


def _clip(s: str, n: int = 78) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def audit(text: str, source: str, max_computation: int = 2) -> Report:
    rep = Report(source=source)
    for i, raw in enumerate(text.splitlines(), start=1):
        m = ASK_RE.match(raw)
        if not m:
            continue
        ask = m.group(1)
        rep.asks += 1

        if not REQUEST_CUE_RE.search(ask):
            rep.descriptive += 1
            continue

        is_new_data = _unnegated(NEW_DATA_RE, ask)
        is_compute = _unnegated(COMPUTE_RE, ask)

        if is_new_data:
            rep.new_data += 1
            rep.findings.append(Finding(
                "NEW_DATA_REQUESTED", "MAJOR", i,
                f"asks for data that does not exist — cannot be satisfied within a "
                f"revision: \"{_clip(ask)}\""))
        elif is_compute:
            rep.computation += 1
            if not JUSTIFY_RE.search(ask):
                rep.findings.append(Finding(
                    "COMPUTATION_UNJUSTIFIED", "MAJOR", i,
                    f"computation request with no stated reason the existing tables "
                    f"cannot answer it — reword as disclosure or justify: "
                    f"\"{_clip(ask)}\""))
        else:
            rep.disclosure += 1

        if NESTED_P_RE.search(ask) and not NESTED_ACK_RE.search(ask):
            rep.findings.append(Finding(
                "NESTED_P_REQUESTED", "MAJOR", i,
                f"requests a P value between a subset and the cohort containing it — "
                f"nested groups, so the test is invalid; ask for the subset's "
                f"characteristics instead: \"{_clip(ask)}\""))

        if (is_compute and EFFECT_ASK_RE.search(ask)
                and not ESTIMATOR_NAMED_RE.search(ask)):
            rep.findings.append(Finding(
                "ESTIMATOR_UNNAMED", "MINOR", i,
                f"an effect size or interval is requested without naming the "
                f"estimator; the authors will adopt the loose phrase verbatim: "
                f"\"{_clip(ask)}\""))

    heavy = rep.computation + rep.new_data
    if heavy > max_computation:
        rep.findings.append(Finding(
            "COMPUTATION_HEAVY", "MAJOR", 0,
            f"{heavy} computation/new-data requests (limit {max_computation}) — each "
            f"is a new, unreviewed error surface produced under revision deadline"))
    return rep


def format_report(rep: Report, color: bool) -> str:
    tag = {"OK": "\033[92m",
           "REQUEST-TYPE VIOLATIONS": "\033[91m"}.get(rep.verdict, "") if color else ""
    end = "\033[0m" if color else ""
    out = [f"{tag}== {rep.verdict} =={end}  {rep.source}",
           f"asks={rep.asks} disclosure={rep.disclosure} "
           f"computation={rep.computation} new_data={rep.new_data} "
           f"descriptive={rep.descriptive}"]
    if not rep.findings:
        out.append("every ask is a disclosure request, or a justified computation.")
        return "\n".join(out)
    for f in sorted(rep.findings, key=lambda x: (x.line, x.kind)):
        out.append(f"[{f.severity}] {f.kind} L{f.line}  {f.detail}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--review", required=True, help="the reviewer's draft (markdown/text)")
    ap.add_argument("--max-computation", type=int, default=2, metavar="N",
                    help="computation/new-data requests allowed before COMPUTATION_HEAVY (default 2)")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any MAJOR finding")
    ap.add_argument("--quiet", action="store_true", help="suppress the report; exit code only")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a text report")
    args = ap.parse_args(argv)
    try:
        text = open(args.review, encoding="utf-8").read()
    except OSError as e:
        print(f"error: cannot read review draft: {e}", file=sys.stderr)
        return 2
    rep = audit(text, args.review, max_computation=args.max_computation)
    if not args.quiet:
        if args.json:
            print(json.dumps({"detector": "check_review_request_types",
                              "source": rep.source, "verdict": rep.verdict,
                              "asks": rep.asks, "disclosure": rep.disclosure,
                              "computation": rep.computation, "new_data": rep.new_data,
                              "descriptive": rep.descriptive,
                              "findings": [asdict(f) for f in rep.findings]},
                             ensure_ascii=False, indent=2))
        else:
            print(format_report(rep, color=sys.stdout.isatty()))
    return 1 if (args.strict and rep.n_major) else 0


if __name__ == "__main__":
    raise SystemExit(main())

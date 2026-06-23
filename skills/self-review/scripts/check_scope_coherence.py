#!/usr/bin/env python3
"""Endpoint↔conclusion scope-coherence gate (self-review §D).

Two overclaim patterns where the conclusion's action exceeds what the design or
endpoint can support. Both are deterministic when a design/endpoint signal and a
conclusion action verb co-occur, and both are documented anti-patterns
(scope-coherence-gate.md):

  CROSS_SECTIONAL_PROGNOSTIC  the design is cross-sectional / single-visit /
                              prevalence, yet the conclusion makes a prognostic or
                              surveillance claim (rescreen interval, surveillance,
                              disease progression, predicting future risk). A single
                              time point cannot license a longitudinal conclusion.
  SURROGATE_CARE_DIRECTIVE    a binary surrogate endpoint (present/absent, >0,
                              dichotomized) drives a patient-care directive (defer,
                              withhold, initiate/discontinue therapy, statin). A
                              risk-stratification marker is not a management trigger.
  CROSS_SECTIONAL_YIELD_LANGUAGE  a cross-sectional / prevalence design uses
                              incidence/prospective-flavored vocabulary — "yield",
                              "detection rate", "number-needed-to-screen/image",
                              "rescreen interval", "screen-detected". On a
                              prevalence design these read as longitudinal screening
                              performance. Minor unless "yield" is defined once as
                              cross-sectional report-positive prevalence.

The gate is conservative: it fires only when both a signal and a conclusion-region
verb are present, to keep false positives low on a widely-used skill.

INPUTS
  --manuscript  manuscript markdown/text (required).

OUTPUT
  A reconciliation table (stdout) and, with --out, a JSON artifact:
    {manuscript, claims[{verdict, severity, detail, where}], summary}
  Both verdicts are Major. Exit 1 (with --strict) when any Major claim exists.

Stdlib-only (json / re / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DESIGN_CROSS_SECTIONAL = re.compile(
    r"cross[-\s]?sectional|single[-\s](?:time[-\s]?point|visit|examination|measurement)|"
    r"at (?:a |one )?(?:single |one )?time[-\s]?point|point[-\s]prevalence|"
    r"prevalence (?:study|survey|design)", re.IGNORECASE)

PROGNOSTIC_VERB = re.compile(
    r"surveillance|re[-\s]?screen|screening interval|rescreening|"
    r"monitor(?:ed|ing)?\s+over\s+time|disease progression|progress(?:es|ion)\s+to|"
    r"prognost|predict(?:s|ing|ed)?\s+(?:incident|future|long[-\s]?term|the risk of developing)|"
    r"longitudinal (?:follow|risk|trajector)", re.IGNORECASE)

# A prognostic/surveillance token sitting inside a negation/deferral frame is a
# correct hedge, not an overclaim ("describes concurrent burden RATHER THAN
# surveillance intervals, which WOULD REQUIRE PROSPECTIVE data"). You cannot
# disavow surveillance without naming it; do not fire CROSS_SECTIONAL_PROGNOSTIC
# when the match is disclaimed in its immediate vicinity.
PROGNOSTIC_DISCLAIMER = re.compile(
    r"rather than|instead of|not\s+(?:a\s+|the\s+)?(?:surveillance|prognostic|longitudinal)|"
    r"does not (?:establish|imply|support|provide|address|determine|permit)|"
    r"cannot (?:establish|determine|inform|assess|address)|"
    r"would require|requires?\s+prospective|warrants?\s+prospective|"
    r"defer(?:s|red|ring)?\b[^.]{0,40}\bprospective|"
    r"beyond the scope|no (?:prognostic|surveillance|longitudinal) (?:claim|inference|conclusion)",
    re.IGNORECASE)

DIRECTIVE_VERB = re.compile(
    r"\bdefer(?:ral|red|ring)?\b|\bwithhold\b|\bforgo\b|\binitiat(?:e|ed|ion)\b|"
    r"\bdiscontinu(?:e|ed|ation)\b|start(?:ing)?\s+(?:statin|therapy|treatment|pharmacotherapy)|"
    r"(?:statin|treatment|therapy|pharmacotherapy)\s+(?:can|should|may)\s+be\s+(?:deferred|withheld|started|initiated)|"
    r"recommend(?:ed)?\s+(?:statin|treatment|therapy|initiation|against treatment)|"
    r"guide\s+(?:treatment|management|therapy)", re.IGNORECASE)

YIELD_LANGUAGE = re.compile(
    r"\byield\b|detection rate|number[-\s]needed[-\s]to[-\s](?:screen|image)|"
    r"\bnn[si]\b|rescreen(?:ing)?\s+interval|screen[-\s]detected", re.IGNORECASE)

# "yield" pinned once to a cross-sectional prevalence reading suppresses the flag.
YIELD_DEFINED = re.compile(
    r"yield (?:is|was|here|,)?\s*(?:defined|refers|denotes|i\.e\.)|"
    r"defined as the (?:cross[-\s]sectional )?(?:report[-\s]positive )?prevalence|"
    r"cross[-\s]sectional (?:report[-\s]positive )?prevalence", re.IGNORECASE)

SURROGATE_SIGNAL = re.compile(
    r"binary (?:surrogate|endpoint|outcome|marker)|dichotom(?:ous|ised|ized)|surrogate (?:endpoint|marker|outcome)|"
    r"presence (?:or absence )?of|present (?:vs\.?|versus|or) absent|positive (?:vs\.?|versus|or) negative|"
    r"categor(?:ised|ized) as (?:positive|present|absent)|>\s?0\b", re.IGNORECASE)

CONCLUSION_HEADINGS = re.compile(
    r"^#{1,4}\s*\*{0,2}(?:CONCLUSIONS?|Conclusions?|DISCUSSION|Discussion|"
    r"Clinical Implications?|Interpretation)\*{0,2}\s*$", re.IGNORECASE | re.MULTILINE)


def conclusion_region(text: str) -> str:
    """Text under Conclusion/Discussion/Implications headings, plus any inline
    'Conclusion:' clause (abstract). Fallback: the last 25% of the document."""
    spans = []
    starts = [m.end() for m in CONCLUSION_HEADINGS.finditer(text)]
    # heading-delimited regions: from each heading to the next top-level heading
    all_headings = [m.start() for m in re.finditer(r"^#{1,4}\s", text, re.MULTILINE)]
    for s in starts:
        nxt = next((h for h in all_headings if h > s), len(text))
        spans.append(text[s:nxt])
    for m in re.finditer(r"(?:^|\n)\s*\*{0,2}Conclusions?\*{0,2}\s*[:.]\s*(.+?)(?:\n\n|$)",
                         text, re.IGNORECASE | re.DOTALL):
        spans.append(m.group(1))
    if not spans:
        spans.append(text[int(len(text) * 0.75):])
    return "\n".join(spans)


def check(text: str) -> list[dict]:
    claims = []
    concl = conclusion_region(text)

    if DESIGN_CROSS_SECTIONAL.search(text):
        # Fire only on a prognostic/surveillance token that is NOT inside a
        # negation/deferral frame; iterate all matches so a real claim later in the
        # conclusion still fires even if an earlier mention was a disclaimer.
        for pm in PROGNOSTIC_VERB.finditer(concl):
            window = concl[max(0, pm.start() - 120):pm.end() + 120]
            if PROGNOSTIC_DISCLAIMER.search(window):
                continue
            claims.append({
                "verdict": "CROSS_SECTIONAL_PROGNOSTIC",
                "severity": "Major",
                "detail": (f"cross-sectional/single-visit design, but the conclusion makes a "
                           f"prognostic/surveillance claim ('{pm.group(0).strip()}')"),
                "where": concl[max(0, pm.start() - 40):pm.end() + 40].strip()[:160],
            })
            break

    dm = DIRECTIVE_VERB.search(concl)
    sm = SURROGATE_SIGNAL.search(concl)
    if dm and sm:
        claims.append({
            "verdict": "SURROGATE_CARE_DIRECTIVE",
            "severity": "Major",
            "detail": (f"a binary surrogate endpoint ('{sm.group(0).strip()}') drives a "
                       f"patient-care directive ('{dm.group(0).strip()}') in the conclusion"),
            "where": concl[max(0, dm.start() - 40):dm.end() + 40].strip()[:160],
        })

    if DESIGN_CROSS_SECTIONAL.search(text):
        ym = YIELD_LANGUAGE.search(text)
        if ym and not YIELD_DEFINED.search(text):
            claims.append({
                "verdict": "CROSS_SECTIONAL_YIELD_LANGUAGE",
                "severity": "Minor",
                "detail": (f"cross-sectional/prevalence design uses incidence-flavored "
                           f"screening vocabulary ('{ym.group(0).strip()}') without defining "
                           f"'yield' as cross-sectional report-positive prevalence; on a "
                           f"single-timepoint design this reads as longitudinal screening "
                           f"performance"),
                "where": text[max(0, ym.start() - 40):ym.end() + 40].strip()[:160],
            })

    return claims


def analyze(manuscript: str) -> dict:
    p = Path(manuscript)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    claims = check(p.read_text(encoding="utf-8"))
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "manuscript": str(p),
        "claims": claims,
        "summary": {
            "n_claims": len(claims),
            "n_major": n_major,
            "n_flag": len(claims) - n_major,
            "verdict": "MAJOR_CANDIDATE" if n_major else "OK",
        },
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | conclusion scope matches the design/endpoint |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Endpoint↔conclusion scope-coherence gate (§D).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manuscript)

    if not args.quiet:
        print("=" * 41)
        print(" Scope Coherence (§D)")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} endpoint↔conclusion scope mismatch(es).")
        elif s["n_flag"]:
            print(f"MINOR flag: {s['n_flag']} scope-language issue(s) (see table).")
        else:
            print("OK: conclusion scope matches the design/endpoint.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())

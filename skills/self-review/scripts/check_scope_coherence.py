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
  UNIVERSAL_NEGATIVE_UNSCOPED  a 'nobody / first to / has not been' novelty claim
                          in a claim region with no named discipline-scope qualifier
                          (Minor): a single-database search cannot support a universal
                          negative. Narrow the claim or widen the search.
  CROSS_SECTIONAL_YIELD_LANGUAGE  a cross-sectional / prevalence design uses
                              incidence/prospective-flavored vocabulary — "yield",
                              "detection rate", "number-needed-to-screen/image",
                              "rescreen interval", "screen-detected". On a
                              prevalence design these read as longitudinal screening
                              performance. Minor unless "yield" is defined once as
                              cross-sectional report-positive prevalence.
  GRADIENT_WITHOUT_INTERACTION  a cross-strata directional claim ("shortest in the
                              high-risk tertile", "monotonically across the age strata")
                              stated as a finding, with a stratification context nearby,
                              but NO interaction test (interaction term / LRT / p-
                              interaction / effect modification) reported anywhere. A
                              difference in significance across strata is not a tested
                              interaction. Minor. Precision-guarded: a physical "pressure
                              gradient" or "gradient echo" and an interaction-tested claim
                              do not fire.

The gate is conservative: it fires only when both a signal and a conclusion-region
verb are present, to keep false positives low on a widely-used skill.

INPUTS
  --manuscript  manuscript markdown/text (required).

OUTPUT
  A reconciliation table (stdout) and, with --out, a JSON artifact:
    {manuscript, claims[{verdict, severity, detail, where}], summary}
  CROSS_SECTIONAL_PROGNOSTIC and SURROGATE_CARE_DIRECTIVE are Major; UNIVERSAL_NEGATIVE_
  UNSCOPED, CROSS_SECTIONAL_YIELD_LANGUAGE and GRADIENT_WITHOUT_INTERACTION are Minor.
  Exit 1 (with --strict) on any Major.

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

# A methods / QC / detector paper — or a review — whose SUBJECT is this very
# anti-pattern NAMES the pattern rather than committing it ("this paper detects
# manuscripts that make a prognostic claim in a cross-sectional setting"). When the
# match sits inside such a meta-framing, it is a description, not an overclaim; do
# not fire. Kept tight (requires the meta-framing structure, not a bare "detect")
# so a real prognostic overclaim is never suppressed.
META_DOC_FRAME = re.compile(
    r"anti[-\s]?pattern|such (?:patterns|claims|conclusions|overclaims)\b|"
    r"(?:papers?|manuscripts?|studies|authors) (?:that|which|who) "
    r"(?:commit|make|assert|report|conflate|claim|treat|use)\b|"
    r"we (?:report|show|find|note|observe) that (?:papers|manuscripts|studies|authors|some|many)|"
    r"(?:this|the present) (?:paper|study|work|review|tool|detector|gate|framework|probe)\b"
    r"[^.]{0,40}?(?:discuss|describ|detect|flag|identif|examin|review|illustrat|catalog)|"
    r"(?:as|is) an? (?:example|illustration|instance|case) of",
    re.IGNORECASE)

# A sentence that LABELS a prognostic/surveillance claim as a defect — "an
# unsupported prognostic claim in a cross-sectional study", "prognostic
# overreach", "an unwarranted surveillance recommendation" — is naming the
# anti-pattern, not committing it. This catches the enumerated-defect framing
# (a defect listed as an appositive in a list of things a tool flags) that
# META_DOC_FRAME misses because the framing verb ("flags"/"detects") sits far
# from the match. Stays high-precision: a manuscript making a real prognostic
# claim never precedes it with "unsupported"/"unwarranted", nor calls it an
# "overreach"/"overclaim" — so no genuine overclaim is suppressed.
ANTIPATTERN_LABEL = re.compile(
    r"(?:unsupported|unwarranted|unjustified|inappropriate|spurious|invalid|"
    r"overreaching|erroneous|illegitimate)\s+(?:\w+\s+){0,2}?"
    r"(?:prognostic|surveillance|longitudinal)|"
    r"(?:prognostic|surveillance|longitudinal)\s+(?:overclaim|overreach|fallacy|error)",
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


# Claim regions where a novelty/neglect claim lives: Abstract, Introduction/
# Background, Discussion, Conclusion.
NOVELTY_REGION_HEADINGS = re.compile(
    r"^#{1,4}\s*\*{0,2}(?:ABSTRACT|Abstract|INTRODUCTION|Introduction|BACKGROUND|Background|"
    r"DISCUSSION|Discussion|CONCLUSIONS?|Conclusions?)\*{0,2}\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE)

# A universal-negative / first-to novelty construction.
UNIVERSAL_NEGATIVE_RE = re.compile(
    r"\bno(?:body|-one| one)\b"
    r"|\bnone of (?:the |these )?(?:\w+\s+){0,2}(?:studies|systems|works|methods|papers|reports)\b"
    r"|\bno (?:\w+\s+){0,3}(?:published |existing |prior )?"
    r"(?:system|study|work|method|approach|dataset|benchmark|paper|report|research)\b"
    r"[^.\n]{0,50}?\b(?:measure|report|quantif|examine|assess|address|exist|investigate|describe|ask)"
    r"|\bnever been (?:measured|examined|studied|reported|asked|quantified|assessed|investigated|addressed|explored)\b"
    r"|\bhas not (?:yet )?been (?:measured|examined|studied|asked|quantified|assessed|investigated|addressed|explored)\b"
    r"|\bfirst (?:study|work|report|paper)\b[^.\n]{0,50}?\b(?:to )?(?:measure|report|examine|quantif|assess|investigate|describe|characteri[sz]e)"
    r"|\bwe are the first\b|\bthe first to (?:measure|report|examine|quantif|assess|investigate|describe|characteri[sz]e)"
    r"|\bremains? (?:largely )?(?:unmeasured|unexamined|unexplored|unaddressed)\b|\bunexamined\b|\bunexplored\b",
    re.IGNORECASE)

# A named discipline/literature FRAME that legitimately scopes the negative. A bare
# epistemic hedge ("to our knowledge") is NOT a frame and does not suppress.
SCOPE_QUALIFIER_RE = re.compile(
    r"\bclinical(?:ly)? (?:published|literature)\b"
    r"|\bin (?:the )?(?:clinical|medical|radiolog\w+|surgical|nursing|imaging|oncolog\w+) (?:literature|domain|setting|field)\b"
    r"|\bin radiology\b|\bin medicine\b|\bpeer-reviewed clinical\b"
    r"|\b(?:within|among|across) (?:the )?(?:published )?\w+ (?:literature|studies)\b"
    r"|\bto date in the \w+ literature\b",
    re.IGNORECASE)


# A cross-strata DIRECTIONAL claim: the estimate trends / differs across the levels of a
# subgroup. Anchored to distinctive phrases so a physical "pressure gradient across the
# stenosis" or an MRI "gradient echo" does not match (bare "gradient" is never enough).
GRADIENT_CLAIM_RE = re.compile(
    r"more pronounced (?:in|among|for)\b"
    r"|(?:short|long|high|low|great|small|strong|weak)(?:est|er) (?:in|among|for)\b"
    r"|monotonic(?:ally)?\b"
    r"|step[-\s]?wise (?:increase|decrease|rise|decline|shorten|across|with)"
    r"|gradient (?:across|among|by|over|with (?:higher|increasing|worsening))"
    r"|dose[-\s]?response (?:relationship|gradient|pattern)?\s*(?:across|with|by)"
    r"|(?:increas|decreas|shorten|worsen)(?:ed|ing) (?:monotonically|step[-\s]?wise|progressively)",
    re.IGNORECASE)

# A stratification CONTEXT (the LEVELS of a subgroup) — required in the same window so
# the directional language is about subgroup strata, not a physical or temporal trend.
STRATA_CONTEXT_RE = re.compile(
    r"tertile|quartile|quintile|decile|stratum|strata|stratified|subgroup"
    r"|categor(?:y|ies)|\bband\b|joint(?:ly)?[-\s]?(?:strat|classif)|cross[-\s]?classif"
    r"|(?:age|risk|score|bmi|dose)[-\s]?(?:group|categor|band|tier)",
    re.IGNORECASE)

# Evidence an interaction WAS actually tested (any hit anywhere -> suppress the flag).
INTERACTION_TEST_RE = re.compile(
    r"interaction (?:term|test|p[-\s]?value|effect|coefficient)"
    r"|p[-_\s]?interaction|p[-_\s]?int\b|effect modification"
    r"|test(?:ed|ing)? for interaction|multiplicative interaction|product term"
    r"|likelihood[-\s]?ratio test|\bLRT\b|(?:OR|HR|RR|beta|β)[-_]?int\b",
    re.IGNORECASE)

# Claim regions where a cross-strata directional statement is a substantive claim
# (not the Methods description of a stratified analysis).
CLAIM_REGION_HEADINGS = re.compile(
    r"^#{1,4}\s*\*{0,2}\s*(?:abstract|results?|discussion|interpretation|conclusions?"
    r"|key results?|principal findings?)\b",
    re.IGNORECASE | re.MULTILINE)


def _region(text: str, heading_re) -> str:
    spans = []
    all_headings = [m.start() for m in re.finditer(r"^#{1,4}\s", text, re.MULTILINE)]
    for m in heading_re.finditer(text):
        s = m.end()
        nxt = next((h for h in all_headings if h > s), len(text))
        spans.append(text[s:nxt])
    mt = re.search(r"^#{1,6}\s+(.+)$", text, re.MULTILINE)  # title
    if mt:
        spans.append(mt.group(1))
    return "\n".join(spans) if spans else text


def check(text: str) -> list[dict]:
    claims = []
    concl = conclusion_region(text)

    # UNIVERSAL_NEGATIVE_UNSCOPED — a "nobody / first to / has not been" claim in a
    # claim region with no named discipline-scope qualifier nearby. Minor: the fix is
    # usually a one-word scope narrowing (or a wider, cross-discipline search).
    region = _region(text, NOVELTY_REGION_HEADINGS)
    seen: set[str] = set()
    for m in UNIVERSAL_NEGATIVE_RE.finditer(region):
        window = region[max(0, m.start() - 200):m.end() + 200]
        if SCOPE_QUALIFIER_RE.search(window):
            continue
        key = re.sub(r"\s+", " ", m.group(0).lower())[:60]
        if key in seen:
            continue
        seen.add(key)
        claims.append({
            "verdict": "UNIVERSAL_NEGATIVE_UNSCOPED",
            "severity": "Minor",
            "detail": (f"a universal-negative / first-to claim ('{m.group(0).strip()}') with no named "
                       f"discipline-scope qualifier; a single-database search supports 'no *clinical* "
                       f"paper does X', never 'nobody does X' — narrow the claim ('...in the clinical "
                       f"literature') or widen the search to the venues where the subject lives"),
            "where": region[max(0, m.start() - 30):m.end() + 40].replace("\n", " ").strip()[:160],
        })

    if DESIGN_CROSS_SECTIONAL.search(text):
        # Fire only on a prognostic/surveillance token that is NOT inside a
        # negation/deferral frame; iterate all matches so a real claim later in the
        # conclusion still fires even if an earlier mention was a disclaimer.
        for pm in PROGNOSTIC_VERB.finditer(concl):
            window = concl[max(0, pm.start() - 120):pm.end() + 120]
            if (PROGNOSTIC_DISCLAIMER.search(window) or META_DOC_FRAME.search(window)
                    or ANTIPATTERN_LABEL.search(window)):
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

    # GRADIENT_WITHOUT_INTERACTION — a cross-strata directional claim ("shortest in the
    # high-risk tertile", "monotonically across the age strata") stated as a finding, with
    # a stratification context nearby, but NO interaction test reported anywhere. A
    # difference in significance across strata is not a tested interaction; the
    # joint-stratification framing escapes the synergy/interaction token trigger.
    if not INTERACTION_TEST_RE.search(text):
        claim_region = _region(text, CLAIM_REGION_HEADINGS)
        for gm in GRADIENT_CLAIM_RE.finditer(claim_region):
            window = claim_region[max(0, gm.start() - 160):gm.end() + 160]
            if not STRATA_CONTEXT_RE.search(window):
                continue
            claims.append({
                "verdict": "GRADIENT_WITHOUT_INTERACTION",
                "severity": "Minor",
                "detail": (f"a cross-strata directional claim ('{gm.group(0).strip()}') is made across "
                           f"subgroup levels, but no interaction test (interaction term / LRT / "
                           f"p-interaction / effect modification) is reported anywhere; a difference in "
                           f"significance across strata is not a tested interaction — report the "
                           f"interaction test, or reframe as descriptive stratified estimates"),
                "where": window.replace("\n", " ").strip()[:160],
            })
            break

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
        Path(args.out).write_text(json.dumps({"detector": "check_scope_coherence", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())

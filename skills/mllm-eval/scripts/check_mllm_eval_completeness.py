#!/usr/bin/env python3
"""LLM / MLLM clinical-evaluation completeness gate (mllm-eval).

A task-aware presence linter for the methods / plan of an LLM or multimodal-LLM
clinical evaluation. It flags the axes a defensible evaluation must cover that are
**absent** from the plan text — it is a presence check on the protocol (the analogue
of check_model_card_complete for documentation), not a judge of results. Conservative:
each verdict fires only when its concept is clearly missing from the text. A concept that
clears a check counts only when stated affirmatively: a mention that is itself negated
("no expert review", "did not evaluate hallucination", "hallucination was not assessed",
"Hallucination: not assessed") does not satisfy it. Negation scope is the concept's own noun
phrase, so a negation elsewhere in the sentence ("studies without IV contrast underwent expert
review", "reports were not edited before hallucination assessment") does not cancel it. The
patterns are sense-specific ("green arrows", "random sampling", "bootstrap CIs" or a
held-out split of a public benchmark do not satisfy GREEN / decoding / multi-run /
contamination).

CHECKS (verdicts; which apply depends on --task):
  1. NGRAM_ONLY                (Major)  report-gen names BLEU/ROUGE/METEOR but no
                                        clinical-efficacy metric (RadGraph-F1 /
                                        CheXbert / CheXpert / RadCliQ).
  2. FAITHFULNESS_MISSING      (Major)  no faithfulness / hallucination / false-premise
                                        evaluation (report-gen, vqa).
  3. REFERENCE_STANDARD_MISSING(Major)  no adjudicated reference-standard statement
                                        (report-gen).
  4. CONTAMINATION_UNADDRESSED (Major)  a public benchmark is named but no
                                        contamination / training-cutoff / held-out
                                        statement.
  5. READER_STUDY_MISSING      (Major)  report-gen with no blinded clinical reader
                                        study.
  6. PROMPT_PROVENANCE_MISSING (Minor)  no prompt + temperature/seed + multi-run
                                        disclosure.
  7. ANSWER_MATCHING_MISSING   (Minor)  vqa/classification with no answer-matching
                                        rule (exact / normalised / LLM-judge).

INPUTS
  --plan   the evaluation plan / methods markdown (required).
  --task   report_generation | vqa | classification (required).

OUTPUT
  A table (stdout) and, with --out, a JSON artifact:
    {plan, task, claims[{verdict, severity, detail, where}], summary}

Stdlib-only (re / json / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# concept -> regex of any phrasing that SATISFIES it (searched case-insensitively).
# Patterns are deliberately sense-specific: a bare word that also has an everyday meaning
# ("green arrows", "random sampling", "bootstrap CIs", "held-out test split of a public
# benchmark", "ground truth is the original report") must not clear a Major check.
_PRIVATE = r"(?:internal|private|in-house|institution\w*|prospective\w*|non-?public|unpublished|post[- ]?cut[- ]?off)"
SAT = {
    "ngram": r"\b(bleu|rouge|meteor|cider)\b",
    "clinical_metric": r"\b(radgraph|chexbert|chexpert[- ]?label|radcliq|f1[\w-]*chexpert|"
                       r"clinical efficacy|entity[- ]?relation|green[- ](?:score|metric)|"
                       r"factual(?:ity)?[- ](?:correctness[- ])?(?:score|metric|f1))\b"
                       r"|(?-i:\bGREEN\b)",
    "faithfulness": r"\b(faithful(?:ness)?|hallucinat\w+|atomic[- ]?fact|false[- ]?premise|"
                    r"fabricat\w+|med-?hal|medvh|med-?halt|confabulat\w+|ungrounded|groundedness|"
                    r"clinical(?:ly)?[- ]?grounded|evidence[- ]?support\w*)\b"
                    r"|not supported by the image",
    "reference_standard": r"\b(reference standard|adjudicat\w+|gold[- ]?standard|"
                          r"expert(?:[- ]?annotat\w+| review| radiologist)|"
                          r"(?:expert|radiologist|reader|panel)s?['\u2019]?\s+consensus|"
                          r"consensus (?:of|among|between|by) (?:[\w-]+ ){0,3}"
                          r"(?:radiologists?|experts?|readers?|clinicians?|pathologists?)|"
                          r"consensus (?:read\w*|panel|review|label\w*)|"
                          r"radiolog\w+[- ]?author\w+)\b",
    "benchmark": r"\b(vqa-?rad|slake|mimic-?cxr|medqa|pmc-?vqa|path-?vqa|openi|pubmedqa|"
                 r"public benchmark)\b",
    "contamination": r"\b(contaminat\w+|(?:training|pre-?training|knowledge)[- ]cut[- ]?off|"
                     r"post[- ]?cut[- ]?off|canary|memoris\w+|memoriz\w+|"
                     r"(?:benchmark|test[- ]?set|pre-?training)[- ](?:data[- ])?leakage|"
                     r"leakage into (?:the )?pre-?training)\b"
                     r"|\bheld[- ]?out\b[^.;\n]{0,40}\b" + _PRIVATE +
                     r"|\b" + _PRIVATE + r"\b[^.;\n]{0,40}\bheld[- ]?out\b",
    "reader_study": r"reader study|blinded read\w+|clinical reader|radiologist review|"
                    r"human evaluation|expert rating|acceptability scale|likert|"
                    r"\d+\s+(?:radiologists?|readers?|clinicians?)[^.\n]{0,60}"
                    r"(?:rated|scored|graded|read|review)|"
                    r"(?:masked|blinded)[^.\n]{0,40}(?:graded|scored|rated)",
    "prompt": r"\b(prompt)\b",
    "decoding": r"\b(temperature|top-?p|top-?k|seed|greedy|nucleus sampling|"
                r"sampling (?:temperature|parameters?|strateg\w+|settings?))\b",
    "multirun": r"\b(\d+\s*runs|repeated runs|multiple runs|across runs|run-to-run|"
                r"mean\s*(?:\u00b1|\+/-|\+-)\s|standard deviation)\b",
    "answer_match": r"\b(exact match|normali[sz]ed match|answer matching|llm[- ]?as[- ]?judge|"
                    r"llm judge|string match|keyword match|semantic (?:equivalence|match\w*)|"
                    r"clinician[- ]?adjudicat\w+|adjudicated (?:correct|equivalent)|"
                    r"human[- ]?judg\w+)\b",
}

# Concepts whose presence only TRIGGERS a check (a metric or benchmark is used). Negation is
# not applied to them, so the negation guard can only ever add flags, never remove one.
TRIGGER_CONCEPTS = {"ngram", "benchmark"}

# Negation scope. A negator cancels a mention only when it GOVERNS the concept's own noun
# phrase, independent of which verb or auxiliary the sentence uses. An unrelated negation in the
# same sentence ("Studies without IV contrast underwent expert review", "Reports were not edited
# before hallucination assessment", "Faithfulness, which was not part of prior work, is
# assessed") must not cancel an affirmative mention.
#
# The rule is a closed-set walk, not a word window. Starting at the concept, walk outward over
# tokens of the concept's own phrase only: determiners, a short list of adjectives and head
# nouns (_PHRASE), "or"/"nor" coordination, and other concept terms. Any other token -- a verb
# of any kind, a preposition, a comma, a parenthesis, "and", a relative pronoun, an ordinary
# noun -- ends the scope. A mention is negated when, inside that scope:
#   before it: a determiner negator ("no", "without", "lack(s|ing)", "neither", "nor") or a
#     negated do-verb ("did not evaluate", "do not have", "was never performed", "without
#     assessing"); or
#   after it: a passive / copular absence ("was not assessed", "are not reported", "was
#     skipped"), a label ("Hallucination: not assessed", "| Hallucination | n/a |", "Expert
#     review -- not performed", "Contamination (not assessed)", "assessment: none") or a scope
#     exclusion ("is out of scope", "is beyond our scope").
# A result is not a withdrawal: "no hallucinations were detected", "no evidence of", "found no",
# "was not detected", "was not significantly different", "Hallucination: none detected".
#
# Hard clause boundaries also bound the walk: sentence punctuation (not decimal points), a
# paragraph break or a new list item / heading / table row (a wrapped prose line is NOT a
# break), and contrastive conjunctions ("no BLEU but RadGraph-F1" -> RadGraph is affirmed).
_CLAUSE_BREAK = re.compile(r"(?<!\d)[.;!?](?!\d)|\n\s*\n|\n[ \t]*(?:[-*+#>|]|\d+[.)])|\b(?:but|whereas|however|although|though|while|except)\b",
                           re.IGNORECASE)
_PRE_WINDOW = 6   # at most this many phrase tokens between a negator and the concept
_POST_WINDOW = 6  # ... and between the concept and a post-negation
_TOK = re.compile(r"§|[\w'’/+-]+|[^\s\w]")
# Tokens that can sit INSIDE the concept's own noun phrase. Closed on purpose: anything not
# listed (in particular every verb) ends the negation scope.
_PHRASE = frozenset("""
a an the any some its their our this these such
formal explicit separate dedicated independent blinded blind masked systematic further additional
external human clinical expert structured quantitative qualitative automated automatic manual
specific other adequate rigorous sufficient direct standardised standardized
kind type form of for or nor and/or /
assessment assessments evaluation evaluations analysis analyses rate rates score scores metric
metrics check checks checking testing test measurement measurements audit study review reviews
reporting statement probe probes
""".split())
# Extra tokens allowed only AFTER the concept: a coordinated list subject ("The prompt,
# temperature and number of runs are not reported").
_POST_PHRASE = _PHRASE | frozenset(", and number details settings parameters value values run runs".split())
_DET_NEG = frozenset("no without lack lacks lacking neither nor".split())
_VERB_NEG = frozenset("not never cannot without".split())
_PRE_RESULT = frozenset("found observed detected identified showed shows show revealed demonstrated".split())
# Verbs whose negation says the axis was NOT DONE.
_ABSENCE = (r"(?:assess|evaluat|perform|report|done|do|does|did|use|used|using|includ|conduct|"
            r"measur|availab|plann|plan|consider|address|appl|disclos|examin|check|provid|undertak|"
            r"collect|obtain|quantif|test|studi|stud|scor|record|specif|state[ds]?|captur|analy[sz]|"
            r"investigat|implement|attempt|feasib|possib|carr|run|ran|account|control|explor)\w*")
_PRE_VERB = re.compile(r"(?:" + _ABSENCE + r"|ha(?:ve|s|d)|ne(?:ed|eds|eded)|requir\w*)$", re.IGNORECASE)
_POST_ABSENCE = r"(?:\w+ly\s+)?(?:" + _ABSENCE + r"|skipp\w*|omitt\w*|deferr\w*)"
_POST_CLAUSE = re.compile(
    r"\s*(?:"
    # passive / copular "not": "was not assessed", "has not been performed", "cannot be used"
    r"(?:(?:was|were|is|are|be|been)\s+(?:not|never)|(?:has|have|had)\s+(?:not|never)\s+been|"
    r"(?:will|shall|could|can|may|would|should)\s+(?:not|never)\s+be|cannot\s+be|"
    r"(?:wasn|weren|isn|aren)['\u2019]t|(?:hasn|haven|hadn)['\u2019]t\s+been|(?:won|can|couldn)['\u2019]t\s+be)"
    r"\s+" + _POST_ABSENCE + r"\b|"
    # affirmative absence: "was skipped", "were omitted"
    r"(?:was|were|is|are|has\s+been|have\s+been)\s+(?:skipped|omitted|deferred|dropped)\b|"
    # scope exclusion: "is out of scope", "is beyond our scope"
    r"(?:is|are|was|were|remains?)\s+(?:considered\s+)?(?:out\s+of|beyond|outside)\s+"
    r"(?:the\s+|our\s+|this\s+)?(?:study['\u2019]?s?\s+|present\s+|current\s+)?scope\b)",
    re.IGNORECASE)
# Label / table cell / dash / parenthesis: "X: not assessed", "| X | n/a |", "X -- none.",
# "X (not assessed)".
_POST_LABEL = re.compile(
    r"\s*(?:[:|(]|\u2014|\u2013|--|-\s)\s*(?:not\s+(?:" + _POST_ABSENCE + r"|applicable)\b|"
    r"none\s*(?:[.;|)]|$)|n/?a\b)",
    re.IGNORECASE)
# "no hallucinations were detected" reports a RESULT of evaluating the axis.
_POST_RESULT = re.compile(r"(?:\s+[\w-]+){0,3}?\s+(?:was|were|is|are)\s+(?:\w+ly\s+)?"
                          r"(?:detected|found|observed|identified|seen|noted|present|evident)\b",
                          re.IGNORECASE)


def _clause_bounds(text: str, start: int, end: int):
    lo, hi = 0, len(text)
    for b in _CLAUSE_BREAK.finditer(text):
        if b.end() <= start:
            lo = b.end()
        elif b.start() >= end:
            hi = b.start()
            break
    return lo, hi


def _mask_terms(segment: str) -> str:
    """Replace other concept terms in the segment by a placeholder token, so a coordinated
    concept ("no reader study or expert review", "an adjudicated reference standard") is part of
    the phrase. A long or negator-bearing match is left alone."""
    for pat in SAT.values():
        def sub(mm):
            s = mm.group(0)
            return " § " if len(s) <= 30 and not re.search(r"\b(?:no|not|without)\b", s, re.I) else s
        segment = re.sub(pat, sub, segment, flags=re.IGNORECASE)
    return segment


def _is_verb_neg(tok: str) -> bool:
    t = tok.lower()
    return t in _VERB_NEG or t.endswith("n't") or t.endswith("n’t")


def _pre_negated(before: str) -> bool:
    toks = _TOK.findall(_mask_terms(before))
    n = 0
    for i in range(len(toks) - 1, -1, -1):
        t = toks[i].lower()
        if t in _DET_NEG:
            return not (i > 0 and toks[i - 1].lower() in _PRE_RESULT)
        if _PRE_VERB.match(t):
            j = i - 1
            if j >= 0 and toks[j].lower().endswith("ly"):
                j -= 1
            if j >= 0 and toks[j].lower() == "be":
                j -= 1
            if j >= 0 and _is_verb_neg(toks[j]):
                return True
        if t == "§" or t in _PHRASE:
            n += 1
            if n > _PRE_WINDOW:
                return False
            continue
        return False
    return False


def _is_subject(before: str) -> bool:
    """The concept heads the subject of its clause: only phrase words (or an adverb, or a
    possessive, or "and" inside a coordinated subject) stand between it and the last comma /
    colon / parenthesis / clause start. So "Hallucination and expert review were not performed"
    withdraws both, while "Reports with hallucination were not used for training" does not
    withdraw hallucination."""
    seg = re.split(r"[,:()\[\]]", _mask_terms(before))[-1]
    for t in _TOK.findall(seg):
        tl = t.lower()
        if not (tl == "\u00a7" or tl in _PHRASE or tl == "and" or tl.endswith("ly")
                or tl.endswith("'s") or tl.endswith("\u2019s")):
            return False
    return True


def _post_negated(before: str, after: str) -> bool:
    s = _mask_terms(after)
    if _POST_LABEL.match(s):
        return True
    if not _is_subject(before):
        return False
    if _POST_CLAUSE.match(s):
        return True
    n = 0
    for tm in _TOK.finditer(s):
        t = tm.group(0).lower()
        if not (t == "\u00a7" or t in _POST_PHRASE):
            return False
        n += t != ","
        if n > _POST_WINDOW:
            return False
        if _POST_CLAUSE.match(s, tm.end()) or _POST_LABEL.match(s, tm.end()):
            return True
    return False


def _negated(text: str, m) -> bool:
    lo, hi = _clause_bounds(text, m.start(), m.end())
    before, after = text[lo:m.start()], text[m.end():hi]
    if _pre_negated(before):
        return not _POST_RESULT.match(after)
    return _post_negated(before, after)


DEPLOY_CLAIM = re.compile(
    r"\b(deploy\w*|clinical use|ready for (?:clinical|practice)|integrat\w+ into (?:practice|workflow)|"
    r"assist\w* (?:radiologists|clinicians)|in practice)\b", re.IGNORECASE)


def has(text: str, concept: str) -> bool:
    """True when the concept is stated affirmatively at least once.

    For satisfying concepts a match inside a negated clause ("no expert review",
    "hallucination was not assessed") does not count; trigger concepts match plainly."""
    for m in re.finditer(SAT[concept], text, re.IGNORECASE):
        if concept in TRIGGER_CONCEPTS or not _negated(text, m):
            return True
    return False


def analyze(plan: str, task: str) -> dict:
    text = Path(plan).read_text(encoding="utf-8")
    claims = []

    def add(verdict, severity, detail):
        claims.append({"verdict": verdict, "severity": severity, "detail": detail, "where": Path(plan).name})

    is_gen = task == "report_generation"
    is_vqa = task == "vqa"

    if is_gen:
        if has(text, "ngram") and not has(text, "clinical_metric"):
            add("NGRAM_ONLY", "Major",
                "report-generation quality is reported with n-gram overlap (BLEU/ROUGE) but no "
                "clinical-efficacy metric (RadGraph-F1 / CheXbert / RadCliQ) — n-gram overlap is weakly "
                "correlated with clinical correctness")
        if not has(text, "reference_standard"):
            add("REFERENCE_STANDARD_MISSING", "Major",
                "no adjudicated expert reference-standard statement for the generated reports")
        if not has(text, "reader_study"):
            sev = "Major" if DEPLOY_CLAIM.search(text) else "Minor"
            add("READER_STUDY_MISSING", sev,
                "no blinded clinical reader study with an error taxonomy" +
                (" for a deployment/utility claim" if sev == "Major" else " (automated metrics only)"))

    if is_gen or is_vqa:
        if not has(text, "faithfulness"):
            add("FAITHFULNESS_MISSING", "Major",
                "no faithfulness / hallucination / false-premise evaluation — a fluent answer is not a "
                "faithful one")

    if has(text, "benchmark") and not has(text, "contamination"):
        add("CONTAMINATION_UNADDRESSED", "Major",
            "a public clinical benchmark is named but pretraining contamination is not addressed "
            "(training cutoff vs benchmark release, a held-out/post-cutoff set, or a contamination probe)")

    if not (has(text, "prompt") and has(text, "decoding") and has(text, "multirun")):
        missing = [m for m, c in (("prompt", "prompt"), ("temperature/seed", "decoding"),
                                  ("multi-run variance", "multirun")) if not has(text, c)]
        add("PROMPT_PROVENANCE_MISSING", "Minor",
            "prompt-sensitivity provenance incomplete — missing: " + ", ".join(missing))

    if (is_vqa or task == "classification") and not has(text, "answer_match"):
        add("ANSWER_MATCHING_MISSING", "Minor",
            "no answer-matching rule stated (exact / normalised / LLM-judge) for free-text answers")

    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {"plan": plan, "task": task, "claims": claims,
            "summary": {"n_claims": len(claims), "n_major": n_major,
                        "verdict": "MAJOR_CANDIDATE" if n_major else "OK"}}


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | evaluation plan covers the required MLLM axes |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="LLM/MLLM clinical-evaluation completeness gate.")
    ap.add_argument("--plan", required=True, help="evaluation plan / methods markdown")
    ap.add_argument("--task", required=True, choices=["report_generation", "vqa", "classification"])
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    if not Path(args.plan).is_file():
        sys.stderr.write(f"ERROR: --plan not found: {args.plan}\n")
        return 2
    result = analyze(args.plan, args.task)

    if not args.quiet:
        print("=" * 41)
        print(" MLLM Evaluation Completeness")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        print(f"MAJOR candidate: {s['n_major']} evaluation-completeness gap(s)." if s["n_major"]
              else "OK: evaluation plan covers the required MLLM axes.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_mllm_eval_completeness", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())

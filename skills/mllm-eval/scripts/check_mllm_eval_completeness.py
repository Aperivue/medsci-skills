#!/usr/bin/env python3
"""LLM / MLLM clinical-evaluation completeness gate (mllm-eval).

A task-aware presence linter for the methods / plan of an LLM or multimodal-LLM
clinical evaluation. It flags the axes a defensible evaluation must cover that are
**absent** from the plan text — it is a presence check on the protocol (the analogue
of check_model_card_complete for documentation), not a judge of results. Conservative:
each verdict fires only when its concept is clearly missing from the text. A concept that
clears a check counts only when stated affirmatively: a mention that is itself negated
("no expert review", "hallucination was not assessed", "Hallucination: not assessed") does
not satisfy it, while a negation elsewhere in the sentence ("studies without prior imaging
were adjudicated") does not cancel it. The
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

# Negation is bounded to the concept's own phrase, not the whole sentence: an unrelated
# negation elsewhere in the sentence ("Studies without prior imaging were adjudicated",
# "Because the data are not public, contamination was probed", "Faithfulness, which was not
# part of prior work, is assessed") must not cancel an affirmative mention.
#
# Hard clause boundaries: sentence punctuation (not decimal points), a paragraph break or a
# new list item / heading / table row (a wrapped prose line is NOT a break), and contrastive
# conjunctions ("no BLEU but RadGraph-F1" -> RadGraph is affirmed).
_CLAUSE_BREAK = re.compile(r"(?<!\d)[.;!?](?!\d)|\n\s*\n|\n[ \t]*(?:[-*+#>|]|\d+[.)])|\b(?:but|whereas|however|although|though|while|except)\b",
                           re.IGNORECASE)
# Soft boundaries close the negation window as well: a comma, a parenthesis, a relative
# pronoun and "and" ("no BLEU and a reader study" -> the reader study is affirmed). "or"/"nor"
# are not boundaries: "no reader study or expert review" negates both.
_SOFT_BREAK = re.compile(r"[,()\[\]]|\b(?:and|which|who|whom|whose|that|where|when|because|since|if)\b",
                         re.IGNORECASE)
# After the concept only a parenthesis or a subordinate clause closes the window: a list or a
# coordinated subject ("The prompt, temperature and runs are not reported") stays in scope.
_POST_SOFT_BREAK = re.compile(r"[()\[\]]|\b(?:which|who|whom|whose|that|where|when|because|since|if)\b",
                              re.IGNORECASE)
# A negator governing the concept: at most _PRE_WINDOW words before it, with no finite
# auxiliary in between ("Reports with no acute findings were checked for hallucinations": a
# verb separates "no" from "hallucinations", so they are not negated).
_PRE_WINDOW = 4
_NEGATOR = re.compile(r"\b(?:no|not|without|never|neither|nor|none|lacks?|lacking|absent|omit(?:s|ted)?)\b|n['\u2019]t\b",
                      re.IGNORECASE)
_WORD = re.compile(r"[\w'\u2019/+-]+")
_AUX = re.compile(r"^(?:is|are|was|were|be|been|being|has|have|had)$", re.IGNORECASE)
# Not a negation: "not only", "no more/less/fewer/later than", "whether or not"; and
# "no evidence of X" / "found no X" report a RESULT of evaluating X.
_NEG_EXEMPT = re.compile(r"^(?:not|no)\s+(?:only|more|less|fewer|later|earlier|longer|greater)\b|"
                         r"^no\s+(?:evidence|signs?|indication)\b", re.IGNORECASE)
_PRE_RESULT = re.compile(r"\b(?:found|observed|detected|identified|showed|revealed|demonstrated)\s+$|"
                         r"\bor\s+$", re.IGNORECASE)
# A negation right after the concept that says the axis itself was NOT DONE ("Hallucination
# was not assessed", "the prompt and temperature are not reported", "Hallucination: not
# assessed", "| Hallucination | n/a |", "Hallucination assessment: none", "Hallucination
# evaluation is out of scope"). The negated word must be an absence verb, so a negated property
# ("expert review is not blinded") or a result ("contamination was not detected", "the rate
# was not significantly different") leaves the concept affirmed.
_ABSENCE = (r"(?:\w+ly\s+)?(?:assess|evaluat|perform|report|done|do\b|use|used|using|includ|conduct|"
            r"measur|availab|plann|plan\b|consider|address|appl|disclos|examin|check|provid|undertak|"
            r"collect|obtain|quantif|test|studi|stud|scor|record|specif|state[ds]?\b|captur|analy[sz]|"
            r"investigat|implement|attempt|feasib|possib|carr|run|ran\b|account|control|explor)\w*")
# The concept is the subject of a passive / copular "not": an active verb with an object ("The
# reader study did not include trainees") describes the axis, it does not withdraw it.
_POST_NEG = re.compile(
    r"^(?:\s*,?\s*[\w'\u2019/+-]+){0,6}?\s*(?:"
    r"\b(?:(?:was|were|is|are|be|been)\s+(?:not|never)|(?:has|have|had)\s+(?:not|never)\s+been|"
    r"(?:will|shall|could|can|may|would|should)\s+(?:not|never)\s+be|cannot\s+be|"
    r"(?:wasn|weren|isn|aren)['\u2019]t|(?:hasn|haven|hadn)['\u2019]t\s+been|(?:won|can|couldn)['\u2019]t\s+be)"
    r"\s+" + _ABSENCE + r"|"
    r"\s*[:|]\s*(?:not\s+(?:" + _ABSENCE + r"|applicable)|none\s*(?:[.;|]|$)|n/?a\b)|"
    r"\b(?:is|are|was|were|remains?)\s+(?:considered\s+)?(?:out of scope|beyond the scope|outside the scope)\b)",
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


def _pre_negated(before: str) -> bool:
    """A negator within _PRE_WINDOW words before the concept, nothing but its own phrase between."""
    soft = list(_SOFT_BREAK.finditer(before))
    if soft:
        before = before[soft[-1].end():]
    negs = list(_NEGATOR.finditer(before))
    if not negs:
        return False
    neg = negs[-1]
    between = _WORD.findall(before[neg.end():])
    if len(between) > _PRE_WINDOW or any(_AUX.match(w) for w in between):
        return False
    if _NEG_EXEMPT.match(before[neg.start():]) or _PRE_RESULT.search(before[:neg.start()]):
        return False
    return True


def _negated(text: str, m) -> bool:
    lo, hi = _clause_bounds(text, m.start(), m.end())
    before, after = text[lo:m.start()], text[m.end():hi]
    if _pre_negated(before):
        return True
    soft = _POST_SOFT_BREAK.search(after)
    if soft:
        after = after[:soft.start()]
    return _POST_NEG.match(after) is not None


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

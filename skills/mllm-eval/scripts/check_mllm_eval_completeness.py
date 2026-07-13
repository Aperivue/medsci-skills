#!/usr/bin/env python3
"""LLM / MLLM clinical-evaluation completeness gate (mllm-eval).

A task-aware presence linter for the methods / plan of an LLM or multimodal-LLM
clinical evaluation. It flags the axes a defensible evaluation must cover that are
**absent** from the plan text — it is a presence check on the protocol (the analogue
of check_model_card_complete for documentation), not a judge of results. Conservative:
each verdict fires only when its concept is clearly missing from the text.

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

# concept -> regex of any phrasing that SATISFIES it (searched case-insensitively)
SAT = {
    "ngram": r"\b(bleu|rouge|meteor|cider)\b",
    "clinical_metric": r"\b(radgraph|chexbert|chexpert[- ]?label|radcliq|green|f1[\w-]*chexpert|"
                       r"clinical efficacy|factual(?:ity| correctness)|entity[- ]?relation)\b",
    "faithfulness": r"\b(faithful(?:ness)?|hallucinat\w+|atomic[- ]?fact|false[- ]?premise|"
                    r"fabricat\w+|med-?hal|medvh|med-?halt|confabulat\w+|ungrounded|groundedness|"
                    r"unsupported|clinical(?:ly)?[- ]?grounded|evidence[- ]?support\w*)\b"
                    r"|not supported by the image",
    "reference_standard": r"\b(reference standard|reference reports?|adjudicat\w+|gold[- ]?standard|"
                          r"expert(?:[- ]?annotat\w+| review| radiologist)|consensus|"
                          r"ground[- ]?truth|radiolog\w+[- ]?author\w+)\b",
    "benchmark": r"\b(vqa-?rad|slake|mimic-?cxr|medqa|pmc-?vqa|path-?vqa|openi|pubmedqa|"
                 r"public benchmark)\b",
    "contamination": r"\b(contaminat\w+|(?:training|pre-?training|knowledge)[- ]cut[- ]?off|"
                     r"held[- ]?out|post[- ]?cut[- ]?off|canary|memoris\w+|memoriz\w+|"
                     r"data leakage)\b",
    "reader_study": r"reader study|blinded read\w+|clinical reader|radiologist review|"
                    r"human evaluation|expert rating|acceptability scale|likert|"
                    r"\d+\s+(?:radiologists?|readers?|clinicians?)[^.\n]{0,60}"
                    r"(?:rated|scored|graded|read|review)|"
                    r"(?:masked|blinded)[^.\n]{0,40}(?:graded|scored|rated)",
    "prompt": r"\b(prompt)\b",
    "decoding": r"\b(temperature|top-?p|top-?k|seed|greedy|sampling)\b",
    "multirun": r"\b(\d+\s*runs|repeated runs|multiple runs|across runs|run-to-run|"
                r"mean\s*(?:±|\+/-|\+-)\s|standard deviation|variance|bootstrap)\b",
    "answer_match": r"\b(exact match|normali[sz]ed match|answer matching|llm[- ]?as[- ]?judge|"
                    r"llm judge|string match|keyword match|semantic (?:equivalence|match\w*)|"
                    r"clinician[- ]?adjudicat\w+|adjudicated (?:correct|equivalent)|"
                    r"human[- ]?judg\w+)\b",
}

DEPLOY_CLAIM = re.compile(
    r"\b(deploy\w*|clinical use|ready for (?:clinical|practice)|integrat\w+ into (?:practice|workflow)|"
    r"assist\w* (?:radiologists|clinicians)|in practice)\b", re.IGNORECASE)


def has(text: str, concept: str) -> bool:
    return re.search(SAT[concept], text, re.IGNORECASE) is not None


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

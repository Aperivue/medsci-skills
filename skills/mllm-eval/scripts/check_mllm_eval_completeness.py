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
  --manifest  eval_manifest.json: the axes DECLARED as structured fields (preferred;
              template in templates/eval_manifest.json, schema in
              references/eval_manifest_schema.md). Each value must come from the
              field's allow-list, or be "other:<description>"; anything else, a wrong
              type or an unknown key exits 2 and names the field. The verdicts above
              fire on what is declared (a missing field or "none" = not covered).
              The gate checks the declaration, not that the work was done.
  --plan      the evaluation plan / methods markdown (prose mode). Prose mode only
              tests that a keyword is present (no negation or sense), and says so.
              With --manifest, --plan is not read.
  --task      report_generation | vqa | classification (required in prose mode; in
              manifest mode it must match the manifest's "task" if given).

OUTPUT
  A table (stdout) and, with --out, a JSON artifact:
    {plan|manifest, mode, task, claims[{verdict, severity, detail, where}], summary}
  Manifest mode adds UNLISTED_METHOD (Minor) for each "other:<description>" value.

Stdlib-only (re / json / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import math
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
    """Prose mode: keyword presence over the whole plan text."""
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
    return {"plan": plan, "mode": "prose", "task": task, "claims": claims,
            "summary": {"n_claims": len(claims), "n_major": n_major,
                        "verdict": "MAJOR_CANDIDATE" if n_major else "OK"}}


# --------------------------------------------------------------------------- manifest mode
# Allow-lists (compared after _key(): lower case, '-' and spaces -> '_'). Every entry is a
# metric or method named in references/evaluation_axes.md (reference standard: SKILL.md
# Phase 2). "none" means "declared absent"; "other:<description>" covers anything else.
TASKS = {"report_generation", "vqa", "classification"}
LEXICAL = {"bleu", "rouge", "meteor", "cider"}
CLINICAL = {"radgraph_f1", "chexbert_f1", "chexpert_labeler", "radcliq", "green"}
FAITHFULNESS = {"atomic_fact_decomposition", "false_premise_probe", "med_halt", "medvh"}
# Only an adjudicated expert reference clears the axis; the other two are accepted values that
# SKILL.md Phase 2 names as NOT acceptable ("not a single unverified report or a model-derived label").
REFERENCE_OK = {"adjudicated_expert"}
REFERENCE = REFERENCE_OK | {"single_unverified_report", "model_derived_label"}
CONTAMINATION = {"cutoff_vs_release_date", "held_out_set", "canary", "perturbed_duplicate_gap",
                 "membership_test"}
ANSWER_MATCH = {"exact", "normalised", "llm_as_judge"}
ALIASES = {"normalized": "normalised", "rouge_l": "rouge", "rouge_1": "rouge", "rouge_2": "rouge"}
MIN_RUNS = 3   # SKILL.md Phase 4: ">= 3 runs with variance"

TOP_KEYS = {"task", "metrics", "faithfulness", "reference_standard", "benchmarks",
            "contamination", "reader_study", "prompt", "decoding", "runs",
            "answer_matching", "claims", "notes"}
SUB_KEYS = {
    "metrics": {"lexical", "clinical"},
    "faithfulness": {"methods"},
    "reference_standard": {"type"},
    "contamination": {"methods"},
    "reader_study": {"performed", "n_readers", "blinded"},
    "prompt": {"template_released"},
    "decoding": {"temperature", "top_p", "seed", "greedy"},
    "runs": {"n"},
    "answer_matching": {"method"},
    "claims": {"clinical_deployment"},
}


class ManifestError(ValueError):
    pass


def _reject_constant(name: str):
    raise ManifestError(f"{name} is not a valid JSON number")


def _key(v: str) -> str:
    k = re.sub(r"[\s\-]+", "_", v.strip().lower())
    return ALIASES.get(k, k)


OTHER = re.compile(r"^\s*other\s*:(.*)$", re.IGNORECASE | re.DOTALL)


def _enum(value, allowed: set, where: str, unlisted: list) -> str:
    """One allow-listed value, "none", or "other:<description>"; anything else is an error."""
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{where}: expected a non-empty string, got {value!r}")
    k = _key(value)
    if k == "none" or k in allowed:
        return k
    om = OTHER.match(value)
    if om:
        if not om.group(1).strip():
            raise ManifestError(f"{where}: 'other:' needs a description")
        if _key(om.group(1)) == "none":
            return "none"
        unlisted.append((where, value.strip()))
        return "other"
    raise ManifestError(f"{where}: {value!r} is not one of {sorted(allowed | {'none'})} "
                        f"(use \"other:<description>\" for a method not listed)")


def _enum_list(value, allowed: set, where: str, unlisted: list) -> list:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        raise ManifestError(f"{where}: expected a list of strings, got {type(value).__name__}")
    out = [_enum(v, allowed, f"{where}[{i}]", unlisted) for i, v in enumerate(value)]
    if "none" in out and len(out) > 1:
        raise ManifestError(f"{where}: 'none' cannot be combined with other values")
    return [v for v in out if v != "none"]


def _obj(m: dict, key: str) -> dict:
    v = m.get(key)
    if v is None:
        return {}
    if not isinstance(v, dict):
        raise ManifestError(f"{key}: expected an object, got {type(v).__name__}")
    extra = set(v) - SUB_KEYS[key]
    if extra:
        raise ManifestError(f"{key}: unknown key(s) {sorted(extra)}; allowed {sorted(SUB_KEYS[key])}")
    return v


def _bool(v, where: str):
    if v is not None and not isinstance(v, bool):
        raise ManifestError(f"{where}: expected true/false, got {v!r}")
    return v


def _int(v, where: str, minimum: int):
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, int) or v < minimum:
        raise ManifestError(f"{where}: expected an integer >= {minimum}, got {v!r}")
    return v


def analyze_manifest(path: str, task_arg: str | None) -> dict:
    try:
        m = json.loads(Path(path).read_text(encoding="utf-8"),
                       parse_constant=_reject_constant)
    except (OSError, ValueError, RecursionError) as e:   # ValueError covers JSONDecodeError
        raise ManifestError(f"cannot read manifest: {e}")
    if not isinstance(m, dict):
        raise ManifestError("manifest must be a JSON object")
    extra = set(m) - TOP_KEYS
    if extra:
        raise ManifestError(f"unknown top-level key(s) {sorted(extra)}; allowed {sorted(TOP_KEYS)}")
    unlisted: list = []

    task = m.get("task")
    if task is None:
        if task_arg is None:
            raise ManifestError("task: missing (set it in the manifest or pass --task)")
        task = task_arg
    else:
        task = _enum(task, TASKS, "task", [])
        if task not in TASKS:
            raise ManifestError("task: must be report_generation, vqa or classification")
        if task_arg is not None and task_arg != task:
            raise ManifestError(f"task: manifest says {task!r} but --task is {task_arg!r}")

    metrics = _obj(m, "metrics")
    lexical = _enum_list(metrics.get("lexical"), LEXICAL, "metrics.lexical", unlisted)
    clinical = _enum_list(metrics.get("clinical"), CLINICAL, "metrics.clinical", unlisted)
    faith_obj = _obj(m, "faithfulness")
    faith = _enum_list(faith_obj.get("methods"), FAITHFULNESS, "faithfulness.methods", unlisted)
    ref_obj = _obj(m, "reference_standard")
    ref = (_enum(ref_obj["type"], REFERENCE, "reference_standard.type", unlisted)
           if ref_obj.get("type") is not None else None)
    bench = m.get("benchmarks")
    if bench is None:
        bench = []
    if isinstance(bench, str):
        bench = [bench]
    if not isinstance(bench, list) or not all(isinstance(b, str) and b.strip() for b in bench):
        raise ManifestError("benchmarks: expected a list of benchmark names")
    if any(_key(b) == "none" for b in bench):
        if len(bench) > 1:
            raise ManifestError("benchmarks: 'none' cannot be combined with other values")
        bench = []
    cont_obj = _obj(m, "contamination")
    cont = _enum_list(cont_obj.get("methods"), CONTAMINATION, "contamination.methods", unlisted)
    rs = _obj(m, "reader_study")
    rs_done = _bool(rs.get("performed"), "reader_study.performed")
    _int(rs.get("n_readers"), "reader_study.n_readers", 1)   # recorded, not gated
    rs_blind = _bool(rs.get("blinded"), "reader_study.blinded")
    pr = _obj(m, "prompt")
    prompt_ok = _bool(pr.get("template_released"), "prompt.template_released")
    dec = _obj(m, "decoding")
    temp = dec.get("temperature")
    if temp is not None and (isinstance(temp, bool) or not isinstance(temp, (int, float))
                             or not math.isfinite(temp) or temp < 0):
        raise ManifestError(f"decoding.temperature: expected a number >= 0, got {temp!r}")
    greedy = _bool(dec.get("greedy"), "decoding.greedy")
    _int(dec.get("seed"), "decoding.seed", 0)   # recorded, not gated
    top_p = dec.get("top_p")
    if top_p is not None and (isinstance(top_p, bool) or not isinstance(top_p, (int, float))
                              or not 0 < top_p <= 1):
        raise ManifestError(f"decoding.top_p: expected a number in (0, 1], got {top_p!r}")
    runs = _int(_obj(m, "runs").get("n"), "runs.n", 1)
    am_obj = _obj(m, "answer_matching")
    am = (_enum(am_obj["method"], ANSWER_MATCH, "answer_matching.method", unlisted)
          if am_obj.get("method") is not None else None)
    deploy = _bool(_obj(m, "claims").get("clinical_deployment"), "claims.clinical_deployment")

    claims = []

    def add(verdict, severity, detail, where):
        claims.append({"verdict": verdict, "severity": severity, "detail": detail, "where": where})

    def why(declared_none: bool) -> str:
        return "declared none" if declared_none else "not declared"

    is_gen = task == "report_generation"
    is_vqa = task == "vqa"

    if is_gen:
        if lexical and not clinical:
            add("NGRAM_ONLY", "Major",
                "n-gram overlap (" + ", ".join(lexical) + ") is declared but no clinical-efficacy "
                "metric (RadGraph-F1 / CheXbert / RadCliQ / GREEN) — n-gram overlap is weakly "
                "correlated with clinical correctness", "metrics.clinical")
        if ref in (None, "none"):
            add("REFERENCE_STANDARD_MISSING", "Major",
                f"no reference standard for the generated reports ({why(ref == 'none')})",
                "reference_standard.type")
        elif ref not in REFERENCE_OK and ref != "other":
            add("REFERENCE_STANDARD_MISSING", "Major",
                f"the declared reference standard ({ref}) is not an adjudicated expert reference",
                "reference_standard.type")
        if rs_done is not True or rs_blind is not True:
            sev = "Major" if deploy is True else "Minor"
            if rs_done is True:
                state = "declared not blinded" if rs_blind is False else "blinding not declared"
            else:
                state = why(rs_done is False)
            add("READER_STUDY_MISSING", sev,
                f"no blinded clinical reader study ({state})" +
                (" for a declared clinical-deployment claim" if sev == "Major"
                 else " (automated metrics only)"),
                "reader_study.blinded" if rs_done is True else "reader_study.performed")

    if (is_gen or is_vqa) and not faith:
        add("FAITHFULNESS_MISSING", "Major",
            "no faithfulness / hallucination / false-premise evaluation "
            f"({why('faithfulness' in m and faith_obj.get('methods') is not None)}) — a fluent "
            "answer is not a faithful one", "faithfulness.methods")

    if bench and not cont:
        add("CONTAMINATION_UNADDRESSED", "Major",
            "public benchmark(s) " + ", ".join(bench) + " declared but no contamination check "
            f"({why(cont_obj.get('methods') is not None)}): cutoff vs release date, a held-out / "
            "post-cutoff set, canary strings, a perturbed-duplicate gap or a membership test",
            "contamination.methods")

    missing = []
    if prompt_ok is not True:
        missing.append("prompt template released")
    if temp is None and greedy is not True:
        missing.append("temperature (or greedy decoding)")
    if runs is None or runs < MIN_RUNS:
        missing.append(f">= {MIN_RUNS} runs" + (f" (declared {runs})" if runs is not None else ""))
    if missing:
        add("PROMPT_PROVENANCE_MISSING", "Minor",
            "prompt-sensitivity provenance incomplete — missing: " + ", ".join(missing),
            "prompt / decoding / runs")

    if (is_vqa or task == "classification") and am in (None, "none"):
        add("ANSWER_MATCHING_MISSING", "Minor",
            f"no answer-matching rule ({why(am == 'none')}): exact / normalised / LLM-as-judge",
            "answer_matching.method")

    for where, value in unlisted:
        add("UNLISTED_METHOD", "Minor",
            f"{value!r} is not on the allow-list; counted as covering the axis, but check by eye "
            "that it is a recognised method", where)

    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {"manifest": path, "mode": "manifest", "task": task, "claims": claims,
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
    ap.add_argument("--manifest", help="eval_manifest.json with the declared axes (preferred)")
    ap.add_argument("--plan", help="evaluation plan / methods markdown (prose mode)")
    ap.add_argument("--task", choices=["report_generation", "vqa", "classification"])
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    if args.manifest is not None:
        if not Path(args.manifest).is_file():
            sys.stderr.write(f"ERROR: --manifest not found: {args.manifest}\n")
            return 2
        if args.plan is not None:
            sys.stderr.write("NOTE: --manifest given; --plan is not read\n")
        try:
            result = analyze_manifest(args.manifest, args.task)
        except ManifestError as e:
            sys.stderr.write(f"ERROR: {args.manifest}: {e}\n")
            return 2
    elif args.plan is not None:
        if args.task is None:
            sys.stderr.write("ERROR: --task is required with --plan\n")
            return 2
        if not Path(args.plan).is_file():
            sys.stderr.write(f"ERROR: --plan not found: {args.plan}\n")
            return 2
        result = analyze(args.plan, args.task)
    else:
        sys.stderr.write("ERROR: pass --manifest (preferred) or --plan\n")
        return 2

    if not args.quiet:
        print("=" * 41)
        print(" MLLM Evaluation Completeness")
        print("=" * 41)
        print(render(result))
        print()
        if result["mode"] == "prose":
            print("PROSE_MODE: keyword presence only (negation and word sense are not read); "
                  "declare the axes in --manifest for a field-level check.")
        else:
            print("Manifest mode: checks what is declared, not that the work was done.")
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

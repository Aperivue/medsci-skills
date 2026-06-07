#!/usr/bin/env python3
"""E2 - Deterministic gates vs a generic LLM self-check (SHIP, NOT_RUN default).

Compares the deterministic detectors against a single fixed generic review
prompt on the SAME seeded-defect variants used by E1. Non-deterministic and
API-dependent: it gracefully records NOT_RUN unless --with-llm is passed AND an
Anthropic API key + SDK are available. arXiv submits deterministic results only;
this harness ships runnable for post-release execution.

Framing is strictly "detection under one fixed generic prompt, one model, one
date" - never a universal model-superiority claim, and never a manuscript-quality
or distinguishability claim (Paper-2 boundary).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0]))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "h1_seeded_defects"))
from _harness.runlog import RunLogger  # noqa: E402
from _harness.workspace import REPO_ROOT  # noqa: E402

PROMPT_PATH = HERE / "prompt.txt"
MODEL = "claude-opus-4-8"  # intended model for a future run; not invoked by default


def _have_runner() -> tuple[bool, str]:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False, "ANTHROPIC_API_KEY not set"
    try:
        import anthropic  # noqa: F401
    except Exception:
        return False, "anthropic SDK not importable"
    return True, ""


def _mi_clear(executed: bool, reason: str = "") -> dict:
    prompt_text = PROMPT_PATH.read_text(encoding="utf-8")
    import hashlib
    return {
        "_note": "MI-CLEAR-LLM-inspired logging for the E2 LLM comparator.",
        "executed": executed,
        "not_run_reason": reason,
        "1_model_identification": {
            "provider": "Anthropic",
            "model_name": MODEL,
            "access_mode": "API (messages)",
            "api_endpoint": "https://api.anthropic.com",
            "query_datetime": datetime.now().isoformat(timespec="seconds") if executed else None,
        },
        "2_stochasticity": {
            "temperature": "not set (parameter deprecated for this model; provider default sampling)",
            "top_p": None,
            "attempts_per_prompt": 1,
            "repeat_policy": "single sample, provider default sampling (temperature not configurable for this model)",
        },
        "3_full_prompt": {
            "prompt_path": str(PROMPT_PATH.relative_to(REPO_ROOT)),
            "prompt_sha256": hashlib.sha256(prompt_text.encode()).hexdigest(),
            "verbatim": prompt_text,
        },
        "4_execution": {
            "sessions": "independent session per variant",
            "batching": "sequential",
            "post_processing": "deterministic signature adjudication (adjudicate.py)",
            "error_handling": "record NOT_RUN on missing key/SDK",
        },
        "5_prompt_development": {
            "fixed": True,
            "tuned_on_test_data": False,
            "revisions": 0,
            "note": "generic prompt fixed before any variant was seen; not tuned per defect",
        },
        "6_test_data_independence": {
            "test_data": "synthetic seeded defects (E1 variants)",
            "contamination": "none; variants are programmatic mutations, not used for prompt tuning",
        },
        "redaction": "raw outputs stored without API keys/account IDs",
    }


def _write_not_run(log, qc_dir, not_run_reason, args, out) -> int:
    (qc_dir / "mi_clear_llm_llm_baseline.json").write_text(
        json.dumps(_mi_clear(False, not_run_reason), indent=2, ensure_ascii=False), encoding="utf-8")
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["status", "reason", "model", "note"])
        w.writerow(["NOT_RUN", not_run_reason, MODEL,
                    "LLM comparator specified and archived; not analyzed in this release"])
    print(f"E2 status: NOT_RUN ({not_run_reason})")
    log.log_component(
        component_type="llm_baseline",
        model_name=MODEL, command_args=["--with-llm"] if args.with_llm else [],
        expected_reproducibility="non-deterministic",
        rerun_policy="run with ANTHROPIC_API_KEY + anthropic SDK; single sample, provider default sampling",
        input_paths=[PROMPT_PATH], output_path=out,
    )
    log.finalize(metrics_path=out,
                 limitations="LLM comparator NOT executed for this release; harness and "
                             "MI-CLEAR-LLM logging schema are shipped for post-release use.",
                 repro_hash_extra=[out])
    print(f"run dir: {log.run_dir}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="E2 LLM self-check comparator (NOT_RUN by default)")
    ap.add_argument("--with-llm", action="store_true",
                    help="attempt to actually call the model (requires ANTHROPIC_API_KEY + anthropic SDK)")
    args = ap.parse_args()

    log = RunLogger.start("E2")
    runnable, reason = _have_runner()
    do_run = args.with_llm and runnable

    qc_dir = log.run_dir / "qc"
    qc_dir.mkdir(exist_ok=True)
    out = log.run_dir / "metrics.csv"

    if not do_run:
        not_run_reason = reason if args.with_llm else "default mode (pass --with-llm to attempt execution)"
        return _write_not_run(log, qc_dir, not_run_reason, args, out)

    # Guard the execution path: any failure (auth, model, network) degrades to a
    # clean NOT_RUN rather than a traceback.
    try:
        return _execute(log, qc_dir, args, out)
    except Exception as e:  # noqa: BLE001
        return _write_not_run(log, qc_dir, f"execution error: {type(e).__name__}", args, out)


def _execute(log, qc_dir, args, out) -> int:
    # --- actual execution path (post-release; not exercised in the default suite) ---
    import anthropic  # type: ignore
    from registry import REGISTRY  # noqa: E402
    from inject import INJECTORS  # noqa: E402
    from adjudicate import adjudicate  # noqa: E402
    from _harness.workspace import golden_inputs, temp_demo, temp_copy

    client = anthropic.Anthropic()
    prompt_tmpl = PROMPT_PATH.read_text(encoding="utf-8")
    demos = golden_inputs()
    fixtures = {"fixture": HERE.parents[0] / "h1_seeded_defects" / "fixtures" / "citation",
                "fixture_artifact": HERE.parents[0] / "h1_seeded_defects" / "fixtures" / "artifact"}
    llm_dir = log.run_dir / "llm_outputs"
    llm_dir.mkdir(exist_ok=True)
    rows = []
    for spec in REGISTRY:
        if spec.network_required:
            continue
        for demo in spec.demos:
            ctx = temp_copy(fixtures[demo]) if demo in fixtures else temp_demo(demos[demo])
            with ctx as root:
                target = root / spec.target_file
                outcome = INJECTORS[spec.injector](target, spec.injector_args)
                if outcome.status != "INJECTED":
                    continue
                # Resolve the manuscript a generic reviewer would read:
                #  - .md target -> the injected manuscript/fixture itself
                #  - fixture dir -> its clean.md
                #  - demo with a non-.md (code) target -> the UNCHANGED manuscript;
                #    a code-level defect is not visible in the prose, so a
                #    manuscript-text reviewer legitimately cannot see it (a real
                #    ablation finding, not an error).
                if target.suffix == ".md":
                    man = target
                elif (root / "clean.md").exists():
                    man = root / "clean.md"
                else:
                    man = root / "manuscript" / "manuscript.md"
                text = man.read_text(encoding="utf-8")[:120000]
                resp = client.messages.create(
                    model=MODEL, max_tokens=1500,
                    messages=[{"role": "user", "content": prompt_tmpl.replace("{manuscript}", text)}],
                )
                body = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
                body = re.sub(r"sk-[A-Za-z0-9_-]{8,}", "[REDACTED]", body)
                (llm_dir / f"{spec.defect_id}_{demo}.txt").write_text(body, encoding="utf-8")
                rows.append({"defect_id": spec.defect_id, "demo": demo,
                             "llm_detected": "yes" if adjudicate(spec.defect_id, body) else "no"})

    out = log.run_dir / "metrics.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["defect_id", "demo", "llm_detected"])
        w.writeheader()
        w.writerows(rows)
    (qc_dir / "mi_clear_llm_llm_baseline.json").write_text(
        json.dumps(_mi_clear(True), indent=2, ensure_ascii=False), encoding="utf-8")
    det = sum(1 for r in rows if r["llm_detected"] == "yes")
    print(f"E2 executed: LLM named {det}/{len(rows)} injected defects (fixed generic prompt, {MODEL})")
    log.log_component(
        component_type="llm_baseline", model_name=MODEL, command_args=["--with-llm"],
        expected_reproducibility="non-deterministic",
        rerun_policy="single sample, provider default sampling (temperature not configurable for this model); output not guaranteed identical across runs",
        input_paths=[PROMPT_PATH], output_path=out,
    )
    log.finalize(metrics_path=out,
                 limitations="Detection under ONE fixed generic prompt, one model, one date. "
                             "Not a universal model-superiority claim; not a quality/distinguishability claim.",
                 api_cost_usd=None)
    print(f"run dir: {log.run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""E9 - Recursive self-review convergence (SHIP, NOT_RUN default).

Tool-process validation: does the self-review loop reduce its OWN actionable
findings over bounded rounds? This is internal rubric / self-review QC
convergence - NOT external manuscript quality, reviewer acceptance,
distinguishability, or human-competitive quality (Paper-2 boundary).

The loop is LLM/agent-driven, so it is non-deterministic and runner-dependent.
Without a configured runner (see runner.py) it records NOT_RUN. When run, it
compares three conditions per input: single-pass, --fix loop (bounded), and
--panel (diagnose-only; the skill forbids --panel + --fix, so panel reports
finding-set depth under fixed lenses, not a fix loop). All inputs are temp
copies; the SSOT is never mutated.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0]))
sys.path.insert(0, str(HERE))
from _harness.runlog import RunLogger  # noqa: E402
from _harness.workspace import REPO_ROOT, golden_inputs, temp_demo  # noqa: E402
from _harness import hashing  # noqa: E402
from runner import self_review_runner, get_runner  # noqa: E402
from stop_rule import should_stop, actionable_majors, MAX_ROUNDS_DEFAULT  # noqa: E402

CONDITIONS = ["single", "fix", "panel"]


def _counts(findings):
    sev = lambda s: sum(1 for f in findings if str(f.get("severity", "")).lower().startswith(s))
    fix_true = sum(1 for f in findings if f.get("fixable_by_ai"))
    return {
        "major": sev("major") + sev("fatal"), "minor": sev("minor"),
        "fixable_true": fix_true, "fixable_false": len(findings) - fix_true,
        "actionable_major": actionable_majors(findings),
    }


def run_condition(demo_id, condition, log, max_rounds) -> dict:
    """Run one condition to convergence on a temp copy. Returns a summary row."""
    g = golden_inputs()[demo_id]
    rounds_dir = log.run_dir / "rounds" / f"{demo_id}_{condition}"
    rounds_dir.mkdir(parents=True, exist_ok=True)
    with temp_demo(g) as root:
        man = root / "manuscript" / "manuscript.md"
        init_verdict = init_score = None
        last_verdict = last_score = None
        last_findings = []
        rounds_run = 0
        stop_reason = ""
        cap = 1 if condition in ("single", "panel") else max_rounds
        for rnd in range(1, cap + 1):
            mode = {"single": "single", "fix": "fix", "panel": "panel"}[condition]
            in_hash = hashing.sha256_file(man)
            result = self_review_runner(man, mode)
            if result is None:
                return {"status": "NOT_RUN"}
            rounds_run = rnd
            findings = result.get("findings", [])
            verdict = result.get("verdict", "")
            score = result.get("overall_score")
            if init_verdict is None:
                init_verdict, init_score = verdict, score
            last_verdict, last_score, last_findings = verdict, score, findings
            # apply fix output (temp copy only) for the fix loop
            if condition == "fix" and result.get("output_manuscript"):
                from _harness.workspace import safe_write
                safe_write(man, result["output_manuscript"])
            out_hash = hashing.sha256_file(man)
            # per-round log
            rd = rounds_dir / f"round_{rnd:02d}"
            rd.mkdir(exist_ok=True)
            (rd / "verdict.json").write_text(json.dumps({
                "round": rnd, "mode": mode, "input_hash": in_hash, "output_hash": out_hash,
                "verdict": verdict, "overall_score": score,
                "model_version": result.get("model_version"),
                "panel_lenses": result.get("panel_lenses", []),
                "counts": _counts(findings),
            }, indent=2, ensure_ascii=False), encoding="utf-8")
            (rd / "findings.json").write_text(json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8")
            (rd / "raw_output.md").write_text(result.get("raw_output", ""), encoding="utf-8")
            (rd / "fix.diff").write_text(result.get("fix_diff", ""), encoding="utf-8")
            if condition == "panel":
                stop_reason = "panel is single diagnostic pass (no fix loop)"
                break
            stop, reason = should_stop(verdict, findings, rnd, max_rounds)
            if stop:
                stop_reason = reason
                break
        init_c = _counts(last_findings if rounds_run == 1 else last_findings)
        return {
            "status": "RUN", "demo": demo_id, "condition": condition,
            "rounds_run": rounds_run, "init_verdict": init_verdict, "final_verdict": last_verdict,
            "init_score": init_score, "final_score": last_score,
            "final_actionable_major": _counts(last_findings)["actionable_major"],
            "final_fixable_true": _counts(last_findings)["fixable_true"],
            "final_fixable_false": _counts(last_findings)["fixable_false"],
            "stop_reason": stop_reason,
        }


def main() -> int:
    ap = argparse.ArgumentParser(description="E9 self-review convergence (NOT_RUN by default)")
    ap.add_argument("--with-llm", action="store_true",
                    help="run the loop (requires a configured runner via MEDSCI_SELFREVIEW_RUNNER)")
    ap.add_argument("--max-rounds", type=int, default=MAX_ROUNDS_DEFAULT)
    ap.add_argument("--demos", nargs="*", default=None, help="subset of demo ids")
    args = ap.parse_args()

    log = RunLogger.start("E9")
    out = log.run_dir / "convergence.csv"
    cols = ["demo", "condition", "rounds_run", "init_verdict", "final_verdict",
            "init_score", "final_score", "final_actionable_major",
            "final_fixable_true", "final_fixable_false", "stop_reason"]

    runner_ok = get_runner() is not None
    if not (args.with_llm and runner_ok):
        reason = ("no runner configured (set MEDSCI_SELFREVIEW_RUNNER=module:function)"
                  if args.with_llm else "default mode (pass --with-llm with a configured runner)")
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["status", "reason", "note"])
            w.writerow(["NOT_RUN", reason,
                        "internal self-review QC convergence harness specified and archived; "
                        "not analyzed in this release"])
        print(f"E9 status: NOT_RUN ({reason})")
        log.log_component(
            component_type="llm_baseline", model_name="self-review-loop (agent/LLM)",
            command_args=["--with-llm"] if args.with_llm else [],
            expected_reproducibility="non-deterministic",
            rerun_policy="configure MEDSCI_SELFREVIEW_RUNNER; bounded 3-5 rounds; N replicates advised",
            input_paths=[], output_path=out,
        )
        log.finalize(metrics_path=out,
                     limitations="Self-review convergence loop NOT executed for this release. "
                                 "Measures internal rubric / self-review QC convergence only - not "
                                 "external manuscript quality, reviewer acceptance, or distinguishability.",
                     repro_hash_extra=[out])
        print(f"run dir: {log.run_dir}")
        return 0

    demos = list(golden_inputs()) if args.demos is None else args.demos
    rows = []
    for demo_id in demos:
        for cond in CONDITIONS:
            r = run_condition(demo_id, cond, log, args.max_rounds)
            if r.get("status") == "RUN":
                rows.append({k: r.get(k, "") for k in cols})
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"E9 executed: {len(rows)} condition-runs across {len(demos)} demos")
    for r in rows:
        print(f"  {r['demo']:22s} {r['condition']:7s} rounds={r['rounds_run']} "
              f"{r['init_verdict']}->{r['final_verdict']} stop='{r['stop_reason']}'")
    log.log_component(
        component_type="llm_baseline", model_name="self-review-loop (agent/LLM)",
        command_args=["--with-llm", "--max-rounds", str(args.max_rounds)],
        expected_reproducibility="non-deterministic",
        rerun_policy="bounded 3-5 rounds; report N replicates for variability",
        input_paths=[golden_inputs()[d].manuscript for d in demos], output_path=out,
    )
    log.finalize(metrics_path=out,
                 limitations="Internal self-review QC convergence only (Paper-2 boundary). "
                             "Non-deterministic; report replicate variability when used in analysis.",
                 api_cost_usd=None)
    print(f"run dir: {log.run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

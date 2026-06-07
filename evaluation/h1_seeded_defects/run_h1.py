#!/usr/bin/env python3
"""E1 - Seeded-defect detector benchmark.

For each defect: copy the clean input, inject one known defect, run the target
detector, and record whether the specific defect code was emitted. Also run each
detector on the clean input to measure the clean false-positive rate (restricted
to the defect signals under test, so verify_refs's expected offline UNVERIFIED
baseline is not miscounted as a false positive).

Deterministic and self-contained by default (offline). --online enables the two
network-required citation defects. --check re-runs and asserts the committed
reference-run reproducibility hash.

Metrics: per-defect recall + clean false-positive rate. No "precision"
(prevalence is undefined in a fault-injection design).
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0]))
from _harness import detectors as dt  # noqa: E402
from _harness.detectors import DETECTORS, DetectorInputs, run_detector  # noqa: E402
from _harness.runlog import RunLogger  # noqa: E402
from _harness.schema import InjectionRecord  # noqa: E402
from _harness.workspace import (REPO_ROOT, golden_inputs, temp_copy,  # noqa: E402
                                temp_demo, temp_dir)
from registry import REGISTRY, DefectSpec  # noqa: E402
from inject import INJECTORS  # noqa: E402

FIXTURE_DIR = HERE / "fixtures" / "citation"
FIXTURES = {
    "fixture": HERE / "fixtures" / "citation",
    "fixture_artifact": HERE / "fixtures" / "artifact",
}


def _clean_run(det_id, *, manuscript=None, analysis_files=(), analysis_dir=None,
               refs_input=None, md_for_keys=None, bib_for_keys=None,
               out_path=None, project_root=None, online=False, cwd=None):
    inp = DetectorInputs(
        manuscript=manuscript, analysis_files=tuple(analysis_files),
        analysis_dir=analysis_dir, refs_input=refs_input,
        md_for_keys=md_for_keys, bib_for_keys=bib_for_keys,
        project_root=project_root,
    )
    return run_detector(det_id, inp, out_path, online=online, cwd=cwd)


def main() -> int:
    ap = argparse.ArgumentParser(description="E1 seeded-defect benchmark")
    ap.add_argument("--online", action="store_true",
                    help="also run network-required citation defects (FABRICATED/MISMATCH)")
    ap.add_argument("--check", metavar="RUN_DIR",
                    help="re-run and assert reproducibility hash matches RUN_DIR/run_manifest.json")
    args = ap.parse_args()

    demos = golden_inputs()
    log = RunLogger.start("E1")
    det_out = log.run_dir / "detector_outputs"

    # --- clean baselines (deduped by detector + input source) ---------------
    clean_codes: dict[tuple, frozenset] = {}

    def clean_key(det_id, demo, target_file):
        return (det_id, demo, target_file)

    needed_clean = {(s.detector_id, d, s.target_file) for s in REGISTRY for d in s.demos}
    with temp_dir("e1clean") as ctmp:
        for det_id, demo, target_file in sorted(needed_clean):
            out = ctmp / f"clean_{det_id}_{demo}_{Path(target_file).name}.json"
            if demo in FIXTURES:
                fxsrc = FIXTURES[demo]
                if det_id == "verify_refs":
                    with temp_copy(fxsrc, label="fxclean") as fx:
                        res = _clean_run("verify_refs", refs_input=fx / "clean.bib",
                                         project_root=fx, out_path=fx / "out.json", cwd=fx)
                elif det_id == "citation_keys":
                    res = _clean_run("citation_keys", md_for_keys=fxsrc / "clean.md",
                                     bib_for_keys=fxsrc / "clean.bib", out_path=out)
                elif det_id == "artifact_coverage":
                    res = _clean_run("artifact_coverage", manuscript=fxsrc / "clean.md",
                                     out_path=out)
                else:
                    continue
            else:
                g = demos[demo]
                tpath = g.root / target_file
                if det_id == "generated_code":
                    res = _clean_run("generated_code", analysis_files=(tpath,), out_path=out)
                elif det_id == "artifact_coverage":
                    res = _clean_run("artifact_coverage", manuscript=tpath,
                                     analysis_dir=g.analysis_dir, out_path=out, cwd=g.root)
                else:  # manuscript detectors
                    data_csv = (g.data_csvs()[0] if det_id == "cohort_arithmetic" and g.data_csvs() else None)
                    res = _clean_run(det_id, manuscript=tpath, out_path=out)
            clean_codes[clean_key(det_id, demo, target_file)] = res.found_codes
            # preserve clean raw
            dest = det_out / demo / "clean" / f"{det_id}.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            if res.json_obj is not None:
                dest.write_text(json.dumps(res.json_obj, indent=2, sort_keys=True, ensure_ascii=False),
                                encoding="utf-8")

    # --- injected variants --------------------------------------------------
    variant_rows = []
    for spec in REGISTRY:
        for demo in spec.demos:
            base_inj = InjectionRecord(
                defect_id=spec.defect_id, defect_class=spec.defect_class, demo=demo,
                target_file=spec.target_file, injector=spec.injector,
                detector_id=spec.detector_id, expected_codes=list(spec.expected_codes),
                status="", reason="",
            )
            if spec.network_required and not args.online:
                base_inj.status = "NOT_RUN"
                base_inj.reason = "network_required; run with --online"
                log.append_injected_defect(base_inj)
                variant_rows.append(_row(spec, demo, "NOT_RUN", None, None))
                continue

            if demo in FIXTURES:
                ctx = temp_copy(FIXTURES[demo], label="fx")
            else:
                ctx = temp_demo(demos[demo])
            with ctx as root:
                target = root / spec.target_file
                outcome = INJECTORS[spec.injector](target, spec.injector_args)
                base_inj.status = outcome.status
                base_inj.reason = outcome.reason
                base_inj.after_excerpt = outcome.after_excerpt
                log.append_injected_defect(base_inj)
                if outcome.status == "SKIPPED":
                    variant_rows.append(_row(spec, demo, "SKIPPED", None, None))
                    continue

                out = root / f"_det_{spec.defect_id}.json"
                if demo in FIXTURES:
                    if spec.detector_id == "verify_refs":
                        res = run_detector("verify_refs",
                                           DetectorInputs(refs_input=target, project_root=root),
                                           root / "out.json", online=args.online, cwd=root)
                    elif spec.detector_id == "citation_keys":
                        res = run_detector("citation_keys",
                                           DetectorInputs(md_for_keys=root / "clean.md",
                                                          bib_for_keys=root / "clean.bib"),
                                           out, cwd=root)
                    else:  # artifact_coverage fixture
                        res = run_detector("artifact_coverage",
                                           DetectorInputs(manuscript=target), out, cwd=root)
                else:
                    g = demos[demo]
                    adir = root / "analysis"
                    if spec.detector_id == "generated_code":
                        res = run_detector("generated_code",
                                           DetectorInputs(analysis_files=(target,)), out, cwd=root)
                    elif spec.detector_id == "artifact_coverage":
                        res = run_detector("artifact_coverage",
                                           DetectorInputs(manuscript=target, analysis_dir=adir),
                                           out, cwd=root)
                    else:
                        res = run_detector(spec.detector_id,
                                           DetectorInputs(manuscript=target), out, cwd=root)

                detected = bool(set(spec.expected_codes) & set(res.found_codes))
                # preserve injected raw
                dest = det_out / demo / spec.defect_id / f"{spec.detector_id}.json"
                dest.parent.mkdir(parents=True, exist_ok=True)
                if res.json_obj is not None:
                    dest.write_text(json.dumps(res.json_obj, indent=2, sort_keys=True, ensure_ascii=False),
                                    encoding="utf-8")
                variant_rows.append(_row(spec, demo, "INJECTED", detected, sorted(res.found_codes)))

    # --- aggregate per defect_id -------------------------------------------
    metrics = []
    for spec in REGISTRY:
        rows = [r for r in variant_rows if r["defect_id"] == spec.defect_id]
        injected = [r for r in rows if r["status"] == "INJECTED"]
        n_injected = len(injected)
        n_detected = sum(1 for r in injected if r["detected"] == "yes")
        n_skipped = sum(1 for r in rows if r["status"] == "SKIPPED")
        n_not_run = sum(1 for r in rows if r["status"] == "NOT_RUN")
        # clean FP: among demos with a clean run, fraction whose clean codes
        # already contain a tested defect code.
        cfp_inputs = 0
        cfp_hits = 0
        for demo in spec.demos:
            ck = (spec.detector_id, demo, spec.target_file)
            if ck in clean_codes:
                cfp_inputs += 1
                if set(spec.expected_codes) & set(clean_codes[ck]):
                    cfp_hits += 1
        metrics.append({
            "defect_id": spec.defect_id,
            "defect_class": spec.defect_class,
            "detector_id": spec.detector_id,
            "detector_family": DETECTORS[spec.detector_id]["family"],
            "expected_codes": ";".join(spec.expected_codes),
            "n_demos": len(spec.demos),
            "n_injected": n_injected,
            "n_detected": n_detected,
            "recall": round(n_detected / n_injected, 3) if n_injected else "",
            "n_skipped": n_skipped,
            "n_not_run": n_not_run,
            "clean_fp_inputs": cfp_inputs,
            "clean_fp_hits": cfp_hits,
        })

    metrics.sort(key=lambda m: (m["detector_family"], m["detector_id"], m["defect_id"]))
    out_metrics = log.run_dir / "metrics.csv"
    cols = ["defect_id", "defect_class", "detector_id", "detector_family",
            "expected_codes", "n_demos", "n_injected", "n_detected", "recall",
            "n_skipped", "n_not_run", "clean_fp_inputs", "clean_fp_hits"]
    with out_metrics.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(metrics)

    # per-variant detail
    out_variants = log.run_dir / "variants.csv"
    vcols = ["defect_id", "defect_class", "detector_id", "demo", "status",
             "detected", "expected_codes", "found_codes"]
    with out_variants.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=vcols)
        w.writeheader()
        w.writerows(variant_rows)

    # --- report -------------------------------------------------------------
    inj_total = sum(m["n_injected"] for m in metrics)
    det_total = sum(m["n_detected"] for m in metrics)
    nr_total = sum(m["n_not_run"] for m in metrics)
    sk_total = sum(m["n_skipped"] for m in metrics)
    fp_total = sum(m["clean_fp_hits"] for m in metrics)
    print(f"variants: injected={inj_total} detected={det_total} "
          f"skipped={sk_total} not_run={nr_total}")
    print(f"overall recall (offline): {det_total}/{inj_total} = "
          f"{det_total / inj_total:.3f}" if inj_total else "no injected variants")
    print(f"clean false-positive hits (tested signals): {fp_total}")
    print()
    for m in metrics:
        print(f"  {m['defect_id']:26s} {m['detector_id']:18s} "
              f"recall={m['recall']!s:>5} ({m['n_detected']}/{m['n_injected']}) "
              f"skip={m['n_skipped']} nrun={m['n_not_run']} cleanFP={m['clean_fp_hits']}/{m['clean_fp_inputs']}")

    log.log_component(
        component_type="deterministic_script",
        script_path=str(Path(__file__).relative_to(REPO_ROOT)),
        command_args=["--online"] if args.online else [],
        expected_reproducibility="exact",
        rerun_policy="rerun any time offline; metrics.csv + detector_outputs hash stable",
        input_paths=[demos[d].manuscript for d in demos] + [FIXTURE_DIR / "clean.bib", FIXTURE_DIR / "clean.md"],
        output_path=out_metrics,
    )
    limitations = (
        "One defect per temp copy; one target detector judged per defect. "
        "Recall = detected/injected; clean FP counts only the *tested* defect "
        "signals on clean inputs (verify_refs's expected offline UNVERIFIED "
        "baseline is not a false positive). Citation defects use a synthetic "
        "fixture because the demo bibs are intentionally empty. FABRICATED and "
        "MISMATCH require live PubMed/CrossRef and are NOT_RUN unless --online. "
        "No 'precision' is reported (prevalence is undefined under fault "
        "injection)."
    )
    log.finalize(metrics_path=out_metrics, limitations=limitations,
                 repro_hash_extra=[out_metrics, out_variants])

    if args.check:
        ref = json.loads((Path(args.check) / "run_manifest.json").read_text())
        cur = json.loads((log.run_dir / "run_manifest.json").read_text())
        ok = ref["reproducibility_hash"] == cur["reproducibility_hash"]
        print(f"\n--check: reproducibility hash {'MATCH' if ok else 'MISMATCH'}")
        print(f"  ref: {ref['reproducibility_hash'][:16]}  cur: {cur['reproducibility_hash'][:16]}")
        return 0 if ok else 1

    print(f"\nwrote {out_metrics}")
    print(f"run dir: {log.run_dir}")
    return 0


def _row(spec: DefectSpec, demo, status, detected, found):
    return {
        "defect_id": spec.defect_id, "defect_class": spec.defect_class,
        "detector_id": spec.detector_id, "demo": demo, "status": status,
        "detected": "" if detected is None else ("yes" if detected else "no"),
        "expected_codes": ";".join(spec.expected_codes),
        "found_codes": ";".join(found) if found else "",
    }


if __name__ == "__main__":
    sys.exit(main())

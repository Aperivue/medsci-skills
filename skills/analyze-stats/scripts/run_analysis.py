#!/usr/bin/env python3
"""Run a bounded binary diagnostic-accuracy workflow with its existing template.

Usage: run_analysis.py run --project-root . --data data.csv --config analysis.json --out runs/run1
       run_analysis.py audit --project-root . --out runs/run1
       run_analysis.py compare --project-root . --previous runs/run1 --out runs/run2

The existing _analysis_outputs.md is both the readable output index and the
execution record. No raw rows/identifiers are copied into reports. Audit checks
recorded file versions, not whether a study design or declaration is true.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path, PurePosixPath
import platform
import sys
import tempfile

SKILL = Path(__file__).resolve().parents[1]
CODE = {"runner": Path(__file__).resolve(),
        "template": SKILL / "references/templates/diagnostic_accuracy.py",
        "style": SKILL / "references/style/figure_style.mplstyle"}
MANIFEST = "_analysis_outputs.md"
BEGIN = "<!-- MEDSCI_ANALYSIS_RUN_BEGIN -->\n```json\n"
END = "\n```\n<!-- MEDSCI_ANALYSIS_RUN_END -->\n"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def local_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ValueError("Use a project-relative POSIX path")
    parts = PurePosixPath(relative).parts
    if not parts or relative.startswith("/") or any(p.startswith(".") for p in parts):
        raise ValueError("Absolute, hidden or traversing paths are not supported")
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("Symlink paths are not supported")
    path.resolve().relative_to(root)
    return path


def configuration(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    fields = {"schema_version", "analysis_unit", "unit_id_col", "truth_col",
              "prediction_col", "missing_policy", "independent_units", "data_status"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("Configuration must contain exactly the documented fields")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValueError("Configuration schema_version must be 1")
    if value["analysis_unit"] not in {"patient", "participant", "exam", "lesion", "image", "case", "study", "sample"}:
        raise ValueError("Unsupported analysis unit")
    if value["independent_units"] is not True:
        raise ValueError("This workflow requires declared independent units; clustered analysis is separate")
    if value["missing_policy"] not in {"error", "complete_case"}:
        raise ValueError("Choose error or complete_case for missing labels")
    if value["data_status"] not in {"synthetic", "deidentified_authorized"}:
        raise ValueError("Declare synthetic or deidentified_authorized data before running")
    columns = [value[k] for k in ("unit_id_col", "truth_col", "prediction_col")]
    if any(not isinstance(x, str) or not x.strip() for x in columns) or len(set(columns)) != 3:
        raise ValueError("Three distinct nonempty input columns are required")
    return value


def read_rows(path: Path, config: dict):
    import numpy as np
    ids, truth, predictions = set(), [], []
    counts = {"input_rows": 0, "included_rows": 0, "excluded_missing_labels": 0,
              "missing_truth": 0, "missing_prediction": 0}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        if len(set(headers)) != len(headers):
            raise ValueError("Duplicate CSV headers")
        if not {config[k] for k in ("unit_id_col", "truth_col", "prediction_col")} <= set(headers):
            raise ValueError("Required row-level columns are missing; aggregate percentages are unsupported")
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError("Malformed CSV row")
            counts["input_rows"] += 1
            unit = row[config["unit_id_col"]].strip()
            if not unit or unit in ids:
                raise ValueError("Missing or repeated unit ID; no raw identifiers are printed")
            ids.add(unit)
            a, b = (row[config[k]].strip() for k in ("truth_col", "prediction_col"))
            if a not in {"", "0", "1"} or b not in {"", "0", "1"}:
                raise ValueError("Labels must be literal 0/1 or empty; scores and rounded summaries are unsupported")
            counts["missing_truth"] += int(a == "")
            counts["missing_prediction"] += int(b == "")
            if not a or not b:
                counts["excluded_missing_labels"] += 1
                if config["missing_policy"] == "error":
                    raise ValueError("Missing labels; choose a justified missing-data policy explicitly")
                continue
            truth.append(int(a))
            predictions.append(int(b))
    counts["included_rows"] = len(truth)
    if not truth:
        raise ValueError("No complete observations")
    return np.array(truth), np.array(predictions), counts


def load_template():
    spec = importlib.util.spec_from_file_location("medsci_diagnostic_template", CODE["template"])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def file_record(path: Path, relative: str) -> dict:
    return {"path": relative, "sha256": sha256(path), "bytes": path.stat().st_size}


def code_records() -> dict:
    return {role: file_record(path, path.relative_to(SKILL).as_posix()) for role, path in CODE.items()}


def render_manifest(record: dict) -> str:
    rows = record["metrics"]
    lines = ["# Analysis Outputs", f"Generated: {record['generated_at']}",
             "Study type: binary diagnostic accuracy from prespecified labels", "",
             "## Tables", "- `diagnostic_accuracy_table.csv` -- Full precision estimates, counts and Wilson 95% CIs", "",
             "## Figures", "- `confusion_matrix.pdf` / `confusion_matrix.png` -- Counts; percentages use included N", "",
             "## Data", "Input data are referenced by hash below; no raw rows or IDs are copied.", "",
             "## Results", f"Declared analysis unit: {record['config']['analysis_unit']}.",
             f"Included: {record['cohort']['included_rows']}/{record['cohort']['input_rows']} rows; "
             f"excluded for missing labels: {record['cohort']['excluded_missing_labels']}.", "",
             "| Metric | Numerator / denominator | Estimate | 95% CI | Status |",
             "|---|---:|---:|---|---|"]
    for row in rows:
        estimate = "undefined" if row["estimate"] is None else f"{row['estimate']:.3f}"
        interval = "undefined" if row["ci_lower"] is None else f"{row['ci_lower']:.3f} to {row['ci_upper']:.3f}"
        lines.append(f"| {row['metric']} | {row['numerator']} / {row['denominator']} | {estimate} | {interval} | {row['status']} |")
    lines += ["", "## Scope", "Wilson intervals are conditional on independent units and the declared sample.",
              "Unique IDs do not establish independence, valid reference labels or representative sampling.",
              "No p-value comparison, AUC, calibration, threshold optimization or clinical-utility analysis is performed.",
              "Study validity, privacy clearance, reuse rights and visual review remain not_assessed.",
              "Hashes identify versions, not a backup or authenticated proof of correct source declarations.", "",
              "## Execution record", BEGIN.rstrip("\n"),
              json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False), END.lstrip("\n").rstrip("\n"), ""]
    return "\n".join(lines)


def read_manifest(directory: Path) -> tuple[dict, bool]:
    path = local_path(directory, MANIFEST)
    text = path.read_text(encoding="utf-8")
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise ValueError("Missing or ambiguous execution record; legacy manifests are not bound")
    payload = text.split(BEGIN, 1)[1].split(END, 1)[0]
    record = json.loads(payload)
    if not isinstance(record, dict) or record.get("schema_version") != 1 or record.get("workflow") != "binary_diagnostic_accuracy":
        raise ValueError("Unsupported execution record")
    return record, text == render_manifest(record)


def run(root: Path, data_rel: str, config_rel: str, out_rel: str) -> dict:
    data, config_path, out = (local_path(root, x) for x in (data_rel, config_rel, out_rel))
    if out.exists():
        raise ValueError("Output directory already exists; use a new run directory")
    if data == config_path or data.samefile(config_path):
        raise ValueError("Data and configuration must be distinct files")
    before = {"data": file_record(data, data_rel), "config": file_record(config_path, config_rel)}
    code = code_records()
    config = configuration(config_path)
    truth, predictions, cohort = read_rows(data, config)
    template = load_template()
    template.np.random.seed(42)
    metrics = template.compute_metrics(truth, predictions)
    tp, fp, tn, fn = (metrics["_counts"][k] for k in ("TP", "FP", "TN", "FN"))
    denominators = {"Sensitivity": (tp, tp + fn), "Specificity": (tn, tn + fp),
                    "PPV": (tp, tp + fp), "NPV": (tn, tn + fn), "Accuracy": (tp + tn, len(truth))}
    rows = []
    for name, (numerator, denominator) in denominators.items():
        estimate, lower, upper = metrics[name]
        rows.append({"metric": name, "numerator": int(numerator), "denominator": int(denominator),
                     "estimate": float(estimate) if math.isfinite(estimate) else None,
                     "ci_lower": float(lower) if math.isfinite(lower) else None,
                     "ci_upper": float(upper) if math.isfinite(upper) else None,
                     "status": "defined" if denominator else "undefined_zero_denominator",
                     "analysis_unit": config["analysis_unit"], "ci_method": "wilson_95_no_continuity_correction"})
    from matplotlib import font_manager
    font = Path(font_manager.findfont(font_manager.FontProperties()))
    environment = {"python": platform.python_version(), "numpy": template.np.__version__,
                   "pandas": template.pd.__version__, "scipy": template.scipy.__version__,
                   "sklearn": template.sklearn.__version__, "matplotlib": template.matplotlib.__version__,
                   "font_file": font.name, "font_sha256": sha256(font)}
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".analysis-run-", dir=out.parent) as temporary:
        stage = Path(temporary) / "result"
        stage.mkdir()
        with (stage / "diagnostic_accuracy_table.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        with contextlib.redirect_stdout(io.StringIO()):
            template.plot_confusion_matrix(truth, {"Prespecified predictions": predictions},
                                           ["Prespecified predictions"], str(stage))
        outputs = [file_record(stage / name, name) for name in (
            "diagnostic_accuracy_table.csv", "confusion_matrix.pdf", "confusion_matrix.png")]
        after = {"data": file_record(data, data_rel), "config": file_record(config_path, config_rel)}
        if before != after or code != code_records():
            raise ValueError("An input, code or style file changed during execution; run not published")
        record = {"schema_version": 1, "workflow": "binary_diagnostic_accuracy",
                  "generated_at": datetime.now(timezone.utc).isoformat(), "inputs": before,
                  "code": code, "config": config, "environment": environment,
                  "random_seed": 42, "randomness_used": False,
                  "cohort": cohort, "counts": metrics["_counts"], "metrics": rows, "outputs": outputs,
                  "command": ["python3", "<analyze-stats>/scripts/run_analysis.py", "run", "--project-root", ".",
                              "--data", data_rel, "--config", config_rel, "--out", out_rel],
                  "checks": {"binary_labels": "passed", "unique_declared_unit_ids": "passed",
                             "input_code_unchanged_during_run": "passed", "study_validity": "not_assessed",
                             "privacy_clearance": "not_assessed", "reuse_rights": "not_assessed", "visual_review": "not_assessed"}}
        (stage / MANIFEST).write_text(render_manifest(record), encoding="utf-8")
        if out.exists():
            raise ValueError("Output appeared during execution; nothing overwritten")
        stage.rename(out)
    return record


def audit(root: Path, out_rel: str) -> dict:
    directory = local_path(root, out_rel)
    record, text_matches = read_manifest(directory)
    changes = [] if text_matches else ["manifest_text_changed"]
    for role, entry in record["inputs"].items():
        path = local_path(root, entry["path"])
        if not path.is_file() or sha256(path) != entry["sha256"]:
            changes.append(f"input:{role}")
    if set(record["code"]) != set(CODE):
        changes.append("code:inventory")
    for role, path in CODE.items():
        if record["code"].get(role, {}).get("sha256") != sha256(path):
            changes.append(f"code:{role}")
    expected = {MANIFEST}
    for entry in record["outputs"]:
        expected.add(entry["path"])
        path = local_path(directory, entry["path"])
        if not path.is_file() or sha256(path) != entry["sha256"]:
            changes.append(f"output:{entry['path']}")
    actual = {p.name for p in directory.iterdir()}
    if actual != expected:
        changes.append("output:inventory")
    return {"status": "drift" if changes else "current", "changes": changes,
            "scope": "Recorded input/code/output bytes only; no re-analysis or design approval",
            "study_validity": "not_assessed"}


def compare(root: Path, previous: str, current: str) -> dict:
    old, _ = read_manifest(local_path(root, previous))
    new, _ = read_manifest(local_path(root, current))
    # Declared units and columns are part of the estimand context, even if the
    # displayed estimate happens to be identical. Do not compare rounded prose.
    keys = ("analysis_unit", "unit_id_col", "truth_col", "prediction_col", "missing_policy", "independent_units")
    comparable = all(old["config"][k] == new["config"][k] for k in keys)
    context_changed = [k for k in ("inputs", "code", "environment") if old[k] != new[k]]
    previous_audit, current_audit = audit(root, previous), audit(root, current)
    drift = any(result["status"] == "drift" for result in (previous_audit, current_audit))
    return {"status": "drift" if drift else "compared",
            "context_status": "not_comparable" if not comparable else "context_changed" if context_changed else "same_context",
            "context_changed": context_changed, "declared_context_matches": comparable,
            "recorded_numeric_results_equal": old["metrics"] == new["metrics"] if comparable else None,
            "cohort_equal": old["cohort"] == new["cohort"],
            "recorded_outputs_equal": old["outputs"] == new["outputs"],
            "previous_audit": previous_audit, "current_audit": current_audit,
            "scope": "Comparison of recorded values, not equivalence or a rerun; consult both byte audits",
            "study_validity": "not_assessed"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "audit", "compare"))
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--data")
    parser.add_argument("--config")
    parser.add_argument("--out", required=True)
    parser.add_argument("--previous")
    args = parser.parse_args()
    try:
        root = Path(args.project_root).resolve()
        if not root.is_dir():
            raise ValueError("Project root must exist")
        if args.mode == "run":
            if not args.data or not args.config or args.previous:
                raise ValueError("run requires --data and --config, without --previous")
            record = run(root, args.data, args.config, args.out)
            result = {"status": "completed", "manifest": f"{args.out}/{MANIFEST}",
                      "included_rows": record["cohort"]["included_rows"], "study_validity": "not_assessed"}
        elif args.data or args.config:
            raise ValueError("audit/compare read recorded inputs; do not supply --data or --config")
        elif args.mode == "audit":
            if args.previous:
                raise ValueError("--previous is only used by compare")
            result = audit(root, args.out)
        else:
            if not args.previous:
                raise ValueError("compare requires --previous")
            result = compare(root, args.previous, args.out)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 1 if result["status"] == "drift" else 0
    except (OSError, ValueError, KeyError, TypeError, ImportError) as exc:
        print(f"Analysis workflow error ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

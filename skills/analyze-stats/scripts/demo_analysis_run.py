#!/usr/bin/env python3
"""Create an original synthetic project, calculate twice and compare the records.

Usage: demo_analysis_run.py --out NEW_PROJECT_DIRECTORY
No study data, downloaded sources or network access are used.
"""
import argparse
import csv
import json
from pathlib import Path

import run_analysis


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="New directory; existing directories are refused")
    args = parser.parse_args()
    root = Path(args.out).resolve()
    root.mkdir(parents=True, exist_ok=False)
    with (root / "data.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["unit_id", "truth", "prediction"])
        for i in range(20):
            writer.writerow([f"synthetic_{i:02}", int(i < 10), int(i < 8 or 10 <= i < 13)])
    config = {"schema_version": 1, "analysis_unit": "case", "unit_id_col": "unit_id",
              "truth_col": "truth", "prediction_col": "prediction", "missing_policy": "error",
              "independent_units": True, "data_status": "synthetic"}
    (root / "analysis.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    first = run_analysis.run(root, "data.csv", "analysis.json", "runs/first")
    # Independent fixture arithmetic: the first ten rows are positive; predictions
    # include eight of those and three of the remaining ten rows.
    if first["counts"] != {"TP": 8, "FN": 2, "FP": 3, "TN": 7}:
        raise RuntimeError("Synthetic confusion counts disagree with the authored fixture")
    run_analysis.run(root, "data.csv", "analysis.json", "runs/repeat")
    comparison = run_analysis.compare(root, "runs/first", "runs/repeat")
    if comparison["status"] != "compared" or not comparison["recorded_numeric_results_equal"]:
        raise RuntimeError("Synthetic rerun failed its execution-record comparison")
    print(json.dumps({"synthetic_counts": first["counts"], "comparison": comparison}, indent=2))


if __name__ == "__main__":
    main()

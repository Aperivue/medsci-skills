#!/usr/bin/env python3
"""Original synthetic controls for execution records and exact binary counts."""
import contextlib
import csv
from fractions import Fraction
import io
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_analysis as run

CONFIG = {"schema_version": 1, "analysis_unit": "case", "unit_id_col": "unit_id",
          "truth_col": "truth", "prediction_col": "prediction", "missing_policy": "error",
          "independent_units": True, "data_status": "synthetic"}


def write_data(root):
    with (root / "data.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["unit_id", "truth", "prediction"])
        # The fixture is assembled from four groups, not inferred from rounded metrics.
        index = 0
        for truth, prediction, count in ((1, 1, 8), (1, 0, 2), (0, 1, 3), (0, 0, 7)):
            for _ in range(count):
                writer.writerow([f"unit_{index}", truth, prediction])
                index += 1
    (root / "analysis.json").write_text(json.dumps(CONFIG))


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.TemporaryDirectory()
        cls.base_path = Path(cls.base.name).resolve()
        write_data(cls.base_path)
        cls.record = run.run(cls.base_path, "data.csv", "analysis.json", "runs/first")

    @classmethod
    def tearDownClass(cls):
        cls.base.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        shutil.copytree(self.base_path, self.root, dirs_exist_ok=True)
        self.output = self.root / "runs/first"

    def config(self, **changes):
        value = {**CONFIG, **changes}
        (self.root / "analysis.json").write_text(json.dumps(value))

    def execute(self, out="runs/second"):
        return run.run(self.root, "data.csv", "analysis.json", out)

    def test_exact_independent_counts_and_denominators(self):
        # Independent integer arithmetic, without calling the implementation's metric helper.
        cells = self.record["counts"]
        self.assertEqual(cells, {"TP": 8, "FP": 3, "TN": 7, "FN": 2})
        expected = {"Sensitivity": Fraction(8, 10), "Specificity": Fraction(7, 10),
                    "PPV": Fraction(8, 11), "NPV": Fraction(7, 9), "Accuracy": Fraction(15, 20)}
        for row in self.record["metrics"]:
            self.assertEqual(Fraction(row["numerator"], row["denominator"]), expected[row["metric"]])
            self.assertAlmostEqual(row["estimate"], float(expected[row["metric"]]), places=14)

    def test_intervals_match_independent_scipy_implementation(self):
        from scipy.stats import binomtest
        for row in self.record["metrics"]:
            reference = binomtest(row["numerator"], row["denominator"]).proportion_ci(method="wilson")
            self.assertAlmostEqual(row["ci_lower"], reference.low, places=12)
            self.assertAlmostEqual(row["ci_upper"], reference.high, places=12)

    def test_unrounded_csv_and_readable_manifest_are_same_record(self):
        with (self.output / "diagnostic_accuracy_table.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertAlmostEqual(float(rows[2]["estimate"]), 8 / 11, places=14)
        self.assertNotEqual(float(rows[2]["estimate"]), 0.727)
        record, matches = run.read_manifest(self.output)
        self.assertTrue(matches)
        self.assertEqual(record["metrics"], self.record["metrics"])
        self.assertEqual(record["checks"]["study_validity"], "not_assessed")

    def test_same_context_rerun_preserves_sources_and_outputs(self):
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in (
            self.root / "data.csv", self.root / "analysis.json")}
        self.execute()
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in (
            self.root / "data.csv", self.root / "analysis.json")})
        result = run.compare(self.root, "runs/first", "runs/second")
        self.assertEqual(result["status"], "compared")
        self.assertEqual(result["context_status"], "same_context")
        self.assertTrue(result["recorded_numeric_results_equal"])
        self.assertTrue(result["recorded_outputs_equal"])

    def test_changed_input_stays_drift_on_repeated_audits(self):
        with (self.root / "data.csv").open("a") as stream:
            stream.write("additional_unit,0,0\n")
        old = (self.output / run.MANIFEST).read_bytes()
        for _ in range(2):
            self.assertIn("input:data", run.audit(self.root, "runs/first")["changes"])
        self.assertEqual(old, (self.output / run.MANIFEST).read_bytes())

    def test_changed_configuration_does_not_rebind_old_run(self):
        self.config(missing_policy="complete_case")
        self.assertIn("input:config", run.audit(self.root, "runs/first")["changes"])

    def test_same_estimates_different_unit_not_comparable(self):
        self.config(analysis_unit="lesion")
        second = self.execute()
        self.assertEqual(self.record["metrics"][0]["estimate"], second["metrics"][0]["estimate"])
        result = run.compare(self.root, "runs/first", "runs/second")
        self.assertEqual(result["context_status"], "not_comparable")
        self.assertIsNone(result["recorded_numeric_results_equal"])

    def test_same_percentage_different_denominator_is_not_equal_result(self):
        with (self.root / "data.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        with (self.root / "data.csv").open("a", newline="") as stream:
            writer = csv.writer(stream)
            for row in rows:
                writer.writerow([row["unit_id"] + "_copy", row["truth"], row["prediction"]])
        second = self.execute()
        self.assertEqual(self.record["metrics"][0]["estimate"], second["metrics"][0]["estimate"])
        self.assertEqual(second["metrics"][0]["denominator"], 20)
        comparison = run.compare(self.root, "runs/first", "runs/second")
        self.assertFalse(comparison["recorded_numeric_results_equal"])
        self.assertFalse(comparison["cohort_equal"])

    def test_repeated_unit_ids_are_not_silently_treated_as_independent(self):
        with (self.root / "data.csv").open("a") as stream:
            stream.write("unit_0,0,0\n")
        with self.assertRaisesRegex(ValueError, "repeated unit"):
            self.execute()
        self.assertFalse((self.root / "runs/second").exists())

    def test_clustered_unit_declaration_is_not_supported(self):
        self.config(independent_units=False)
        with self.assertRaisesRegex(ValueError, "independent"):
            self.execute()

    def test_missing_labels_require_explicit_policy(self):
        with (self.root / "data.csv").open("a") as stream:
            stream.write("missing_1,,1\nmissing_2,0,\nmissing_both,,\n")
        with self.assertRaisesRegex(ValueError, "Missing labels"):
            self.execute()
        self.config(missing_policy="complete_case")
        result = self.execute()
        self.assertEqual(result["cohort"], {"input_rows": 23, "included_rows": 20,
            "excluded_missing_labels": 3, "missing_truth": 2, "missing_prediction": 2})

    def test_one_class_keeps_undefined_metrics_and_two_by_two_figure(self):
        (self.root / "data.csv").write_text("unit_id,truth,prediction\na,0,0\nb,0,0\n")
        result = self.execute()
        sensitivity = result["metrics"][0]
        self.assertEqual(sensitivity["status"], "undefined_zero_denominator")
        self.assertIsNone(sensitivity["estimate"])
        self.assertIsNone(sensitivity["ci_lower"])
        self.assertEqual(result["metrics"][-1]["estimate"], 1.0)
        self.assertTrue((self.root / "runs/second/confusion_matrix.pdf").is_file())

    def test_rounded_scores_and_nonbinary_labels_rejected_without_echo(self):
        for value in ("0.727", "2", "NaN", "private_marker"):
            (self.root / "data.csv").write_text(f"unit_id,truth,prediction\na,1,{value}\n")
            with self.subTest(value=value), self.assertRaises(ValueError) as error:
                self.execute()
            self.assertNotIn(value, str(error.exception))

    def test_aggregate_metrics_cannot_be_reverse_engineered_into_rows(self):
        (self.root / "data.csv").write_text("sensitivity,specificity,N\n0.800,0.700,20\n")
        with self.assertRaisesRegex(ValueError, "aggregate"):
            self.execute()

    def test_duplicate_headers_and_malformed_rows_rejected(self):
        for text in ("unit_id,truth,truth,prediction\na,1,1,1\n", "unit_id,truth,prediction\na,1\n"):
            (self.root / "data.csv").write_text(text)
            with self.assertRaises(ValueError):
                self.execute()

    def test_unknown_configuration_and_privacy_status_not_silently_ignored(self):
        for changes in ({"threshold": 0.5}, {"data_status": "unknown"}, {"truth_col": "unit_id"}):
            self.config(**changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.execute()

    def test_existing_output_and_input_alias_not_overwritten(self):
        original = (self.output / run.MANIFEST).read_bytes()
        for target in ("runs/first", "data.csv"):
            with self.assertRaisesRegex(ValueError, "already exists"):
                self.execute(target)
        self.assertEqual(original, (self.output / run.MANIFEST).read_bytes())

    def test_symlinks_traversal_hidden_and_absolute_paths_rejected(self):
        for path in ("../outside", "/tmp/output", ".hidden", "a/../b", "C:/outside", "a\\b"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                run.local_path(self.root, path)
        (self.root / "alias").symlink_to(self.root / "data.csv")
        with self.assertRaises(ValueError):
            run.local_path(self.root, "alias")

    def test_modified_or_missing_output_is_drift(self):
        (self.output / "diagnostic_accuracy_table.csv").write_text("manually edited\n")
        (self.output / "confusion_matrix.png").unlink()
        result = run.audit(self.root, "runs/first")
        self.assertIn("output:diagnostic_accuracy_table.csv", result["changes"])
        self.assertIn("output:confusion_matrix.png", result["changes"])

    def test_extra_file_and_edited_readable_summary_are_visible(self):
        (self.output / "unexpected.txt").write_text("synthetic")
        path = self.output / run.MANIFEST
        path.write_text(path.read_text().replace("Included: 20/20", "Included: 19/20", 1))
        result = run.audit(self.root, "runs/first")
        self.assertIn("manifest_text_changed", result["changes"])
        self.assertIn("output:inventory", result["changes"])

    def test_changed_code_is_visible_with_identical_numeric_results(self):
        self.execute()
        path = self.output / run.MANIFEST
        old, _ = run.read_manifest(self.output)
        old["code"]["runner"]["sha256"] = "0" * 64
        path.write_text(run.render_manifest(old))
        result = run.compare(self.root, "runs/first", "runs/second")
        self.assertTrue(result["recorded_numeric_results_equal"])
        self.assertEqual(result["status"], "drift")
        self.assertEqual(result["context_status"], "context_changed")
        self.assertIn("code", result["context_changed"])
        self.assertIn("code:runner", result["previous_audit"]["changes"])

    def test_actual_code_change_invalidates_prior_run(self):
        copied = self.root / "skill_copy"
        for path in run.CODE.values():
            destination = copied / path.relative_to(run.SKILL)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
        replacements = {role: copied / path.relative_to(run.SKILL) for role, path in run.CODE.items()}
        with patch.object(run, "SKILL", copied), patch.object(run, "CODE", replacements):
            self.execute()
            with replacements["template"].open("a") as stream:
                stream.write("\n# Synthetic code-version change.\n")
            result = run.audit(self.root, "runs/second")
            self.assertIn("code:template", result["changes"])

    def test_equal_records_do_not_hide_modified_output_or_exit_successfully(self):
        self.execute()
        (self.output / "diagnostic_accuracy_table.csv").write_text("edited output\n")
        result = run.compare(self.root, "runs/first", "runs/second")
        self.assertTrue(result["recorded_numeric_results_equal"])
        self.assertTrue(result["recorded_outputs_equal"])
        self.assertEqual(result["status"], "drift")
        proc = subprocess.run([sys.executable, str(run.CODE["runner"]), "compare",
            "--project-root", str(self.root), "--previous", "runs/first", "--out", "runs/second"],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["status"], "drift")

    def test_input_changes_during_plot_do_not_publish_a_run(self):
        template = run.load_template()
        original = template.plot_confusion_matrix
        def changing(*args):
            original(*args)
            with (self.root / "data.csv").open("a") as stream:
                stream.write("added_during_run,0,0\n")
        with patch.object(template, "plot_confusion_matrix", side_effect=changing), patch.object(run, "load_template", return_value=template):
            with self.assertRaisesRegex(ValueError, "changed during execution"):
                self.execute()
        self.assertFalse((self.root / "runs/second").exists())
        self.assertTrue((self.output / run.MANIFEST).is_file())

    def test_failed_plot_leaves_no_completed_manifest(self):
        template = run.load_template()
        with patch.object(template, "plot_confusion_matrix", side_effect=OSError("synthetic renderer failure")), patch.object(run, "load_template", return_value=template):
            with self.assertRaises(OSError):
                self.execute()
        self.assertFalse((self.root / "runs/second").exists())

    def test_legacy_or_corrupt_manifest_is_not_a_current_run(self):
        for text in ("# Analysis Outputs\n- table.csv\n", run.BEGIN + "[]" + run.END):
            (self.output / run.MANIFEST).write_text(text)
            with self.assertRaises(ValueError):
                run.audit(self.root, "runs/first")

    def test_real_pdf_png_and_no_raw_identifiers_in_record(self):
        self.assertTrue((self.output / "confusion_matrix.pdf").read_bytes().startswith(b"%PDF"))
        self.assertTrue((self.output / "confusion_matrix.png").read_bytes().startswith(b"\x89PNG"))
        self.assertNotIn("unit_0", (self.output / run.MANIFEST).read_text())

    def test_cli_run_and_read_only_audit(self):
        base = [sys.executable, str(run.CODE["runner"])]
        proc = subprocess.run(base + ["run", "--project-root", str(self.root), "--data", "data.csv",
                                     "--config", "analysis.json", "--out", "runs/cli"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        path = self.root / "runs/cli" / run.MANIFEST
        before = path.read_bytes(), path.stat().st_mtime_ns
        proc = subprocess.run(base + ["audit", "--project-root", str(self.root), "--out", "runs/cli"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(before, (path.read_bytes(), path.stat().st_mtime_ns))

    def test_template_import_and_zero_denominator_contract(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            template = run.load_template()
        self.assertEqual(output.getvalue(), "")
        self.assertTrue(all(math.isnan(x) for x in template.wilson_ci(0, 0)))

    def test_shipped_demo_runs_and_refuses_existing_project(self):
        command = [sys.executable, str(run.SKILL / "scripts/demo_analysis_run.py"),
                   "--out", str(self.root / "demo")]
        proc = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["comparison"]["status"], "compared")
        source = self.root / "demo/data.csv"
        before = source.read_bytes(), source.stat().st_mtime_ns
        proc = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(before, (source.read_bytes(), source.stat().st_mtime_ns))


if __name__ == "__main__":
    unittest.main()

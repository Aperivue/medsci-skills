# Binary diagnostic accuracy with an execution record

Use this bounded workflow when reference labels and **prespecified predictions**
are already literal `0`/`1`, with one row per independent analysis unit. It uses
the existing diagnostic-accuracy template to produce counts, five proportions
with Wilson 95% confidence intervals, and a confusion-matrix figure. It does not
train a model, select a threshold, calculate AUC or compare models. Those tasks
require a separate analysis plan and the corresponding template.

## Try the original synthetic example

From this skill's directory, with Python 3.10+ and `numpy`, `pandas`, `scipy`,
`scikit-learn` and `matplotlib` installed:

```bash
python3 scripts/demo_analysis_run.py --out demo-project
```

The new project contains generated row-level data, configuration and two runs.
Open `demo-project/runs/first/_analysis_outputs.md`, the full precision CSV and
both confusion-matrix files. The example checks independently specified TP/FP/
TN/FN counts and reruns the calculation. Tests additionally compare the intervals
against SciPy's implementation. It is an authored software control, not a clinical
validation dataset or an independent evaluation of the whole skill.

## Run on a defined project

Keep the complete installed skill directory: the runner imports its bundled
template and style; it does not require another MedSci skill at runtime. Set
`SKILL_DIR` to that directory and run these commands from the project directory:

```bash
python3 "$SKILL_DIR/scripts/run_analysis.py" run --project-root . \
  --data data.csv --config analysis.json --out runs/first
python3 "$SKILL_DIR/scripts/run_analysis.py" audit --project-root . --out runs/first
python3 "$SKILL_DIR/scripts/run_analysis.py" run --project-root . \
  --data data.csv --config analysis.json --out runs/repeat
python3 "$SKILL_DIR/scripts/run_analysis.py" compare --project-root . \
  --previous runs/first --out runs/repeat
```

The configuration must contain exactly these fields; unknown options are errors:

```json
{
  "schema_version": 1,
  "analysis_unit": "case",
  "unit_id_col": "unit_id",
  "truth_col": "truth",
  "prediction_col": "prediction",
  "missing_policy": "error",
  "independent_units": true,
  "data_status": "synthetic"
}
```

- Allowed declared units: `patient`, `participant`, `exam`, `lesion`, `image`,
  `case`, `study`, `sample`. Unique nonempty IDs are required, including excluded
  rows. Uniqueness alone does not establish independence: multiple lesions or
  images from one patient may require clustering and are outside this workflow.
- Positive class is `1`; negative class is `0`. Scores, other labels and rounded
  aggregate percentages are refused. Do not reconstruct purported raw observations
  from a paper's rounded results. Map labels and fix predictions in separately
  preserved preprocessing code before running.
- Empty labels fail by default. Use `complete_case` only with a justified plan;
  it records input/included rows, excluded rows and missing counts for each label.
  This records exclusion, without establishing that complete-case inference is valid.
- For real inputs, `data_status` must be `deidentified_authorized`. This is the
  operator's declaration, not automatic de-identification or privacy approval.
  Reports omit row values and IDs but contain project-relative paths, column names,
  aggregate counts and hashes. Keep paths/column names non-identifying and review
  small-cell disclosure and reuse rights before sharing the outputs.
- Inputs and output paths are relative to the project root. Hidden paths, symlinks,
  traversal and an existing output directory are refused. Raw inputs are read only;
  failed rendering or changed inputs/code during execution do not publish a completed
  run. Preserve data, configuration and code versions separately: hashes are not backups.

## One output manifest, with bounded checks

`_analysis_outputs.md` retains the existing Tables/Figures/Data discovery sections
and embeds one JSON execution record. It records the data/configuration hashes,
runner/template/style hashes, dependency versions, resolved font hash, exact
confusion counts, every metric's numerator/denominator, missing-data counts and
output hashes. The command uses `<analyze-stats>` as a portable skill-path
placeholder. The deterministic count workflow records seed 42 but uses no random
sampling. Archive the recorded dependency/code versions for later reproduction;
figure bytes may differ across rendering environments.

The CSV stores proportions on the 0–1 scale at full float precision. Markdown
rounding is display only. Sensitivity uses TP+FN, specificity TN+FP, PPV TP+FP,
NPV TN+FN and accuracy all included rows. A zero denominator produces an undefined
estimate and CI (JSON `null`, empty CSV cells), never zero performance. Figure cell
percentages use **all included rows**, not the metric-specific denominators.

`audit` reads without rewriting the record. `current` means that recorded input,
code and output bytes still match and the readable manifest is unchanged; it does
not rerun the analysis or audit the current environment. Legacy output lists
without an execution record are not silently promoted. A mismatch returns `drift`
and exit code 1; invalid/missing records or inputs return an error and exit code 2.

`compare` compares recorded full precision values, including denominators and CIs,
and includes both read-only byte audits. A different declared unit or label column
sets `context_status: not_comparable`; changed input/code/environment records stay
visible even if estimates match. Any byte-audit mismatch makes the top-level status
`drift` and exits 1. `recorded_*_equal` describes the stored records, not an assertion
that current files are equal or that the analyses are statistically equivalent.
Preserve versioned input files if both old and new runs must remain current.

These unsigned records are not tamper-proof. Study validity, reference-label
correctness, independence, privacy clearance, reuse rights and visual inspection
remain `not_assessed`; read the actual figure and analysis plan before reporting.

## Method and source scope

The repository's existing Wilson implementation is retained and checked against
the documented [SciPy Wilson interval](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html)
without continuity correction. Binary figure ordering is explicitly `[0, 1]`,
consistent with the [scikit-learn confusion-matrix interface](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html).
The example and documentation are original contributions under the repository
license. No third-party paper, dataset, image, font or documentation text is bundled.

Run the synthetic regression controls from the skill directory:

```bash
python3 tests/test_analysis_run.py
bash scripts/analysis_run_challenge/verify.sh
```

## Other analysis outputs

For analyses outside the bounded binary workflow, retain the existing output-list
format below. This list supports discovery but does not claim to bind an execution.

After all analyses complete, save a manifest file `_analysis_outputs.md` in the output directory:

```markdown
# Analysis Outputs
Generated: {YYYY-MM-DD}
Study type: {detected or user-specified type}

## Tables
- `table1_demographics.csv` -- Baseline characteristics
- `diagnostic_accuracy_table.csv` -- Performance metrics with 95% CIs

## Figures
- `roc_curve.pdf` / `roc_curve.png` -- ROC curves (vector / 300 DPI)

## Data
- `predictions.csv` -- Per-subject model predictions with ground truth
```

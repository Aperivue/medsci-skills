# Exemplar anatomy — ROC and precision–recall (PR) curves

A worked **anatomy model** for ROC and PR figures, complementing the `critic_rubrics/data_plot.md`
§C *ROC* checklist (this composes; the rubric scores). Synthetic — describes *what each element
must show* and the errors to avoid; not an image to copy. Pairs with `analyze-stats`
`templates/diagnostic_accuracy.py`.

## Elements
- **ROC curve** with axes **fixed 0–1** (TPR/sensitivity vs FPR/1−specificity); a diagonal
  chance line; **AUROC with its 95% CI** in the panel.
- **Confidence band** around the curve (bootstrap), or at least the **AUC CI** (DeLong or
  Hanley–McNeil for the AUC; bootstrap for the curve band) — a bare curve hides sampling error,
  especially at small n.
- **Operating point(s)** marked on the curve — the threshold actually proposed for use, with its
  sensitivity/specificity; state how it was chosen (and on which data, not the test set).
- **Multiple models**: distinguish by line style as well as colour; report a **test of the AUC
  difference** (DeLong) rather than two standalone AUCs.
- **A precision–recall (PR) curve alongside ROC when classes are imbalanced** — ROC looks
  optimistic under low prevalence because FPR has a huge negative denominator; report **AUPRC**
  and note the **baseline = prevalence** (the PR "chance" line is not 0.5).

## Discipline (what the figure must not do)
- **Do not read ROC as clinical performance under imbalance** — a high AUROC can coexist with a
  low PPV at the real base rate; pair it with PR / PPV-at-threshold (see `calibration_plot.md` for
  the probability side).
- **Do not pick the operating point on the test set** (threshold optimism); fix it on training/
  derivation data and report it.
- **Do not compare AUCs without a paired test** (DeLong) on the same cases; whether the two
  AUCs' CIs overlap is not a valid test of their difference.
- For a model that outputs probabilities, ROC/PR show **discrimination only** — discrimination is
  not calibration; a deployable probability still needs a calibration plot.

## Common omission
- The **AUC confidence interval / curve band**, the **marked operating point**, and **AUPRC under
  imbalance** — the elements ROC figures most often drop, and the ones that turn a pretty curve
  into an overstatement of real-world performance. Cross-reference `critic_rubrics/data_plot.md`
  §C (ROC) and `analyze-stats` `templates/diagnostic_accuracy.py`.

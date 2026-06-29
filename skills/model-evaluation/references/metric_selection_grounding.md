# Metric-selection grounding and CLAIM 2024 reporting fit (model-evaluation)

The *why* behind the operational checklist in `metric_guide.md`. Where `metric_guide.md` says
**what** to compute, this doc grounds **why** that pairing is required and where the outputs land
in the manuscript. Anchored to **Metrics Reloaded** (Maier-Hein & Reinke et al., *Nature Methods*
2024) and its pitfalls companion (Reinke et al., *Nature Methods* 2024), **CLAIM 2024** (Tejani et
al., *Radiology: Artificial Intelligence* 2024), **TRIPOD+AI** (the AI extension of TRIPOD; Collins
et al., *BMJ* 2024), calibration work (Guo et al., *ICML* 2017), and the Model Card **Factors**
(Mitchell et al., *FAT\** 2019). The deliverable is still the per-case CSV; the deterministic gate
is `scripts/check_metric_reporting.py`.

> Verify exact **CLAIM 2024 item numbers** and any **NSD tolerance** against the source before
> quoting them as formal values — the mapping and tolerances below are described qualitatively by
> design. Do not hand-type a metric value: every number comes from executed code.

## The Metrics Reloaded principle: task fingerprint → metric

- **The metric is derived from the problem, not from habit.** Metrics Reloaded selects metrics from
  the problem fingerprint — task category (classification / segmentation / detection-localization),
  structure size and shape, class prevalence, and whether *where* the model is right matters. A
  metric that ignores a property that matters clinically is the wrong metric.
- **No single metric is sufficient.** Pair a counting/overlap metric with a complementary one (a
  boundary metric, a calibration summary) so a blind spot in one is covered by the other. A lone
  headline number is the recurring pitfall the companion paper warns about.
- **Report per-class / per-structure with a distribution**, not only a global mean — a mean hides
  minority-class and small-structure failure.
- **Define edge-case behaviour explicitly** (empty reference, no positive cases): several metrics
  are undefined there, and a silent convention changes the score.

## Segmentation — overlap **and** boundary, per structure

- Report an overlap metric (Dice or IoU) **with** a boundary metric (**HD95** or **NSD**). Dice is
  a volume-overlap measure: it is insensitive to boundary error and unstable on small or thin
  structures, so it can look high while the contour is clinically wrong.
- **HD95** = 95th-percentile Hausdorff distance — robust to a few outlier surface points relative to
  the raw maximum Hausdorff. **NSD** (normalised surface distance / surface Dice) = the fraction of
  the predicted surface within a **task-specific tolerance τ** of the reference surface; **τ must be
  stated** and is chosen from clinical acceptability, not invented.
- Compute **per structure** with bootstrap 95% CIs obtained by resampling **patients, not pixels**
  (Efron–Tibshirani bootstrap). State the rule for **empty-reference / false-positive-only** cases
  (a Dice of 0/0 is undefined).
- Gate: `PIXEL_ACCURACY_SEG` (pixel/voxel accuracy is dominated by background — never the headline)
  and `NO_BOUNDARY_METRIC`.

## Classification — discrimination, operating point at prevalence, then calibration

- **AUROC and AUPRC.** AUROC summarises ranking across thresholds; under class imbalance the
  precision–recall view (AUPRC) is more informative, because the ROC's false-positive rate uses the
  large negative denominator and can look optimistic when negatives dominate (Saito & Rehmsmeier,
  *PLoS ONE* 2015).
- **Operating-point metrics at the deployment prevalence.** **PPV/NPV** (and accuracy) move with the
  base rate, so values read off an artificially balanced test set mislead at deployment — report
  them at the real prevalence. Sensitivity and specificity are prevalence-independent but depend on
  the operating threshold, so **fix the threshold on the training/tuning folds, never the test set**
  (choosing it on the test set is tuning-on-test and inflates the estimate).
- Bootstrap **95% CIs at the patient level**.
- Gate: `ACCURACY_ONLY` (a bare-accuracy headline under imbalance is flagged).

## Detection / localization — FROC or mAP with the IoU criterion stated

- Report **FROC** (sensitivity versus mean false positives per image) or **mAP**, and **state the
  match criterion** — a prediction counts as a true positive only if its overlap with a
  ground-truth object meets the stated IoU (or centroid/mask) threshold. Per Metrics Reloaded's
  localization category, the metric is undefined without that criterion.
- **Patient-level accuracy is not a detection metric**, and a per-lesion result must not be reported
  as per-patient — respect the analysis unit set in Phase 1.
- Gate: `DETECTION_METRIC_MISSING`.

## Calibration — a separate axis from discrimination

- A model can **discriminate well (high AUROC) and still be miscalibrated**; report calibration
  separately (Guo et al., *ICML* 2017). Use a **reliability diagram** plus a summary (**ECE** or the
  **Brier** score).
- **ECE is binning-sensitive** — state the binning scheme (or prefer a binning-robust summary) and
  do not over-read a single ECE value.
- **TRIPOD+AI** requires reporting **both** discrimination and calibration for a clinical prediction
  model — calibration is not optional reporting.

## Subgroup slices — disaggregated reporting

- Slice every headline metric by the Model Card **Factors** (scanner/vendor, site, age, sex,
  disease severity), and report the **per-subgroup n** so the reader can see which estimates are
  thin.
- Need enough events per subgroup to estimate the metric; otherwise **say so** rather than report a
  noisy point estimate.
- This is disaggregated *reporting*. The formal fairness/equity audit lives in `/model-validation`
  plus the equity probe — cross-reference, do not duplicate it here.

## CLAIM 2024 reporting fit — where the eval outputs land

CLAIM 2024 organises items under the manuscript sections. The model-evaluation deliverable feeds the
**Methods** (metric definitions, reference standard, data partition, threshold selection) and the
**Results** (metrics with uncertainty, calibration, subgroup/failure analysis). `/check-reporting`
owns the item-by-item CLAIM 2024 / TRIPOD+AI audit; this is the routing map.

| Eval output | CLAIM 2024 area (verify item #) | Note |
|---|---|---|
| Metric definitions + how each was computed | Methods | Name the metric and its formula/library; no undefined "accuracy" headline. |
| Reference / ground-truth standard + how derived | Methods | Reader count, blinding, adjudication — state it. |
| Held-out, patient-level data partition | Methods | Cross-link `/model-validation` (split leakage). |
| Performance metrics **with uncertainty (CIs)** | Results | Bootstrap CIs at the analysis unit. |
| Calibration (reliability diagram + ECE/Brier) | Results | Required alongside discrimination (TRIPOD+AI). |
| Subgroup + failure-case analysis | Results | Per-subgroup n; flag thin slices. |
| Threshold + operating point at prevalence | Methods / Results | Threshold fixed on tuning folds, reported prevalence. |

## What the skill checks / advises

1. Run the gate — `PIXEL_ACCURACY_SEG` / `NO_BOUNDARY_METRIC` / `ACCURACY_ONLY` /
   `DETECTION_METRIC_MISSING` must all be zero.
2. Advise the author to **state τ** (NSD), **state the IoU criterion** (detection), and **state the
   deployment prevalence** (operating-point metrics); report **per-structure / per-subgroup with n**;
   give **patient-level bootstrap CIs**; and report **calibration alongside discrimination**.
3. Emit `eval/per_case_metrics.csv` for `/analyze-stats` (DeLong / NRI / IDI / decision curves /
   MRMC) — numbers are never hand-typed, and an uncertain metric or CI method is flagged `[VERIFY]`.

## Verification notes

- **Metrics Reloaded** + pitfalls companion (Maier-Hein, Reinke et al., *Nature Methods* 2024):
  named public standard — grounds the task-fingerprint principle, single-metric-insufficiency,
  per-class reporting, edge-case definition, boundary metrics, and the detection/localization
  category. Cited as a named method, not quoted.
- **CLAIM 2024** (Tejani et al., *Radiology: Artificial Intelligence* 2024): named reporting
  checklist. Exact item numbers are **not** quoted — the table maps outputs to manuscript sections;
  resolve item numbers against the source (`[VERIFY]`). `/check-reporting` owns the audit.
- **TRIPOD+AI** (Collins et al., *BMJ* 2024): named standard; grounds the calibration-and-
  discrimination requirement. Written as base TRIPOD + AI extension.
- **AUPRC under imbalance** (Saito & Rehmsmeier, *PLoS ONE* 2015, **CC-BY**): principle only (ROC vs
  PR on imbalanced data); no text copied.
- **Calibration / ECE** (Guo et al., *ICML* 2017): named methods paper; reliability diagram + ECE,
  with the binning-sensitivity caveat stated qualitatively.
- **NSD / surface Dice with tolerance**: the tolerance-based surface metric (e.g., Nikolov et al.,
  head-and-neck OAR segmentation) recommended for boundary error by Metrics Reloaded; **τ described
  qualitatively, no value invented**.
- **Bootstrap CIs** (Efron & Tibshirani): canonical resampling method; patient-level resampling
  principle.
- **Model Card Factors** (Mitchell et al., *FAT\** 2019): named documentation standard for
  disaggregated reporting axes.
- No DOIs, dataset names, numeric thresholds, prevalences, NSD tolerances, or CLAIM item numbers are
  fabricated; any uncertain specific is flagged `[VERIFY]`.

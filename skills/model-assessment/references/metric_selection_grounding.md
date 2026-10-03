# Metric-selection grounding and CLAIM 2024 reporting fit (model-assessment, Part B)

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

- **AUROC and AUPRC.** AUROC summarises ranking across thresholds and does not depend on
  prevalence. The precision–recall view adds the PPV side, which matters when positives are rare
  (Saito & Rehmsmeier, *PLoS ONE* 2015). AUPRC is **prevalence-dependent**: its no-skill value is
  the prevalence, so report it with the test-set prevalence, and do not carry an AUPRC from an
  enriched or case-control test set over to deployment or compare it across datasets. Whether AUPRC
  should be preferred to AUROC under imbalance is itself contested (McDermott et al., *NeurIPS*
  2024); report both.
- **Operating-point metrics at the deployment prevalence.** **PPV/NPV** (and accuracy) move with the
  base rate, so values read off an artificially balanced test set mislead at deployment — report
  them at the real prevalence. Sensitivity and specificity do not depend on prevalence
  arithmetically, but they often shift with it in practice, through spectrum and case-mix (Leeflang
  et al., *CMAJ* 2013), so the test set's case-mix must match the intended use. They also depend on
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
- **CIs respect clustering.** Lesions and false positives within a patient are correlated, so a
  binomial (Wilson) interval over lesions is too narrow; bootstrap **patients**, carrying all their
  lesions and false positives (Genders et al., *Radiology* 2012; Obuchowski, *Biometrics* 1997).
  Compare two detectors on the same patients with **JAFROC** (Chakraborty & Berbaum, *Med Phys*
  2004; RJafroc), not with per-lesion tests.
- Gate: `DETECTION_METRIC_MISSING`.

## Calibration — a separate axis from discrimination

- A model can **discriminate well (high AUROC) and still be miscalibrated**; report calibration
  separately.
- **Binary risk or diagnostic output** (the usual clinical case): **calibration-in-the-large**
  (intercept), the **calibration slope**, and a **flexible (loess) calibration curve**, plus the
  **Brier** score (Van Calster et al., *BMC Med* 2019, calibration hierarchy). The slope is what
  exposes overfitting: predictions that are too extreme give a slope below 1.
- **ECE** (Guo et al., *ICML* 2017) comes from multi-class top-label confidence. It is
  binning-sensitive and mostly reflects where the predictions cluster; at low prevalence a model
  with a calibration slope of 0.61 can show an ECE of 0.03. Use it only as a supplementary summary
  for multi-class confidence, with the binning stated, never as the calibration evidence for a
  binary risk model.
- **TRIPOD+AI** requires reporting **both** discrimination and calibration for a clinical prediction
  model — calibration is not optional reporting.

## Subgroup slices — disaggregated reporting

- Slice every headline metric by the Model Card **Factors** (scanner/vendor, site, age, sex,
  disease severity), and report the **per-subgroup n** so the reader can see which estimates are
  thin.
- Need enough events per subgroup to estimate the metric; otherwise **say so** rather than report a
  noisy point estimate.
- This is disaggregated *reporting*. The formal fairness/equity audit lives in Part A
  plus the equity probe — cross-reference, do not duplicate it here.

## CLAIM 2024 reporting fit — where the eval outputs land

CLAIM 2024 organises items under the manuscript sections. The Part B deliverable feeds the
**Methods** (metric definitions, reference standard, data partition, threshold selection) and the
**Results** (metrics with uncertainty, calibration, subgroup/failure analysis). `/check-reporting`
owns the item-by-item CLAIM 2024 / TRIPOD+AI audit; this is the routing map.

| Eval output | CLAIM 2024 area (verify item #) | Note |
|---|---|---|
| Metric definitions + how each was computed | Methods | Name the metric and its formula/library; no undefined "accuracy" headline. |
| Reference / ground-truth standard + how derived | Methods | Reader count, blinding, adjudication — state it. |
| Held-out, patient-level data partition | Methods | Cross-link Part A Phase 2 (split leakage). |
| Performance metrics **with uncertainty (CIs)** | Results | Bootstrap CIs at the analysis unit. |
| Calibration (intercept + slope + flexible curve, Brier; ECE only for multi-class confidence) | Results | Required alongside discrimination (TRIPOD+AI). |
| Subgroup + failure-case analysis | Results | Per-subgroup n; flag thin slices. |
| Threshold + operating point at prevalence | Methods / Results | Threshold fixed on tuning folds, reported prevalence. |

## What the skill checks / advises

1. Run the gate — `PIXEL_ACCURACY_SEG` / `NO_BOUNDARY_METRIC` / `ACCURACY_ONLY` /
   `DETECTION_METRIC_MISSING` (and, in manifest mode, `CLASSIFICATION_METRIC_MISSING` /
   `SEGMENTATION_METRIC_MISSING`: no headline metric declared) must all be zero.
2. Advise the author to **state τ** (NSD), **state the IoU criterion** (detection), and **state the
   deployment prevalence** (operating-point metrics); report **per-structure / per-subgroup with n**;
   give **patient-level bootstrap CIs**; and report **calibration alongside discrimination**.
3. Emit `eval/per_case_metrics.csv` for `/analyze-stats` (paired comparison of frozen models,
   added value per `incremental_value.md`, decision curves, MRMC) — numbers are never hand-typed,
   and an uncertain metric or CI method is flagged `[VERIFY]`.

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
  PR on imbalanced data; the PR no-skill line is the prevalence); no text copied. The counterpoint
  that AUPRC is not generally preferable under imbalance: McDermott et al., *NeurIPS* 2024
  (arXiv:2401.06091).
- **Calibration / ECE** (Guo et al., *ICML* 2017): named methods paper; ECE is scoped to
  multi-class top-label confidence, with the binning-sensitivity caveat.
- **Calibration hierarchy** (Van Calster et al., *BMC Med* 2019, doi:10.1186/s12916-019-1466-7):
  intercept, slope and flexible curve for a binary risk model.
- **Clustered detection data** (Genders et al., *Radiology* 2012, doi:10.1148/radiol.12120509;
  Chakraborty & Berbaum, *Med Phys* 2004, doi:10.1118/1.1769352 — JAFROC).
- **Prevalence and case-mix** (Leeflang et al., *CMAJ* 2013, doi:10.1503/cmaj.121286).
- **NSD / surface Dice with tolerance**: the tolerance-based surface metric (e.g., Nikolov et al.,
  head-and-neck OAR segmentation) recommended for boundary error by Metrics Reloaded; **τ described
  qualitatively, no value invented**.
- **Bootstrap CIs** (Efron & Tibshirani): canonical resampling method; patient-level resampling
  principle.
- **Model Card Factors** (Mitchell et al., *FAT\** 2019): named documentation standard for
  disaggregated reporting axes.
- **Generative / synthesis, multiclass, and time-to-event metrics** (Park, Han & Lee, *Radiol Med*
  2024, "Conceptual review of outcome metrics and measures used in clinical evaluation of AI in
  radiology"): named review. Grounds the full-reference (MSE / RMSE / PSNR / SSIM) and no-reference
  (SNR / CNR) image-quality metrics, the **image-quality-vs-downstream-efficacy divergence** (a
  denoised CT with higher CNR but lower lesion sensitivity), multiclass aggregation (one-vs-rest /
  macro / micro / pairwise / Obuchowski index), and time-to-event discrimination (Harrell's C,
  time-dependent ROC). Concepts described qualitatively; no numeric values copied.
- No DOIs, dataset names, numeric thresholds, prevalences, NSD tolerances, or CLAIM item numbers are
  fabricated; any uncertain specific is flagged `[VERIFY]`.

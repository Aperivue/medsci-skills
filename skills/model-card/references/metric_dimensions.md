# Data-quality audit dimensions (model-card)

A short, defensible data-quality checklist to run alongside the Model Card + Datasheet,
informed by the **METRIC framework** for assessing data quality for trustworthy medical AI
(Schwabe et al., *npj Digital Medicine* 2024) and **Datasheets for Datasets** (Gebru et al.,
*Commun. ACM* 2021). It is an **appraisal reference** (it is deliberately *not* a counted
reporting guideline). For each dimension, record a finding in the Datasheet rather than a
score; the goal is disclosure, not a number.

> Verify the exact dimension list / wording against the METRIC paper before quoting it as a
> formal instrument; the dimensions below are the well-established data-quality axes the
> framework and Datasheets converge on, phrased for medical imaging.

| Dimension | What to check | Where it surfaces |
|---|---|---|
| **Completeness** | Missing images / labels / fields; missingness pattern (MCAR/MAR/MNAR) and how handled. | Datasheet Composition / Preprocessing |
| **Correctness / plausibility** | Implausible values, mislabeled cases, label noise; reference-standard quality and inter-reader agreement. | Datasheet Preprocessing/Labeling; Model Card Training Data |
| **Consistency** | Same definition / units / protocol across sites and time; harmonisation applied **after** the split. | Datasheet Collection / Preprocessing |
| **Representativeness / spectrum** | Does the cohort match the deployment population (age, sex, severity, scanner/vendor, site)? Selection on an optional modality is a spectrum bias. | Datasheet Collection; Model Card Factors |
| **Timeliness / recency** | Acquisition time frame; drift vs. current practice/scanners; temporal split if a temporal claim is made. | Datasheet Collection; Model Card Evaluation Data |
| **Provenance / traceability** | Where each instance came from; can the dataset version be reproduced (pair with `/version-dataset`)? | Datasheet Motivation / Maintenance |
| **Label provenance** | Human vs. automated / model-derived ("silver") labels; circularity if model-derived labels evaluate the same model. | Datasheet Preprocessing/Labeling |
| **Fairness / subgroup coverage** | Are protected / clinically-relevant subgroups represented enough to estimate per-subgroup performance? | Model Card Quantitative Analyses; defer depth to `/model-validation` + equity probe |
| **Leakage safety** | Patient-level disjoint split; preprocessing fit on the training fold only; no site/scanner shortcut. | Model Card Evaluation Data; verify with `/model-validation` `check_split_leakage` |

## How to use
1. Walk the table; for each dimension, write the relevant fact into the **Datasheet** (or note
   it as a Model Card caveat). Unknown → `[NEEDS INPUT]`, never a guess.
2. Anything that affects the validity of the headline metric (leakage, representativeness,
   label provenance) is also a `/model-validation` finding — cross-check there.
3. The audit is **disclosure-oriented**: the deliverable is a complete, honest Datasheet +
   Model Card, not a quality score.

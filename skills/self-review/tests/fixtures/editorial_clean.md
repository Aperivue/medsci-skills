# A Deep-Learning Marker for Synthetic Outcome X: Development and Internal Validation

## Abstract

**Background:** Marker X may aid early triage of outcome X. **Methods:** We developed and internally validated a model on a patient-level split. **Results:** The model discriminated outcome X with an area under the curve of 0.84 (95% CI 0.79–0.89) and was well calibrated. **Conclusion:** Marker X identifies patients at higher risk of outcome X and supports triage. These findings are preliminary and require external validation.

## Introduction

Outcome X is common and its early identification changes triage. Existing tools rely on manual scoring, which is slow and operator-dependent. We asked whether a deep-learning marker derived from routine inputs could identify patients at higher risk and inform the triage decision. This study develops such a marker and tests it on a held-out internal cohort, addressing a gap left by prior manual approaches.

## Methods

We assembled a cohort and split it at the patient level into development and held-out sets before any preprocessing. A regularised model was trained with five-fold cross-validation. All analysis code, the dataset schema, and a content-hash manifest are archived (see Data Availability).

## Results

The model discriminated outcome X with an area under the curve of 0.84 (95% CI 0.79–0.89). Calibration was good, with a slope of 0.97 and a Brier score of 0.12. At the triage threshold, sensitivity was 0.82 and specificity was 0.79. In a sensitivity analysis excluding the 41 borderline cases, the adjusted odds ratio was unchanged at 2.18 (95% CI 1.40–3.39), and results were consistent across the two recruitment years. Decision-curve analysis showed net benefit over the manual score across the clinically relevant threshold range.

## Discussion

A routine-input marker identified patients at higher risk of outcome X and added net benefit over the existing manual score, which is the decision it is meant to inform. The effect size corresponds to a clinically meaningful shift in pretest probability. The marker is reproducible and its calibration supports use at the stated threshold.

## Limitations

This single-centre study has three main limitations: it was developed on retrospective data, the marker was measured once, and external validation in an independent cohort is the necessary next step before deployment.

## Data Availability

The analysis code, the dataset schema, the patient-level split assignment, and a reproducibility manifest with the dataset content hash are archived in the project repository, so every reported number can be regenerated from a single committed pipeline.

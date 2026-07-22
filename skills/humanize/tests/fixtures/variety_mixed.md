The cohort was retrospective. Consecutive adults who underwent chest computed tomography at two
centers between January 2019 and December 2022 were eligible, and no patient was excluded on
the basis of scanner vendor or reconstruction kernel. Two radiologists read every examination
independently. Disagreements went to a third reader. That reader was blinded to both prior
assessments, which matters because the second opinion would otherwise inherit the anchor of the
first. The reference standard combined histology with twelve months of imaging follow-up.
Baseline characteristics were compared using the chi-square test. Continuous variables were
summarized as medians with interquartile ranges. The model was trained on the derivation cohort
and locked before any validation data were examined, so no tuning decision could have been
informed by the numbers we now report. Calibration was assessed with reliability diagrams.
Sensitivity and specificity carry bootstrap confidence intervals from two thousand resamples,
computed at the deployment prevalence rather than at the enriched prevalence of the development
set. Subgroup estimates were produced for scanner vendor and slice thickness. Missing
covariates were rare. Complete-case analysis was therefore used, and a sensitivity analysis
with multiple imputation reproduced every point estimate to within one percentage point. All
tests were two-sided. Analyses ran in R 4.3.1. The institutional review board approved the
protocol and waived written informed consent because the extracted data were fully
de-identified before any investigator saw them.

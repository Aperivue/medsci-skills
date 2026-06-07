# Synthetic original-research draft (Methods named methods now cited)

## Introduction

Chronic disease burden continues to rise worldwide [@smith2019]. Risk
stratification tools have proliferated over the last decade [@jones2020], yet
external validation remains uneven [@lee2021]. Prior cohorts established the
prognostic value of the index biomarker [@kim2018], and registry analyses
extended this to older adults [@park2022]. The evidence base nonetheless lacks
competing-risk-aware modeling [@choi2017].

## Methods

### Study population

We assembled a retrospective single-center cohort of adults meeting the
eligibility criteria below. The analytic dataset was frozen before any modeling.

### Statistical analysis

We fitted a Fine-Gray subdistribution hazard model for the competing risk of
non-event mortality [@finegray1999]. Missing covariate data were addressed with
multiple imputation (MICE) under the fully conditional specification
[@white2011]. The robustness of the primary association to unmeasured
confounding was quantified with the E-value [@vanderweele2017]. Estimated
glomerular filtration rate was computed with the CKD-EPI 2021 equation
[@inker2021]. Discrimination was summarized with the concordance statistic
[@harrell1996].

## Results

The cohort comprised consecutive patients over the study window. The primary
model reproduced the previously reported direction of effect [@smith2019].

## Discussion

Our findings align with earlier prognostic work [@brown2015] and extend it to a
competing-risk framework [@white2016]. The magnitude is consistent with two
external cohorts [@green2018; @black2019]. Mechanistically, the association is
plausible [@gray2020], although residual confounding cannot be excluded
[@adams2021]. Generalizability is limited by the single-center design
[@baker2014].

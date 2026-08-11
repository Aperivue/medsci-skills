# ROBINS-E Assessment Guide

Risk Of Bias In Non-randomized Studies — of Exposures.
Reference: Higgins JPT et al. Environment International 2024;186:108602. doi: 10.1016/j.envint.2024.108602.
Website: https://www.riskofbias.info/welcome/robins-e-tool

Version: ROBINS-E (2024)
Licence: CC BY-NC 4.0 (non-commercial) — confirmed via Crossref. Not redistributable verbatim under this repository's MIT licence.
Verification: the seven bias domains and their order were compared against Table 1 of the article
(Europe PMC full text, PMC11098530), and the preliminary-considerations parts A–E, the four
domain-judgement levels, the three per-domain outputs and the domain-1 label
"Low risk of bias (except for concerns about uncontrolled confounding)" against its section 4–6
text. All matched. Item wording stays paraphrased: the source is CC BY-**NC**, which cannot be
redistributed under this repository's MIT licence. Complete the official instrument for anything
you report.

## Purpose

ROBINS-E assesses the risk of **material bias** in individual observational studies examining the effect of an **exposure** on an outcome. Designed for follow-up (cohort) studies. Material bias = bias sufficient to affect the direction of the estimated effect or impact the ability to draw conclusions.

## Structure

ROBINS-E has:
- **Planning stage**: List confounders and consider appropriateness
- **Preliminary considerations** (per study): Sections A-E
- **7 bias domains** with signalling questions
- **Overall judgment** across domains

Signalling question responses: Yes / Probably yes / Probably no / No / No information
(Some questions have domain-specific response options)

Domain judgments: Low risk of bias / Some concerns / High risk of bias / Very high risk of bias

Three outputs per domain:
1. Risk of bias judgment (algorithmic, overridable)
2. Predicted direction of bias
3. Whether bias threatens conclusions (Yes / No / Cannot tell)

## Planning Stage

### P1: List Important Confounding Factors
Specify confounders relevant to all or most studies on this topic. State whether they are particular to specific exposure-outcome combinations.

### P2: Appropriateness Assessment
Will the review use the ROBINS-E assessment of appropriateness (study sensitivity)? → Yes / No
If Yes, complete Appendix 1 (Parts I, II, III).

## Preliminary Considerations (Per Study)

### A. Specify the Result Being Assessed
- ROBINS-E is specific to a particular study result
- Different results from the same study may have different risks of bias
- Specify the numerical result (e.g., RR=1.52, 95% CI 0.83 to 2.77)

### B. Decide Whether to Proceed
- Some study characteristics may directly indicate very high risk of bias
- Screening section to identify such situations before detailed assessment

### C. Specify the Analysis
- Gather information about participants, exposure measure(s), outcome, and analysis methods

### D. Specify the Causal Effect
- Define the causal effect of exposure being estimated
- This is essential: the causal effect defines what the result would be in the absence of bias

### E. Specify Important Confounding Factors
- Specify the known important confounding factors likely to influence the exposure–outcome association
- Identify them by reviewing the literature **and** consulting experts, including members of the review team
- Parts C and D may be completed in either order, but both come before part E

## Domain 1: Risk of Bias Due to Confounding

### Key Signalling Questions
- Were all important confounding domains measured?
- Were all important confounding domains adequately controlled for?
- Was the analysis adjusted for all important confounders, or was matching/restriction used?
- Were appropriate methods used to control confounding (regression, propensity score, IP weighting)?

### Judgment
- **Low risk of bias (except for concerns about uncontrolled confounding)**: All critical confounders well addressed, but residual uncontrolled confounding cannot be eliminated in observational studies
- **Some concerns**: Minor concerns about residual confounding
- **High risk of bias**: Important confounders not adequately controlled
- **Very high risk of bias**: Critical confounding renders the estimate unreliable

*Note: For Domain 1, 'Low risk' is expressed as "Low risk of bias (except for concerns about uncontrolled confounding)" because uncontrolled confounding can never be fully excluded in observational studies.*

## Domain 2: Risk of Bias Arising from Measurement of the Exposure

### Key Signalling Questions
- Was the exposure clearly defined and consistently measured?
- Was exposure assessment valid and reliable?
- Was exposure measured at the appropriate time point?
- Was exposure classification differential with respect to the outcome?

### Judgment
- **Low**: Exposure well-defined, measured validly, non-differential misclassification
- **Some concerns**: Minor measurement issues unlikely to materially affect results
- **High**: Exposure measurement likely to introduce material bias
- **Very high**: Exposure so poorly measured that no useful estimate possible

## Domain 3: Risk of Bias in Selection of Participants

### Key Signalling Questions
- Was selection into the study (or into the analysis) related to both exposure and outcome?
- Was start of follow-up aligned with exposure assessment?
- Were adjustments made for selection effects?

### Judgment
- **Low**: Selection not related to both exposure and outcome
- **Some concerns**: Minor selection issues
- **High**: Selection bias likely to materially affect results
- **Very high**: Extreme selection bias

## Domain 4: Risk of Bias Due to Post-exposure Interventions

### Key Signalling Questions
- Were there post-exposure interventions that could have affected the outcome?
- Were these interventions differential across exposure groups?
- Were they likely to affect the estimated exposure effect?

### Judgment
- **Low**: No important post-exposure interventions, or balanced across groups
- **Some concerns**: Some differential post-exposure interventions
- **High**: Important post-exposure interventions likely bias the result
- **Very high**: Post-exposure interventions dominate the observed effect

## Domain 5: Risk of Bias Due to Missing Data

### Key Signalling Questions
- Were outcome data available for all or nearly all participants?
- Were participants excluded due to missing data on exposure or other variables?
- Was the proportion of missing data similar across exposure groups?
- Were appropriate methods used to handle missing data?

### Judgment
- **Low**: Complete data or minimal, non-differential missingness
- **Some concerns**: Some missing data but unlikely to materially bias results
- **High**: Missing data pattern likely to introduce material bias
- **Very high**: Extensive missing data with differential patterns

## Domain 6: Risk of Bias Arising from Measurement of the Outcome

### Key Signalling Questions
- Could outcome measurement have been influenced by knowledge of exposure status?
- Were outcome assessors blinded to exposure?
- Were outcome measures comparable across exposure groups?
- Was the outcome defined and assessed using validated methods?

### Judgment
- **Low**: Objective outcome or blinded assessment, non-differential measurement
- **Some concerns**: Minor measurement concerns
- **High**: Outcome measurement likely differentially affected by exposure knowledge
- **Very high**: Outcome measurement severely compromised

## Domain 7: Risk of Bias in Selection of the Reported Result

### Key Signalling Questions
- Were multiple outcome measurements reported?
- Were multiple analyses performed (different adjustments, subgroups, models)?
- Is the reported result likely selected from among multiple measurements or analyses?

### Judgment
- **Low**: Pre-specified analysis plan or single planned analysis
- **Some concerns**: Minor concerns about selective reporting
- **High**: Reported result likely selected to favor a particular conclusion
- **Very high**: Clear evidence of selective reporting

## Overall Risk of Bias

Three overall judgments are derived from the domain judgments:

1. **Overall risk of bias**: Most conservative across domains
   - **Low**: Low in all domains
   - **Some concerns**: Some concerns in at least one domain, but no high/very high
   - **High**: High in at least one domain, but not very high in any
   - **Very high**: Very high in at least one domain

2. **Overall predicted direction of bias**: Considering all domains together

3. **Overall: does bias threaten conclusions?**: Yes / No / Cannot tell

Justification should be provided when overriding algorithm-suggested judgments.

## When to Use

- Systematic reviews of observational studies examining exposure effects (environmental, occupational, behavioral, dietary)
- Currently designed for cohort (follow-up) studies
- Not for case-control studies (extension planned)
- Not for intervention studies (use ROBINS-I instead)
- Complementary to GRADE for rating certainty of evidence from observational studies

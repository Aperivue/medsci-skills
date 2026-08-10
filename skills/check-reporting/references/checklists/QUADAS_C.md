# QUADAS-C Assessment Guide

Quality Assessment of Diagnostic Accuracy Studies — Comparative (extension to QUADAS-2).
Reference: Yang B et al. Guidance on how to use QUADAS-C. 2021. Available from: https://osf.io/hq8mf/files/

Version: QUADAS-C (2021)
Source: Yang B, Mallett S, Takwoingi Y, Davenport CF, Hyde CJ, Whiting PF, et al. QUADAS-C: a tool for assessing risk of bias in comparative diagnostic accuracy studies. *Ann Intern Med* 2021;174(11):1592-1599 (DOI 10.7326/M21-2234).
Licence: *Annals of Internal Medicine* (© American College of Physicians) — no open licence.
Verification: **NOT VERIFIED.** The items below have not been compared against the published table. They are an in-house summary; complete the official instrument for anything you report.

## Purpose

QUADAS-C is an extension (add-on) to QUADAS-2 for assessing risk of bias in **comparative diagnostic test accuracy studies** — studies comparing two or more index tests in the same population.

QUADAS-C should be used **together with** QUADAS-2:
- QUADAS-2 assesses risk of bias for each individual test
- QUADAS-C assesses additional risk of bias for the **comparison** between tests

## Structure

QUADAS-C assesses the same 4 domains as QUADAS-2, with comparative signalling questions:
- **Signalling questions**: answered Yes / No / Unclear
- **Risk of bias judgment**: Low / High / Unclear (for the comparison)
- **No applicability assessment** (inferred from QUADAS-2 judgments)

## Comparative Study Designs

1. **#1 Fully paired**: All participants receive all index tests (most robust)
2. **#2 Randomized**: Participants randomly allocated to one index test
3. **#3 Partially paired, random subset**: Some randomly selected for multiple tests
4. **#4 Partially paired, nonrandom subset**: Some receive multiple tests by clinical decision
5. **#5 Unpaired nonrandomized**: Different participants receive different tests

Designs #1, #2, and #3 protect against confounding. Designs #4 and #5 have serious confounding potential.

## Four Phases of Completion

1. State the review question (which tests are compared, for what condition, in which population)
2. Tailor the tool (add/omit signalling questions per review)
3. Review the flow diagram (must show how participants were assigned to index tests)
4. Judge risk of bias (and applicability, based on QUADAS-2)

## Domain 1: Patient Selection

### Signalling Questions
1. **(C1.1)** Was the risk of bias for each index test judged 'low' for this domain?
   - If any index test is judged 'unclear' or 'high' in QUADAS-2, answer 'no'
2. **(C1.2)** Was a fully paired or randomized design used?
   - Designs #1, #2, and #3 (partially paired, random subset) → 'yes' or imply low risk
   - A 'no' answer should almost always prompt 'high risk' for this domain
3. **(C1.3)** Was the allocation sequence random? *(only applicable to randomized designs)*
   - Random: computer-generated numbers, random number tables, drawing lots
   - Non-random: alternation, dates, clinician preference
4. **(C1.4)** Was the allocation sequence concealed until patients were enrolled and assigned? *(only applicable to randomized designs)*
   - Appropriate: central randomization, telephone/internet service, sealed opaque envelopes

### Risk of Bias Judgment
- **Low**: 'Yes' to all applicable signalling questions
- **High**: 'No' to C1.2 (not fully paired/randomized) almost always → high risk; 'No' to other questions raises concern
- **Unclear**: Insufficient information to judge

## Domain 2: Index Test

### Signalling Questions
1. **(C2.1)** Was the risk of bias for each index test judged 'low' for this domain?
   - If any test is 'high' or 'unclear' in QUADAS-2, the comparison is also at risk
2. **(C2.2)** Were the index test results interpreted without knowledge of the results of the other index test(s)? *(only for paired/partially paired designs #1, #3, #4)*
   - Consider: subjectivity of interpretation, order of testing, whether output is automated
3. **(C2.3)** Is undergoing one index test unlikely to affect the performance of the other index test(s)? *(only for paired/partially paired designs #1, #3, #4)*
   - Consider: learning effects, fatigue, tissue distortion, sample depletion
4. **(C2.4)** Were the index tests conducted and interpreted without advantaging one of the tests?
   - Tests should be performed under similar conditions; differences in sample handling, equipment generation, or operator experience may bias the comparison

### Risk of Bias Judgment
- **Low**: 'Yes' to all applicable signalling questions
- **High**: 'No' to any question suggesting the comparison is unfairly biased
- **Unclear**: Insufficient information

## Domain 3: Reference Standard

### Signalling Questions
1. **(C3.1)** Was the risk of bias for each index test judged 'low' for this domain?
   - Reference standard misclassification biases both individual and comparative accuracy
2. **(C3.2)** Did the reference standard avoid incorporating any of the index tests?
   - If one index test is part of the reference standard, its accuracy is artificially inflated relative to the other test

### Risk of Bias Judgment
- **Low**: 'Yes' to all signalling questions
- **High**: 'No' to any, particularly if incorporation affects tests asymmetrically
- **Unclear**: Insufficient information

## Domain 4: Flow and Timing

### Signalling Questions
1. **(C4.1)** Was the risk of bias for each index test judged 'low' for this domain?
   - Timing, verification, and exclusion issues for individual tests also bias the comparison
2. **(C4.2)** Was there an appropriate interval between the index tests?
   - Simultaneous or near-simultaneous testing avoids disease progression bias
   - What is 'appropriate' depends on the disease (acute vs. chronic)
3. **(C4.3)** Was the same reference standard used for all index tests?
   - Different reference standards across test groups (e.g., surgery vs. follow-up) introduce differential verification bias
   - If reference standards are exchangeable (detect same condition equally), a 'no' may not imply high risk
4. **(C4.4)** Are the proportions and reasons for missing data similar across index tests?
   - Differential missing data between test groups can bias the comparison
   - Consider both proportion and mechanism of missingness

### Risk of Bias Judgment
- **Low**: 'Yes' to all signalling questions
- **High**: 'No' to any question, particularly C4.3 (differential verification) or C4.4 (differential missing data)
- **Unclear**: Insufficient information

## Optional Additional Signalling Questions (Table 4)

These are not part of the core tool but can be added to tailor for specific reviews:

| Domain | Question | Applicable to |
|--------|----------|---------------|
| Patient Selection | Were the same patient selection criteria used for those assigned to each index test? | Unpaired nonrandomized studies |
| Patient Selection | If patients received all index tests, was the decision to use all tests made before participants were recruited? | Paired studies |
| Patient Selection | Did the study avoid using prior tests as inclusion criteria that were correlated with only one of the index tests? | All |
| Index Test | Did the study avoid using index test thresholds that are likely to advantage some of the index tests? | Studies with nonbinary tests |
| Reference Standard | Is the mechanistic basis of one index test more closely shared with the reference standard than the other? | All |

## Presenting QUADAS-C Results

- Present QUADAS-2 and QUADAS-C results side by side
- QUADAS-C results are specific to each test comparison (present separately if multiple comparisons)
- Use traffic-light tables: + (low risk, green), - (high risk, red), ? (unclear, yellow)
- Templates available at www.quadas.org

## When to Use

- Systematic reviews comparing two or more diagnostic tests head-to-head
- Should always be used alongside QUADAS-2 (not as a replacement)
- Primarily designed for fully paired (#1) and randomized (#2) designs
- Can be adapted for other comparative designs with appropriate tailoring

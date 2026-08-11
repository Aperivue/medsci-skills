# QUADAS-2 Assessment Guide

Quality Assessment of Diagnostic Accuracy Studies, version 2.
Version: QUADAS-2 (2011) — 4 domains, **10 signalling questions** (3 / 2 / 2 / 3), risk of bias for every
domain and applicability for the first three only.
Source: Whiting PF, Rutjes AWS, Westwood ME, Mallett S, Deeks JJ, Reitsma JB, et al. QUADAS-2: a
revised tool for the quality assessment of diagnostic accuracy studies. *Ann Intern Med*
2011;155(8):529-536 (DOI 10.7326/0003-4819-155-8-201110180-00009). The tool itself, training material
and worked examples were distributed from www.quadas.org; that domain no longer resolves, and the
QUADAS group now distributes its tools from
https://www.bristol.ac.uk/population-health-sciences/projects/quadas/

> **Fidelity and licence.** QUADAS-2 is published in *Annals of Internal Medicine* (© American College
> of Physicians) under **no open licence**. **Verified against the published article**: the four
> domains, the 3 / 2 / 2 / 3 split of signalling questions, what each question asks, the answer
> options, the judgement levels, and the restriction of applicability to the first three domains all
> match. The descriptions below state what each question asks **in our own words** rather than
> reproducing the published wording. **Complete the official QUADAS-2 form from www.quadas.org for
> any assessment you report.**
>
> **QUADAS-3 has superseded this tool.** The QUADAS group states that "QUADAS-3 is the current
> iteration of the QUADAS tool and is the current recommended version" — it extends QUADAS-2 by
> introducing an explicit ideal-test-accuracy-trial comparator and by moving assessment **from the
> study level to the level of individual accuracy estimates**. This file documents QUADAS-2, which
> remains what most published reviews used. For a new review use **`QUADAS3.md`**;
> `QUADAS_C.md` should now be paired with QUADAS-3 rather than with this tool.

## How the tool is applied — four phases

QUADAS-2 is not a fixed questionnaire. The statement specifies four phases, and skipping the second
is the most common misuse:

1. **State the review question** — patients, index test, reference standard and target condition.
   Describe patients by setting, the intended use of the index test, presentation, and prior testing,
   because accuracy depends on where in the diagnostic pathway the test sits.
2. **Tailor the tool to the review.** Add or omit signalling questions and write review-specific
   guidance on how each is to be judged. (For an objective index test, for example, the question about
   blinding the interpreter to the reference standard may not apply.) Avoid piling on extra questions.
   At least two people should pilot the tailored tool; refine it if agreement is poor.
3. **Draw the study's flow diagram** — use the published one, or draw it yourself if it is absent or
   inadequate. It need not be reported; it exists to make the flow-and-timing judgements possible.
4. **Judge bias and applicability**, recording the information each judgement rests on.

## Answers and judgements

- **Signalling questions**: Yes / No / Unclear, phrased so that **Yes indicates low risk of bias**.
- **Risk of bias**: Low / High / Unclear.
- **Applicability concern** (domains 1–3 only): Low / High / Unclear.
- **Unclear is only for insufficient reporting**, not for a difficult judgement.

**How a "No" is handled.** If every signalling question in a domain is Yes, risk of bias can be judged
low. A **No does not automatically make the domain High** — it establishes that *potential for bias
exists*, and the reviewer then applies the review-specific guidance written in phase 2 to reach the
judgement. A file or workflow that maps "any No → High" has removed the judgement the tool asks for.

## Domain 1: Patient Selection

**Risk of bias — could patient selection have introduced bias?**

1. Whether enrolment took a consecutive or random sample of eligible patients.
2. Whether a case–control design was avoided.
3. Whether the study avoided inappropriate exclusions.

*Why it matters*: enrolling patients whose diagnosis is already confirmed, or excluding the
difficult-to-diagnose, inflates apparent accuracy; excluding patients with obvious signs of the target
condition can deflate it.

**Applicability** — whether the included patients and the setting differ from the review question
(severity, demographics, comorbidity and differential diagnosis, setting, prior testing).

## Domain 2: Index Test

**Risk of bias — could the conduct or interpretation of the index test have introduced bias?**

1. Whether the index test was interpreted without knowledge of the reference standard result.
2. Whether a threshold, if one was used, was prespecified.

*Why it matters*: this is the diagnostic equivalent of blinding, and its force depends on how
subjective the index test is and on the order of testing. Choosing the threshold after the fact to
maximise sensitivity or specificity overstates performance that will not hold in a new sample.

**Applicability** — whether the index test, how it was carried out, or how it was interpreted differs
from the review question.

## Domain 3: Reference Standard

**Risk of bias — could the reference standard, its conduct or its interpretation have introduced bias?**

1. Whether the reference standard is likely to classify the target condition correctly.
2. Whether the reference standard was interpreted without knowledge of the index test result.

*Why it matters*: accuracy estimates assume the reference standard is correct, so that any
disagreement is the index test's error.

**Applicability** — whether the target condition **as the reference standard defines it** differs from
the one in the review question.

## Domain 4: Flow and Timing

**Risk of bias — could patient flow have introduced bias?**

1. Whether the interval between index test and reference standard was appropriate.
2. Whether all patients received the same reference standard.
3. Whether all patients were included in the analysis.

*Why it matters*: an interval long enough for the condition to change causes misclassification, and
how long is too long depends on the condition. Verifying only some patients, or verifying different
patients with different reference standards, biases the estimate. Patients lost between enrolment and
the 2 × 2 table differ systematically from those who remain.

**This domain has no applicability judgement.**

## Reporting the assessment

- **Do not produce a summary quality score.** The statement is explicit about this, for the reasons
  well established in the literature on quality scores.
- A study low on every domain may be called low risk of bias, or low concern for applicability,
  overall. High or unclear on one or more domains means it is at risk of bias, or of concern.
- At minimum, report the assessment across all included studies — how many were low, high or unclear
  per domain — and consider highlighting signalling questions on which studies consistently do badly.
- Restricting the primary analysis to low-risk studies is legitimate, but it is often better to
  include everything and then investigate heterogeneity — by subgroup, sensitivity analysis, or by
  entering domains as covariates in meta-regression.
- QUADAS-2 does **not** cover studies comparing multiple index tests. The development group considered
  it and concluded the evidence base was insufficient.

## Common Issues in DTA Studies

- **Partial verification bias**: Not all patients receive the reference standard (especially when invasive, e.g., biopsy)
- **Differential verification**: Different reference standards used for different patients
- **Incorporation bias**: Index test forms part of the reference standard
- **Review bias**: Knowledge of index test results influences reference standard interpretation
- **Clinical review bias**: Additional clinical information available during index test interpretation
- **Uninterpretable results**: Exclusion of technically inadequate or indeterminate results

## Related

- `PRISMA_DTA.md` items 12 and 19 are the reporting counterparts: the methods used for this
  assessment, and its result presented **for each study**.

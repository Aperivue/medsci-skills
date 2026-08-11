# RoB 2 Assessment Guide

Revised Cochrane Risk-of-Bias tool for Randomised Trials.
Version: RoB 2 (22 August 2019). Full guidance and the current tool: https://www.riskofbias.info
Source: Sterne JAC, Savović J, Page MJ, Elbers RG, Blencowe NS, Boutron I, et al. RoB 2: a revised
tool for assessing risk of bias in randomised trials. *BMJ* 2019;366:l4898 (DOI 10.1136/bmj.l4898;
PMID 31462531).

> **Fidelity and licence.** **No open licence was found for the article** — Crossref returns only
> BMJ's text-and-data-mining policy, and `LICENSES.md` previously claimed CC BY for it on no
> evidence. The signalling questions below were checked against the **official RoB 2 template and
> full guidance document** distributed at riskofbias.info (version of 22 August 2019); their
> wording is short-form and paraphrased. **Complete the official RoB 2 form for any assessment you
> report.**
>
> Verification: every signalling question, its conditionality, the response options and the
> domain- and overall-judgement rules were compared against that template and guidance. Four
> problems were found and corrected: two questions were **missing** from the assignment variant of
> domain 2 (2.5, 2.7), question 2.5 of the adherence variant had **inverted polarity** (the tool
> asks about *non-adherence*), domain 5's three questions had been **collapsed into two**, and the
> missing-data judgement carried a **">95%" threshold that the tool does not define** — the
> guidance defines "nearly all" qualitatively and gives no percentage.

Reference: Sterne JAC et al. BMJ 2019;366:l4898. PMID: 31462531.

## Structure

RoB 2 is applied **to a specific result** — one outcome, one numerical result, in one trial. Record
the experimental and comparator interventions, the outcome, and the numerical result before you
start.

- **Signalling question responses**: Yes / Probably yes / Probably no / No / No information (and
  **NA** where a question is conditional and its condition was not met)
- **Domain judgement**: Low risk of bias / Some concerns / High risk of bias
- **Optional, per domain and overall**: the predicted **direction** of bias — NA, favours
  experimental, favours comparator, towards null, away from null, or unpredictable

Questions written as "If … to N.n" are **conditional**: ask them only when the stated answer was
given to the earlier question.

## Before domain 2: state the effect of interest

The review team must declare whether the aim for this result is to assess **the effect of
assignment** to intervention (the intention-to-treat effect) or **the effect of adhering** to
intervention. Domain 2 has a different set of questions for each; do not mix them.

## Domain 1: Bias arising from the randomisation process

| # | Signalling question |
|---|---------------------|
| 1.1 | Was the allocation sequence random? |
| 1.2 | Was the allocation sequence concealed until participants were enrolled and assigned to interventions? |
| 1.3 | Did baseline differences between intervention groups suggest a problem with the randomisation process? |

The tool does not aim to identify baseline imbalances that arose by chance; a small number of
"statistically significant" differences at 0.05 is usually compatible with chance.

## Domain 2: Bias due to deviations from the intended interventions

### Variant A — effect of **assignment** to intervention

| # | Signalling question |
|---|---------------------|
| 2.1 | Were participants aware of their assigned intervention during the trial? |
| 2.2 | Were carers and people delivering the interventions aware of participants' assigned intervention during the trial? |
| 2.3 | *If Y/PY/NI to 2.1 or 2.2:* Were there deviations from the intended intervention that arose because of the trial context? |
| 2.4 | *If Y/PY to 2.3:* Were these deviations likely to have affected the outcome? |
| 2.5 | *If Y/PY/NI to 2.4:* Were these deviations from intended intervention balanced between groups? |
| 2.6 | Was an appropriate analysis used to estimate the effect of assignment to intervention? |
| 2.7 | *If N/PN/NI to 2.6:* Was there potential for a substantial impact (on the result) of the failure to analyse participants in the group to which they were randomised? |

### Variant B — effect of **adhering** to intervention

| # | Signalling question |
|---|---------------------|
| 2.1 | Were participants aware of their assigned intervention during the trial? |
| 2.2 | Were carers and people delivering the interventions aware of participants' assigned intervention during the trial? |
| 2.3 | *If applicable, and if Y/PY/NI to 2.1 or 2.2:* Were important non-protocol interventions balanced across intervention groups? |
| 2.4 | *If applicable:* Were there failures in implementing the intervention that could have affected the outcome? |
| 2.5 | *If applicable:* Was there **non-adherence** to the assigned intervention regimen that could have affected participants' outcomes? |
| 2.6 | *If N/PN/NI to 2.3, or Y/PY/NI to 2.4 or 2.5:* Was an appropriate analysis used to estimate the effect of adhering to the intervention? |

## Domain 3: Bias due to missing outcome data

| # | Signalling question |
|---|---------------------|
| 3.1 | Were data for this outcome available for all, or nearly all, participants randomised? |
| 3.2 | *If N/PN/NI to 3.1:* Is there evidence that the result was not biased by missing outcome data? |
| 3.3 | *If N/PN to 3.2:* Could missingness in the outcome depend on its true value? |
| 3.4 | *If Y/PY/NI to 3.3:* Is it likely that missingness in the outcome depended on its true value? |

**"Nearly all" is not a percentage.** The guidance defines it as: the number of participants with
missing outcome data is so small that their outcomes, whatever they were, could have made no
important difference to the estimated effect. Do not substitute a 95% or 80% rule — RoB 2 states
none.

**Low risk** requires any one of: (i) outcome data available for all, or nearly all, randomised
participants; **or** (ii) evidence that the result was not biased by missing outcome data;
**or** (iii) missingness in the outcome could not depend on its true value.

## Domain 4: Bias in measurement of the outcome

| # | Signalling question |
|---|---------------------|
| 4.1 | Was the method of measuring the outcome inappropriate? |
| 4.2 | Could measurement or ascertainment of the outcome have differed between intervention groups? |
| 4.3 | *If N/PN/NI to 4.1 and 4.2:* Were outcome assessors aware of the intervention received by study participants? |
| 4.4 | *If Y/PY/NI to 4.3:* Could assessment of the outcome have been influenced by knowledge of intervention received? |
| 4.5 | *If Y/PY/NI to 4.4:* Is it likely that assessment of the outcome was influenced by knowledge of intervention received? |

## Domain 5: Bias in selection of the reported result

| # | Signalling question |
|---|---------------------|
| 5.1 | Were the data that produced this result analysed in accordance with a pre-specified analysis plan that was finalised before unblinded outcome data were available for analysis? |
| 5.2 | Is the numerical result being assessed likely to have been selected, on the basis of the results, from multiple eligible outcome **measurements** (e.g. scales, definitions, time points) within the outcome domain? |
| 5.3 | Is the numerical result being assessed likely to have been selected, on the basis of the results, from multiple eligible **analyses** of the data? |

5.2 and 5.3 are separate questions. Selecting a measurement and selecting an analysis are
different acts, and a result can be at risk from one and not the other.

## Overall risk of bias

- **Low risk of bias**: low risk of bias for all domains
- **Some concerns**: some concerns in at least one domain, but not high risk of bias in any domain
- **High risk of bias**: high risk of bias in at least one domain, **or** some concerns for multiple
  domains in a way that substantially lowers confidence in the result

## When to Use

- Use for **individually randomised, parallel-group trials** (default)
- Variants are published for cluster-randomised trials and crossover trials — use the matching variant
- Do NOT use for non-randomised studies (use ROBINS-I instead)

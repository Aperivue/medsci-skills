# RoB NMA Assessment Guide

Risk of Bias in Network Meta-Analysis tool.
Website: https://www.riskofbias.info

Version: RoB NMA (2025) — 17 items in 3 domains
Source: Lunny C, Higgins JPT, White IR, Dias S, Hutton B, Pham B, et al. Risk of Bias in Network Meta-Analysis (RoB NMA) tool. *BMJ* 2025;388:e079839 (DOI 10.1136/bmj-2024-079839).
Licence: CC BY 4.0 — confirmed via Crossref.
Verification: all 17 signalling statements were extracted from the guidance article's own item
sections (Europe PMC full text, PMC11915405) and compared statement by statement, together with
the domain and overall judgement rules. **This file previously carried 18 invented items**; only
statement 1.1 survived the comparison.

## Purpose

The RoB NMA tool assesses the risk of bias in **a single network meta-analysis** by identifying
limitations in how the NMA was conducted, including how the evidence was assembled, that could
bias the NMA's results or conclusions.

It is **not** a tool for the primary studies inside the network (use RoB 2 or ROBINS-I) and
**not** a tool for the systematic review that contains the NMA (use ROBIS or AMSTAR 2). It is
meant to be used alongside one of the latter. One review yields one ROBIS assessment but as many
RoB NMA assessments as there are NMAs.

## Structure

**17 items** as signalling statements, in 3 domains:

1. Interventions and network geometry (4 statements)
2. Effect modifiers (4 statements)
3. Statistical synthesis (9 statements)

Response options: **true / probably true / probably false / false / no information**. *True*
indicates the lowest risk of bias. Item 3.9 may also be answered *not applicable*.

Statements 2.4 and 3.8 are **conditional** — they are considered only when a preceding statement
was answered false or probably false.

Domain-level judgment: **low risk of bias / some concerns / high risk of bias**, supported by
written justification and quotes from the NMA manuscript.

## Domain 1: Interventions and Network Geometry

How the interventions were selected and grouped, and whether they are an appropriate set for
performing an NMA.

| # | Signalling statement |
|---|----------------------|
| 1.1 | All interventions and their comparators included in the NMA are reasonable alternatives for the whole target population |
| 1.2 | All eligible interventions were included in the network |
| 1.3 | Interventions were appropriately grouped into nodes in the network |
| 1.4 | All compared interventions were connected through a suitable chain of within study comparisons |

## Domain 2: Effect Modifiers

Whether the studies contributing to different direct comparisons are similar enough on the
characteristics that modify the intervention effect (the transitivity requirement).

| # | Signalling statement |
|---|----------------------|
| 2.1 | Outcome definitions and time points were similar across direct comparisons in the network |
| 2.2 | Effect modifying participant characteristics were similar across direct comparisons in the network |
| 2.3 | Effect modifying study characteristics were similar across direct comparisons in the network |
| 2.4 | *(only if 2.1, 2.2 or 2.3 was false or probably false)* The analysis appropriately looked at the differences in effect modifiers across the network |

## Domain 3: Statistical Synthesis

Non-reporting biases, biases within the primary studies, statistical methods, and conflict
between direct and indirect evidence.

| # | Signalling statement |
|---|----------------------|
| 3.1 | The analysis respected within study randomisation |
| 3.2 | No publication bias or other selective non-reporting biases were suspected |
| 3.3 | All predefined analyses, and only those analyses, were reported, or discrepancies were explained |
| 3.4 | Biases in primary studies were minimal or addressed in the synthesis |
| 3.5 | Appropriate methods were used to handle multi-arm studies |
| 3.6 | Appropriate assumptions were made about homogeneity or heterogeneity of effects within comparisons |
| 3.7 | No evidence of conflict between direct and indirect estimates of the same effect |
| 3.8 | *(only if 3.7 was false or probably false)* Conflicting results between direct and indirect evidence were adequately dealt with |
| 3.9 | If a bayesian analysis was performed, the choice of prior distributions was appropriate |

## Overall Judgment

An overall judgment may be made about the **results** of the NMA, its **conclusions**, or both —
whichever the assessor intends to use. Risk of bias at the systematic-review level (ROBIS or
AMSTAR 2) is combined with the three RoB NMA domain judgments. When RoB NMA is used with ROBIS,
ROBIS phase 3 is omitted and only its first three domains are considered.

**Bias in the results of the NMA** — low risk of bias / some concerns / high risk of bias. If all
domains were judged low risk, a judgment of low risk should generally be made; otherwise the
assessor decides between some concerns and high risk. Some concerns in multiple domains may
warrant an overall judgment of high risk.

**Bias in the conclusions of the NMA** — concerns / no concerns. The question is whether the NMA
authors dealt with all the limitations identified. Items 3.5, 3.6 and 3.8 should be reconsidered
here, because inappropriate modelling choices can lead to uncertainty being under- or
overestimated. The two judgments can differ: estimated effects may be at high risk of bias
because of the primary studies while the conclusions are at low risk, if that risk was carefully
taken into account. If the effects are at high risk because of how the NMA itself was conducted,
the conclusions are unlikely to be at low risk.

Focus on bias in results when the NMA results feed a decision model; focus on bias in conclusions
when the conclusions are used for decision making.

## Note on treatment rankings

There is **no separate item for ranking probabilities**. The tool's authors state that the factors
affecting rankings — unequal numbers of studies per comparison, study sample sizes, network
configuration, effect sizes — are already covered by the items above. Assessors should, however,
consider potential bias from rankings when judging the conclusions, since overinterpretation of
rankings can bias them.

## When to Use

- Assessing the risk of bias of a published network meta-analysis
- Guideline development involving multiple treatment comparisons
- Overviews of NMAs
- Paired with ROBIS or AMSTAR 2 for the review, and RoB 2 / ROBINS-I for the primary studies

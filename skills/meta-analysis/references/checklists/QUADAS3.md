# QUADAS-3 Assessment Guide

Quality Assessment of Diagnostic Accuracy Studies, version 3 — **the current recommended version**.
Version: QUADAS-3 tool v1.2 — 6 phases, 4 domains, **20 signalling questions** (4 / 4 / 8 / 4).
Source: Whiting PF, Tomlinson E, Rutjes AWS, Davenport C, Yang B, Westwood M, et al. QUADAS-3: a
revised tool for the quality assessment of diagnostic test accuracy studies. *Ann Intern Med*
2026;179(4):548-555 (DOI 10.7326/ANNALS-25-02104). The tool itself, the Explanation & Elaboration
report and an introductory video are distributed by the QUADAS group at
https://www.bristol.ac.uk/population-health-sciences/projects/quadas/quadas-3/
Explanation & Elaboration: Davenport CF, Rutjes AWS, Mallett S, Tomlinson E, Yang B, et al.
QUADAS-3 explanation and elaboration: guidance for quality assessment of diagnostic test accuracy
studies. *Ann Intern Med* 2026;179(4):e2504943 (DOI 10.7326/ANNALS-25-04943).
Resource site: **www.quadas.info** (the older www.quadas.org no longer resolves).

> **Fidelity and licence.** QUADAS-3 is published in *Annals of Internal Medicine* (© American
> College of Physicians) under **no open licence** — Crossref returns only ACP's text-and-data-mining
> policy. The descriptions below state what each question asks **in our own words** rather than
> reproducing the published wording. **Complete the official QUADAS-3 form (`QUADAS-3 1.2.docx`)
> from the page above for any assessment you report, and read the E&E report before using it.**
>
> Verification: the six phases and when each is completed, the four domains, all 20 signalling
> questions, the response options, the domain-level rule, which domains carry an applicability
> judgement, and the overall-judgement rules were compared against **the official tool document
> v1.2** distributed by the QUADAS group. All matched. The *Using QUADAS-C with QUADAS-3*,
> *Tailoring* and *no "moderate" grade* sections below are taken from the **Explanation and
> Elaboration paper**, read directly.

## QUADAS-3 supersedes QUADAS-2

The QUADAS group states QUADAS-3 "is the current version of QUADAS and the tool that we recommend."
For a new review, use this file. `QUADAS2.md` documents the 2011 tool, which is what most published
reviews used and what you will still be reading in them.

What changed, in the group's own framing:

| | QUADAS-2 | QUADAS-3 |
|---|---|---|
| Unit of assessment | the **study** | **each set of accuracy estimates** |
| Comparator for judging | implicit | an explicit **ideal test accuracy trial**, defined per synthesis question |
| Synthesis questions | one, implicit | **multiple, defined up front** |
| Overall judgment | none | **a formal phase (6)** |
| Phases | 4 | **6** |
| Domains | Patient Selection, Index Test, Reference Standard, Flow and Timing | **Participants, Index Test, Target Condition, Analysis** |
| Signalling questions | 10 (3/2/2/3) | **20 (4/4/8/4)** |
| Third judgement level | "unclear" | **"insufficient information" (II)** |

Note the domain rename: QUADAS-2's *Flow and Timing* is gone. Timing moved into **Target
Condition** (the index-test-to-reference-standard interval), and participant exclusions, missing
data and the unit of analysis moved into the new **Analysis** domain.

**Comparative accuracy reviews**: the group recommends using **QUADAS-C in addition to QUADAS-3**
(`QUADAS_C.md`). QUADAS-C was written against QUADAS-2 and needs adaptation — see the next section.

## Using QUADAS-C with QUADAS-3

For comparative accuracy studies — where two or more index tests are compared — the guideline says
to use **QUADAS-C alongside QUADAS-3**, because such studies carry additional sources of bias
(confounding between tests, and interference of one test with another).

QUADAS-C was written as an extension of QUADAS-2, so it needs adapting. **An updated QUADAS-C is
in development**; what follows are the E&E's own *preliminary* modifications, not a finished tool.

### What you assess

The unit is a **comparative measure** — for example the difference in sensitivity or in specificity
between two tests. Most primary studies report only the separate estimate for each index test, so
**you will usually have to compute the comparative measure yourself.** Specify which estimate a
QUADAS-C assessment refers to, exactly as you do in QUADAS-3 phase 4.

### Domains are renamed onto QUADAS-3's

| QUADAS-C (as published) | becomes |
|---|---|
| Patient Selection | **Participants** |
| Index Test | Index Test *(unchanged)* |
| Reference Standard | **Target Condition** |
| Flow and Timing | **Analysis** |

### Three signalling questions change (E&E Table 8)

| QUADAS-C question | Change |
|---|---|
| **C3.2** Did the reference standard avoid incorporating any of the index tests? | **Removed** — it overlaps QUADAS-3 item 3.4 |
| **C4.2** Was there an appropriate interval between the index tests? | **Moved to domain 2** (Index Test) |
| **C4.3** Was the same reference standard used for all index tests? | **Moved to domain 3** (Target Condition) |

Everything else carries over unchanged.

### Answers and judgements follow QUADAS-3

Signalling questions take **Y / PY / PN / N / NI**; each domain is judged **low / high /
insufficient information**. The overall judgement for the comparative estimate:

- **low** if all domains are low
- **high** if at least one domain is high
- **insufficient information** if at least one domain is II and none is high

## The six phases

| Phase | What | How often |
|---|---|---|
| 1 | State the systematic review synthesis question(s) | once per review |
| 2 | Define the **ideal test accuracy trial** for each synthesis question | once per review |
| 3 | Draw a flow diagram | once per study |
| 4 | Identify which accuracy estimates to assess | once per study |
| 5 | Assess risk of bias and applicability | for each selected estimate |
| 6 | Overall judgment | for each selected estimate |

Phases 1 and 2 are review-level and **belong in the review protocol**. Phases 3–4 are study-level.
Phases 5–6 run once per selected set of estimates.

**Phase 1** — a review may address more than one synthesis question. Specify each with its
population, index test(s) and target condition, and pre-specify them in the protocol.

**Phase 2** — the ideal test accuracy trial is the study that would answer the synthesis question
with minimum bias and maximum applicability. Define it per question across: objective,
participants, index test(s), definition of the target condition, and analysis. Every later
judgement is made **against this trial**, not against an unstated ideal.

**Phase 4** — a single primary study usually yields several two-by-two tables. Assess only the
estimates relevant to a synthesis question. Record, for each: the synthesis question, the numerical
result, participants, index test and threshold, target condition, reference standard, unit of
analysis, and the analysis method. After the first estimate, **only the domains whose
characteristics differ between estimates need reassessing**.

## Phase 5 — signalling questions

Signalling questions: **Y / PY / PN / N / NI**. Domain risk-of-bias judgement: **low / high /
insufficient information (II)**.

### Domain 1: Participants (4)

| # | Signalling question |
|---|---------------------|
| 1.1 | Was a single-gate design used? |
| 1.2 | Were participants prospectively enrolled? |
| 1.3 | Was a consecutive or random sample of participants included? |
| 1.4 | Is the study group a representative sample of the intended-use population? |

*Applicability*: does the included population match the ideal trial's?

Participants who dropped out or were excluded because they did not receive the index test or the
reference standard belong in **Domain 4 (Analysis)**, not here.

### Domain 2: Index Test (4)

| # | Signalling question |
|---|---------------------|
| 2.1 | Was the index test conducted and interpreted according to the recommended instructions? |
| 2.2 | Were the index test results interpreted without knowledge of the reference standard results? |
| 2.3 | Were the index test results interpreted with the same information that would be available when the test is used in practice? |
| 2.4 | If an index test threshold was used, was it standard or pre-specified? |

*Applicability*: does the index test, its conduct and its interpretation match the ideal trial's?

2.3 is new relative to QUADAS-2 and cuts both ways — a reader given **more** information than they
would have in practice is as much a problem as one given less.

### Domain 3: Target Condition (8)

| # | Signalling question |
|---|---------------------|
| 3.1 | Does the reference standard adequately identify those with and without the target condition? |
| 3.2 | Was the target condition assessed in all participants? |
| 3.3 | Was the target condition assessed in the same way in all participants? |
| 3.4 | Did the reference standard avoid incorporating the index test? |
| 3.5 | Was the reference standard conducted and interpreted according to the recommended instructions? |
| 3.6 | Were the reference standard results interpreted without knowledge of the index test results? |
| 3.7 | If a reference standard threshold was used, was it standard or pre-specified? |
| 3.8 | Was there an appropriate time interval between index test and reference standard? |

*Applicability*: does the target condition as defined by the reference standard match the ideal
trial's?

This domain absorbs QUADAS-2's Reference Standard domain **and** its verification and timing
questions. 3.2 and 3.3 are partial and differential verification; 3.8 is the interval that used to
sit in Flow and Timing.

### Domain 4: Analysis (4)

| # | Signalling question |
|---|---------------------|
| 4.1 | Were all participants included in the analysis? |
| 4.2 | Were missing data handled appropriately? |
| 4.3 | Does the unit of analysis match the ideal test accuracy trial? |
| 4.4 | Were the estimates of sensitivity and specificity calculated appropriately? |

**No applicability judgement** — applicability is assessed for the first three domains only.

4.3 is where a lesion-level or sample-level analysis meets a participant-level synthesis question.
That mismatch had no home in QUADAS-2.

## Judgement rules

**Domain level.** If all signalling questions in a domain are answered *yes* or *probably yes*,
risk of bias can be judged **low**. A *no* or *probably no* **flags potential** for bias — it does
not settle it. Reviewers then apply their judgement and their review-specific guidance to decide
whether the issue is likely to have influenced the accuracy estimates.

> **A study can still be at low risk of bias with one or more signalling questions answered "no."**
> The tool says this explicitly. Do not implement "any No → High" as a rule; that replaces the
> judgement the tool asks for.

Use **insufficient information** only when too little is reported to permit a judgement. It is not
a middle rating between low and high.

**Overall (phase 6)**, per estimate, done separately for risk of bias and for applicability:

- any domain **high** → overall **high**
- all domains **low** → overall **low**
- any domain **insufficient information** and none high → overall **insufficient information**

Record a rationale naming the major limitations behind the overall judgement.

**Do not add a "moderate" grade.** Reviewers sometimes want one, to separate a study that is high
risk in a single domain from one that is high risk in several. The E&E says plainly that the
authors *do not support* this: if an estimate is high risk for one domain, it is high risk,
whatever the other domains say.

## Tailoring the tool to your review

Phase 2's tailoring is the step most often skipped, and the E&E is specific about it.

- Do it **at the protocol stage, alongside phases 1 and 2** — not when you reach the studies.
- Write review-specific guidance on how to answer each signalling question, adapting the general
  guidance tables. Publish it as a web appendix so the application is auditable.
- Draw on **both clinical and methodological** expertise in the review area.
- **Do not remove signalling questions.** Keep them even when they cannot bite: if two-gate designs
  were excluded, every study answers "yes" to 1.1, and recording that shows the issue was
  considered. Deleting the question hides that.
- If you add a question, it must: address **one** issue only; concern **risk of bias, not reporting
  quality**; and be **factual**, phrased so that "yes"/"probably yes" means bias is absent.

## When to Use

- Systematic reviews assessing the accuracy of tests used for **diagnosis, screening or staging**
- New reviews — QUADAS-3 is the current recommended version
- Alongside **QUADAS-C** when the review compares the accuracy of two or more index tests
- Read the **Explanation & Elaboration report** before first use, and tailor the signalling
  questions and their guidance to your review (that tailoring is the step most often skipped)
- Not for prediction models (PROBAST), non-randomised intervention studies (ROBINS-I), or
  randomised trials (RoB 2)

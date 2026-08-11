# QUADAS-3 Assessment Guide

Quality Assessment of Diagnostic Accuracy Studies, version 3 — **the current recommended version**.
Version: QUADAS-3 tool v1.2 — 6 phases, 4 domains, **20 signalling questions** (4 / 4 / 8 / 4).
Source: Whiting PF, Tomlinson E, Rutjes AWS, Davenport C, Yang B, Westwood M, et al. QUADAS-3: a
revised tool for the quality assessment of diagnostic test accuracy studies. *Ann Intern Med*
2026;179(4):548-555 (DOI 10.7326/ANNALS-25-02104). The tool itself, the Explanation & Elaboration
report and an introductory video are distributed by the QUADAS group at
https://www.bristol.ac.uk/population-health-sciences/projects/quadas/quadas-3/

> **Fidelity and licence.** QUADAS-3 is published in *Annals of Internal Medicine* (© American
> College of Physicians) under **no open licence** — Crossref returns only ACP's text-and-data-mining
> policy. The descriptions below state what each question asks **in our own words** rather than
> reproducing the published wording. **Complete the official QUADAS-3 form (`QUADAS-3 1.2.docx`)
> from the page above for any assessment you report, and read the E&E report before using it.**
>
> Verification: the six phases and when each is completed, the four domains, all 20 signalling
> questions, the response options, the domain-level rule, which domains carry an applicability
> judgement, and the overall-judgement rules were compared against **the official tool document
> v1.2** distributed by the QUADAS group. All matched.

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

Both tools say to pair them: the QUADAS-3 tool states that "for reviews involving comparative
accuracy, we recommend using the QUADAS-C tool in addition to QUADAS-3", and the QUADAS group says
QUADAS-C "cannot be used alone and must be used alongside the main QUADAS tool", now meaning
QUADAS-3.

**They do not slot together unchanged, and it is worth knowing where before you start.** Each of
QUADAS-C's four opening questions hard-references a QUADAS-2 question number:

| QUADAS-C | asks whether | referencing | QUADAS-3 counterpart |
|---|---|---|---|
| C1.1 | each index test was low risk for this domain | QUADAS-2 **1.4** | Domain 1 **Participants** judgement |
| C2.1 | 〃 | QUADAS-2 **2.3** | Domain 2 **Index Test** judgement |
| C3.1 | 〃 | QUADAS-2 **3.3** | Domain 3 **Target Condition** judgement (the domain was renamed from Reference Standard) |
| C4.1 | 〃 | QUADAS-2 **4.5** | **no single counterpart** |

**C4 is the one that does not map.** QUADAS-C's domain 4 is *Flow and Timing*, and QUADAS-3 split
that domain: the index-test-to-reference-standard interval became **3.8** inside Target Condition,
while exclusions, missing data and the unit of analysis became the new **Analysis** domain. So
QUADAS-C's C4.1 has no one judgement to read, and its C4.2 (interval between the index tests),
C4.3 (same reference standard for all index tests) and C4.4 (missing data comparable across index
tests) sit astride two QUADAS-3 domains.

There is a second mismatch of granularity: **QUADAS-3 judges each set of accuracy estimates, while
QUADAS-C judges a test comparison**, which spans at least two estimates. Decide, and record, which
estimates a given QUADAS-C assessment is standing on.

> **The authority for this adaptation is the QUADAS-3 E&E report, which this file has not read.**
> Davenport C, Rutjes A, Mallett S, Tomlinson E, Yang B, et al. QUADAS-3 explanation and
> elaboration. *Ann Intern Med* 2026;179:e2504943 (DOI 10.7326/ANNALS-25-04943). It is **CC BY**
> and open access, but every route to it — the ACP site, the Bristol repository landing page, and
> the handle — returns a bot challenge to automated retrieval, so it was not fetched. The mapping
> above is **our reading of the two tool documents**, not the E&E's guidance. Read the E&E before
> relying on it for a review you will publish.

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

## When to Use

- Systematic reviews assessing the accuracy of tests used for **diagnosis, screening or staging**
- New reviews — QUADAS-3 is the current recommended version
- Alongside **QUADAS-C** when the review compares the accuracy of two or more index tests
- Read the **Explanation & Elaboration report** before first use, and tailor the signalling
  questions and their guidance to your review (that tailoring is the step most often skipped)
- Not for prediction models (PROBAST), non-randomised intervention studies (ROBINS-I), or
  randomised trials (RoB 2)

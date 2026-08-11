# ROB-ME Assessment Guide

Risk Of Bias due to Missing Evidence in a meta-analysis.
Reference: Page MJ et al. BMJ 2023;383:e076754; ROB-ME cribsheet Version 1, October 2023.
Website: https://www.riskofbias.info/welcome/rob-me-tool

Version: ROB-ME (2023)
Source: Page MJ, Sterne JAC, Boutron I, Hróbjartsson A, Kirkham JJ, Li T, et al. ROB-ME: a tool for assessing risk of bias due to missing evidence in systematic reviews with meta-analysis. *BMJ* 2023;383:e076754 (DOI 10.1136/bmj-2023-076754).
Licence: Crossref returns only a BMJ text-and-data-mining policy; no Creative Commons licence.
Verification: the five steps, the Results Matrix symbols, all eleven signalling questions
(3.1–3.3, 4.1–4.8) with their conditions and response options, and the judgement scale were
compared word by word against the **official ROB-ME cribsheet Version 1 (October 2023)** and the
completion template distributed at riskofbias.info. All matched; only the truncated citation on
line 4 was wrong.

> A newer cribsheet exists, generalised from "meta-analysis" to "**synthesis**". Its question 4.5
> takes Y / PY / PN / N rather than Y / N, and 4.7's condition widens to "Y to 4.1 or 4.3 **or
> Y/PY to 4.5**". This file documents Version 1, which its citation names; check riskofbias.info
> before appraising against a version.

## Purpose

ROB-ME assesses the risk of bias in a **pairwise meta-analysis result** due to missing evidence — encompassing both non-reporting biases (selective reporting of results) and non-publication biases (unpublished studies). It is applied at the synthesis level (not individual study level).

## Structure

ROB-ME has 5 steps applied to **each meta-analysis** in a systematic review:
1. Select and define meta-analyses to assess
2. Determine which studies have missing results (Results Matrix)
3. Consider the potential for missing studies across the systematic review
4. Assess risk of bias due to missing evidence (signalling questions)
5. Overall risk of bias judgment

Response options: Y (Yes) / PY (Probably Yes) / PN (Probably No) / N (No) / NI (No Information) / NA (Not Applicable)

Green-underlined responses are potential markers for **low** risk of bias.
Red responses are potential markers for **a** risk of bias.

## Step 1: Select and Define Meta-analyses

For each meta-analysis, specify:
- The PICO: Participants, Intervention, Comparator, Outcome
- Eligible study designs
- Eligible outcome definitions (measures, metrics, time points)
- Eligible methods of analysis (analysis populations, crude vs adjusted estimates)

## Step 2: Determine Which Studies Have Missing Results (Results Matrix)

For each study meeting inclusion criteria, create a Results Matrix using these symbols:

| Symbol | Meaning |
|--------|---------|
| check (green) | A study result is available for inclusion in the meta-analysis |
| ~ (yellow) | No study result available, for a reason **unrelated** to the P value, magnitude or direction |
| ? (orange) | Unclear whether an eligible result was generated |
| X (red) | No study result available, **likely because of** the P value, magnitude or direction |

Record: Study ID, Source(s) used, Number of participants analysed, and availability status for each meta-analysis.

Also record any known information about the results (direction of effect, statistical significance, or narrative descriptions).

## Step 3: Consider the Potential for Missing Studies

Answer the following questions **once** for the systematic review as a whole:

### Signalling Questions
3.1 Were prospectively registered studies or studies identified for a prospective meta-analysis the only type of study eligible for inclusion?
   - **Y**: inception cohort → lower risk of missing studies
   - **N**: proceed to 3.2

3.2 If N to 3.1: Would you expect every eligible study to be identifiable regardless of its results?
   - **NA/Y/PY**: lower risk
   - **PN/N**: higher risk — proceed to 3.3

3.3 If Y/PY to 3.2: Were you likely to have found all eligible studies regardless of their results?
   - Consider: trial registers searched, search strategy designed to retrieve regardless of outcomes
   - **NA/Y/PY**: lower risk
   - **PN/N**: higher risk — check the box indicating potential for missing studies

## Step 4: Assess Risk of Bias (per meta-analysis)

Specify the meta-analysis details: description, summary effect estimate (95% CI), number of included studies and participants.

### Within-study Assessment ('Known Unknowns')

4.1 Of the studies identified, was there any for which no result was available for inclusion in the meta-analysis, **likely because of the P value, magnitude or direction** of the result generated (refer to Step 2)?
   - Answer 'Yes' if any study has an 'X' in the Results Matrix for this meta-analysis
   - **Y/N**

4.2 If Y to 4.1: Is it likely that there would be a notable change to the summary effect estimate if the omitted results had been included?
   - Consider: amount of missing evidence relative to total; direction of effect in omitted studies; fixed-effect vs random-effects model
   - **Trivial missing → 'No/Probably no'**; Non-trivial with differing direction → 'Yes/Probably yes'
   - **NA/Y/PY/PN/N/NI**

### Within-study Assessment ('Unknown Unknowns')

4.3 Of the studies identified, was there any for which it was unclear whether an eligible result was generated (refer to Step 2)?
   - Answer 'Yes' if any study has a '?' in the Results Matrix
   - **Y/N**

4.4 If Y to 4.3: Is it likely that there would be a notable change to the summary effect estimate if the potentially omitted results had been included?
   - Consider same factors as 4.2 but for 'potentially' missing evidence
   - **NA/Y/PY/PN/N/NI**

### Across-study Assessment

4.5 Do circumstances (identified in Step 3) indicate potential for some eligible studies not being identified because of the P value, magnitude or direction of the results generated?
   - Answer 'Yes' if the checkbox in Step 3 was checked
   - **Y/N**

4.6 If Y to 4.5: Is it likely that studies not identified had results that were eligible for inclusion in the meta-analysis?
   - Consider: core outcome sets, scope of outcome domain, whether missing studies would have measured this outcome
   - **NA/Y/PY/PN/N**

4.7 If Y to 4.1, 4.3, or 4.5: Does the pattern of observed study results suggest that the meta-analysis is likely to be missing results that were systematically different (in terms of P value, magnitude or direction) from those observed?
   - Methods: (1) funnel plot inspection, (2) funnel plot asymmetry test, (3) compare fixed-effect vs random-effects estimates, (4) inspect P values/direction in forest plot
   - Distinguish small-study effects from non-reporting biases
   - **NA/Y/PY/PN/N**

4.8 If Y/PY/NI to 4.2, 4.4, 4.6, or 4.7: Did sensitivity analyses suggest that the summary effect estimate was biased due to missing results?
   - Consider: selection models, regression-based adjustment, restricting to largest studies
   - **NA/Y/PY/PN/N**

## Step 5: Risk of Bias Judgment

### Judgment Scale
- **Low**: Little or no concern about missing evidence biasing the meta-analysis result
- **Some concerns**: Some concern but not sufficient to judge high risk
- **High**: The meta-analysis result is likely biased due to missing evidence

### Optional: Predicted Direction of Bias
- Favours experimental / Favours comparator / Towards null / Away from null / Unpredictable

## When to Use

- Every pairwise meta-analysis in a systematic review (PRISMA 2020 recommends this)
- Replaces informal funnel plot interpretation with a structured assessment
- Complements individual study RoB tools (RoB 2, ROBINS-I, QUADAS-2)
- Not designed for network meta-analysis (use RoB NMA instead)
- Should be completed by someone familiar with the meta-analysis methods and included studies

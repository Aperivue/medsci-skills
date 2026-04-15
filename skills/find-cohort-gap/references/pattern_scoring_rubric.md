# 6-Pattern Scoring Rubric

## Overview

Score each pattern 0 (absent) or 1 (present). Total: 0-6 points.
Interpretation: 5-6 = top-tier, 3-4 = specialty journal, 1-2 = restructure or kill.

---

## P1: Longitudinal Advantage

**Question:** Does the cohort's serial/repeated measurement structure create a clear
edge over existing cross-sectional studies?

**Score 1 if ALL of:**
- The cohort has 3+ measurement timepoints for the key exposure variable
- No prior study on this topic used serial/trajectory data
- The research question benefits from temporal modeling (change over time, trajectory
  clusters, time-to-event with time-varying exposure)

**Score 0 if ANY of:**
- The exposure is a one-time measurement (e.g., genetic variant, birth weight)
- Prior longitudinal studies already exist for this topic
- Serial data adds no interpretive value (e.g., stable demographic variable)

**Examples:**
- Score 1: Serial body composition → sarcopenia trajectory → mortality (no prior serial study)
- Score 0: Blood type → cancer risk (blood type doesn't change over time)

**Theoretical basis:** Repeated measures increase statistical efficiency by reducing
within-subject variance and enabling trajectory-based phenotyping that cross-sectional
designs cannot achieve (Lee et al., 2014, PMID 25464127).

---

## P2: Endpoint Upgrade

**Question:** Can we escalate to a harder endpoint than existing studies?

**Score 1 if BOTH of:**
- The cohort links to mortality, cancer, or major cardiovascular event registries
- Existing studies on this topic used only surrogate endpoints (biomarkers, imaging
  findings, composite scores) without hard clinical outcomes

**Score 0 if ANY of:**
- The cohort lacks hard endpoint linkage
- Prior studies already reported hard endpoints for this topic
- The research question is inherently about a surrogate (e.g., mechanism study)

**Examples:**
- Score 1: Existing studies link fatty liver to liver enzymes only; our cohort links to
  liver-related mortality and HCC incidence
- Score 0: Existing studies already report all-cause mortality for this exposure

**Endpoint hierarchy** (strongest to weakest):
1. All-cause mortality
2. Cause-specific mortality
3. Major adverse events (MACE, cancer diagnosis)
4. Hospitalization
5. Disease incidence (physician diagnosis)
6. Surrogate markers (lab values, imaging scores)

---

## P3: Cohort Uniqueness

**Question:** Is the cohort's population, scale, or setting distinctive?

**Score 1 if ANY of:**
- Largest cohort for this topic (>5x larger than existing studies)
- First study in this ethnic/geographic population
- Screening-based population (no referral bias) when prior studies used hospital cohorts
- Unique data linkage not available elsewhere (e.g., national registry + health checkup)
- Community-dwelling general population when prior studies used disease-specific cohorts

**Score 0 if:**
- Similar-sized cohorts with the same population type have published on this topic

**Examples:**
- Score 1: 486K health checkup participants vs existing studies of 3-9K referral patients
- Score 0: Another 500K cohort from the same country already published on this topic

---

## P4: PI-Topic Alignment

**Question:** Does the PI's expertise and reputation strengthen this topic?

**Score 1 if ANY of:**
- PI holds a society leadership role directly relevant to the topic
- PI has 5+ first/corresponding author papers in this specific domain
- PI is an editorial board member of a target journal in this field

**Score 0 if:**
- PI's expertise is only tangentially related
- No specific PI identified (skip this pattern; score out of 5 instead)

**Why this matters:** A PI with society standing in the topic area signals that the
study has expert oversight. Editors recognize this. The PI's name also guides target
journal selection (e.g., hepatology society president -> J Hepatol).

**When no PI is specified:** Remove this pattern from scoring. Interpret:
4-5/5 = top-tier, 2-3/5 = specialty, 0-1/5 = restructure.

---

## P5: Comparison Table Gaps (3+)

**Question:** Does the THIS STUDY column show 3+ unique features vs all existing papers?

**Score 1 if:**
- The comparison table has at least 3 rows where THIS STUDY has a checkmark/advantage
  that NO prior paper has

**Score 0 if:**
- Fewer than 3 unique differentiators

**Common differentiator categories:**
1. Study design (longitudinal vs cross-sectional)
2. Sample size (order of magnitude larger)
3. Serial measurements (multiple timepoints vs single)
4. Hard endpoints (mortality vs surrogate)
5. Population type (screening vs referral)
6. Ethnicity/geography (first in this population)
7. Subgroup analyses (age/sex/comorbidity stratification)
8. Adjustment for key confounders (missing in prior studies)
9. Exposure definition (validated operational definition vs ICD-only)
10. Follow-up duration (significantly longer)

**Construction method:**
1. Identify 3-5 most relevant existing papers from saturation scan
2. Create table with Feature rows and Paper columns + THIS STUDY column
3. For each feature, check whether each paper and THIS STUDY address it
4. Count features unique to THIS STUDY

---

## P6: Complementary Design

**Question:** Can this topic pair with another study from the same cohort?

**Score 1 if ANY of:**
- A complementary analysis using the same DB but different population subset is
  feasible (e.g., diabetic vs non-diabetic; viral vs non-viral liver disease)
- The same exposure can be studied against a different outcome in a companion paper
- The topic creates a "series" with a previously published paper from the same cohort

**Score 0 if:**
- The topic is standalone with no natural complement
- The complementary analysis would be trivially similar (not publishable separately)

**Why this matters:** Paired papers from the same cohort strengthen both: the second
paper can reference the first as "in this cohort, we previously showed..." and reviewers
see a programmatic research line, not a one-off analysis.

---

## Quick Reference Card

```
Pattern         | Key Signal
----------------|------------------------------------------
P1 Longitudinal | "No prior study used serial data for this"
P2 Endpoint     | "We add mortality/cancer to surrogate-only literature"
P3 Uniqueness   | "Largest / first in this population / no referral bias"
P4 PI Alignment | "PI is society president in this exact field"
P5 Comparison   | "3+ checkmarks unique to THIS STUDY"
P6 Complement   | "Natural pair study exists in same DB"
```

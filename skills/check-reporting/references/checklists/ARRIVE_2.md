# ARRIVE 2.0 Checklist — Animal Research

**Reference:** Percie du Sert N et al. The ARRIVE guidelines 2.0: Updated guidelines for reporting animal research. PLoS Biol. 2020;18(7):e3000410. PMID: 32663219

**Website:** https://arriveguidelines.org

---

## How to Use This Checklist

ARRIVE 2.0 has two tiers:
- **Essential 10** (Items 1–10): Non-negotiable. All journals require these. Missing any = REJECTED.
- **Recommended** (Items 11–21): Best practice. Complete if possible.

For each item: **PRESENT** / **PARTIAL** / **MISSING**

---

## ESSENTIAL 10 — Non-Negotiable

### Item 1 — Study Design ⚠️ commonly missed
**Description:** For each experiment, provide brief details of the study design.
**Required content:**
- Type of study design (e.g., parallel group, crossover, factorial, dose-response)
- Number of experimental groups and description of each
- Independent experimental units (e.g., animal, litter, cage)
- For any within-animal design: outline the design clearly

**Example:** "Animals were randomly allocated to one of three parallel groups: (1) vehicle control (n=10), (2) low-dose treatment (n=10), (3) high-dose treatment (n=10). Each animal was an independent experimental unit."

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING
**Location:** ___

---

### Item 2 — Sample Size ⚠️ commonly missed
**Description:** Specify the number of animals used and rationale for this number.
**Required content:**
- Total number of animals used AND number per group
- Method of sample size determination:
  - Formal power calculation (provide effect size, α, power, formula, software) **OR**
  - Pragmatic reasons (limited number of animals available, pilot study) — state explicitly

**Power calculation example:**
"Sample size was estimated using G*Power 3.1 based on a two-sample t-test, assuming an expected effect size of Cohen's d = 1.2 (derived from [Author Year]), α = 0.05 (two-tailed), and 80% power. The calculation indicated 15 animals per group were required. Accounting for 20% expected attrition, 18 animals per group were enrolled."

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING
**Location:** ___

---

### Item 3 — Inclusion/Exclusion Criteria ⚠️ commonly missed
**Description:** Describe any criteria used for including or excluding animals or data.
**Required content:**
- Criteria for excluding animals from the experiment (pre-specified, not post-hoc)
- Criteria for excluding data from analysis (e.g., outliers — method for outlier detection)
- Any animals that were excluded and why

**Example:** "Animals were excluded if: (a) weight loss exceeded 20% at any time point, (b) technical failure of surgical procedure occurred, or (c) infection was detected. Any exclusion was documented in the study log at the time of occurrence. Two animals were excluded (one from Group A due to procedure failure; one from Group C due to infection)."

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING
**Location:** ___

---

### Item 4 — Randomization ⚠️ commonly missed
**Description:** Describe how animals were allocated to experimental groups.
**Required content:**
- Method of randomization (computer-generated, random number table)
- Type: simple, block, stratified
- Who performed randomization (and whether separate from who conducted experiments)
- If randomization not used, justify

**Example:** "Animals were randomly allocated to groups using computer-generated random numbers (R version 4.2.0). Block randomization (block size = 6) was used to ensure balanced allocation across experimental days. Allocation was performed by a researcher (initials) not involved in data collection."

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING
**Location:** ___

---

### Item 5 — Blinding ⚠️ commonly missed
**Description:** Describe who was aware of group allocation during different stages.
**Required content:**
State who was blinded (or not) at each stage:
- During the experiment (treatment administration)
- During outcome assessment
- During data analysis

"Outcome assessors were blinded to group allocation during behavioral testing and histological analysis. The researcher administering treatments could not be blinded due to the nature of the procedure; however, outcome assessment was performed by a blinded assessor."

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING
**Location:** ___

---

### Item 6 — Outcome Measures ⚠️ commonly missed
**Description:** Clearly define all outcome measures used and how they were assessed.
**Required content:**
- Primary outcome: define explicitly (what is measured, how, by whom)
- Secondary outcomes: same level of detail
- Timing of measurements (baseline, Day 7, Day 14, etc.)
- Observer reliability: intra- and inter-observer variability assessed?

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING
**Location:** ___

---

### Item 7 — Statistical Methods ⚠️ commonly missed
**Description:** Describe the statistical methods used for each analysis.
**Required content:**
- Primary statistical test for primary outcome
- Rationale for choice (parametric vs. non-parametric, based on what?)
- Handling of repeated measures (linear mixed-effects model preferred over repeated ANOVA)
- Multiple comparison correction: which method (Bonferroni, FDR)?
- Significance threshold (α)
- Software: R (version), SPSS (version), GraphPad Prism (version)

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING
**Location:** ___

---

### Item 8 — Experimental Animals ⚠️ commonly missed
**Description:** Provide details of animals used in the study.
**Required content:**
- Species and strain/substrain (with substrain details — this matters!)
- Source (commercial vendor; in-house breeding)
- Sex (justify if single sex)
- Age and weight at start of experiment (mean ± SD or range)
- Health status (specific pathogen-free, germ-free, defined flora, conventional)
- For transgenic animals: complete genotype

**Example:** "Male C57BL/6J mice (Jackson Laboratory, Bar Harbor, ME; stock #000664) aged 8–10 weeks (weight: 22.3 ± 1.8 g at enrollment) were used. Only males were used because [biological justification]. All animals were specific pathogen-free."

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING
**Location:** ___

---

### Item 9 — Experimental Procedures ⚠️ commonly missed
**Description:** For each experiment and each experimental group, including controls, describe the procedures in enough detail to allow replication.
**Required content:**
- Exact procedure steps
- Anesthesia: agent, dose, route, monitoring (temperature, heart rate)
- Analgesia: pre- and post-operative
- Humane endpoints: pre-specified criteria for euthanasia
- Equipment: manufacturer, model, settings
- Any details that could affect reproducibility (time of day, number of animals per session)

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING
**Location:** ___

---

### Item 10 — Results ⚠️ commonly missed
**Description:** Report the results for each experiment conducted, with a measure of precision (e.g., SD, SEM, 95% CI).
**Required content:**
- All pre-specified outcomes (not just significant ones)
- Effect size with 95% CI
- Exact p-values
- N at each time point (with attrition documented)
- Adverse events (even if none: "No adverse events were observed")
- Individual data points for small groups (dot plots)

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING
**Location:** ___

---

## RECOMMENDED ITEMS — Best Practice

### Item 11 — Abstract ⚠️ commonly missed
**Description:** Provide an accurate summary of the research objectives, animal species used, key methods, principal findings, and study conclusions.
**Required content:** Abstract should contain enough information for readers to understand: what species, what procedure, primary result with magnitude, conclusion.
**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### Item 12 — Background
**Description:** Explain why the study was done; include sufficient background to inform the reader why this animal model was chosen.
**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### Item 13 — Objectives
**Description:** Clearly describe the research question, hypothesis, and the specific objectives of the study.
**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### Item 14 — Ethical Statement ⚠️ commonly missed
**Description:** Provide the name of the ethics committee or equivalent, and the approval ID.
**Required content:** "All animal experiments were approved by the Institutional Animal Care and Use Committee of [Institution] (protocol number [XXX])."
**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### Item 15 — Housing and Husbandry ⚠️ commonly missed
**Description:** Describe the conditions under which animals were housed and cared for.
**Required content:** Cage type and dimensions, group or individual housing (N per cage), temperature (°C), humidity (%), light cycle, food and water access (ad libitum or restricted; diet specification), acclimatization period, enrichment.
**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### Item 16 — Animal Care and Monitoring
**Description:** Describe the welfare assessments that were carried out before, during, and after the experiment.
**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### Item 17 — Interpretation
**Description:** Interpret the results, taking into account the study objectives and hypotheses, current theory, and other relevant studies.
**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### Item 18 — Generalisability/Translation
**Description:** Comment on whether, and how, the findings of this study are likely to translate to other species or systems, and the relevance to human biology.
**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### Item 19 — Limitations ⚠️ commonly missed
**Description:** Discuss the potential limitations of the study.
**Required content:** At minimum: (a) model limitations relative to human disease, (b) single sex (if applicable), (c) single center/vendor, (d) follow-up duration, (e) sample size for secondary outcomes.
**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### Item 20 — Protocol Registration
**Description:** Provide a statement indicating whether a study protocol was pre-registered.
**Required content:** OSF (osf.io), PROSPERO for systematic reviews, or equivalent. State registration ID or that registration was not done (with justification if exploratory study).
**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### Item 21 — Data Availability ⚠️ commonly missed
**Description:** Provide a statement describing if and where study data are available.
**Required content:** "Data supporting this study are available at [repository/DOI]." or "Data are available upon reasonable request from the corresponding author."
**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

---

## Summary

| Category | PRESENT | PARTIAL | MISSING |
|----------|---------|---------|---------|
| Essential 10 | /10 | /10 | /10 |
| Recommended | /11 | /11 | /11 |
| **TOTAL** | /21 | /21 | /21 |

**Verdict:** [ ] All Essential 10 PRESENT → proceed to submission
[ ] Any Essential 10 MISSING → MUST REVISE before submission

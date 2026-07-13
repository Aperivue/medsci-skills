# Cohort Profile Template

Fill in the sections below to describe the cohort database. This profile drives
the intersection matrix and feasibility checks.

---

## Basic Information

- **Cohort name:**
- **Institution/Organization:**
- **Country:**
- **Population type:** (general population / health checkup / disease registry / claims data / hospital EMR)
- **Enrollment period:** (e.g., 2002-2019)
- **Total N at baseline:**
- **N with follow-up data:**
- **Mean/median follow-up duration:**
- **Measurement intervals:** (e.g., annual, biennial, at-event)

## Variable Categories

Check all that apply and list key variables in each category:

- [ ] **Demographics**: (age, sex, BMI, smoking, alcohol, exercise, income, education)
- [ ] **Laboratory**: (CBC, metabolic panel, lipid panel, liver function, kidney function, tumor markers, HbA1c, ...)
- [ ] **Imaging**: (chest X-ray, CT, ultrasound, DEXA, mammography, ...)
- [ ] **Questionnaires**: (PHQ-9, IPAQ, diet, sleep, quality of life, ...)
- [ ] **Vital signs**: (BP, heart rate, ...)
- [ ] **Anthropometry**: (height, weight, waist circumference, body composition, ...)
- [ ] **Medications**: (prescription records, drug categories, ...)
- [ ] **Procedures**: (surgery codes, intervention records, ...)
- [ ] **Diagnoses**: (ICD codes, physician diagnosis, ...)

## Endpoints Available

Check all that apply:

- [ ] **All-cause mortality** (linkage to: ___)
- [ ] **Cause-specific mortality** (categories: ___)
- [ ] **Cancer incidence** (linkage to: ___)
- [ ] **Cardiovascular events** (definition: ___)
- [ ] **Hospitalization** (source: ___)
- [ ] **Disease incidence** (ICD-based / physician-confirmed / registry)
- [ ] **Other**: ___

## Special Strengths

What makes this cohort unique? (check all that apply)

- [ ] **Serial measurements** (same variables measured repeatedly over time)
- [ ] **Large scale** (>100K participants)
- [ ] **Long follow-up** (>10 years)
- [ ] **National registry linkage** (mortality, cancer, insurance claims)
- [ ] **Screening-based** (no referral bias — general population health checkups)
- [ ] **Unique population** (ethnicity, occupation, geography not well-studied)
- [ ] **Rich phenotyping** (imaging + labs + questionnaires)
- [ ] **Biobank/genetic data available**
- [ ] **Other**: ___

## Known Limitations

- [ ] **Healthy volunteer bias** (participants may be healthier than general population)
- [ ] **Attrition** (estimated dropout rate: ___%)
- [ ] **Missing data** (key variables with >20% missing: ___)
- [ ] **Limited demographics** (e.g., single sex, narrow age range, single institution)
- [ ] **Claims-only diagnoses** (no clinical validation of ICD codes)
- [ ] **No imaging data**
- [ ] **No medication data**
- [ ] **Other**: ___

## Existing Publications

List known papers already published from this cohort (to avoid topic duplication):

1. (Author, Year, Topic, Journal)
2. ...

## Data Access

- **IRB status:** (approved / needs application)
- **Access method:** (on-site analysis center / remote access / direct download)
- **Estimated turnaround:** (application to data receipt)
- **Cost:** (if applicable)

---

## Variable Cluster Map (Auto-generated)

If a codebook / data dictionary / CSV export is available, do not fill this in by hand
and do not summarise the file yourself — run the input adapter:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/build_cohort_profile.py" --codebook <file> --out-dir .
```

It writes `cohort_profile.md` + `cohort_profile.json` with:

| Section | Content |
|---------|---------|
| Variable cluster map | every variable copied **verbatim**, with its source (`file:row`) and the keyword that placed it in its cluster |
| Serial / repeated measures | measurement groups that genuinely repeat (evidence for **P1**) |
| Endpoint candidates | mortality / cancer / CVD / hospitalisation variables (evidence for **P2**) |
| `[UNKNOWN]` list | sample size, follow-up, IRB, prior publications — **ask the user; never guess** |

Variables that match no cluster keyword are reported as `unclassified` rather than forced
into a bucket. Review them: the lexicon is not exhaustive, and a mis-clustered exposure
variable will distort the intersection matrix.

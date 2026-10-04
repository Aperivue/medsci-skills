# CHNS variable coding (3-country design)

Load-on-demand companion to `/cross-national` Phase 2. Read it when the design includes China (CHNS);
a 2-country (KR+US) design needs none of it.

## CHNS Variable Coding Reference (validated via 3-country batch)

**Data source**: cpc.unc.edu/projects/china (free registration)
**Biomarker wave**: 2009 only (fasting blood was first collected in 2009; N=9,549 in the
biomarker file — Yan et al. 2012, PMID 22738663, analysed 9,244 aged ≥ 7 with fasting blood and
anthropometry, so confirm the N against the CHNS codebook). Other variables available 1989-2015.
**Survey design**: No formal weights. Use `svydesign(id=~COMMID, weights=~1)` or cluster-robust SE.

### Key Files and Merge Strategy

| File | Key Variables | Join Key |
|------|--------------|----------|
| mast_pub_12 | IDind, GENDER (1=M/2=F), WEST_DOB_Y (birth year) | IDind |
| pexam_00 | HEIGHT, WEIGHT, U10 (waist), SYSTOL1-3, DIASTOL1-3, U22 (HBP dx), U24 (HBP meds), U24A (DM dx), U25 (ever smoked), U27 (still smokes), U40 (alcohol), U41 (freq), U48A (self-health), COMMID | IDind + filter WAVE==2009 |
| biomarker_09 | GLUCOSE_MG, HbA1c, TC_MG, TG_MG, HDL_C_MG, LDL_C_MG, HS_CRP, HGB, WBC, ALT, CRE_MG | IDind |
| educ_12 | A12 (education 0-6) | IDind + filter WAVE==2009 |
| indinc_10 | indwage (yuan, continuous → quartiles) | IDind + filter wave==2009 |

### Variable Coding

| Variable | Raw Var | Coding | Notes |
|----------|---------|--------|-------|
| Sex | GENDER | 1=Male, 2=Female | Same as KNHANES/NHANES |
| Age | WEST_DOB_Y | age = wave_year - WEST_DOB_Y | Integer truncation |
| BMI | HEIGHT, WEIGHT | WEIGHT / (HEIGHT/100)^2 | **Obesity: BMI ≥ 28 (WGOC, NOT 25 or 30)** |
| Waist | U10 | cm, direct measurement | **Central obesity: ≥90M / ≥80F (IDF-Asian)** |
| SBP | SYSTOL1-3 | mean(SYSTOL1, SYSTOL2, SYSTOL3) | 3 readings averaged |
| DBP | DIASTOL1-3 | mean(DIASTOL1, DIASTOL2, DIASTOL3) | 3 readings averaged |
| HBP diagnosed | U22 | 0=No, 1=Yes, 9=Don't know (→NA) | |
| HBP medication | U24 | 0=No, 1=Yes | |
| DM diagnosed | U24A | 0=No, 1=Yes, 9=Don't know (→NA) | |
| Smoking | U25 + U27 | never(U25==0) / former(U25==1 & U27==0) / current(U25==1 & U27==1) | |
| Alcohol | U40 + U41 | never(U40==0) / occasional(U41≥4) / frequent(U41≤3, ≥1x/week) | U41: 1=daily, 2=3-4x/wk, 3=1-2x/wk, 4=1-2x/mo, 5=<1x/mo |
| Education | A12 | 0=none, 1=primary, 2=lower-mid, 3=upper-mid, 4=technical, 5=university, 6=master+. Recode: 0-2→low, 3-4→mid, 5-6→high | |
| Income | indwage | Continuous yuan → quartiles within wave | |
| Glucose | GLUCOSE_MG | mg/dL (also GLUCOSE in mmol/L) | 2009 only |
| HbA1c | HbA1c | % (direct) | 2009 only |
| TC | TC_MG | mg/dL | 2009 only |
| TG | TG_MG | mg/dL | 2009 only |
| HDL | HDL_C_MG | mg/dL | 2009 only |
| hsCRP | HS_CRP | mg/L | 2009 only |
| Hemoglobin | HGB | **g/L (divide by 10 for g/dL)** | Unit differs from KR/US |
| Self-health | U48A | Self-reported health status | 2004-2011 |
| Depression | — | **NOT AVAILABLE** in standard download. CES-D exists but needs separate dataset. | Cannot directly compare with PHQ-9 |

### CHNS-Specific Warnings

1. **No survey weights**: CHNS is NOT a formally weighted survey. Use unweighted analysis with cluster-robust SE by COMMID. Report as limitation.
2. **Biomarker = 2009 only**: Glucose, HbA1c, lipids, hsCRP available only in 2009 wave. Other waves lack lab data.
3. **CES-D not in standard download**: Depression comparison requires separate dataset download from cpc.unc.edu.
4. **BMI cutoff ≠ KR ≠ US**: China=28, Korea=25, US=30. Use country-specific cutoffs AND sensitivity analysis with WHO cutoff=25.
5. **SES-health gradient may reverse**: Low education and low income are NOT always risk factors in China (null/protective). This is the "developing country health transition" — do NOT treat as a bug.
6. **Hemoglobin unit**: CHNS reports g/L (KR/US report g/dL). Divide by 10 when comparing.
7. **Education scale**: 7-level (0-6) vs KR 4-level vs US 5-level. Harmonize to 3-level for comparison.

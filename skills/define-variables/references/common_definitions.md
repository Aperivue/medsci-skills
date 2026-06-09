# Canonical Definitions Index (Tier 1)

Curated index of high-frequency phenotype/variable definitions for observational research. Each entry gives the authoritative source, year, cutoff, BibTeX key stub, and DOI. **Always quote the cutoff verbatim** — do not paraphrase.

Update cadence: review annually or when a major guideline revision drops.

---

## Hepatology

### MASLD (Metabolic dysfunction-associated Steatotic Liver Disease)
- **Source**: Rinella et al., AASLD multi-society Delphi consensus, *Hepatology* 2023
- **Definition**: Hepatic steatosis (imaging/histology) + ≥1 cardiometabolic risk factor, no other identifiable cause
- **Cardiometabolic criteria (≥1 of 5)**:
  - BMI ≥25 kg/m² (≥23 for Asian populations) OR WC >94 cm (M) / >80 cm (F)
  - FPG ≥100 mg/dL OR 2h-PG ≥140 OR HbA1c ≥5.7% OR T2DM OR T2DM treatment
  - BP ≥130/85 OR antihypertensive treatment
  - TG ≥150 mg/dL OR lipid-lowering treatment
  - HDL ≤40 (M) / ≤50 (F) mg/dL OR lipid-lowering treatment
- **BibTeX**: `@rinella2023_aasld_masld`
- **DOI**: 10.1097/HEP.0000000000000520

### MetALD
- **Source**: Same AASLD 2023 consensus
- **Definition**: MASLD criteria + moderate alcohol (M 140–350 g/wk, F 70–210 g/wk)
- **BibTeX**: `@rinella2023_aasld_masld`

### ALD (Alcohol-associated Liver Disease)
- **Source**: AASLD 2023 consensus + Crabb et al., AASLD practice guidance 2020
- **Definition**: Steatosis + alcohol >350 g/wk (M) / >210 g/wk (F)
- **BibTeX**: `@crabb2020_aasld_ald`, `@rinella2023_aasld_masld`

### MAFLD (legacy, 2020)
- **Source**: Eslam et al., international expert consensus, *J Hepatol* 2020
- **BibTeX**: `@eslam2020_mafld`
- **Note**: Superseded by MASLD (2023) — use only for backwards comparability.

### HBV chronic infection
- **Source**: Terrault et al., AASLD 2022/2018 guidance
- **Definition**: HBsAg positive ≥6 months
- **BibTeX**: `@terrault2018_aasld_hbv`

### HCV chronic infection
- **Source**: AASLD-IDSA HCV guidance (latest rolling update at hcvguidelines.org)
- **Definition**: Anti-HCV positive + HCV RNA detectable
- **BibTeX**: `@aasld_idsa_hcv_guidance`

### Liver fibrosis non-invasive scores
- **FIB-4**: Sterling et al. 2006. Cutoffs <1.3 exclude advanced fibrosis (<65 y); <2.0 (≥65 y). >2.67 rule-in. `@sterling2006_fib4`
- **NFS (NAFLD fibrosis score)**: Angulo et al. 2007. `@angulo2007_nfs`

---

## Metabolic / Endocrine

### Type 2 Diabetes
- **Source**: ADA Standards of Care in Diabetes — 2024, *Diabetes Care*
- **Definition (any ONE)**:
  - FPG ≥126 mg/dL
  - 2h-PG ≥200 mg/dL on 75g OGTT
  - HbA1c ≥6.5%
  - Classic hyperglycemia symptoms + random PG ≥200
  - Physician diagnosis OR antidiabetic medication
- **BibTeX**: `@ada2024_standards`
- **DOI**: 10.2337/dc24-S002

### Prediabetes
- **Source**: ADA 2024
- **Definition**: FPG 100–125 OR 2h-PG 140–199 OR HbA1c 5.7–6.4%

### Metabolic Syndrome
- **Source**: IDF 2009 harmonized (Alberti et al., *Circulation*) — ≥3 of 5 criteria
- **Criteria**:
  - WC (ethnicity-specific: Asian M ≥90, F ≥80 cm)
  - TG ≥150 OR treatment
  - HDL <40 (M) / <50 (F) OR treatment
  - BP ≥130/85 OR antihypertensive treatment
  - FPG ≥100 OR T2DM treatment
- **BibTeX**: `@alberti2009_idf_harmonized`
- **DOI**: 10.1161/CIRCULATIONAHA.109.192644

### Obesity (BMI)
- **WHO global**: Overweight ≥25, obese ≥30 kg/m². `@who2000_obesity`
- **WHO Asian (2004, *Lancet*)**: Overweight ≥23, obese ≥25. `@who2004_asian_bmi`
- **Korean Society for the Study of Obesity (KSSO) 2022**: Same 23/25 thresholds. `@ksso2022_obesity`

### Hypertension
- **ACC/AHA 2017**: ≥130/80 = stage 1. `@whelton2017_accaha_htn`
- **JNC-8 / ESC (legacy)**: ≥140/90. `@james2014_jnc8`
- **Pick one explicitly** — do not mix.

### Dyslipidemia
- **Source**: 2018 AHA/ACC/multi-society cholesterol guideline; 2023 update
- **BibTeX**: `@grundy2019_aha_cholesterol`

---

## Renal

### CKD
- **Source**: KDIGO 2024 CKD guideline, *Kidney Int*
- **Definition**: eGFR <60 mL/min/1.73m² OR markers of kidney damage (ACR ≥30 mg/g etc.) ≥3 months
- **Staging**: G1–G5 by eGFR; A1–A3 by albuminuria
- **BibTeX**: `@kdigo2024_ckd`

### eGFR formulas
- **CKD-EPI 2021 (race-free)** — *NEJM* 2021, Inker et al. `@inker2021_ckdepi2021`. Current KDIGO-recommended.
- **CKD-EPI 2009** — legacy, race-based. `@levey2009_ckdepi`
- **MDRD** — obsolete for clinical use; still seen in older datasets. `@levey2006_mdrd`

### Incidental Renal Mass
- **Source**: ACR White Paper 2018 (Herts et al., *JACR*)
- **Cutoffs**: <1 cm too small to characterize; ≥1 cm workup per size/attenuation; growth >5 mm/y concerning
- **BibTeX**: `@herts2018_acr_renal`
- **DOI**: 10.1016/j.jacr.2017.10.028

### Bosniak Classification (cystic renal mass)
- **Source**: Silverman et al., *Radiology* 2019 update
- **BibTeX**: `@silverman2019_bosniak`

---

## Pulmonary

### COPD
- **Source**: GOLD 2024 Report
- **Definition**: Post-bronchodilator FEV1/FVC <0.70 + compatible symptoms/exposure
- **Severity (GOLD 1–4)** by FEV1% predicted: ≥80 / 50–79 / 30–49 / <30
- **BibTeX**: `@gold2024`

### Emphysema (imaging)
- **Source**: Fleischner Society 2015 statement (Lynch et al., *Radiology*)
- **CT pattern classification**: centrilobular (trace/mild/moderate/confluent/advanced destructive), paraseptal, panlobular
- **BibTeX**: `@lynch2015_fleischner_emphysema`
- **DOI**: 10.1148/radiol.2015141579

---

## Cardiovascular

### CAC (Coronary Artery Calcium)
- **Agatston method**: Agatston et al., *JACC* 1990. `@agatston1990`
- **MESA percentiles** (age/sex/race): McClelland et al. 2015. `@mcclelland2015_mesa`
- **Categories**: 0 / 1–99 / 100–399 / ≥400 (widely used)

### ASCVD risk
- **Pooled Cohort Equations**: 2013 ACC/AHA. `@goff2014_pce`
- **PREVENT (2023)**: AHA new risk calculator, Khan et al., *Circulation*. `@khan2023_prevent`

---

## Oncology / Imaging incidentalomas

### Thyroid nodule
- **ACR TI-RADS 2017**: Tessler et al., *JACR*. `@tessler2017_tirads`

### Gallbladder polyp
- **European joint guideline 2022**: Foley et al., *Eur Radiol*. `@foley2022_gb_polyp`

### Adrenal incidentaloma
- **ACR 2023 white paper**: Mayo-Smith et al. `@mayosmith2023_acr_adrenal`
- **ESE 2023 clinical**: Fassnacht et al., *Eur J Endocrinol*. `@fassnacht2023_ese_adrenal`

### Pancreatic cystic lesion
- **ACR 2017 white paper**: Megibow et al., *JACR*. `@megibow2017_acr_pancreas`

### H. pylori / gastric
- **Maastricht VI / Florence Consensus 2022**: Malfertheiner et al., *Gut*. `@malfertheiner2022_maastricht6`

---

## Alcohol exposure

### Standard drink (Korea)
- 1 drink ≈ 10 g ethanol (KNHANES; KCDC standard-drink definition)
- ALD cutoffs above use grams/week, not drinks/week — convert when operationalizing.

### AUDIT-C / AUDIT
- Bush et al. 1998; Saunders et al. 1993. `@bush1998_auditc`, `@saunders1993_audit`

---

## How to extend this file

1. Add a new subsection under the appropriate organ/domain.
2. Cite the authoritative guideline/consensus (not a secondary review).
3. Quote the cutoff exactly — include units.
4. Provide BibTeX key stub + DOI.
5. If multiple competing guidelines exist (e.g., HTN 130 vs 140), list both and note "pick one explicitly."
6. Commit with message: `define-variables: add {construct} canonical definition ({guideline year})`.

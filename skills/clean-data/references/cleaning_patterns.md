# Common Clinical Data Cleaning Patterns

Reference document for the clean-data skill. Covers recurring data quality issues
in electronic health records, registries, and research databases.

---

## 1. Missing Data Patterns

### Classification

- **MCAR (Missing Completely At Random)**: Missingness is unrelated to any variable.
  Example: random equipment failure during lab measurement.
  Test: Little's MCAR test (chi-square). If p > 0.05, MCAR is plausible.

- **MAR (Missing At Random)**: Missingness depends on observed variables but not the
  missing value itself. Example: younger patients less likely to have bone density measured.
  Cannot be directly tested; inferred from associations between missingness indicators
  and observed covariates.

- **MNAR (Missing Not At Random)**: Missingness depends on the unobserved value itself.
  Example: severely ill patients too sick to complete follow-up surveys.
  Cannot be tested from the data alone; requires domain knowledge.

### Heuristic Assessment

1. Compute missing percentage per variable.
2. Create missingness indicator (0/1) for each variable with >5% missing.
3. Correlate missingness indicators with observed variables (chi-square, t-test).
4. If strong correlations exist: likely MAR. If none: plausible MCAR. If clinical
   reasoning suggests the value itself drives missingness: suspect MNAR.

### When to Use Each Imputation Method

| Method | When appropriate | Caution |
|--------|-----------------|---------|
| Listwise deletion (complete case) | MCAR, low % missing (<5%), large sample | Biased if MAR/MNAR; reduces power |
| Mean/median imputation | Quick exploratory analysis only | Underestimates variance; distorts distributions |
| Last observation carried forward | Longitudinal data, slow-changing variables | Biased if trajectory is changing |
| Multiple imputation (MICE) | MAR, moderate missing (5-40%), multivariate | Requires careful model specification |
| Maximum likelihood (FIML) | MAR, SEM or regression contexts | Needs software support |
| Sensitivity analysis | Always for MNAR suspicion | Report results under multiple assumptions |

### Key Rule

Never impute the outcome variable in the primary analysis without explicit justification.
Report the missing data mechanism assumption in the methods section.

---

## 2. Outlier Detection

### Statistical Methods

**IQR Method (Tukey Fences)**:
- Lower fence: Q1 - 1.5 * IQR
- Upper fence: Q3 + 1.5 * IQR
- Robust to non-normal distributions
- Preferred for clinical data where normality is rarely guaranteed

**Z-Score Method**:
- Flag values with |z| > 3 (or |z| > 2.5 for smaller samples)
- Assumes approximate normality
- Sensitive to the outliers themselves (mean and SD are affected)

**Modified Z-Score (MAD-based)**:
- Uses median and Median Absolute Deviation instead of mean/SD
- More robust than standard Z-score
- Formula: M_i = 0.6745 * (x_i - median) / MAD

### Decision Framework

| Scenario | Recommended action |
|----------|--------------------|
| Data entry error (clearly impossible) | Correct if source available; else set to missing |
| Measurement error (instrument fault) | Set to missing; document in cleaning log |
| True extreme value (biologically plausible) | Keep in dataset; consider sensitivity analysis with/without |
| Ambiguous | Flag for domain expert review; do not remove without justification |

### Clinical Context Matters

A BMI of 50 is an outlier statistically but clinically real. An age of 200 is impossible.
A creatinine of 15 mg/dL is extreme but occurs in dialysis patients. Always consult the
codebook and clinical context before removing outliers.

---

## 3. Duplicate Detection

### Exact Duplicates

- Identical across ALL columns.
- Usually safe to remove (keep first occurrence).
- Common cause: accidental double-submission or ETL errors.

### Near-Duplicates

- Same patient identifier, different records.
- May be legitimate (multiple visits) or errors (same visit entered twice with typos).

### Detection Strategy

1. Check for exact row duplicates: `df.duplicated().sum()`
2. Check for duplicate patient IDs: `df['patient_id'].duplicated().sum()`
3. For near-duplicates: group by patient ID, sort by date, check for records within
   a suspiciously short time window (e.g., same day for what should be annual visits).
4. Fuzzy matching: consider Levenshtein distance on name fields if no unique ID exists.

### Resolution

- Exact duplicates: drop duplicates, log count.
- Same-patient near-duplicates: present to researcher for manual review.
- Never auto-merge patient records without explicit approval.

---

## 4. Date Handling

### Common Date Formats in Clinical Data

| Format | Example | Source |
|--------|---------|--------|
| YYYY-MM-DD | 2024-03-15 | ISO 8601, most databases |
| MM/DD/YYYY | 03/15/2024 | US clinical systems |
| DD/MM/YYYY | 15/03/2024 | European systems |
| YYYYMMDD | 20240315 | DICOM, HL7 |
| DD-Mon-YYYY | 15-Mar-2024 | Some EMR exports |
| Excel serial | 45366 | Excel numeric date |

### Common Issues

- **Ambiguous dates**: Is 03/04/2024 March 4th or April 3rd? Check the data source locale.
  Look for values >12 in the first or second position to disambiguate.
- **Impossible dates**: February 30, month 13, year 0001.
- **Future dates**: Dates after the data extraction date (except for scheduled appointments).
- **Timezone issues**: Rarely relevant for clinical research dates, but critical for timestamps
  in multi-site studies across time zones.
- **Two-digit years**: 24 could be 1924 or 2024. Use a pivot year (e.g., 30: <=30 means 2000s,
  >30 means 1900s) or infer from context.

### Standardization

1. Parse all date columns to datetime using `pd.to_datetime(col, format=..., errors='coerce')`.
2. Check for NaT (failed parses) and investigate.
3. Standardize to ISO 8601 (YYYY-MM-DD) for storage.
4. Calculate derived variables (age at event, follow-up duration) from standardized dates.

---

## 5. Category Harmonization

### Common Inconsistencies

| Raw values | Harmonized |
|-----------|-----------|
| "Male", "male", "M", "MALE", " Male " | "Male" |
| "Y", "Yes", "yes", "YES", "1", "True" | 1 or "Yes" |
| "Right", "Rt", "R", "right", "RT" | "Right" |
| "Non-small cell", "NSCLC", "non small cell" | "NSCLC" |

### Harmonization Steps

1. Strip whitespace: `series.str.strip()`
2. Normalize case: `series.str.lower()` or `series.str.title()`
3. Build a mapping dictionary for known synonyms.
4. Review unmapped values manually.
5. Apply mapping: `series.map(mapping_dict).fillna(series)`

### Encoding Standards

- **ICD-10**: Diagnosis codes. Watch for version differences (ICD-10-CM vs ICD-10-PCS).
- **SNOMED CT**: Clinical terminology. More granular than ICD-10.
- **LOINC**: Laboratory observations. Use for standardizing lab test names.
- **CPT/HCPCS**: Procedure codes.

When possible, map free-text categories to standard coding systems. Document the mapping
table and include it in supplementary materials.

---

## 6. Common Clinical Data Pitfalls

### Lab Values with Inequality Prefixes

Values like "<0.01", ">10000", "<=5" are common for lab results at detection limits.

**Handling options**:
- Replace with the limit value: "<0.01" -> 0.01 (conservative)
- Replace with half the limit: "<0.01" -> 0.005 (common in environmental studies)
- Replace with limit / sqrt(2): "<0.01" -> 0.00707 (EPA method)
- Keep as censored data and use appropriate statistical methods (Tobit regression)

Document the chosen method in the statistical analysis plan.

### Mixed Units

Common in multi-site studies or data merged from different systems.

| Analyte | Unit A | Unit B | Conversion |
|---------|--------|--------|-----------|
| Glucose | mg/dL | mmol/L | mg/dL = mmol/L * 18.018 |
| Creatinine | mg/dL | umol/L | mg/dL = umol/L / 88.4 |
| Hemoglobin | g/dL | g/L | g/dL = g/L / 10 |
| Calcium | mg/dL | mmol/L | mg/dL = mmol/L * 4.008 |

**Detection**: look for bimodal distributions in lab values -- one mode per unit system.

### Sentinel Values

Values used as placeholders for missing data in legacy systems:

| Sentinel | Meaning |
|----------|---------|
| 999, 9999, 99999 | Missing / not recorded |
| -1, -9, -99 | Missing / not applicable |
| 0 | Could be true zero OR missing -- context-dependent |
| 88, 77 | "Not applicable" or "Refused" in survey data |
| 01/01/1900 | Default/missing date |

**Action**: Replace sentinel values with `NaN` BEFORE computing any statistics.
Document which values were treated as sentinel.

### Excel Date Corruption

Excel auto-converts certain strings to dates:
- Gene names: SEPT1 -> Sep-1, MARCH1 -> Mar-1, DEC1 -> Dec-1
- Sample IDs: 1-3 -> Jan-3, 2/4 -> Feb-4

**Prevention**: Open CSV in a text editor first to verify. Import with explicit dtypes
in pandas: `pd.read_csv(path, dtype={'gene': str})`.

**Detection**: Look for datetime values in columns that should contain gene names or
sample identifiers.

### Numeric Precision

- Floating point: 0.1 + 0.2 != 0.3. Use `np.isclose()` for comparisons.
- Rounding: Be consistent. Define rounding rules before analysis.
- Integer overflow: Rare in Python, but watch for 32-bit integer limits in R or
  database imports (max 2,147,483,647).

---

## 7. Recommended Workflow

The recommended end-to-end data cleaning workflow:

1. **Profile**: Run the profiling script. Understand what you have.
2. **Flag**: Identify potential issues. Categorize by type and severity.
3. **Review**: Present flags to the domain expert (you, the researcher).
4. **Approve**: Decide which flags to act on. Document rationale for each decision.
5. **Clean**: Generate and run cleaning code for approved actions only.
6. **Verify**: Compare before/after summaries. Check that cleaning did not introduce
   new problems.
7. **Document**: Save the cleaning log, mapping tables, and decision rationale.
   Include in supplementary materials or methods section.

### Documentation Checklist

- [ ] Number of rows before and after cleaning
- [ ] Number and percentage of missing values per variable (before/after)
- [ ] Outlier handling decisions with justification
- [ ] Duplicate removal count
- [ ] Category mapping tables
- [ ] Imputation method and variables imputed
- [ ] Any variables excluded from analysis and why

---

## 8. Key References

1. Van den Broeck J, Cunningham SA,"; R,"; AB. Data cleaning: detecting,
   diagnosing, and editing data abnormalities. *PLoS Med*. 2005;2(10):e267.
   DOI: 10.1371/journal.pmed.0020267

2. Kang H. The prevention and handling of the missing data.
   *Korean J Anesthesiol*. 2013;64(5):402-406.
   DOI: 10.4097/kjae.2013.64.5.402

3. Sterne JAC, White IR, Carlin JB, et al. Multiple imputation for missing data
   in epidemiological and clinical research: potential and pitfalls.
   *BMJ*. 2009;338:b2393.
   DOI: 10.1136/bmj.b2393

4. Altman DG, Bland JM. Missing data. *BMJ*. 2007;334(7590):424.
   DOI: 10.1136/bmj.38977.682025.2C

5. White IR, Royston P, Wood AM. Multiple imputation using chained equations:
   Issues and guidance for practice. *Stat Med*. 2011;30(4):377-399.
   DOI: 10.1002/sim.4067

6. Ziemann M, Eren Y, El-Osta A. Gene name errors are widespread in the
   scientific literature. *Genome Biol*. 2016;17(1):177.
   DOI: 10.1186/s13059-016-1044-7

---

*This reference is part of the clean-data skill for the medical-research-skills package.*

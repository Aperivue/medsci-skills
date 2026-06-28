# Implausible-Value & Cross-Field Validity Rules

Reference for the clean-data skill, used in **Stage 2 (Flagging)** item 5 ("Implausible values").
It supplies domain-default **hard plausibility bounds** and **cross-field logical-consistency
rules** so the skill can flag likely data-entry errors *even when the codebook does not state a
valid range* — while never auto-correcting them.

This complements `cleaning_patterns.md` §2 (statistical outlier detection): that section finds
values that are *statistically extreme*; this one finds values that are *biologically impossible
or internally contradictory*. The two are different and must not be conflated (§ "Implausible vs
outlier" below).

---

## Implausible vs outlier (the distinction that drives the action)

- **Implausible (compatible-with-life violation / impossible)** — outside the range a living
  human can take, or an impossible code (age 200, SBP 0 in a live patient, BMI 4, % > 100,
  negative count, future birth date). Almost always a **data-entry / unit / sentinel error**.
  Action: correct from source if available, else set to missing and log — do **not** keep it in
  the analytic distribution. (A frank sentinel like 999/9999 is handled in `cleaning_patterns.md`
  §6; treat it as missing *before* range-checking.)
- **Outlier (statistically extreme but biologically possible)** — a BMI of 55, creatinine 12
  mg/dL in dialysis, WBC 300 in leukemia. Action: **keep**; consider a with/without sensitivity
  analysis (`cleaning_patterns.md` §2). Removing a real extreme value as if it were an error
  biases the result.
- The same variable has **both** a hard implausibility bound and a soft outlier fence; apply the
  hard bound first (error removal), then assess outliers among the survivors.

## Population & codebook first

These are **screening bounds to catch errors, not reference/normal ranges, and not analysis
cut-points.** Always reconcile against the data dictionary (dictionary-first) and the **study
population**: neonatal/pediatric, pregnancy, dialysis, ICU, and post-surgical cohorts legitimately
exceed several adult bounds. When the codebook states a valid range, the codebook wins; use this
table only to fill silence, and present every hit as a **flag for review**, never an auto-fix.

## 1. Single-field hard plausibility bounds (adult human, screening)

> Units matter — a bound violation is often a **unit error** (e.g., height in cm stored as m,
> temperature in °F stored as °C, glucose mg/dL vs mmol/L). Check units before treating as an
> error (`cleaning_patterns.md` §6 Mixed Units).

| Domain | Variable (unit) | Implausible if outside | Notes / common error |
|---|---|---|---|
| Demographics | Age (years) | 0–120 | >120 entry error; negative impossible; check DOB-derived age |
| Demographics | Body weight (kg) | 1–400 | <1 = unit error (g?); adult typically 30–250 |
| Demographics | Height (cm) | 30–250 | values 1.5–2.5 = metres stored as cm; >250 entry error |
| Demographics | BMI (kg/m²) | 8–80 | derive and cross-check vs height/weight (§2) |
| Vitals | Systolic BP (mmHg) | 40–300 | 0 in a live patient = error; >300 entry error |
| Vitals | Diastolic BP (mmHg) | 20–200 | must be < systolic (§2) |
| Vitals | Heart rate (bpm) | 20–300 | 0 in a live patient = error |
| Vitals | Respiratory rate (/min) | 4–80 | |
| Vitals | Temperature (°C) | 30–45 | 95–105 = °F stored as °C; outside 30–45 incompatible with life |
| Vitals | SpO₂ (%) | 50–100 | >100 impossible; <50 rarely survivable, suspect error |
| Labs | Blood pH | 6.6–7.8 | outside is incompatible with life |
| Labs | Glucose (mg/dL) | 10–2000 | ÷18 for mmol/L unit error; <10/>2000 suspect |
| Labs | Sodium (mmol/L) | 100–190 | |
| Labs | Potassium (mmol/L) | 1.5–9.5 | |
| Labs | Creatinine (mg/dL) | 0.1–25 | high real in renal failure (outlier, keep) |
| Labs | Hemoglobin (g/dL) | 2–25 | g/L stored as g/dL = ×10 unit error |
| Labs | WBC (×10⁹/L) | 0–500 | high real in leukemia (outlier) |
| Labs | Platelets (×10⁹/L) | 0–3000 | |
| General | Any percentage / proportion | 0–100 (or 0–1) | >100% or >1 impossible; mixed 0–1 vs 0–100 scales |
| General | Any count / duration / dose | ≥ 0 | negative impossible (except intentionally signed change scores) |

(Extend per dataset from the codebook; keep the table version-controlled with the project.)

## 2. Cross-field logical-consistency rules

Single-field bounds miss contradictions *between* fields. Flag a record when:

- **Temporal ordering**: birth date ≤ index/event date ≤ death/last-seen date; admission ≤
  discharge; surgery date ≤ complication date; first ≤ last visit. Any future date beyond the
  extraction date (except scheduled appointments) is suspect (`cleaning_patterns.md` §4).
- **Derived-vs-source**: recomputed BMI from height/weight matches the stored BMI (±rounding);
  age matches (event date − DOB); eGFR consistent with creatinine/age/sex if both stored;
  a "total" equals the sum of its parts; a subset count ≤ its superset count.
- **Sex-specific / state-specific**: pregnancy, parity, or gestational fields present for
  `sex == male`; PSA recorded for females; menopause age < current age; pediatric-only or
  adult-only fields outside the eligible age.
- **Mutually exclusive / dependency**: `deceased == no` with a death date populated;
  `smoking_status == never` with `pack_years > 0` (vs the structural-zero case where it is NULL —
  see SKILL Stage 2 item 7); treatment-stop date before treatment-start date.
- **Range pair**: a "min" field exceeding its paired "max"; diastolic ≥ systolic.

## 3. Flagging discipline (no auto-fix)

- Emit each violation as a **flag** in the Stage 2 table (`Issue Type = Implausible value` or
  `Cross-field inconsistency`), with the rule that fired, the count, and a **suggested** action —
  never an automatic edit (clean-data philosophy: researcher approves each action).
- Severity: a compatible-with-life violation or a hard cross-field contradiction is **High**; a
  bound exceeded only under a special population (possible unit issue) is **Medium** pending unit
  confirmation.
- Prefer **"unit-error" correction over deletion** when a unit mistake is the likely cause (a
  height of 1.75 in a cm column → ×100), but only after confirming the unit; otherwise set to
  missing and log. Record every decision in the cleaning log (`cleaning_patterns.md` §7).

## 4. Key reference

- Van den Broeck J, et al. Data cleaning: detecting, diagnosing, and editing data abnormalities.
  *PLoS Med* 2005;2(10):e267. DOI: 10.1371/journal.pmed.0020267 (the diagnose-vs-edit framework
  this section operationalizes).

---

*This reference is part of the clean-data skill for the medical-research-skills package. The
bounds are error-screening defaults, not clinical reference ranges — verify against the codebook
and study population.*

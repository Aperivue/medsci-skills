# Phase 4 Reference — KM Reconstruction & Composite Exposure Disaggregation

Load this reference when `/meta-analysis` Phase 4 data extraction encounters either
of two special cases: (a) studies that report outcomes only as Kaplan-Meier curves
without raw event counts, or (b) studies whose intervention is a composite of
multiple techniques. The main Phase 4 body of SKILL.md lists the standard
extraction-form fields and the cross-verification checklist; this reference holds
the procedural detail for these two scenarios.

---

## 4b. KM Curve Reconstruction (when raw events not reported)

When studies report outcomes only as Kaplan-Meier curves without raw event counts:

1. **Digitise the KM curve**: Use WebPlotDigitizer
   (https://automeris.io/WebPlotDigitizer/)
   - Calibrate X/Y axes carefully — verify output range matches the original axis labels.
   - If coordinates come out in 0–1 range, multiply X by the actual time range
     (e.g., ×30 for months).
   - Clip negative Y values to 0 (digitisation artifact).
   - Export as CSV: `time, survival`, one file per arm. `IPDfromKM::preprocess()` expects
     **survival probabilities**. A rising curve may be converted (`survival = 1 - y`) **only
     when the paper confirms it is 1 − Kaplan-Meier** — one event type, or a composite
     endpoint with no competing event. Feeding a rising curve in unconverted reconstructs
     nonsense.
   - ⚠️ **A cumulative incidence function (CIF) under competing risks is not 1 − KM.** If the
     figure is a CIF (Aalen-Johansen, Gray's test, Fine-Gray, or "death as a competing risk" in
     the Methods), do **not** convert it, reconstruct KM-type IPD from it, or take a Cox HR from
     it. Example: 100 patients, 50 have the competing event first, 10 of the remaining 50 the
     target event — CIF = 0.10 (1 − CIF = 0.90), but the KM that censors competing events gives
     0.80. Instead extract what the paper reports on the competing-risk scale — the CIF at a
     pre-specified time with its CI, or the subdistribution HR (Fine-Gray) or cause-specific
     HR — and pool like with like; never pool CIF-derived estimates with KM-based HRs. The
     survival package's vignette "Multi-state models and competing risks"
     (`vignette("compete", package = "survival")`): "A common mistake with competing risks is
     to use the Kaplan-Meier separately on each event type while treating other event types as
     censored."

2. **Extract number-at-risk**: Record from the table below the KM plot at each time point.

3. **Reconstruct IPD**: Use the R `IPDfromKM` package (Guyot et al. 2012 method), one
   reconstruction per arm:
   ```r
   library(IPDfromKM)
   dat <- read.csv("digitised_control.csv")          # columns: time, survival
   trisk <- c(0, 6, 12, 18, 24, 30)                   # times of the number-at-risk table
   nrisk <- c(51, 41, 30, 15, 7, 4)                   # numbers at risk at those times
   ipd <- getIPD(preprocess(dat, trisk, nrisk, totalpts = 51, maxy = 1),  # maxy = 100 if in %
                 armID = 0)$IPD                       # data frame: time, status, treat
   ```
   - ⚠️ `getIPD()` returns a list; the reconstructed patients are in `$IPD`.
   - ⚠️ `preprocess()` does NOT accept a `mateflag` parameter (common error).
   - `armID` is only the label written to the `treat` column (the package examples use 0
     for control and 1 for treatment).

4. **Verify**: Generate a reconstructed KM plot and visually compare to the
   original figure; if the paper reports an HR or median survival, check the
   reconstruction reproduces it.

5. **Derive the meta-analysis input** — never `sum(status) / nrow(ipd)`: that count ignores
   censoring and has no time horizon (a 2×2 table is valid only when every patient's status
   at a fixed time is known).
   - Two-arm study: reconstruct both arms, stack them, and take the log HR and its SE from
     `coxph(Surv(time, status) ~ treat)`; pool with `metagen(..., sm = "HR")`. Time-to-event
     outcomes are synthesised as HRs (Tierney et al. 2007, doi:10.1186/1745-6215-8-16).
   - Single-arm outcome: the KM estimate and its SE at a time point pre-specified in the
     protocol, `summary(survfit(Surv(time, status) ~ 1, data = ipd), times = t)`.
   Full code: `r_templates.md` (KM Curve Reconstruction).

6. **Report in Methods**: Cite Guyot et al. 2012 (doi:10.1186/1471-2288-12-9) and
   state which studies required reconstruction.

**Alternative — Text-based extraction**: When no subgroup-specific KM curve exists
but the text reports "0% LTP at 12 months" or similar, extract directly from text.
Document the page number and exact quote.

---

## Composite Exposure Disaggregation

When a study's intervention is a composite of multiple techniques:

1. **Subgroup-specific KM curve** → use KM reconstruction (section 4b above).
2. **Component-specific Table/multivariate** → extract per-component data from Tables.
3. **Text-based subgroup report** → extract from narrative (e.g., "APE arm: 0% LTP").
4. **None available** → include as composite; flag in sensitivity analysis for exclusion.

Always pre-specify a sensitivity analysis excluding composite-exposure studies.
Document the extraction strategy in the data extraction form Notes column.

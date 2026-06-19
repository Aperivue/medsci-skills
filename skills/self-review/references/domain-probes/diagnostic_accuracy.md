<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a design-level
         flaw (verification bias, two-gate sampling, unblinded reference) is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Diagnostic-accuracy / reader-study probes (D1–D6)

A checklist for **diagnostic test accuracy (DTA) primary studies** — an index test against a reference standard, including **multi-reader multi-case (MRMC)** reader studies (e.g., AI-vs-reader or modality-comparison). These probes complement (do not replace) the generic Phase 2 issue checklist and the STARD / QUADAS-2 items; they target the biases QUADAS-2 names and the MRMC design/variance issues a reader study adds. Pairs the `analyze-stats` `table-standards/table-types/reader_study.md` table and the `make-figures` `exemplar_plots/mrmc_roc.md` figure. (For a DTA **meta-analysis**, use `sr_ma.md`.)

**D1 — Reference standard validity + verification bias**:
- Is the **reference standard** appropriate and applied to (essentially) all participants? Partial verification (only test-positives get the gold standard), differential verification (different reference standards by index result), and **incorporation bias** (the index test is part of the reference) each inflate accuracy. QUADAS-2 Domain 3/4.
- Was the reference standard interpreted **without** knowledge of the index result, and was the **time interval** between index and reference short enough that the target condition did not change? A long or undefined interval, or a reference that incorporates the index, → MAJOR.

**D2 — Spectrum + sampling design**:
- How were participants sampled — a **single-gate** consecutive/random series of those with the target condition suspected (preserves spectrum and prevalence), or a **two-gate** case-control design (known cases vs healthy controls)? Two-gate sampling **overestimates** accuracy and distorts spectrum; it is a MAJOR interpretive limit when the headline is clinical accuracy, not just proof-of-concept.
- Is the study **prospective** with a pre-specified index threshold, or retrospective with a threshold chosen on the same data (D-linked to optimism)? Spectrum (disease severity, comorbid mimics) should match the intended-use population.

**D3 — Blinding of index and reference interpretation**:
- Was the **index test** interpreted blind to the reference standard and to clinical information that would not be available at the point of use, and vice versa? Unblinded interpretation (review bias) inflates agreement.
- For an AI index test, was the **operating threshold pre-specified** (not tuned on the test set)? A test-set-tuned threshold reported as the result is an optimistic-validation finding (pair with `exemplar_reviews/optimistic_validation_reporting.md`).

**D4 — Indeterminate / uninterpretable results**:
- How were **indeterminate, uninterpretable, or intermediate** index results handled — excluded, or counted (intention-to-diagnose)? Silently dropping them inflates accuracy. State the rule and report an **intention-to-diagnose** sensitivity analysis (non-diagnostic counted as wrong). Undisclosed exclusion of indeterminates → MAJOR.

**D5 — MRMC reader-study design**:
- Is the design **fully crossed** (every reader reads every case in every modality) or a nested/split-plot variant — and is that stated? Was **reading order randomized** and a **washout** interval used between modalities so a case is not recognised from a prior read? Absent washout/order control in a within-reader modality comparison → MAJOR (memory/recognition bias).
- Are the **readers sampled to generalise** to the intended reader population (number, expertise mix), and were **training/instructions and the information available** (priors, clinical data) standardised? A 2–3 expert-reader convenience panel cannot support a population-level "AI matches radiologists" claim — flag the generalisation gap.

**D6 — MRMC analysis + estimand**:
- Does the analysis account for **both reader and case variability** (Obuchowski–Rockette / Dorfman–Berbaum–Metz or an equivalent multi-reader model), or does it treat readers as fixed / pool reads as if independent? Ignoring reader variance understates uncertainty and is a MAJOR statistical flaw for a generalising claim.
- Is the **estimand** clear: reader-averaged vs a fixed specific reader; per-**patient** vs per-**lesion** (clustered) unit; superiority vs **non-inferiority** with a pre-specified margin? Are **per-reader** results shown alongside the reader-averaged estimate (a single averaged AUC can hide one weak reader)? A non-inferiority claim with no pre-specified margin, or a clustered design analysed as independent, → MAJOR.

**D7 — Index-test-as-enrollment-criterion circularity**:
- Cross-check the **inclusion criteria** against the **index / proposed test**. When a study proposes or validates a diagnostic or classification instrument *and* uses a threshold of that **same** instrument (or a component of it) as an enrollment criterion, the validation is circular: the spectrum is built into the design, and sensitivity/specificity (or the instrument's apparent discrimination) are inflated by construction.
- Typical signatures: "patients were included if [index score] ≥ T" in a paper whose aim is to evaluate that index; enrolling on a positive screening test to then "validate" the screening test; defining the diseased group by the same reader/algorithm output under study.
- This is **design-level, not a reporting fix** — escalate past an ordinary Major (a co-reviewer / editor reads it as a fatal selection/spectrum artifact). The fix is a reference standard and an enrollment criterion that are independent of the index test (a consecutive suspected-disease series), not a re-analysis.

**Output template (D2 / D6 example)**:
> "The study uses a case-control (two-gate) design — confirmed cases versus healthy controls — rather than a consecutive series of patients in whom the diagnosis was suspected. This typically overestimates accuracy and does not reflect the intended-use spectrum, so I'd read the reported sensitivity/specificity as proof-of-concept rather than clinical accuracy, and suggest tempering the Abstract accordingly. Separately, the reader study reports a single reader-averaged AUC; because readers are a sample, I'd suggest an MRMC analysis (e.g., Obuchowski–Rockette) that accounts for both reader and case variance, with per-reader estimates shown and the unit of analysis (per-patient vs per-lesion) stated."

**Discipline — leads vs findings (applies to D1–D6)**:
- A verification/blinding/spectrum concern from a quick scan is a **lead until Methods and the participant flow are read together** — distinguish under-reporting (ask to clarify) from a true design bias (MAJOR).
- Anchor each comment to the exact bias (partial vs differential verification; single- vs two-gate; reader-averaged vs fixed-reader; per-patient vs per-lesion) and the location. Keep severity tied to what the flaw does: two-gate sampling, incorporation bias, or ignoring reader variance is design/analysis-level (MAJOR, often Major #1); an unreported reading-order detail is a clarify-request.

# Empirical Lessons — SR-MA peer-review cycles

Accumulated, dated lessons from real systematic-review / meta-analysis peer-review and
submission cycles. They drive the Phase 4 extraction-form schema, the Phase 4c QC scripts,
and the Phase 8 submission gates. **Load this file when designing the extraction form
(before Phase 4) and before submission (Phase 8).**

> Note: the 2026-05 list below carries a duplicate "9." (the "Prognostic / survival-outcome"
> item) inherited from the source; it is the 11th lesson of that batch. Left as-is here to
> avoid a renumber that would desync any external cross-reference; treat the numbers as labels.

## Empirical Lessons (2026-05)

Synthesized from recent SR-MA peer-review cycles. Drives the Phase 4 extraction form schema, Phase 4c QC scripts, and submission-gate enhancements documented in the skill.

1. **Dual-extractor + source-page-reference + verbatim quote** is mandatory for 2x2 cell integrity. Single-extractor without source-page citation invites sens/spec swap that is invisible to forest-plot-level review.

2. **Cohort overlap detection** must cluster by shared public database + institution + author. Independent-cohort assumption for MA pooling fails when multiple included studies use the same public ICU/EHR cohort with overlapping enrollment windows. Sensitivity analysis excluding overlap is the minimum acknowledgment.

3. **Diagnostic subset N transparency** in mixed DTA + prognostic MAs: report `sample_n_dta_pool` separately from `sample_n_prognostic_pool` with explicit prevalence. Aggregate N in Abstract misleads readers about diagnostic-subset power.

4. **Small-k subgroups are not robust (k < 4)**: a subgroup test driven by a single study (k=1) is descriptive-only, and the same caution extends to k=2–3 — heterogeneity and the trend are not estimable from so few strata. Any subgroup with k < 4 must be labelled descriptive / exploratory rather than entered into a formal subgroup interaction test. Post-hoc subgroups require a PROSPERO amendment with a visible record.

5. **Supplementary 8-file package** is the minimum bar for high-impact journals: PRISMA checklist, PROSPERO PDF, full search strategy, full-text exclusion list with reasons, per-study extraction table, per-study x per-domain RoB, subgroup forests, sensitivity / publication-bias analyses. See `templates/supplementary_8file_checklist.md`.

6. **PROSPERO 14-char ID format** (`^CRD42\d{9}$` = `CRD42` + 4-digit year + 5-digit sequence, e.g. `CRD42024500001`). A 15-character ID is a stray-digit transcription error; pre-2020 IDs may be shorter. Validate with `grep -oE 'CRD42[0-9]+'` + length assert, and request the live registration URL in the cover letter for protocol cross-check.

7. **AI Disclosure presence** for SR-MA submissions to RYAI / Radiology / RSNA / Lancet / JAMA / BMJ / Nature families. Absence triggers MINOR-to-MAJOR finding at peer review.

8. **Sensitivity analyses are recomputed, not copied** (Phase 6b rule 5). Leave-one-out / erosion / alternative-model effect sizes identical to the primary analysis to 2 decimals across ≥4 values means the recomputation did not run. Re-derive from the modified dataset; the inputs (means/SDs/counts) change even when the effect size is close.

9. **Outcome harmonization before pooling.** Studies that report the same-named outcome under different definitions (an imaging-detected event vs a clinically diagnosed one; different thresholds) must not be presented as a single pooled range or pooled estimate. Split by ascertainment method (or pool only the harmonizable subset) and state the definition per stratum — a "6.9–46%" range that silently mixes imaging-detected and clinical events is a heterogeneity artifact, not a finding.

10. **Heterogeneous RoB instruments → no single pooled κ.** When studies are assessed with different risk-of-bias tools (QUADAS-2 for DTA + NOS for cohorts, etc.), do not report one pooled inter-rater κ across the mixed set. Report agreement per instrument, and use an ordinal weighted κ when the domain judgments are ordered (low/some/high). A single κ over a heterogeneous instrument set is uninterpretable.

9. **Prognostic / survival-outcome MAs carry survival-specific concerns** beyond the DTA pitfalls: censoring handling, competing risks (cause-specific vs Fine-Gray), cutoff-derivation optimism, comparator time-horizon alignment, C-index variant transparency (Harrell vs Uno vs IPCW), and calibration beyond discrimination. When pooling prognostic models, pre-specify these in the protocol and report them per study; for the reviewing counterpart see the survival/prognostic 7-probe in `/peer-review`.


## Empirical Lessons (2026-06)

From a CBCT lung-ablation SR-MA submission cycle (Springer / CVIR Editorial Manager). Submission-stage; complements the 2026-05 lessons.

11. **Supplementary materials need the same blinding + de-scaffolding + cross-consistency pass as the manuscript.** The largest source of pre-submission defects this cycle was the supplement shipping as raw internal artifacts — `/check-reporting` output carrying an "Assessed by: <AI tool>" line and a JSON verdict block, and a pre-search planning doc with the author's real name, sibling-project cross-references, unresolved `[Check on execution]` placeholders, and estimate tables that contradicted the actual PRISMA counts. Presence (Lesson 5) is not enough; apply the Phase 8 supplementary gate.

12. **A submitted analysis script must reproduce the manuscript and be self-contained.** A hard-coded study-id subset silently drifted (a pool was k=7 in the script vs k=9 in the results table — the manuscript was correct, the script was stale) and the script read a path outside the bundle. Run the bundled code from a clean copy before submission: it must read the bundled dataset, write to cwd, and regenerate every reported pool. Remove stale figures produced by an out-of-sync script.

13. **Re-sync sidecars (cover letter, title-page Word-Counts table) whenever the reference or word count changes.** Adding methodological/software citations took the list from 12 to 24, but the cover letter and title page still said "12 references" — a contradiction visible in the built PDF. Reference/word-count changes are sidecar drift targets (mirror `submission-portal-verification` cover-letter drift).

14. **Methodological + software citations are a routine SR-MA gap.** The reporting standard (PRISMA 2020), each risk-of-bias tool (JBI, ROBINS-I, …), the pooling method (random-effects GLMM / logit, Hartung-Knapp, the choice over Freeman-Tukey arcsine), the certainty framework (GRADE), and the analysis software (R `meta`, `metafor`) should each be cited where named in Methods. Frequently missing from an early draft and an easy reviewer comment to pre-empt. Verify every added citation via PubMed/CrossRef with a first-author cross-check — never from memory.

15. **Wide characteristics tables (≥ ~10 columns) render as character-wrapped gibberish in the journal's built PDF** when the docx uses fixed narrow columns. Put the table in a landscape section with autofit layout and a smaller font, and verify by converting the docx to PDF (`soffice --headless --convert-to pdf`) and viewing the page — the docx alone does not reveal the problem.

16. **Verify the submission portal's journal identity before entering metadata.** A classification taxonomy that does not match the target journal's scope (e.g., a liver/hepatology list at an interventional-radiology journal) is the tell that you are in the wrong journal's Editorial Manager instance.

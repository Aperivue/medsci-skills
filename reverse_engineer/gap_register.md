# Skill gap register

A living, scored ledger of **skill weaknesses the loop targets**. This supersedes the old
fixed "priority order" — each iteration consults this register (PLAYBOOK Step 0), works the
highest-scoring **open** gap, and feeds newly discovered gaps back in (Step B). The point is to
find the weaknesses across the *whole* suite — including ones we did not know about — by
reading strong papers and noticing what our skills do not yet cover or check.

## Scoring

`score = impact × frequency × deficit` (each 1–5; higher = work it sooner).

- **impact** — how much a real manuscript benefits when this gap is filled.
- **frequency** — how often the relevant study type / task actually shows up.
- **deficit** — how missing it is now (5 = absent, 1 = minor polish).

**status:** `open` · `in-progress` · `shipped (#PR)` · `saturated` (lane's gaps are filled —
stop adding marginal items there).

## How gaps enter the register

1. **Paper-driven (Step B).** While analyzing a strong paper/review, note not only what *it*
   does well but **what a strong paper in this area needs that our skills do not cover or
   check** — a missing exemplar, table-type, figure anatomy, probe, checklist item, or
   template. Add it as a row.
2. **Cross-skill audit (every ~4 iterations).** Pick one skill the loop has not touched
   recently and scan its `references/` against the common cases in its domain (what table
   types / figure types / probes / templates a practitioner expects). Record what is absent.
   Rotate the audited skill so coverage spreads beyond the obvious (figures, review skills).
3. **User-flagged.** Areas the user calls out (e.g., figures).

## Open gaps (work highest score first)

| id | skill | gap | impact | freq | deficit | score | status |
|----|-------|-----|:------:|:----:|:-------:|:-----:|--------|
| G1 | make-figures | `exemplar_plots/km_curve.md` — KM survival-curve anatomy (number-at-risk, censoring marks, CI band, no extrapolation past follow-up); pairs the survival table-type | 4 | 5 | 5 | 100 | shipped (#151) |
| G2 | analyze-stats | `table-types/agreement.md` — reliability table (ICC / weighted κ / Bland–Altman LoA) — supported by `agreement_analysis.py` but no table-type template | 4 | 4 | 5 | 80 | shipped (#151) |
| G3 | make-figures | `exemplar_plots/roc_pr.md` — ROC / precision-recall anatomy (CI band, operating point, AUPRC under imbalance) | 4 | 5 | 5 | 100 | shipped (#151) |
| G4 | make-figures | `exemplar_plots/calibration_plot.md` — calibration anatomy (bins/loess, slope/intercept, distribution rug) | 4 | 4 | 5 | 80 | shipped (#151) |
| G5 | peer-review + self-review | `domain-probes/` RCT / intervention-trial probe (CONSORT: randomisation, allocation concealment, blinding, ITT, selective-outcome) — no trial probe despite trials being common | 5 | 4 | 5 | 100 | shipped (#151) |
| G6 | make-figures | `exemplar_plots/bland_altman.md` + `confusion_matrix.md` | 3 | 3 | 5 | 45 | shipped (#146) |
| G7 | write-paper | `exemplar_introduction.md` + `exemplar_abstract.md` (the two sections without exemplars; section_guides exist) | 3 | 5 | 3 | 45 | shipped (#147) |
| G8 | check-reporting | `appraisal_tools/METRICS.md` — radiomics methodological-quality tool (named in the critical-item floor but no fuller reference). Placed under `appraisal_tools/` (NOT counted `checklists/`) because METRICS is a quality/RoB tool, not a reporting guideline — no reporting-guideline count change | 3 | 3 | 4 | 36 | shipped (#148) |
| G9 | calc-sample-size | `references/justification_examples.md` — reviewer-safe sample-size justification prose per design (found via cross-skill audit; SKILL.md promised "IRB-ready justification text" but no exemplar library) | 4 | 4 | 4 | 64 | shipped (#151) |
| G10 | present-paper | `scripts/inject_speaker_notes.py` run-level markdown parser — general speaker notes rendered `**bold**` literally (the failure mode pptx-speaker-notes.md warns against); the parser existed only in inject_pronunciation_notes.py. Found while triaging the unmerged `present-paper-md-notes-glossary` branch (whose verify_refs/academic-aio parts were already superseded by main) | 3 | 4 | 4 | 48 | shipped (rescue PR) |
| G11 | manage-refs | `scripts/render_pandoc.sh` had no pre-render reference audit — a direct render call could ship fabricated/mismatched citations (the master pre_submission_gate audits, but direct calls bypass it). Found while triaging the unmerged present-paper-md-notes-glossary branch | 4 | 3 | 4 | 48 | shipped (cleanup PR) |
| G12 | make-figures | `exemplar_plots/decision_curve.md` — net-benefit decision-curve (DCA) anatomy (treat-all/treat-none reference lines, threshold-probability range, model curve, operating-point); the clinical-utility counterpart to ROC/calibration. Cross-cutting: unblocks prognostic + TRIPOD+AI + clinical-impact. Found while reverse-engineering adjacent clinical-research areas (prognostic external validation) | 4 | 4 | 5 | 80 | shipped (#141) |
| G13 | check-reporting | `checklists/TRIPOD_LLM.md` — TRIPOD-LLM reporting guideline for studies using large language models (base TRIPOD + LLM extension). Step 4e already routes the name but no checklist is vendored — a `MISSING_CHECKLIST_CONTRACT_VIOLATION` waiting to happen. Found while reverse-engineering the LLM-study reporting area | 5 | 3 | 5 | 75 | shipped (#141) |
| G14 | analyze-stats | `table-types/incremental_value.md` — "beyond baseline" added-value table standard (ΔAUC + DeLong CI, NRI, IDI, net-benefit); no table-type covers incremental-value claims, which AI-vs-baseline and prognostic papers routinely make. Pre-builds the clinical-impact NRI/IDI need | 4 | 3 | 5 | 60 | shipped (#141) |
| G15 | peer-review + self-review | `domain-probes/survival_prognostic.md` TRIPOD+AI subsection — model/dataset-flow (train/tune/internal-test/external-test), subgroup/fairness performance, calibration paired with decision-curve. The survival/prognostic probe (S1–S8) checks survival design but not the AI-prediction-model reporting flow that TRIPOD+AI governs | 4 | 4 | 4 | 64 | shipped (#141) |
| G16 | check-reporting | `checklists/CONSORT_AI.md` — CONSORT-AI extension (AI clinical-trial **reports**). Already routed in Step 1 + aliased (`consortai`) but unvendored — the fail-fast test asserts it as a MISSING_CHECKLIST_CONTRACT_VIOLATION. Vendoring closes that contract gap. Found reverse-engineering the AI-RCT reporting area | 5 | 3 | 5 | 75 | shipped (#142) |
| G17 | check-reporting | `checklists/SPIRIT_AI.md` — SPIRIT-AI extension (AI clinical-trial **protocols**). Same unvendored-but-routed contract gap as CONSORT-AI; the protocol counterpart | 5 | 3 | 5 | 75 | shipped (#142) |
| G18 | peer-review + self-review | `domain-probes/rct_trial.md` AI-extension subsection — the RCT probe (RC0–RC7) checks trial design but not the CONSORT-AI/SPIRIT-AI reporting flow (algorithm version, input-data criteria, human–AI interaction, poor-input handling, performance-error analysis, code accessibility) | 4 | 3 | 4 | 48 | shipped (#142) |
| G19 | peer-review + self-review | `domain-probes/diagnostic_accuracy.md` (NEW MODULE, D1–D6) — DTA primary studies + MRMC reader studies had no probe (sr_ma covers DTA *meta-analysis* only): verification/spectrum/blinding bias, indeterminate handling, MRMC fully-crossed/washout design, reader+case variance (Obuchowski–Rockette). Found reverse-engineering the prospective-DTA/MRMC area | 5 | 3 | 5 | 75 | shipped (#143) |
| G20 | make-figures | `exemplar_plots/mrmc_roc.md` — MRMC reader-study ROC anatomy (per-reader + reader-averaged curves, MRMC reader+case CI, ΔAUC + margin, unit/design note); no reader-study figure exemplar existed | 4 | 3 | 5 | 60 | shipped (#143) |
| G21 | analyze-stats | `table-types/reader_study.md` — MRMC per-reader + reader-averaged performance table (OR/DBM reader+case CI, per-patient vs per-lesion, non-inferiority margin); distinct from agreement.md (reliability) | 4 | 3 | 5 | 60 | shipped (#143) |
| G22 | check-reporting | `checklists/DECIDE_AI.md` — DECIDE-AI reporting guideline for the early-stage live clinical evaluation of AI decision-support systems (the development-to-implementation gap between offline validation and a definitive trial). No checklist covered live-deployment/human-factors/safety reporting. Found reverse-engineering the clinical-impact area | 5 | 3 | 5 | 75 | shipped (#144) |
| G23 | peer-review + self-review | `domain-probes/ai_overclaiming.md` decision-impact subsection (DI1–DI5, DECIDE-AI axis) — live/prospective vs retrospective evidence, intended-use/deployment pathway, threshold + calibration/utility, workflow integration + human–computer override, safety/error capture + subgroup safety. Sharpens AO4 for the deployment-evaluation case | 4 | 3 | 4 | 48 | shipped (#144) |
| G24 | write-paper | `references/exemplar_case_report.md` — CARE narrative-flow and 150-word Introduction / Case Presentation / Conclusion abstract anatomy; catches rarity-without-teaching-value, consent/de-identification gaps, chronology collapse, and n=1 causal overclaiming | 4 | 3 | 5 | 60 | shipped (#150) |
| G25 | peer-review + self-review | `domain-probes/case_report.md` (NEW MODULE, CR1–CR6) — case-report novelty/teaching-value, consent + image de-identification, temporal-vs-causal discipline, similar-case comparison, CARE timeline/follow-up completeness, and teaching-point scope | 4 | 3 | 5 | 60 | shipped (#150) |
| G26 | make-figures | `exemplar_plots/clinical_timeline.md` — CARE clinical-timeline anatomy with relative time axis, event lanes, index-presentation marker, final follow-up endpoint, and annotated imaging-panel pairing | 3 | 3 | 5 | 45 | shipped (#150) |
| G27 | write-paper | `references/paper_types/case_series.md` (NEW) + Phase 0 case-series mode — a case series is a methods-light mini-cohort (design/setting/identification/eligibility/protocol + all-cases summary table + cross-case synthesis), not N stacked single reports; enforces counts-not-rates and selection/ascertainment disclosure. Found reverse-engineering a CC-BY imaging case series (TOS, n=8) | 4 | 3 | 5 | 60 | shipped (#151) |
| G28 | write-paper | `exemplar_case_report.md` adverse-event + diagnostic-pitfall subtypes — pharmacovigilance causality (Naranjo/WHO-UMC + dechallenge + severity/preventability + denominator) and mimic/pitfall differential-adjudication + diagnostic-delay + self-critical mechanism reasoning. Found reverse-engineering CC-BY ADR (amox-clav), contrast-extravasation, and NPC-mimic case reports | 4 | 3 | 4 | 48 | shipped (#151) |
| G29 | peer-review + self-review | `domain-probes/case_report.md` CR7 (adverse-event causality discipline: instrument/dechallenge/denominator/alternative-exclusion) + CR8 (case-series design: cohort-methods/summary-table, selection/ascertainment, counts-not-rates). CR1–CR6 → CR1–CR8 | 4 | 3 | 4 | 48 | shipped (#151) |
| G30 | make-figures | `exemplar_plots/imaging_panel.md` (NEW) — annotated multimodality/multi-sequence imaging panel: lettered sub-panels, arrow-to-finding, quantitative labels (size/SUVmax/category), same-lesion correspondence for discordance/response, de-identification. Distinct from clinical_timeline (chronology). Found reverse-engineering CC-BY radiology case reports (mammo/US/PET discordance; per-sequence MRI; CT/PET-CT staging) | 3 | 3 | 5 | 45 | shipped (#151) |
| G31 | find-journal | Case-report/series venue profiles (Journal of Medical Case Reports, Cureus, Radiology Case Reports, BMJ Case Reports) — compact profiles; identity/scope/article-types/OA verified from primary CC-BY articles + Cureus author guide; word/figure limits flagged for pre-submission verification (publisher pages auth-gated). journal_profiles_find 68→72. Detail (write-paper) profiles deferred until guidelines are fetchable | 3 | 3 | 4 | 36 | shipped (#151, compact) |
| G32 | check-reporting | `CARE.md` enrichment — adverse-event case reports add a causality instrument (Naranjo/WHO-UMC) + dechallenge/severity/preventability; case series need cohort-style methods + all-cases table (CARE alone is single-patient). Item-level guidance edited into existing CARE.md, not a new checklist (count stays 36) | 3 | 2 | 3 | 18 | shipped (#151) |
| G33 | write-paper | `references/exemplar_case_report_radiology.md` (NEW) — imaging-led case-report discipline: per-modality technique→findings→impression, structured-reporting lexicons (BI-RADS/LI-RADS/PI-RADS/TI-RADS/Lung-RADS/O-RADS), quantitative anchors + ROI method + threshold honesty, multimodality discordance + modality-completeness, IR procedure/complication subtype, incidental-finding reporting, DICOM de-identification + real alt text + device-vendor COI. Found reverse-engineering 6 CC-BY radiology case reports (multimodality US/MRI, photon-counting CT, CT-guided cryoablation, endovascular hemobilia, spectral-CT BI-RADS, FDG-PET incidental) | 5 | 4 | 4 | 80 | shipped (this PR) |
| G34 | peer-review + self-review | `domain-probes/case_report.md` CR9 — imaging-led reporting discipline (per-modality technique/finding/impression + reproducible technique, structured-reporting category use, quantitative threshold honesty, multimodality discordance, IR complication latency, DICOM de-id/real alt text, device-vendor COI). CR1–CR8 → CR1–CR9 | 5 | 4 | 4 | 80 | shipped (this PR) |
| G35 | find-journal | BJR Case Reports compact venue profile (BIR/Oxford, CC-BY, imaging case-report scope) — identity verified from a CC-BY article; complements Radiology Case Reports. journal_profiles_find 72→73. JRCR deferred (not OA-indexed in Europe PMC) | 3 | 3 | 4 | 36 | shipped (this PR) |
| G36 | verify-refs | corporate/collective-author handling — a guideline body double-braced in BibTeX (`{{EASL} and {EASD}}`, `{{KDIGO Work Group}}`) tripped the first-author cross-check as MISMATCH and **aborted `render_pandoc.sh`** on every guideline-citing cohort manuscript. Detect corporate authors (double-brace / `<CollectiveName>` / org keyword) and exempt them from the personal-name cross-check. Found in the a cross-sectional fatty-liver cohort cycle | 5 | 4 | 5 | 100 | shipped (this PR) |
| G37 | self-review | `scripts/check_paren_spans.py` (NEW detector) — post em-dash→paren conversion safety scan: a bulk `— X —`→`(X)` edit can pair unrelated dashes across a sentence boundary and wrap a whole sentence / ordinal limitation inside parens (paren-balanced, so a balance check misses it). Wired into `/self-review` `--fix` post-edit + `/humanize` pattern 13. Detector 26→27 | 5 | 4 | 4 | 80 | shipped (this PR) |
| G38 | self-review | `check_classical_style.py` em-dash counter counts **prose only** — excludes table-cell `—` (N/A placeholders, panel labels), ORCID separators, and author/affiliation lines, reporting prose-vs-structural separately. Avoids forcing destructive edits on correct table dashes in cohort manuscripts with large Table 1/3 | 4 | 4 | 4 | 64 | shipped (this PR) |
| G39 | peer-review + self-review | `domain-probes/survival_prognostic.md` S9 — panel-data / multistate variance: occupancy & intensity CIs must be person-clustered (bootstrap-by-person or robust sandwich), not naive model-based on visit-transitions; report N persons (and contributing transitions), not just visit-pairs. Found in a multistate-Markov cohort cycle | 4 | 3 | 4 | 48 | open |
| G40 | peer-review + self-review | `domain-probes/observational_confounding.md` O10 — overlapping-subset gradient (descriptive vs inferential): an HR/OR "gradient/trend across nested or overlapping cohorts" with no difference/interaction test must use descriptive language only ("shift attributable by construction"), not "attenuated/accounted for". Comparator-refinement analogue of the scope-coherence sensitivity-envelope rule | 4 | 3 | 4 | 48 | open |
| G41 | self-review + analyze-stats | extended-adjustment missingness-frame discipline — when an extended-adjustment model changes the analytic N (covariate missingness), compare the adjusted estimate to the **unadjusted complete-case estimate on the same reduced frame**, not the full-frame anchor; flag any "adjustment changes the estimate" claim that compares across different frames | 4 | 3 | 4 | 48 | open |
| G42 | sync-submission | `scripts/assemble_supplement.py` (candidate) — cohort supplements are ad-hoc `S{N}_*.md` + `00_index.md` + hand-concatenated `_combined.md`; validate index↔file 1:1, detect duplicate/skipped sub-section numbers after inserts, rebuild `_combined` in index order, render docx/pdf, emit section→callout coverage. Reuses the supplementary-numbering lock | 3 | 3 | 4 | 36 | open |
| G43 | render-pdf-doc | scientific-symbol + CJK font-coverage check — xelatex supplement PDFs drop arrows (→ ubiquitous in transition tables), `− ↑ ↓ √ ∪ ≤ ≥ ★ ✓`, and CJK in default fonts; warn/fail on residual missing-character classes rather than silently dropping glyphs (DOCX authoritative). Found rendering a multistate-Markov cohort supplement | 3 | 3 | 4 | 36 | open |
| G44 | (cross-sectional-cohort lane) | paper-driven discovery: acquire strong CC-BY **cross-sectional / prevalence / health-screening** cohort papers from good journals and surface what the suite does not yet cover or check beyond O1–O9 / the cohort gates. Lane seed — specific gaps added as papers are read | 4 | 4 | 3 | 48 | open |

> Numbering note: G12–G23 are this reverse-engineering batch (decision-curve+TRIPOD-LLM, AI-RCT, prospective-DTA+MRMC, DECIDE-AI); rows are marked shipped (#PR) post-merge.

## Lane status

- **make-figures** (figure exemplars): forest shipped (#130); km/roc/calibration/bland-altman/
  confusion/visual-abstract open — **the suite's weakest area, keep returning here.**
- **write-paper exemplars**: methods/results/discussion trio + intro/abstract shipped; case-report
  exemplar (incl. adverse-event + diagnostic-pitfall subtypes) + case-series paper type + radiology/
  imaging-led case-report exemplar shipped.
- **review domain-probes**: case-report module CR1–CR9 (incl. adverse-event causality + case-series +
  imaging-led radiology discipline); survey/qualitative/economic still open.
- **case-report venues (find-journal)**: JMCR, Cureus, Radiology Case Reports, BMJ Case Reports, BJR
  Case Reports shipped (compact); detail/write-paper venue profiles + JRCR deferred.
- **cross-sectional cohort (cross-sectional-cohort harvest + paper-driven)**: observational probes O1–O9
  (over-adjustment, analysis-unit/clustering, outcome construct validity, exposure-defining exemption,
  reference-arm contamination), clinical-prediction module CP1–CP4, cohort gates (ANALYSIS_UNIT,
  YIELD_LANGUAGE, wordcount-cap, confounding alias+SMD-from-mean±SD) shipped (PR #153); cohort-cycle follow-up
  verify-refs corporate-author + paren-span detector + prose-em-dash shipped (this PR); S9 panel-data,
  O10 overlapping-subset gradient, missingness-frame, supplement-assembly, PDF-font-coverage **open**;
  cross-sectional-cohort paper-driven discovery (G44) **open** — acquire CC-BY prevalence/screening
  cohorts and surface new gaps. Rule-side C2 (sensitivity↔suppl-table number collision) + E3
  (supplement-prose CJK leak) routed to `~/.claude/rules` (not medsci-skills).

## Shipped (audit trail)

| id | shipped | skill | note |
|----|---------|-------|------|
| — | #128–#130 | peer-review/self-review/write-paper/analyze-stats/make-figures/check-reporting | optimistic-validation seam, exemplar trio, survival table, forest exemplar, critical-item floor, selective-outcome exemplar |

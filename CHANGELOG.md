# Changelog

## [Unreleased]

### Added

- **Observational / cohort probe + gate hardening** (sourced from two cross-sectional health-screening cohort self-review→revise loops). Expands `observational_confounding.md` **O1–O6 → O1–O9** (vendored byte-identical into `/self-review`): **O7 — over-adjustment** (conditioning on a mediator or consequence of the outcome — the opposite-direction failure to O1, e.g. a renally-excreted lab in an eGFR model; "adjust for everything that differs in Table 1" is not a confounder-selection rule), **O8 — analysis unit & clustering** (records vs unique subjects → anti-conservative CIs), **O9 — outcome construct validity** for report-/registry-derived outcomes (composite homogeneity, ascertainment/κ, dictionary-first label provenance, misclassification direction). O1 also gains an **exposure-defining-covariate exemption** for guideline-defined exposures and a reference-arm-contamination-vs-selection-bias note (O3); `check_confounding_completeness.py` now **computes SMD from per-stratum mean ± SD** when the wide Table 1 carries no p / SMD column (interop with `/analyze-stats`).
- **New domain-probe module `clinical_prediction_model.md` (CP1–CP4)** for cross-sectional / observational prediction models (TRIPOD / TRIPOD+AI nested predictor-set comparisons): apparent-vs-optimism-corrected calibration/DCA, the incremental-value-vs-marginal-effect **two-null distinction**, EPV per nested model, and net benefit as a model comparison (not a policy endorsement). Vendored byte-identical into `/self-review`; `MODULES` 9 → 10; routed from peer-review (new Phase 2E-2) and self-review. Plus two `/self-review` `exemplar_findings/` (`over_adjustment_collider.md`, `prediction_two_null_conflation.md`).
- **`check_cohort_arithmetic.py` — new `ANALYSIS_UNIT_UNDISCLOSED` check** (`--id-col`, auto-detect with a cardinality guard): when records > unique subjects and the manuscript discloses neither the analysis unit nor a one-record-per-subject sensitivity, emits a Major with a `records / unique_subjects / repeat_subjects / max_visits` reconciliation (probe O8).
- **`check_scope_coherence.py` — new `CROSS_SECTIONAL_YIELD_LANGUAGE` lexicon** (Minor): a cross-sectional / prevalence design using incidence-flavored vocabulary ("yield", "detection rate", "number-needed-to-screen/image", "rescreen interval") without defining "yield" once as cross-sectional report-positive prevalence.
- **New detector `check_paren_spans.py`** (`/self-review`, integrity detectors **26 → 27**, family *Style & review-process*) — a post em-dash→paren-conversion safety scan (cohort-cycle follow-up): a bulk `— X —` → `(X)` edit can pair two *unrelated* dashes across a sentence boundary and wrap a whole sentence — or an ordinal limitation ("Sixth, …") — inside one parenthesis, paren-balanced so a balance check misses it. Flags `PAREN_SPAN_ORDINAL` and `PAREN_SPAN_SENTENCE` (long spans only, so short legitimate parentheticals like "(Dr. Smith)", "(Fig. 2)", "(95% CI …)" are clean). Wired into `/self-review` `--fix` post-edit and `/humanize` pattern 13. Fixtures + regression test (CI-gated).
- **New detector `check_wordcount_cap.py`** (`/sync-submission`, integrity detectors **25 → 26**, family *Reporting compliance*) — the **revision-inflation trap**: a revise loop monotonically adds words and silently breaches the target journal's body cap. Counts the body (Introduction → Discussion, skipping abstract/refs/tables/declarations), compares to a cap from `--limit` or a parsed `--journal-profile` article-type line, and emits `WORDCOUNT_OVER_CAP` (Major) / `WORDCOUNT_NEAR_CAP` (Minor, >0.95×). The binding number is the rendered count (citeproc expands `[@key]`), so it prefers `--rendered-words N` and otherwise estimates from the markdown body + inline-citation expansion. Wired as `/sync-submission` Gate 13, a `/revise` exit gate (re-run after every pass), and a `/self-review` §F check. Ships fixtures + regression test.

### Fixed

- **`verify_refs.py` — corporate/collective-author render-abort fix (cohort-cycle follow-up).** A guideline body double-braced in BibTeX (`{{EASL} and {EASD}}`, `{{KDIGO CKD Work Group}}`) or returned by PubMed as `<CollectiveName>` tripped the first-author cross-check as MISMATCH, which **aborted `render_pandoc.sh` on every guideline-citing cohort manuscript**. Corporate authors are now detected (surviving brace / `<CollectiveName>` / organization keyword) and exempted from the personal-name family cross-check (annotated `corporate/collective author`, never MISMATCH). Personal-author entries are unaffected.
- **`check_classical_style.py` — em-dash counter counts prose only (cohort-cycle follow-up).** It excludes structural dashes — markdown table cells (incl. "—" N/A placeholders and `(A) —` panel-label captions), ORCID separators, and author/affiliation lines — and reports prose-vs-structural separately, so a cohort manuscript with large baseline tables is not pushed into destructive edits on correct table dashes.
- **`check_confounding_completeness.py` — DB-column-code ↔ prose alias map.** A DB-exported Table 1 carrying column codes (`he_sbp`, `b_uric`, `b_chol_hdl`) was false-flagged as imbalanced-and-unadjusted when the adjustment set was written in prose ("systolic blood pressure"). An alias map now resolves both to a shared concept; it only ever *adds* matches (no new false ✓). Genuinely unadjusted covariates still flag.
- **`check_confounding_completeness.py` — exposure-defining-covariate exemption (O1 false-positive on guideline-defined exposures).** For a guideline-defined exposure (MASLD / metabolic syndrome / CKM / sarcopenia / frailty), the components of its own diagnostic criteria (BMI, glycaemia, lipids, BP) are imbalanced *by construction* and correctly unadjusted — the gate flagged each as a Major. New `--exposure-defining-list/-file` marks these `EXPOSURE_DEFINING_EXEMPT` (adjusting for them is over-adjustment, probe O7), so the Major remains only for genuine non-defining prognostic covariates. O1 wording updated; also a fixed `_pick_col` substring bug (a 1–2-char hint like "p" matched an unrelated column such as "exposed").

### Changed

- **`/self-review`** — adds a **difference-in-significance discipline** check (§C; "stronger in A (p<0.05) than B (p=NS)" without a formal interaction test), **statistic-type fidelity** and **stale-derived-CSV (n-mismatch)** checks (Phase 2.5a), **`POWER_MODEL_MISSPEC` / `POWER_VALUE_INTERPOLATED`** (Phase 2.5a-2; the power/MDE simulation must use the primary-model adjustment set and not be interpolated), an additive **`requires_reanalysis`** issue-schema field that routes data-level fixes to `/analyze-stats` instead of a prose `--fix` (Phase 4), and **re-run-the-panel-after-a-large-revision** guidance (Phase 2.6).
- **`/analyze-stats`** — over-adjustment covariate-selection guidance for cross-sectional outcome models, and a **Table 1 mean(SD)-vs-median(IQR) rule by `|skewness|>1`** (not a mean−median/SD heuristic) coupled to Wilcoxon / t-test.
- **`/check-reporting`** — STROBE common-gap items: power-aware framing of a null result, and confounder-selection rationale (no kitchen-sink / no outcome-consequence adjustment).
- **`/write-paper`** — observational-cohort Discussion exemplar gains power-aware null framing and an over-adjustment limitation.
- **`/revise`** — `requires_reanalysis` self-review findings auto-route to `/analyze-stats`; adds a Body-word-count-vs-cap exit gate (re-run `check_wordcount_cap.py` after every pass).
- **`/self-review`** — `--panel` now treats the SSOT-singularity gate (Phase 1 step 4) as a **blocking precondition**: if >1 manuscript-like `.md` exists and none is pinned (`SSOT.yaml` / `--ssot`), it halts before spawning reviewers rather than risk a whole panel on a stale copy.

No skill / reporting-guideline count change (45 / 36); integrity detectors 25 → 27 (`check_wordcount_cap`, `check_paren_spans`).

## [4.2.0] - 2026-06-15

### Added

- **Radiology / imaging-led case-report track (G33–G35)** — a dedicated layer for radiology, nuclear-medicine, and interventional-radiology case reports, grounded in six CC-BY radiology case reports (Europe PMC, learn-only under `distill.py`; `_corpus/` gitignored, no source prose reproduced). Adds a `write-paper` **`exemplar_case_report_radiology.md`** (per-modality technique→findings→impression discipline; structured-reporting lexicons BI-RADS/LI-RADS/PI-RADS/TI-RADS/Lung-RADS/O-RADS with category meaning; quantitative anchors with ROI method and threshold honesty; multimodality discordance + modality-completeness; an interventional-radiology procedure/complication subtype; incidental-finding reporting; DICOM de-identification, real alt text, and device-vendor COI) wired into Phase 0 for imaging-led cases; extends the `/peer-review` + `/self-review` case-report probe to **CR1–CR9** (CR9 imaging-led discipline); and adds a compact `/find-journal` **BJR Case Reports** profile (`journal_profiles_find` 72→73). No new skill or reporting-guideline count.
- **Case-report depth batch (G27–G30)** — extends the case-report feature, grounded in six CC-BY case reports (fetched via Europe PMC, learn-only under the `distill.py` license firewall; `_corpus/` gitignored). Adds a `write-paper` **case-series** paper type (`references/paper_types/case_series.md`) + Phase 0 case-series mode — a methods-light mini-cohort (design/identification/eligibility/protocol + all-cases summary table + cross-case synthesis), not N stacked single reports, enforcing counts-not-rates and selection disclosure; enriches `exemplar_case_report.md` with **adverse-event/pharmacovigilance** (Naranjo/WHO-UMC causality, dechallenge, severity/preventability, denominator framing) and **diagnostic-pitfall/mimic** (differential adjudication, diagnostic-delay framing, self-critical mechanism reasoning) subtypes; extends the `/peer-review` + `/self-review` case-report probe to **CR1–CR8** (CR7 adverse-event causality discipline, CR8 case-series design); and adds a `/make-figures` **annotated multimodality imaging-panel** exemplar (`exemplar_plots/imaging_panel.md`) for discordance/response figures, distinct from the clinical-timeline chronology figure. Also adds four compact `/find-journal` **case-report venue profiles** (Journal of Medical Case Reports, Cureus, Radiology Case Reports, BMJ Case Reports; `journal_profiles_find` 68→72, identity/scope verified from primary CC-BY articles, submission limits flagged for pre-submission verification) and enriches `/check-reporting` `CARE.md` with adverse-event (causality instrument) and case-series (cohort-methods) application notes. No new skill or reporting-guideline count (36).
- **Reverse-engineering batch — adjacent clinical-research scaffolds (reporting guidelines 32 → 36).** A scored, gap-register-driven loop (`reverse_engineer/`) added guideline-grounded scaffolds for clinical-AI areas the project did not yet cover, each authored under the license firewall (`distill.py`): own-words **educational summaries** of the guideline item *intent* (no verbatim wording from copyrighted/NC sources), with `_corpus/` raw sources gitignored. Four new vendored reporting checklists in `skills/check-reporting/references/checklists/` — **TRIPOD-LLM** (studies using large language models; numbered to the official 19-item scheme), **CONSORT-AI** + **SPIRIT-AI** (AI clinical-trial reports + protocols; close a pre-existing `MISSING_CHECKLIST_CONTRACT_VIOLATION` where both were routed/aliased but unvendored), and **DECIDE-AI** (early-stage live clinical evaluation of AI decision-support). Each wired end-to-end (alias map, fail-fast test, `LICENSES.md` row, Step 1 auto-detect row, `skill.yml` card) and CI-gated by `validate_catalog_consistency.py` (32 → 36).
- **METRICS radiomics appraisal reference (`skills/check-reporting/references/appraisal_tools/METRICS.md`)** — a methodological-quality / risk-of-bias tool (EuSoMII; Kocak et al. *Insights Imaging* 2024, CC BY 4.0), 9 categories / 30 weighted condition-dependent items. Deliberately placed under `appraisal_tools/` (NOT counted `references/checklists/`) so it does **not** inflate the reporting-guideline count — the repo keeps appraisal tools distinct from reporting checklists (`critical_item_floor.md`). Wired as the load-on-demand reference behind the Step 4f appraisal cross-check; reporting-guideline count stays 36.
- **New domain-probe module + AI-extension subsections** (`skills/peer-review/references/domain-probes/`, vendored byte-identical into `/self-review`). New module **`diagnostic_accuracy.md` (D1–D6)** for DTA primary studies + multi-reader multi-case (MRMC) reader studies (verification/spectrum/blinding bias, indeterminate handling, fully-crossed/washout design, reader+case variance). Plus AI reporting-flow subsections on three existing modules: **TRIPOD+AI (T1–T4)** on `survival_prognostic.md`, **CONSORT-AI/SPIRIT-AI (A1–A5)** on `rct_trial.md`, and **decision-impact (DI1–DI5, DECIDE-AI axis)** on `ai_overclaiming.md`. `MODULES` tuple 7 → 8; routed from both peer-review (new Phase 2I) and self-review.
- **Figure-anatomy exemplars (`skills/make-figures/references/exemplar_plots/`)** — four new synthetic, citation-free anatomy models: **`decision_curve.md`** (net-benefit / DCA), **`mrmc_roc.md`** (MRMC reader-study ROC with per-reader + reader-averaged curves and reader+case CIs), **`bland_altman.md`** (agreement: bias + ±1.96·SD limits with CIs, proportional-bias check, not-a-correlation discipline), and **`confusion_matrix.md`** (raw + row/column-normalized, class-imbalance caveat).
- **Table-type standards (`skills/analyze-stats/references/table-standards/table-types/`)** — **`incremental_value.md`** (added value beyond a baseline: paired ΔAUC + DeLong CI, NRI event/non-event split, IDI, net benefit) and **`reader_study.md`** (MRMC per-reader + reader-averaged performance with Obuchowski–Rockette/DBM reader+case CIs, per-patient vs per-lesion unit).
- **Structured-abstract exemplar (`skills/write-paper/references/exemplar_abstract.md`)** — completes the write-paper exemplar set (intro/methods/results/discussion already shipped); mandates a primary estimate with 95% CI + denominator and a failure-modes section (no estimate-free "significant", no body↔abstract number mismatch). Wired into Phase 6.
- **Case-report writing feature (G24–G26)** — adds a clean-room `write-paper` case-report exemplar (`references/exemplar_case_report.md`) for CARE narrative flow and 150-word Introduction / Case Presentation / Conclusion abstracts; a new byte-vendored `/peer-review` + `/self-review` case-report domain probe (`domain-probes/case_report.md`, CR1–CR6) covering novelty/teaching value, consent and image de-identification, n=1 causal overclaiming, literature-boundary claims, CARE timeline/follow-up completeness, and teaching-point scope; and a `/make-figures` clinical-timeline anatomy model (`exemplar_plots/clinical_timeline.md`) for CARE timeline figures and annotated imaging-panel pairing. No new skill or reporting-guideline count.

### Changed

- **CARE version label aligned to the vendored checklist** — `/write-paper` case-report mode and paper-type template now refer to CARE 2013, matching `/check-reporting`'s bundled `CARE.md` (Gagnier et al. 2014 / care-statement.org), instead of the previous CARE 2016 label.
- **Recommendation-calibration gate (Phase 2F) extended to review articles + fixable/unfixable tier-domination** (`skills/peer-review/SKILL.md`). Phase 2F (previously "AI/Method Papers" only) now also fires for **Review / narrative / primer** articles and adds three rules: (1) **fixable vs unfixable tier-domination** — when repairable defects (extraction errors, missing supplementary, mislabeled table) coexist with unrepairable ones (poolability of incommensurable studies, broken construct, invalid evaluation instrument), the unfixable class governs the recommendation; (2) **review/narrative escalation** — for a review article the distinct contribution (novelty/synthesis/domain-specificity) *is* the product, so weak-novelty/no-distinct-contribution is **unfixable-in-current-form** ("add a contribution" = a different paper) and escalates one tier toward Reject rather than defaulting to the revision/Reconsider tier; (3) **confidential-note Reject-grade self-grep** — deferring the value/priority judgment to the editorial board is itself a Reject-grade tell, not a neutral hand-off. QC items 11/12 and the final checklist updated. Sourced from a review-article (LLM-hallucination primer) decision self-audit in which the reviewer recommended a Reconsider tier and the editor rejected — the 6th lenient-calibration recurrence; diagnosis remains calibration discipline, not a new type-probe.
- **Narrative-review RV4/RV5 sub-probes** (`skills/peer-review/references/domain-probes/narrative_review.md`, vendored byte-identical into `/self-review`). **RV4** gains a **model-class conflation** check for LLM/VLM-in-radiology reviews (text-only LLM language-support vs multimodal VLM image-interpretation vs conventional CAD treated as one risk profile; the actionable radiology contribution is usually a task-risk stratification, not a generic "LLMs hallucinate" statement). **RV5** gains a **source/cause vs masking/amplifying-factor** check (e.g., black-box opacity and automation bias listed as "sources" of hallucination when they hide or amplify rather than generate it — a sharper defect than "scattered taxonomy"). Both are in-niche conceptual catches missed in the source review but caught by other reviewers; bundled into existing RV4/RV5 (no new RV, no probe-count change).
- **Narrative-review probe expanded RV1–RV8 → RV1–RV9** (`skills/peer-review/references/domain-probes/narrative_review.md`, vendored byte-identical into `/self-review`). Adds **RV9 — Bibliometric circularity of a curated base**: a non-systematic review asserting a field-level/bibliometric asymmetry ("the field invested in X, neglected Y") is making a *measured* claim from an *unmeasured*, author-curated base; a hostile reviewer manufactures the reverse thesis by re-curating. RV9 names the two acceptable resolutions as a strategy fork — down-scope every claim site to "within the surveyed literature" (zero field-level residue) **or** add a documented search + per-axis counts — plus the engineering-density-vs-clinical-validation reframe. **RV6** gains the single-anchor-overload check (Abstract "landmark" ↔ body "base is thin" register mismatch); **RV8** gains the self-citation-architecture disclosure check (weakest axes coinciding with the authors' own forthcoming work). The `/self-review` narrative panel reviewer-set gains an **R4 Adversarial reject-hunter** seat (structural: RV9/RV6/RV8), with a matching focus checklist in `panel_review_template.md`. No skills/detector count change. Probe-count pointers across peer-review / self-review / review-paper SKILLs and the AJR reviewer profile updated to RV1–RV9.

## [4.1.0] - 2026-06-11

Theme: **distribution + a submission pre-flight gate.** Ships the borrow-distribution levers (Claude Code plugin marketplace, the named MedSci-Audit detector registry, and standalone hero-skill mirror tooling with two live mirror repos) and a single submission pre-flight halt-on-failure gate that bundles the existing detectors + `/verify-refs`. Analysis-integrity detectors **24 → 25** (still 43 skills). Frozen `demo/` and `evaluation/runs/canonical` artifacts (pinned to the published methods paper) are unchanged.

### Added

- **Claude Code plugin marketplace (`.claude-plugin/marketplace.json`)** — one-line install via `/plugin marketplace add Aperivue/medsci-skills`, then `/plugin` discovery of eight `medsci-*` category plugins (`medsci-literature`, `-data`, `-analysis`, `-writing`, `-review`, `-submission`, `-project`, `-presentation`) mirroring the storefront categories. Generated from `metadata/skills_catalog.json` by `scripts/gen_marketplace_json.py` (a pure downstream transform — the SSOT chain stays single-source) and CI-gated with `--check` plus `tests/test_marketplace_json.sh` (validated by `claude plugin validate`). The marketplace tracks `main`: no `version` is emitted, so each plugin's version is its git commit SHA. No skills change (still 43).
- **MedSci-Audit detector registry (`metadata/detectors_catalog.json` + `MEDSCI_AUDIT.md`)** — names and enumerates the 24 deterministic analysis-integrity detectors (previously only *counted* in `catalog_counts.json`) as a citable suite grouped into six audit families. Generated by `scripts/gen_detectors_catalog_json.py` using the same `skills/*/scripts/` glob as `validate_catalog_consistency.py`, so `detector_count` always equals `catalog_counts.json::integrity_detectors` (24); CI-gated with `--check` + `tests/test_detectors_catalog_json.sh`. `MEDSCI_AUDIT.md` documents the suite, the anti-hallucination vs mechanical-fix split, and keeps the current catalog (24) distinct from the v3.8-era canonical evaluation evidence (E1: 19 specs / 17 injectors; E7: n=21). No skills change (still 43).
- **Hero-skill standalone mirrors (`metadata/hero_skills.json` + `scripts/sync_hero_skill.py`)** — distribution lever: mirror a focused single skill out to its own repo as a star funnel that backlinks to the full suite. `sync_hero_skill.py` builds a complete standalone tree (skill copied verbatim + generated README/LICENSE/CITATION.cff/`.claude-plugin/marketplace.json`/installer/minimal CI; author metadata read at runtime from the canonical `CITATION.cff`) and force-pushes it; `.github/workflows/mirror-hero-skills.yml` auto-syncs on `main` changes (no-ops without the `HERO_SKILL_TOKEN` secret). First hero: **`verify-refs`** → [`Aperivue/verify-refs`](https://github.com/Aperivue/verify-refs). The canonical `verify-refs` SKILL.md companion note was made tool-agnostic so it mirrors verbatim. CI-gated with `tests/test_sync_hero_skill.sh`. No skills change (still 43).
- **Second hero skill: `check-reporting`** → [`Aperivue/check-reporting`](https://github.com/Aperivue/check-reporting) — audit a manuscript against 32 EQUATOR reporting guidelines. Added as one `hero_skills.json` entry (no new tooling). The skill's `references/LICENSES.md` third-party carve-out (CC BY-NC for CARE / MI-CLEAR-LLM, RSNA for CLAIM) is carried into the standalone `LICENSE` by the sync script. `tests/test_sync_hero_skill.sh` now builds and verifies every hero skill (28 checks). No skills change (still 43).
- **Placeholder/marker detector (`skills/write-paper/scripts/check_placeholders.py`)** — promotes the previously grep-in-prose pre-submission marker check (write-paper Phase 0/7, self-review Phase 2.5c) to a deterministic, CI-tested gate. Flags unresolved `[@NEW:topic]` citation placeholders, AI-disclosure `[version]/[date]/[tool]/[model]/[channel]` tokens, `TODO`/`FIXME`/`TBD`/`XXX` markers, and template/empty URLs (`example.com`, `doi.org/XXXX`, empty `]( )`, `[URL]`) as **blockers**; bare `[N]`/`[N–N]` numeric citations as **warn** (legitimate in Vancouver style — escalated with `--strict`). Guards skip fenced code blocks and the References section. Stdlib-only; exit 1 on any blocker. Registered in the MedSci-Audit catalog under *citation & reference integrity*, bringing the analysis-integrity detector count **24 → 25**; CI-gated by `gen_detectors_catalog_json.py --check` + `skills/write-paper/tests/test_placeholders.sh` (A5). No skills change (still 43).
- **Submission pre-flight gate (`skills/sync-submission/scripts/preflight_gate.py`)** — the single last-step-before-freeze halt check. Orchestrates the existing detectors + `/verify-refs` into one command that writes an aggregated manifest (`qc/preflight_gate_report.json`) and **exits non-zero on any blocker** so a build/CI wrapper halts the freeze. Composes the per-check scripts via subprocess (reimplements none); the halt decision is driven by each sub-check's normalized exit code, not by parsing its JSON. By default it halts only on the unambiguous deterministic errors (**P0**: leftover placeholders, undefined `[@key]` citations, duplicate references, canonical-vs-submission hash drift); the heuristic/conditional checks (`check_xref`, `detect_copy_divergence`, `scope_drift_check`, `cover_letter_drift_check`, `cross_document_n_check`, `check_cross_artifact_stale`) run and report as **P1 warn** unless promoted with `--strict`/`--require`, and `check_asset_anonymization` under `--double-blind`. Absent inputs are `skipped`, never blockers (tolerant of projects with no docx/cover letter/copies). Normalizes the inverted `cover_letter_drift_check.py` exit code. The offline references pass is the deterministic subset (duplicates + pagination placeholders); an online `/verify-refs --strict` remains the authoritative fabrication/author check. CI-gated by `skills/sync-submission/tests/test_preflight_gate.sh` (A6). Not a detector (no catalog change); no skills change (still 43).

## [4.0.0] - 2026-06-10

Theme: extend the project's own deterministic, no-drift SSOT discipline to the public storefront, finish the detector backlog, and roll up the English-canonical i18n migration. Analysis-integrity detectors **21 → 24** (still 43 skills). Frozen `demo/` and `evaluation/runs/canonical` artifacts (pinned to the published methods paper) are unchanged.

### Added

- **Storefront catalog SSOT (`metadata/skills_catalog.json`)** — a generated, machine-readable catalog (slug + research-lifecycle category + one-line description for all 43 skills, derived from each `SKILL.md` + `skill.yml` `owner_domain`) via `scripts/gen_skills_catalog_json.py`, CI-gated with `--check`. The aperivue.com storefront vendors this file behind an offline sync gate so the public site can never silently drift behind the repo (it had shown 40 skills while the repo shipped 43).
- **Asset/figure anonymization gate** — `skills/sync-submission/scripts/check_asset_anonymization.py` scans figure-generating scripts, figure-PDF rendered text, and docx/PDF metadata authors (`dc:creator`, `/Author`) for the institution/author leaks a body-text scan misses. Generic English+Korean institution patterns + a local-only `--names-file`; degrades gracefully when poppler is absent.
- **Cross-artifact staleness gate** — `check_cross_artifact_stale.py` flags supplement values that disagree with the corrected body (reconciliation-prone labels) and reporting checklists built against an older manuscript version. `/check-reporting` now emits a `target_manuscript` / `target_version` / `source_sha256` contract (report `check_reporting_version` 1.1) verified by `check_checklist_version.py`.
- **Survival reporting hardening** — `/analyze-stats`'s survival template now reports median survival with its 95% CI, a Cox events-per-variable gate, and cluster-robust (cluster-sandwich) SE for nested observation units (`--cluster`); the cluster-robust rule extends to logistic/linear regression.
- **Language Policy + locale-inventory gate** — MedSci Skills is now explicitly English-canonical: skill mechanics and prose are English, and non-English (currently Korean) text is allowed only as a labeled locale feature, a locale-jurisdiction mode (e.g. `grant-builder`'s Korean Government Grant Mode), a bilingual `triggers:` alias, or an opt-in `*_ko` variant. A new [`docs/locale_inventory.md`](docs/locale_inventory.md) lists every Korean-bearing file under `skills/` with a one-line justification, and a new stdlib detector `scripts/check_locale_inventory.py` (wired into CI + `tests/test_locale_inventory.sh`) fails if any Korean-bearing file is missing from that inventory — the authoritative allowlist, complementing the WARN-only Korean-prose check in `validate_skills.sh`. CONTRIBUTING gains a Language Policy section + PR-checklist item. This is the policy/scaffold step (PR1); incidental-prose translation (PR2) and English-default-with-Korean-opt-in redesign (PR3) follow. Catalog unchanged at 43 skills.

### Changed

- **English-canonical translation of incidental skill prose (PR2)** — translated leftover Korean *prose* to English across 12 files with zero functional loss: `humanize/references/ai_patterns.md` (Patterns 19–21), the four `meta-analysis/references/*.md` (data-integrity / release-ops / review-orchestration / package-drift), `meta-analysis/SKILL.md`, `ma-scout/SKILL.md` (internal tables), `author-strategy/SKILL.md` (example query), `define-variables/{references/common_definitions.md, templates/variable_operationalization.md}`, `check-reporting/references/step4d_prisma_figure_audit.md`, `write-paper/references/section_guides/step7_1_classical_qc.md`, `orchestrate/references/dialogue_nodes.md`, and `peer-review/references/reviewer_profiles/RYAI.md`. Functional/locale Korean is preserved and inventory-tracked (KNHANES labels, Korean PHI pack, Korean-form-matching demo in `fill-protocol/references/best_practices.md`, bilingual triggers). The `validate_skills.sh` Korean-prose check now passes for every skill except one inventory-justified locale example. No behavior change; catalog unchanged at 43 skills. (PR3 = English-default + Korean-opt-in redesign follows.)
- **English-default skills with opt-in Korean (PR3)** — the skills that previously *defaulted* to Korean output/interaction now default to English, with Korean preserved as an opt-in `*_ko` variant or via a "communicate in the user's preferred language" instruction. User-facing prompts are English by default (`write-paper` Discussion-planning Q1–Q5 + review prompt, `analyze-stats` / `make-figures` / `orchestrate` PHI prompts, `fill-icmje-coi` co-author email). `present-paper` speaker-notes default to the user's language (Korean register still supported; pronunciation dict + legacy Korean slide-marker parser kept). `lit-sync` defaults to English vault folders (`Literature/`, `Concepts/`) and English note headings but **honors an existing Korean vault layout** (never renames a user's folders); the Korean layout + templates move to `references/locale/ko/note_templates.md`. `render-pdf-doc` body/skill.yml are English and each `templates/*.md` starter gains a `*_ko.md` Korean sibling; `orchestrate/references/report_template.md` and `ma-scout/references/project_readme_template.md` become English defaults with `*_ko.md` variants. The locale inventory is reconciled (50 Korean-bearing files, all justified; `check_locale_inventory.py --strict` clean). No catalog change (43 skills); the 7 new `*_ko`/locale files are opt-in variants, not new skills.
- **Locale labels + finalize (PR4)** — added explicit "Locale: Korean" header notes to the whole-file Korean locale references (`render-pdf-doc/references/{pandoc_korean_cheatsheet,known_pitfalls}.md`, `deidentify/references/korean_phi_patterns.md`) so an internal reader sees the intent immediately, and marked `docs/locale_inventory.md` as migration-complete (steady state). The English-canonical migration is now complete: every remaining Korean string is a justified locale feature, a Korean-jurisdiction mode (`grant-builder`'s Korean Government Grant Mode), a bilingual trigger, or an opt-in `*_ko` variant. Validator #9 stays WARN-only by design; `check_locale_inventory.py` is the authoritative allowlist gate.

## [3.8.0] - 2026-06-07

An `evaluation/` harness suite that validates the instrument itself, plus a reconcile of the README Live-Demos numbers with the v3.7.0 clean-room demo artifacts. Catalog unchanged at 43 skills, 21 detectors — this release adds tooling and tracked evidence, not skills.

### Added

- **Evaluation harness suite (`evaluation/`)** — stdlib-only harnesses that validate the tool (not manuscript quality): **E1** seeded-defect detector benchmark (one defect injected per temp copy, recall + clean false-positive rate; offline-deterministic with a `--check` reproducibility-hash gate; network-required citation defects marked NOT_RUN unless `--online`), **E4** fresh-clone manifest reproducibility (`--ref` RC-SHA pre-tag / `v3.8.0` tag post-tag), **E5** claim audit-trail completeness (deterministic provenance pre-fill: manuscript → analysis table → manifest → QC), **E6** host-portability smoke (installer `--self-test` + path-contract scan + host-target mapping), **E7** detector coverage inventory, **E8** catalog claim-drift resistance (temp-copy only), and **E3** cost/time. Each run writes a self-describing log package (`run_manifest.json` with per-component determinism class + input/output hashes, `commands.sh`, `environment.txt`, `git_commit.txt`, `metrics.csv`, `limitations.md`). A committed canonical run lives under `evaluation/runs/canonical/`. The LLM comparator (**E2**) and a self-review convergence harness (**E9**) ship runnable with MI-CLEAR-LLM-inspired logging but are NOT executed in this release (graceful NOT_RUN without an API key / runner). All harnesses operate on temp copies and never mutate the real `demo/` tree or repo.

### Changed

- **README Live-Demos reconcile** — demo numbers re-derived from the v3.7.0 QC artifacts (STARD 60.9% (14/23), PRISMA 57.1% (24/42), STROBE 83.3% (25/30); Demo 3 analytic N 5,010; Demo 3 adjusted OR 3.03 (2.29–4.02); self-review verdicts from `qc/self_review.md`); figure links relinked to actual paths (`forest.png`, `forest_or.png`, `figures/stard_flow.svg`); unproduced slide/cover-letter/bubble-plot entries removed. Provenance for every number is logged in `evaluation/_readme_reconcile_sources.md`.

## [3.7.0] - 2026-06-07

Three new deterministic, stdlib-only detectors extend the v3.6.0 panel-derived gates — reference *adequacy*, panel lens-diversity, and generated-code quality — bringing the analysis-integrity detector count in `skills/` to 21. A publish-time skill-worthiness gate and public adoption/impact tracking round out the release. Catalog unchanged at 43 skills; every addition is a check, probe, or convention inside an existing skill.

### Added

- **Reference adequacy gates (`/self-review` Phase 2.5c-2, `/write-paper` Step 7.3c, `/search-lit`)** — a new stdlib detector `scripts/check_reference_adequacy.py` adds a reference *adequacy* layer (enough refs, the right sections, every named method cited), complementing the existing reference *integrity* gate (`/verify-refs`). The dominant failure mode in an autonomous draft is a Statistical Analysis subsection that names a competing-risk model, multiple imputation, the E-value, and an eGFR equation with zero citations — internally consistent prose no integrity check flags. The checker carries an article-type alias map + count targets, a two-tier named-method registry (STATISTICAL → Major / GUIDELINE → Minor), and paragraph-level citation clustering; `/self-review` Phase 2.5c-2 folds findings into `issues[]` (category F). `/write-paper` Step 7.3c invokes the same checker via the `${MEDSCI_SKILLS_ROOT}` cross-skill pattern and loops `/search-lit → /lit-sync → /verify-refs`; `/search-lit` gains a "Manuscript Paper Reference Pool" mode (25–40 candidates across six categories, appended to `references/library.bib` only). Every finding is `fixable_by_ai:false` (diagnose only). PII-free fixtures + regression test (#88).
- **Adoption & impact tracking** — a public [`IMPACT.md`](IMPACT.md) dashboard, an automated weekly metrics snapshot (`.github/workflows/metrics.yml` → `metrics/traffic_log.csv`, capturing stars/forks/release-downloads/14-day traffic/Zenodo stats that GitHub otherwise discards after 14 days), a [`docs/citations.md`](docs/citations.md) ledger for academic citations and named downstream use, and a "Used in research" issue template (`.github/ISSUE_TEMPLATE/used-in-research.yml`) for collecting user reports. No skill behavior changes; catalog unchanged at 43 skills.
- **Skill-worthiness gate (`/publish-skill` Phase 0.5)** — before the PII scrub, a three-way gate (Uniqueness: not reconstructable by a 5-minute web search; Specificity: encodes a domain/workflow heuristic, not a generic snippet; Effort: took real debugging, design, or reviewer-anticipation effort) decides whether a workflow merits distribution as a skill at all. A failing workflow is routed to documentation or a memory note rather than diluting the catalog — the publish-time analogue of the "reusable pattern vs one-off hack" distinction. Prose-only.
- **Panel lens-diversity gate (`/self-review` Phase 2.6, `--panel`)** — a new stdlib detector `scripts/check_panel_diversity.py` post-processes the panel's reviewer outputs so its cost buys breadth, not a louder echo of one theme: `UNCOVERED_AXIS` (an axis the research type is expected to probe drew zero major findings — re-probe before finalizing), `FAMILY_MONOCULTURE` (the majors concentrate in one concern family), and `LENS_COLLAPSE` (a fully-redundant reviewer adding no independent axis). Healthy CONSENSUS is preserved — the checks fire on panel-level coverage and full redundancy, never on agreement. A new Step 3.5 wires it into the editor synthesis, and `panel_review_template.md` documents the expected-axis manifest. PII-free fixtures + regression test.
- **Generated-code quality gate (`/analyze-stats` Phase 3.5; pointers in `/batch-cohort` rule 10 and `/make-figures`)** — a new stdlib detector `scripts/check_generated_code.py` lints emitted `.py`/`.R` analysis scripts for the reproducibility/integrity slop AI-generated code recurrently carries: `MISSING_SEED`, `HARDCODED_DATA_LITERAL` (hand-typed tabular data instead of read_csv + subset — the data-integrity rule), `HARDCODED_ABS_PATH`, and `INPLACE_SOURCE_OVERWRITE` (writing to the source path) as Major, plus `DEBUG_LEFTOVER` and `UNUSED_IMPORT` flags. Conservative on the Major checks (Python uses AST for unused-import detection). Dogfooding it over the shipped analysis templates surfaced and removed ten genuinely dead imports. PII-free fixtures + regression test. Catalog unchanged at 43 skills.

## [3.6.0] - 2026-06-06

A 13-project panel self-review distilled 158 cross-project traces into 12 recurring defect patterns; this release lands the 18 resulting gates (P1/P2/P3) as deterministic, stdlib-only checks wherever a grep is clean, and as prose/probe guidance where the call needs a human. Six new detectors join the existing trio, each with PII-free synthetic fixtures and a regression test. Catalog unchanged at 43 skills — every addition is a check, probe, or convention inside an existing skill.

### Added

- **Cohort arithmetic gate (`/self-review` Phase 2.5 / 2.5b)** — a new stdlib detector `scripts/check_cohort_arithmetic.py` recomputes the numbers a reviewer checks by hand: `RATE_BACKCALC` (an incidence rate must invert to its own events ÷ person-years), `CASCADE_SUM` (a STROBE exclusion cascade must balance — start − Σexclusions == final; total − missing == complete), and `PARTITION_OVERLAP` (an ordinal tier/stratum split claimed disjoint must satisfy Σn == unique total and Σevents == total events; all-equal-n is a stratum-total mis-entry). Parses prose equations + GFM tables, recomputes from a committed CSV when given one. Phase 2.5b's screening-count reconciliation is extended from SR/MA to observational tier/stratum partitions.
- **Methods ↔ Results ↔ disk artifact coverage (`/self-review` Phase 2.5f, `/write-paper` Step 7.3b)** — a new detector `scripts/check_artifact_coverage.py` reconciles both directions: `PROMISED_ABSENT` (an analysis named in Methods that never reaches Results) and `DISK_UNREPORTED` (an analysis output on disk — an added-value DeLong CSV, a calibration table — never mentioned in the body, the run-but-unreported result that may undercut the headline). The reverse direction is calibrated against false positives via an `_analysis_outputs.md` manifest (source of truth when present) and analysis-bearing file-stem escalation otherwise.
- **Endpoint ↔ conclusion scope gate (`/self-review` §D, `/design-study`, `/write-paper`)** — a new detector `scripts/check_scope_coherence.py` flags `CROSS_SECTIONAL_PROGNOSTIC` (a cross-sectional/single-visit design with a prognostic or surveillance conclusion) and `SURROGATE_CARE_DIRECTIVE` (a binary surrogate endpoint driving a defer/withhold/initiate-therapy directive). Fires only when a design/endpoint signal and a conclusion-region action verb co-occur.
- **Reporting-framework naming audit (`/check-reporting` Step 4e)** — a new detector `scripts/check_framework_naming.py` flags `BASE_MISSING` (an AI extension — PROBAST+AI, STARD-AI, TRIPOD+AI, PRISMA-DTA — invoked without naming/citing its base instrument), plus `HYPHEN_MIX`, `CITE_MISSING`, `SELF_COINED_LABEL`, and `VAGUE_GUIDANCE` ("adapted per recent guidance"). `/write-paper` Step 7.1 adds an AI-disclosure meta-applicability gate (a disclosure paragraph must itself carry version + access channel + date range + responsible party, with zero placeholders).
- **Classical-style body lint (`/self-review` §J, `/write-paper` Step 7.1)** — a new detector `scripts/check_classical_style.py` flags `SECTION_SYMBOL` (any § in the body) and `INBODY_AI_DISCLOSURE` (an AI-disclosure paragraph that belongs on the title page) as Major, and `ELIGIBILITY_PROSE`, `DECIMAL_INCONSISTENCY` (mixed OR/HR decimal places), `EM_DASH_OVERUSE` as Minor — the machine-checkable subset of the classical-QC checklist.
- **Reviewer-team 3-way (`/self-review` §K)** — `scripts/check_reviewer_team_consistency.py` extends beyond the dual-claim/single-confession conjunction to the prose ↔ JSON ↔ confession 3-way: an LLM named in an extraction JSON's reviewer field (`--extraction-json`) is fatal (a tool is not a reviewer), and a future-tense deferred mitigation ("will be completed before submission") is a Major. The existing contract is preserved.
- **Estimand & CI output contract (`/analyze-stats`)** — quantile estimands (T25, median time-to-event), pooled proportions, and subdistribution HRs must emit a 95% CI, not a bare point estimate; a Cox events-per-variable ≥ 10 gate (Firth/penalized fallback); single-arm proportion meta-analysis bans Egger's (Peters'/arcsine, k ≥ 10) and standardizes τ² + a 95% prediction interval; naive Wilson CIs on study-nested proportions are flagged; Fine-Gray requires a subdistribution-PH check. Interaction/synergy questions must anchor the estimand to the interaction parameter, and equivalence claims must declare a margin (TOST/MCID).
- **Stratified & survival reporting (`/analyze-stats`)** — a strata-disjointness gate before any Cochran-Armitage trend test; a secondary stratum-HR checklist (referent + per-stratum events + sparse caveat); a proportion-CI lower-bound clamp to max(0, ·); an interval-censoring auto-trigger for visit-dated events; a PH-violation rule (piecewise/time-stratified HR, never a single time-averaged HR); and a number-at-risk requirement when a KM/CIF is quoted past median follow-up.
- **Meta-analysis pool & method guards (`/meta-analysis`)** — the FINAL_POOL_LOCK now also locks patient/lesion aggregate totals (arm-separable vs both-arm), a "fixed"/"resolved" audit note requires re-run evidence, the k=1-subgroup lesson extends to k < 4, a PROSPERO ID format gate (`^CRD42\d{9}$`, 14 chars) lands in both `/meta-analysis` Phase 1 and `/check-reporting` Step 4c, plus new lessons on outcome harmonization (do not pool different outcome definitions into one range) and heterogeneous-RoB κ (per-instrument agreement, never one pooled κ), and a flag → form-edit forced transition in Phase 4c.
- **Leakage, time-origin & construct concordance (`/design-study`, survival probe)** — Phase 2 gains a time-origin & survivorship subsection (immortal time, left-truncation, mediator-ascertainment-window survivorship, complete-case primary-set selection) and the survival domain-probe S1 escalates a "not formally assessed" self-confession to Major; Phase 2C adds construct ↔ nominal-definition match, per-flag reference-standard concordance, and a manuscript-definition ↔ `variable_operationalization.md` cross-check.
- **Reference placeholder gate (`/verify-refs` Gate 6, `/self-review` Phase 2.5c, `/write-paper` Phase 0)** — `verify_refs.py` flags pagination/publication-stage placeholders (`e000–e000`, `in press`, `TBD`, `forthcoming`) as `UNVERIFIED + note="pagination_placeholder"` while staying manuscript-agnostic; the centrality call (a method/headline-load-bearing cite → P0) is made by `/self-review` Phase 2.5c, and `/write-paper` Phase 0 blocks bare `[N]`/`[N–N]` citation placeholders alongside `[@NEW:]`.

## [3.5.0] - 2026-06-06

Analysis-integrity guards across the manuscript pipeline — backporting the findings a multi-agent panel review caught into deterministic, stdlib-only single-pass checks, and pushing them upstream into the source, writing, figure, and submission stages. Catalog unchanged at 43 skills; the new probes are checks and reference files inside existing skills.

### Added

- **`/self-review` category C — power-aware null interpretation**: a new check that scores non-significant primary results (p > 0.05, 95% CI crossing the null) for whether the analysis is powered to *exclude* a clinically meaningful effect. An underpowered null is flagged as "not yet established" rather than "no effect," and the check watches for bilateral over-correction (a prior overclaim swinging to an equally unsupported negative claim during revision). Undocumented null = Minor; a null driving a clinical recommendation without power/CI-compatibility justification = Major. Backports a panel-only finding into the single-pass review (prose check, no new dependency).
- **`/self-review` Phase 2.5e — confounding completeness (observational)** + a new **`observational_confounding.md` domain-probe module (O1–O6)**: a deterministic gate (`scripts/check_confounding_completeness.py`, stdlib-only) joins the exposure-stratified Table 1 against the Methods adjustment set and flags every covariate that is measured, imbalanced by exposure (p < 0.05 or SMD > 0.1), yet absent from the adjustment set as an `UNADJUSTED_IMBALANCED` Major candidate, with an extended-adjustment sensitivity fix. The O1–O6 probe module (confounding completeness, adjustment-set provenance, selection/collider bias, exposure measurement validity, missing-data / complete-case collapse, residual-confounding E-value) closes the gap where observational studies had no domain-probe set; it is vendored byte-identical into `/peer-review` (canonical, new Phase 2E) and `/self-review`, and added to the `check_domain_probe_sync.py` drift gate (now 5 modules). `/design-study` gains a matching DAG-first adjustment-set planning note. Backports the panel's highest-yield observational finding into the single-pass review.
- **Structural-zero / dose-duration covariate guards (`/analyze-stats`, `/clean-data`, `/define-variables`)**: a coupled source-side defense against the most common observational miscoding — a dose/duration variable anchored to a categorical exposure (pack-years under smoking status, grams/week under alcohol use). `/clean-data` gains a Stage-2 flag for *categorical-implied zeros* (a `never` record with a NULL dose is a contradiction, not missing data) plus a stdlib detector `scripts/check_structural_zero.py`; `/analyze-stats` gains a "Covariate Pitfalls" section warning against imputing structural zeros (MICE fabricates a non-zero dose for the unexposed) and against complete-case collapse (the unexposed stratum is silently dropped, shrinking n 40–60%), recommending adjustment on the categorical status with the continuous dose reserved for an exposed-only secondary analysis; `/define-variables` gains a matching failure mode requiring `IF status == 'never' THEN dose = 0` to be operationalized explicitly. Synthetic PII-free fixtures + regression test included.
- **`/self-review` Phase 2.5f — claim-vs-artifact cross-check** + survival probe **S8 (estimand provenance)**: a deterministic gate (`scripts/check_claim_artifact.py`, stdlib-only) checks claims against the artifacts they should trace to — it flags `PRIMARY_REASSIGNED` / `ESTIMAND_DRIFT` when the manuscript's primary contrast was re-designated after results were known or does not match the pre-registration, and `EVALUE_ARITHMETIC` / `EVALUE_NON_PRIMARY` when a reported E-value does not recompute from its primary estimate or is borrowed from a secondary one. A primary-change guard accompanies it. The survival/prognostic domain-probe module gains **S8 (estimand provenance)** and an **S2** note on structural-zero covariates collapsing the complete-case Cox sample (both vendored byte-identical into `/peer-review` canonical Phase 2B and `/self-review`; module now S1–S8). Figure/flow-count, Methods-promised-analysis, and imputation-input subchecks are reserved in the JSON schema for follow-up. Backports the panel's estimand-provenance findings into the single-pass review.
- **`/write-paper` Step 7.3b — estimand provenance & promised-analysis audit** + Abstract estimand-shopping guardrail: a new Phase-7 step delegates the claim-vs-artifact cross-check to `/self-review` Phase 2.5f (P0 blocker → Audit Recovery on `PRIMARY_REASSIGNED` / `ESTIMAND_DRIFT` / `EVALUE_ARITHMETIC`) and adds an inline Methods→Results promised-analysis grep (a promised-but-absent analysis HALTs the pipeline). Phase 6 (Abstract) gains a guardrail to lead with the *pre-specified primary estimand* rather than the largest effect — tightening effect-size language is fine, but promoting a secondary/exploratory/post-hoc estimate to the headline is estimand shopping. Prevents the estimand-provenance failure at write time.
- **`/make-figures` — Figure 1 caption ↔ flow-SSOT reconciliation**: a new stdlib detector `scripts/derive_figure_legend_counts.py` re-derives participant counts from the flow-diagram config (the SSOT consumed by `generate_flow_diagram.R`) and flags any `n = N` in the Figure 1 caption that is not a box count in the diagram (the classic "caption says n = 1,284 analytic, box says n = 998" defect that surfaces only at submission). Parses the config as text, so it is flow-tool-agnostic; pairs with numerical-safety's re-derive-every-revision rule. Synthetic fixtures + regression test included.
- **`/sync-submission` Phase 8 + Gate 11 — multi-copy manuscript divergence**: a new stdlib detector `scripts/detect_copy_divergence.py` compares a designated SSOT manuscript against each hand-maintained copy (circulation, portal) and reports the SSOT numeric claims (`n = N`, percentages, `p`, OR/HR/RR, 95% CI) and headings that did not propagate — the "14 edits applied to the SSOT, only 8 reached the portal copy" failure. A `STALE_COPY` is a P0 blocker; the recommended fix is to generate the variants from the single SSOT via a build step rather than hand-maintain parallel copies. Claims match as normalized strings (wording differences do not register). Synthetic fixtures + regression test included.
- **Incremental-value probe (`/design-study`, `/write-paper`)**: when a study frames a model/marker as adding value *beyond* an existing tool, `/design-study` Phase 3 now requires pre-specifying the in-routine-use baseline comparator plus an incremental metric (ΔC-index/ΔAUC with a paired CI, NRI, IDI, or decision-curve net benefit), and `/write-paper` Results requires the nested-model comparison to be reported — a standalone discrimination number does not support a "beyond X" claim, and the gap cannot be filled post hoc without the baseline model. Prose-only.

## [3.4.0] - 2026-06-06

Dual-review consolidation and a multi-agent panel mode for self-review — depth without broadening the catalog (still 43 skills).

### Added

- **`/self-review --panel`**: an opt-in multi-agent panel mode — several domain-expert reviewers run independently (blinded), then an editor consolidates their findings with CONSENSUS (≥2-reviewer) flags and R1/R2/R3 attribution, for a high-stakes pre-submission final pass. The default single-pass review stays the fast path. Portable across hosts: parallel subagents where the host provides them, with an explicit sequential blinded fallback and no `Workflow`-tool dependency. Output maps onto the existing Fatal/Fixable framing and R0 numbering, so `/revise` still consumes it; ships a PII-scrubbed `panel_review_template.md` and a structural + leak test (PR #73).
- **Shared domain-probe modules**: the SR-MA (P0–P10), survival/prognostic (S1–S7), radiomics (R1–R4), and narrative-review (RV1–RV8) critique probes are now reusable modules under `references/domain-probes/`, vendored byte-identical into both `/peer-review` (canonical) and `/self-review`. This closes the gap where `/self-review` had no survival / time-to-event probe set. A new `scripts/check_domain_probe_sync.py` drift gate (sha256 byte-identity) is wired into CI and `validate_skills.sh` (PR #72).
- **`/orchestrate`**: routes harsh / top-tier / multi-reviewer requests to `/self-review --panel`; the panel is opt-in and never auto-applied in chains or `--e2e` (PR #73).

### Changed

- **`/peer-review` Phase 2A–2D** now point to the shared domain-probe modules instead of carrying the probe bodies inline; the Major / Minor + Confidential-to-editor routing is applied at the pointer, so review behavior is unchanged. `references/reviewer_profiles/`, the Aczel tone audit, and `narrative_review_audit.md` remain peer-review-only (PR #72).

Catalog unchanged at 43 skills — the panel is a mode of an existing skill, and the probes are reference files inside existing skills.

## [3.3.0] - 2026-06-03

Packaging, portability, and trust signals — sharpening the "submission-grade clinical manuscript workflow" wedge without broadening scope.

### Added

- **Per-skill Quality Cards**: every skill now ships a `skill.yml` (42/42) with an optional, additive **v2.1 quality-card** extension — `purpose`, `safety_boundaries`, `known_limitations`, `validation_commands`, and a strict `evidence_surface` label (`ci_validator` / `demo` / `bundled_script` / `manual_workflow` / `not_yet_demonstrated`). `scripts/gen_skill_docs.py` renders the card into each `docs/skills/` page and tags the index with each skill's evidence level. Labels are grounded in repo reality, not asserted (PR #57, #58, #59).
- **`docs/skills/AUDIT.md`**: the validation story grounded in the actual CI gates and the three manifest-locked demos, with explicit trust boundaries — what is automated, what is reviewed by hand, and what is deliberately not claimed (PR #59).
- **`docs/host_compatibility.md`**: a verified host-compatibility matrix (Claude Code, Codex, Cursor, GitHub Copilot). Each VERIFIED cell carries a source URL and retrieval date; OpenClaw/Hermes are marked UNVERIFIED-roadmap. Confirms Codex reads `~/.agents/skills` and that Cursor + GitHub Copilot read the same directories as Claude Code, so the existing two install targets already cover four hosts (PR #60).
- **`docs/competitive_positioning.md`**: a neutral comparison to broad skill catalogs, with caveated, dated skill counts (PR #54).
- **`installers/install.py --self-test`**: simulates Claude/Codex/Cursor installs into temporary directories, asserts every skill is discoverable, and proves no real host directory is touched; real installs now run a post-copy discoverability check (PR #56).

### Changed

- **README positioning sharpened**: adds the canonical lines (a submission-grade clinical manuscript workflow; competes on clinical submission reliability, not skill count), removes volatile competitor skill counts from the body, and softens the citation claim to validator-backed language (reference-verification gates + citation-audit workflows) (PR #54).
- **`skill.yml` contract now required**: with all 42 skills shipping a contract, a missing `skill.yml` is a CI failure rather than a migration warning — closing the v1→v2 migration (PR #57, #58).

### Fixed

- CITATION.cff EQUATOR-guideline count corrected from 33 to 32 (matches the catalog count SSOT).

## [3.2.0] - 2026-06-01

### Added

- **`/version-dataset`** (new skill, brings the catalog to 42): dataset version control — a deterministic content-hash manifest (file SHA-256 + tabular schema + per-column value hashes), `verify` to detect drift (schema / row-count / value changes), and `diff` between versions. Each bundled `demo/*/` now carries a `manifest.lock.json` (input data + deterministic result tables) verified in CI — closing codex Improvement E (demo reproducibility).
- **`/generate-codebook`** (new skill, brings the catalog to 41): generates a citable data dictionary / codebook (`codebook.md` + `codebook.json`) from a tabular dataset, profiling variable role / type / level frequencies / range / missingness. Coded variables whose level meanings are unknown are flagged `[NEEDS DICTIONARY]` rather than guessed — the generator side of the dictionary-first workflow; feeds `/define-variables`.
- `/calc-sample-size`: observational-cohort precision-branch reference for retrospective / fixed-extract studies (PR #40).
- `/verify-refs`: **v1.3.0** full-author cross-check via PubMed `efetch` — co-author hallucinations at positions #2..#N are now caught, not just the first author; `schema_version` → 4 (PR #41).
- `/check-reporting`: fail-fast guard (`scripts/check_checklist_exists.py`) — a routed guideline with no vendored checklist now halts with `MISSING_CHECKLIST_CONTRACT_VIOLATION` instead of silently constructing items from model memory; from-memory requires explicit `--allow-from-memory` (PR #42).
- `/check-reporting`: vendored four previously-gitignored checklists — **CONSORT 2025, SPIRIT 2025, CARE 2013, CLAIM 2024** — with per-file license attribution and a "Third-party licenses" note (PR #43, #45).
- `scripts/validate_routing_assets.py`: CI gate that every `${CLAUDE_SKILL_DIR}` asset reference and check-reporting checklist bullet resolves to a real file (PR #43).
- `metadata/catalog_counts.json` + `scripts/validate_catalog_consistency.py`: single source of truth for skill / guideline / journal-profile counts, wired into CI — public-doc counts that drift from disk now fail the build. The check now also gates the README shields **badge** (`Skills-N`) and matches guideline-count claims case-insensitively, so a drifted badge or section heading fails CI (PR #50).
- **`/revise`**: R1 vs R2+ cover-letter protocol — on a second-or-later revision the editor cover letter folds into the response-letter "head" rather than a separate document; adds a "Succinctness & non-defensiveness (R2+)" voice section, a synthetic before/after gallery, and matching verification gates. `/humanize` cross-references it as a triage cue (PR #51).
- **Contributor funnel**: GitHub issue forms (skill request / bug report / docs improvement), a pull-request template, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1 by reference), and `docs/seed_issues.md` (PR #50).

### Changed

- **Reporting-guideline count corrected from 33 to 32** across README, `/orchestrate`, `/check-reporting`, and the make-figures guideline map — the enumeration and vendored checklist files were both 32; "33" was an off-by-one now backed by the count SSOT.
- **README restructured for faster onboarding** — a Quick Start (install + first command) above the demos, the three heavy demo output tables collapsed behind `<details>`, and "What's New" refreshed and moved below the demos (PR #50).
- Skill badge corrected from 40 to 42 (PR #50).

### Fixed

- **DOI badge now renders on GitHub** — the Zenodo-hosted badge SVG was served with `Cache-Control: no-cache`, which GitHub's Camo image proxy cannot cache, so it displayed as a broken image; replaced with a shields.io static DOI badge (Camo-cacheable). The DOI value and link are unchanged (PR #50).

### Hygiene

- Validator precedent blocklist no longer stores the maintainer's name, mentor names, institutions, or project codes in cleartext: `scripts/validate_skills.sh` delegates to `scripts/check_precedent.py`, which keeps generic structural shapes as regex but matches sensitive identifiers against SHA-256 digests (`scripts/precedent_hashes.txt`), with an `--allow-author` exemption for citation files (PR #44).
- Fixed `/present-paper` note-injection script path (`references/` → `scripts/`) (PR #43).

### Stats

- 42 skills (was 40); Zenodo concept DOI `10.5281/zenodo.20155321` preserved.

## [3.1.0] - 2026-05-23

### Added — v2.10 cycle integration

- `/peer-review`: Phase 2A SR-MA 8-probe extension (P1-P8) for systematic review meta-analyses (PR #22).
- `/verify-refs`: Gate 5 PMID/DOI duplicate detection; `submission_safe` / `fully_verified` synchronous propagation (PR #23).
- `/meta-analysis`: SR-MA dual-extractor workflow, cohort overlap detection, and supplementary 8-file pack (PR #24).

### Changed

- Validator scope extended to `templates/` and `scripts/` for permanent PII blocklist enforcement.
- `setup-medsci` skill now reflected in the public skill roster so filesystem, README, and external mirrors can align at 40 skills.
- `README.md` refreshed with v2.10 public-surface highlights and 40-skill badge/text sync.

### Hygiene

- Generalized legacy non-hyphenated MA project codes in `skills/meta-analysis/SKILL.md`.
- Added the non-hyphenated MA project-code family to the validator blocklist.

### Stats

- 40 skills (was 39); Zenodo concept DOI `10.5281/zenodo.20155321` preserved.

## [3.0.1] - 2026-05-13

### Added — first Zenodo-archived release with DOI

- First release archived on Zenodo. **Concept DOI**: [`10.5281/zenodo.20155321`](https://doi.org/10.5281/zenodo.20155321) (always-latest); **versioned DOI for this release**: [`10.5281/zenodo.20155322`](https://doi.org/10.5281/zenodo.20155322).
- README DOI badge populated; `CITATION.cff` `doi:` field + `identifiers:` block added.
- Bumps `version: 3.0.1` in `CITATION.cff`.

This release archives the v3.0.0 Tier 0 polish bundle (see entry below) so it becomes academically citable. No code changes vs v3.0.0 except the DOI back-fill commit.

## [3.0.0] - 2026-05-13

### Added — Tier 0 polish: CITATION.cff, Zenodo integration, setup onboarding, peer-review tone audit (2026-05-13)

- `CITATION.cff` (cff-version 1.2.0) and `.zenodo.json` for academic citation backlink. DOI populates after first Zenodo archive of a tagged release.
- `.github/workflows/release.yml` — on `v*` tag push, builds classroom ZIPs, creates GitHub Release with notes from CHANGELOG, attaches ZIPs. Zenodo integration (toggle once at `https://zenodo.org/account/settings/github/`) auto-archives the release.
- `docs/setup/` — five-doc onboarding guide for clinicians new to Python/R/Claude Code/MCP: `README.md` (decision tree), `mac.md` (Homebrew → pyenv → R → Node → Claude Code), `windows.md` (winget-based, no WSL), `mcp-setup.md` (Zotero / Google Drive / PubMed servers), `common-issues.md` (top 10 issues with copy-paste fixes).
- `skills/setup-medsci/` — diagnostic-only skill that runs `which python3 / Rscript / claude / node` and `claude mcp list`, prints a checklist with status (✅ / ⚠️ / ❌) and links to the right setup doc for any missing component. Intentionally read-only — does not install anything.
- README: added `## What This Is NOT` scope-out section (positions vs K-Dense scientific-agent-skills and OpenClaw Medical Skills) and `## Setup` section linking the new docs and `/setup-medsci`. Citation badge added.
- GitHub topics: swapped 4 generic (`ai-tools`, `academic-writing`, `open-source`, `research-tools`) for 4 specific (`agent-skills`, `tripod-ai`, `irb-protocol`, `physician-researcher`) — capped at GitHub's 20-topic limit.
- `skills/peer-review/` — Aczel 2021 anti-reviewer-2 tone patterns integrated into Phase 4 Self-QC and Tone Calibration sections (PR #11 merged 2026-05-13).

### Changed — `/publish-skill` Phase 2 `audit_skill.sh` rewritten for parity with monorepo linter (2026-05-03)

`skills/publish-skill/scripts/audit_skill.sh` was overhauled to mirror the per-skill rules in `scripts/validate_skills.sh`. Old behavior had three structural problems: (1) raster bytes inside compiled `.pyc` and PNG images falsely tripped path / email regexes (a known-clean skill reported 3 findings), (2) the institutional-reference category used `(?<!...)` lookbehinds that `grep -E` silently does not support — the entire category was inert, (3) several monorepo rules had no equivalent here, so a personal skill that passed `audit_skill.sh` could still fail when moved into the public repo.

New coverage matches the monorepo categories one-for-one:

- **rule 6 / 7 / 7b** — text-pass with `--binary-files=without-match` so PNG / DOCX / pyc byte collisions stop generating findings.
- **rule 7c** — author-style filename pattern (`<Surname>{Year}_*`) with the same generic-token allow-list as the monorepo (`Issue`, `Sample`, `Example`, etc.).
- **rule 8** — blockquote dated precedent (`> YYYY-MM-DD ...`) with allow-list for routine version stamps (`Last updated:`, `Created:`, `Updated:`, `Date:`, `Version:`, `Released:`).
- **rule 10** — binary EXIF metadata scan via `exiftool` (DOCX / PPTX / XLSX / PDF / PNG / JPG / TIFF). exiftool is a soft dependency; the script prints a one-line install hint and continues if missing, so users without the binary can still get the other nine categories.
- **email whitelist** — `example.com` / `example.org` / `example.net` / `your@email` / `noreply@` / `placeholder` / `<your-email>` / `<email>` placeholders no longer flag.
- **institutional regex** — `(?<!...)` lookbehinds replaced with `\b` word boundaries so the rule actually fires.
- **single-file EXIF mode fix** — exiftool only emits `======== <file>` headers when given two or more files; the parser now pre-primes `current_file` from `binary_files[0]` so a one-file EXIF audit attributes hits correctly.

`skills/publish-skill/SKILL.md` Phase 2 was rewritten to enumerate the ten audit categories, document the second positional argument (user-specific name / institution / collaborator alternation pattern), and explain the false-positive guard. The "Cross-validation" section was scoped down to the things the script does not yet automate (uncommon institutional acronyms, project-specific identifiers like `CK-NN` / `MA-NN`).

Regression sweep across all 39 monorepo skills: **30 clean, 9 with legitimate generalization flags** (language hardcoding to a specific natural language, location-specific examples, institution names in documentation prose). The flagged set is the cross-publication scope by design — the medsci-skills internal `validate_skills.sh` deliberately allows these because the monorepo is medical-domain-specific, while `audit_skill.sh` enforces the broader publish-time scope.

### Changed — 14 skill contracts migrated from schema_version 1 → 2 (2026-05-03)

All remaining v1 skill.yml contracts (`calc-sample-size`, `check-reporting`, `lit-sync`, `manage-refs`, `meta-analysis`, `orchestrate`, `peer-review`, `render-pdf-doc`, `revise`, `search-lit`, `self-review`, `sync-submission`, `verify-refs`, `write-paper`) gained `layer:` (A/B/C/D per `docs/skill_yml_schema_v2.md`), `when_to_use:` (3–5 trigger entries each), and `when_NOT_to_use:` (3–5 routing-guard entries each). Existing v1 fields preserved verbatim; the only schema-level change is the bump to `schema_version: 2`. Closes the 2026-07-24 v1 sunset deadline; `validate_skill_contracts.py` now reports `v1 contracts: 0  |  v2 contracts: 15`.

Layer assignments follow the schema doc (`/verify-refs` → A, `/write-paper` → C, `/orchestrate` → D, `/self-review` → D, `/revise` → B) and infer the rest from skill role: deterministic-script skills (calc-sample-size, check-reporting, lit-sync, manage-refs, render-pdf-doc, search-lit, sync-submission) on Layer A; structured-data skills (meta-analysis) on Layer B; free-form prose skills (peer-review) on Layer C.

## [2.4.0] - 2026-05-03

### Added — Binary EXIF metadata scan (validate_skills.sh rule 10)

`scripts/validate_skills.sh` now scans every shipped DOCX / PPTX / XLSX / PDF / PNG / JPG / TIFF for personal-name PII in document and image metadata. The text linter (rules 6 / 7 / 7b) cannot see fields like PDF `Author`, OOXML `dc:creator` / `cp:lastModifiedBy`, or EXIF `Artist`, so a personally-authored slide deck or annotated screenshot could ship with the author's real name in metadata while the file content read clean. Rule 10 closes that gap by piping the same `precedent_patterns` regex used for text scanning over an `exiftool -S` dump of `Author / Creator / LastModifiedBy / LastSavedBy / Copyright / Artist / Owner / OwnerName / CompanyName / Manager / HostComputer / UserComment / Subject / Title / Description / Keywords / Comment / Producer / CreatorTool / Software`. Upstream / 3rd-party document authors not in the precedent list (e.g., STARD's Patrick Bossuyt, the python-pptx maintainer) pass without an explicit allow-list. exiftool is now a hard dependency; the script exits early with an install hint if missing, and `.github/workflows/validate.yml` installs it via `apt-get` so server-side enforcement matches the local pre-commit hook.

Sanity-tested by injecting representative English- and Korean-script precedent identifiers from the blocklist into a tracked PNG's `Author` and `Artist` fields — both name forms are caught and FAIL on the next `validate_skills.sh` run, with cleanup automatically restoring the clean baseline.

### `/make-figures` v1.1.0 — design principles + flow diagram lessons (2026-05-03)

Adds a communication-first design layer to the figure pipeline and codifies five production lessons distilled from a multi-revision PRISMA Figure 1 cycle. The skill previously documented *which* figure type to use; v1.1.0 documents *what message to convey first* and *which template-fidelity / PDF-export pitfalls reliably waste a circulation round*. Skill contract bumped from schema_version 1 → 2 (sunset deadline 2026-07-24).

- **Added** — `skills/make-figures/references/design_principles.md` (~150 lines). Communication-first guide based on Brunner et al., *Nat Hum Behav* (2026) "Designing effective figures for scientific communication" (DOI: 10.1038/s41562-026-02466-9). Five strategies in reading order: (1) identify the one-sentence key message, (2) match the reading-time budget to the deployment context, (3) match graph type to data structure with intentional color use, (4) keep ≤7 visual elements / ≤3 colors per panel, (5) ask whether a figure is genuinely needed. Includes a figure-vs-table decision table, an audience-context matrix (specialist / generalist / mixed), a cognitive-load Step-4 checklist, and an anti-pattern list (default-palette syndrome, legend-dependence, decorative 3-D, chart-of-three-values, caption-as-Methods, mismatched detail).

- **Added** — `skills/make-figures/references/flow_diagram_lessons.md` (~150 lines). Five generalized lessons from a meta-analysis Figure 1 cycle (PII-scrubbed): (1) custom Graphviz prototypes are fine but switch to the official template before circulation, (2) headless LibreOffice corrupts PRISMA 2020 docx → PDF because of VML fallback drift; use macOS AppleScript / Windows COM driving native Word, (3) raw `str.replace` on `word/document.xml` breaks on `&`, `<`, `>` — always entity-escape via `xml.sax.saxutils.escape()` before substitution, (4) the PRISMA 2020 docx duplicates each numeric box as `<w:t>` pairs in non-rendering order; build a sequential placeholder map and validate with a `999`-sentinel render, (5) freeze figures alongside the manuscript v_N — never edit `figures/v3/*.pdf` after circulation, branch to `v4/` instead. Closes with a 4-row stage-vs-tool table that maps draft / QC / circulation / submission to the right approach.

- **Added** — `skills/make-figures/references/reporting_guideline_figure_map.md` (~140 lines). Bridges this skill to `/check-reporting` (33 reporting guidelines) by mapping 17 study designs and AI-extension guidelines to their mandatory figures and current support status: ✅ official template + R generator (PRISMA 2020, CONSORT 2025, STARD 2015, SPIRIT 2025, TRIPOD calibration), ⚠️ generic flow generator only (PRISMA-DTA, STROBE, CARE), ❌ no template — manual production via D2/Graphviz (CONSORT-AI 2020 PMID 32908283, STARD-AI 2025 PMID 40954311, TRIPOD+AI 2024 PMID 38636956, CLAIM 2024 PMID 38809149, DECIDE-AI 2022 PMID 35585198, PRISMA-NMA, PRISMA-P, CHEERS 2022, SQUIRE 2.0). Includes a "AI-specific figures most often missing" priority list (dataset-flow, calibration, fairness/subgroup panel, decision-curve analysis, architecture, saliency overlay) ranked by reviewer-checklist frequency.

- **Added** — `skills/make-figures/references/pipeline_concepts_medical_ai.md` (~200 lines). Four canonical diagram types not covered by reporting-guideline flows: (1) DICOM workflow (scanner → PACS → de-id → research store → splits), (2) annotation pipeline (annotator pool, consensus rule, inter-rater agreement), (3) federated learning topology (per-site cohorts, what flows between sites, aggregation algorithm), (4) model architecture (input shape, backbone, head, parameter count, trainable layers). Each section gives canonical layout, required annotations, common pitfalls, and preferred tool (D2 / drawio / NN-SVG / PlotNeuralNet). Closes with a 6-row "use this section if your figure shows…" selector.

- **Added** — `skills/make-figures/references/design_principles.md` companion citations: Rougier et al., *PLoS Comput Biol* 2014 (PMID 25210732) "Ten simple rules for better figures" — foundational general-purpose checklist; Crameri F., *Curr Protoc* 2024 (DOI 10.1002/cpz1.1126) "Choosing the right colors" — definitive 2024 reference for perceptually-uniform colorblind-safe palettes (`viridis` / `cividis` / `batlow`) and redundant encoding. Updated the Color section to recommend `vik` for diverging diagnostic data and to make redundant encoding explicit when color carries diagnostic meaning.

- **Changed** — `skills/make-figures/references/critic_rubrics/flow_diagram.md`. Appended Section G "Communication-first checks" with five new rubric items (22–26): cognitive load (≤7 boxes per column, ≤3 shapes, ≤3 colors), key-message visibility (analytic cohort visually emphasized within 2 seconds), official-template fidelity (PRISMA 2020 / CONSORT 2010 / STARD 2015 / STROBE), exclusion-box geometry (rectangles with `\l` left-aligned bullets, not `shape: note`), and frozen-version sync with the manuscript v_N path.

- **Changed** — `skills/make-figures/references/critic_rubrics/data_plot.md`. Appended Section G "Medical AI / prediction-model checks" with five new rubric items (21–25): calibration plot accompanies discrimination (TRIPOD+AI), subgroup/fairness panel for deployment claims (CLAIM 2024 §C, TRIPOD+AI), colorblind-safe + redundant encoding stronger than the existing D.13 (Crameri 2024), dataset-flow visible (STARD-AI / CLAIM 2024 / TRIPOD+AI), decision-curve analysis when the paper claims clinical utility (Vickers & Elkin, *Med Decis Making* 2006).

- **Changed** — `skills/make-figures/SKILL.md` Step 1 "Specify" now opens with a three-tier reading directive: (1) `design_principles.md` for every figure (key message + reading-time budget), (2) `reporting_guideline_figure_map.md` for any figure mandated by a reporting guideline, (3) `pipeline_concepts_medical_ai.md` for DICOM / annotation / federated / architecture diagrams. Step 4b "Critic Loop" Stage 2 now loads (a) `flow_diagram_lessons.md` for PRISMA / CONSORT / STARD / STROBE flows, (b) `reporting_guideline_figure_map.md` for AI-extension guidelines (CONSORT-AI / STARD-AI / TRIPOD+AI / CLAIM 2024 / DECIDE-AI) so the worker knows which figures the target guideline mandates, and (c) `pipeline_concepts_medical_ai.md` for AI/engineering pipeline figures.

- **Changed** — `skills/make-figures/SKILL.md` Journal AI-Image Policies section now declares an explicit sync pointer to `~/.claude/rules/journal-ai-image-policies.md` (the user's authoritative global rule), preventing the local copy from drifting silently when the policy table is updated upstream.

- **Changed** — `skills/make-figures/SKILL.md` triggers expanded with `key message`, `figure design`, `figure planning`, `effective figure`, and `cognitive load` so design-first prompts route here.

- **Changed** — `skills/make-figures/skill.yml` migrated to schema_version 2: added `layer: B`, `when_to_use` (5 entries covering /write-paper Phase 5 trigger, post-/analyze-stats visualization, PRISMA/CONSORT/STARD/STROBE flows, journal-specific abstracts), `when_NOT_to_use` (4 entries — tabular results → /analyze-stats, decorative slides → /present-paper, logos out of scope, AI images for prohibited targets), and `version: 1.1.0`. Existing `inputs / outputs / deterministic_scripts / side_effects / downstream_consumers / forbidden_actions` retained; `forbidden_actions` gained `generate_AI_images_for_prohibited_targets` to make the JACC / NEJM policy machine-checkable.

- **Added** — `skills/make-figures/scripts/validate_pptx_mac_compat.py` (~210 lines, deterministic). Codifies the four PowerPoint-Mac-only defect classes from `~/.claude/rules/pptx-mac-compatibility.md`: (1) TIFF images embedded in `ppt/media/` (Mac silently drops), (2) `<a:sp3d>` 3-D bevels (renders as red outlines invisible in PDF export), (3) `docProps/app.xml` slide-count mismatch with actual slide XML files (triggers PowerPoint recovery dialog), (4) `<a:srcRect>` values >100000 (1/1000-percent overflow → 99 % over-crop on Mac only). Pure-stdlib (zipfile + regex), no python-pptx dependency. Returns JSON report + human-readable summary; `--strict` exits 1 on any FAIL. Wired into SKILL.md Step 5 Export for any visual-abstract / central-illustration PPTX.

#### Cross-skill harmonization (2026-05-03)

- **Changed** — `skills/check-reporting/SKILL.md` Step 4d (PRISMA Figure 1 audit) now performs a `_figure_manifest.md` cross-check as step 3 of its procedure: verifies the manifest row whose Type matches the audit target points at the same source path and that the row's `Critic` field is not `no`. A missing row, mismatched path, or `Critic = no` logs `[MANIFEST-XREF]` (advisory). Skips silently if `_figure_manifest.md` does not exist (older projects). Closes the prior gap where a figure could pass the arithmetic audit while a parallel `_figure_manifest.md` recorded `critic_pass: no`.

- **Changed** — `skills/write-paper/SKILL.md` Phase 2 step 9 ("Manifest verification") promoted from advisory to **HALT gate** in autonomous mode. Previous behavior was log-and-continue, which silently dropped all figures from the Phase 7 DOCX build (manifest is the figure-embedding source at line 567). New behavior in `--autonomous`: HALT with `MANIFEST_MISSING` error code, log to `qc/_pipeline_log.md`, and write recovery instructions to `manuscript/<id>/REPORT.md` Tier-3 section. Interactive mode unchanged.

- **Changed** — `skills/present-paper/SKILL.md` slide-type templates section now declares the figure source-format contract for `T_image_right`: PNG ≥300 dpi preferred for slides, PDF only when projection >1080p (convert via `pdftoppm -r 300` first because python-pptx PDF embedding is unreliable across PowerPoint versions); TIFF / JPEG-for-line-art / raw-SVG forbidden. Caption contract: re-draft for spoken-narration context (5–10 s of attention) rather than copying journal legends verbatim.

#### Follow-up (deferred, not in this PR)

- 14 remaining skill.yml files still on schema_version 1 (deadline 2026-07-24).
- `scripts/generate_flow_diagram.R` itself unchanged — the new lessons live in references/ text only; codifying the lessons into the R generator (e.g., `--official-template` flag, `--sentinel` mode) is a separate PR.

### `/orchestrate --e2e` v4 integration — pre-flight + REPORT + Tier-3 guard (2026-05-01)

Folds the delegated-mode plan v4 into `skills/orchestrate/` so `/orchestrate --e2e` becomes a "single-researcher" mode: one delegation, no per-phase confirmations except the PHI gate, and a single REPORT.md the user reviews at the end. Replaces the earlier scheme that put the report template and the usage rule under `~/.claude/templates/` + `~/.claude/rules/` (both deleted) — the repo is now the only source of truth.

- **Added** — `skills/orchestrate/references/report_template.md`. Canonical 11-section REPORT layout written to `manuscript/<id>/REPORT.md` at every `--e2e` termination (success or halt). Sections: 한 줄 요약, Frozen / Version status, Source artifacts checked, 변경 파일, Changed claims, 검토 포인트, 환각 게이트 결과, QC artifact links, Human-only missing fields, Tier-3 차단 항목, 다음 액션 + Next safe command + Pipeline log. The Tier-3 section is split into hook-confirmed (`tier3-confirm.sh`) vs prompt/skill-guard-only blocks so a future hook regression cannot silently re-open a prompt-only block.

- **Changed** — `skills/orchestrate/SKILL.md` `### --e2e Flag` now opens with a Pre-flight Validation block (4 checks): STATUS / project_state, frozen artifact (v_N `_FROZEN` marker → v_(N+1) branch only), required inputs, dependency miss. Default on dependency miss is halt; `--auto-extend` is the only opt-in that prepends missing phases. PHI Safety Gate remains the only legitimate interrupt after pre-flight passes.

- **Added** — `skills/orchestrate/SKILL.md` `### REPORT.md Generation` section after Post-Skill Validation. Worker MUST write `manuscript/<id>/REPORT.md` from the new template at every `--e2e` termination. Empty fields render as `(none)` / `(unknown)` — never omitted. The §"Pipeline log" entry is a 5-line summary, not the full log.

- **Added** — `skills/orchestrate/SKILL.md` `### Tier-3 Worker Guard` section. Permanently forbids `--e2e` auto-entry into `git push`, `gh pr create`, MCP Gmail/Calendar send, MCP GitHub create-pr, `/sync-submission build` external publication paths, Phase 8 submission DOCX auto-build, and senior-mentor automatic email reply. `git commit` is allowed; subsequent `git push` halts. Reinforces the existing `### Post-E2E` boundary (Phase 8 already required explicit user invocation).

- **Changed** — `skills/orchestrate/SKILL.md` `check-reporting` row in the Available Skills table now reads "33 reporting guidelines and risk-of-bias tools" to match README and the skill's own SKILL.md (was stale at 22).

#### Follow-up (deferred, not in this PR)

- Release ZIP refresh — `dist/medsci-skills-classroom-*.zip` is stale at v2.1.1 / 37 skills (current 39, including `/manage-refs`, `/render-pdf-doc`, and the e2e+REPORT contract).
- skill.yml v1 → v2 contract migration — 15 skill.yml files still v1; v2 schema not yet adopted across the bundle.
- Mock test for frozen-artifact halt under `--e2e` (Plan v4 Verification §3) — current PR ships docs/contract only.

### Integration cleanup — orchestrator hardening + `/render-pdf-doc` adoption (2026-05-01)

End-to-end integration sweep after the parallel-session conflict around the manage-refs split. Three sessions had been editing the repo simultaneously (`/render-pdf-doc` spinoff, `/write-paper` backbone Phase 0, manage-refs split + circulation memo). This cleanup folds the surviving artifacts together, fixes the runtime breakage left in `/write-paper` Phase 7.6, registers the four previously-unrouted skills with `/orchestrate`, and standardizes per-skill `## Gates` sections.

- **Fixed (P0 blocker)** — `skills/write-paper/SKILL.md` Phase 7.6 hardcoded `${CLAUDE_SKILL_DIR}/scripts/check_citation_keys.py` / `render_manuscript.sh` / `check_xref.py`, all of which moved to `/manage-refs` in the previous release. The hardcoded paths produced a runtime "file not found" the moment the autonomous pipeline tried to render a DOCX. Replaced all three with `${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/manage-refs/scripts/...` and added a one-line delegation note pointing users at `/manage-refs` directly. The Phase summary table at line 861 was updated to label step 7.6 / 7.6a as `/manage-refs` calls.

- **Added** — `skills/render-pdf-doc/` (147-line SKILL.md + scripts/{render_pdf.sh, infer_colwidths.py, check_deps.sh} + 4 templates + 2 references). Skill renders non-bibliography academic markdown (proposal, briefing, anchor doc, IRB cover, reference table) to PDF via pandoc + xelatex with CJK font fallback (Apple SD Gothic Neo / Noto Sans CJK KR) and content-proportional pipe-table column widths. Boundary opposite of `/manage-refs scripts/render_pandoc.sh` (bibliography-driven). Origin: a calibration-anchor PDF that needed manual column-width fixes twice in succession.

- **Added** — `skills/render-pdf-doc/skill.yml` v1 contract (inputs / outputs / forbidden_actions / quality_gates). `bibliography_rendering`, `institutional_word_form_filling`, `figure_or_pptx_generation` are explicitly forbidden so the skill cannot drift into adjacent domains.

- **Changed** — `skills/orchestrate/SKILL.md` Available Skills table now includes `verify-refs`, `manage-refs`, `lit-sync`, `humanize`, `academic-aio`, `render-pdf-doc`, `fill-protocol`, `fill-icmje-coi`, `sync-submission`, `peer-review` (all previously referenced in workflows but not registered). Classification Logic gained 9 new routing rows (manage-refs, lit-sync, render-pdf-doc, fill-protocol, fill-icmje-coi, academic-aio, humanize, peer-review). Multi-skill Workflows table gained 6 new chains (Submission rendering & cascade reformat, Cascade rejection re-target, Non-bibliography academic deliverable, Reference housekeeping cycle, ICMJE COI batch, plus `/manage-refs` insertion into the existing "Draft exists, prepare for submission" chain). Standard Pipeline now lists `/manage-refs` as step 7 (DOCX build + xref QC `--strict` submission gate). Data Flow Contract table gained rows for lit-sync, manage-refs, render-pdf-doc, fill-protocol, fill-icmje-coi, sync-submission, peer-review.

- **Added** — `skills/orchestrate/references/dialogue_nodes.md` two new fork nodes: **N10** Reference Workflow (manage-refs Workflow A pandoc vs B Zotero CWYW vs hybrid 3-phase) and **N11** Protocol Delivery Format (`/fill-protocol` vs `/render-pdf-doc`). Defaults align with `~/.claude/rules/manuscript-references.md` (hybrid) and `~/.claude/rules/institutional-form-fill.md` (institutional template first).

- **Changed** — SSOT writer boundaries declared in `skill.yml`:
  - `skills/search-lit/skill.yml` — `references/library.bib` is search-candidate pool only; sole writer of `manuscript/_src/refs.bib` is `/lit-sync`. New forbidden_action: `write_to_manuscript_refs_bib`.
  - `skills/lit-sync/skill.yml` — declared sole writer of `manuscript/_src/refs.bib` (via Better BibTeX auto-export). New downstream consumer: `manage-refs`. New quality_gates: `refs_bib_refreshed`, `bbt_auto_export_active`. New forbidden_action: `hand_edit_manuscript_refs_bib`.
  - `skills/calc-sample-size/skill.yml` (new) — declares `protocol/sample_size_justification.md` + `sample_size_calc.{R,py}` as canonical outputs; `/write-protocol` and `/write-paper` embed verbatim, never rephrase numbers.

- **Changed** — `skills/write-protocol/SKILL.md` input contract for calc-sample-size now references `protocol/sample_size_justification.md` (canonical artifact path) and mandates verbatim embedding per `~/.claude/rules/numerical-safety.md`.

- **Changed** — `skills/manage-refs/SKILL.md` Anti-Hallucination Guarantees expanded with `[@NEW:topic]` placeholder convention. `check_citation_keys.py` classifies these as `NEW_PLACEHOLDER` (not UNDEFINED) so drafting can proceed; Phase 7.6 (DOCX render) is a hard gate where zero NEW_PLACEHOLDER entries must remain.

- **Added** — Per-skill `## Gates` sections classifying every gate as ENFORCED / ADVISORY / OPT-IN. Updated: `/write-paper` (13-row Phase 0–8+ table + cross-cutting rule list), `/self-review` (5 gates), `/check-reporting` (4 gates), `/humanize` (6 gates including Pattern 19–21 ENFORCED), `/revise` (6 gates including [VERIFY-CSV] tagging + post-revision `/verify-refs --strict`).

- **Added** — `docs/rule-application-map.md` — single-page matrix mapping every global rule (`~/.claude/rules/`) to the skill / phase that triggers it, with severity. Index only; rule bodies remain in the user's `.claude/rules/` directory.

- **Moved** — internal planning note for the `render-pdf-doc` skill from project-root scratchpad into the per-session planning area (now gitignored).

### Added — `/manage-refs` skill split (2026-05-01)

The reference-handling lifecycle (citekey validation, journal-CSL pandoc rendering, manuscript ↔ DOCX cross-reference QC, marker conversion, native Zotero CWYW field-code injection) was extracted from `/write-paper` Phase 7.6 into a new cross-cutting `/manage-refs` skill so it can be invoked uniformly from `/revise`, `/peer-review`, `/sync-submission`, and `/find-journal` (cascade rejection re-render). Validated against a 21-reference systematic-review manuscript, both pandoc-citeproc and Zotero-CWYW paths.

- **New skill** `skills/manage-refs/`:
  - `SKILL.md` (216 lines, MID tier) — decision tree, Workflows A–D (pandoc citeproc / Zotero CWYW / cascade rejection / cross-reference QC), Anti-Hallucination Guarantees (6 items), Quality Gates (3 submission gates + 1 user approval gate).
  - `skill.yml` — v1 contract with full `inputs / outputs / deterministic_scripts / side_effects / downstream_consumers / forbidden_actions` declaration plus provenance entry for the vendored Zotero CWYW writer.
  - `citation_styles/` — 9 journal CSL files relocated from `write-paper/references/citation_styles/` (european-radiology, radiology, AJR, CVIR, KJR, vancouver, vancouver-superscript, springer-basic-brackets, springer-vancouver-brackets).
  - `scripts/check_citation_keys.py`, `scripts/check_xref.py`, `scripts/render_pandoc.sh` — relocated from `write-paper/scripts/` (`render_manuscript.sh` renamed to `render_pandoc.sh`).
  - `scripts/md_marker_convert.py` (new) — generalized `[N]` ↔ `[@key]` converter, mapping-driven, supports `.md` and `.docx`, partial-conversion safe with `--active-ns`. Extracted and generalized from a per-project temporary `build_zotero_docx.py` replacer.
  - `scripts/inject_zotero_cwyw.py` (new) — wraps the vendored `citation_writer.insert_citations` and patches `zotero_to_csl_json` to fetch native CSL-JSON via Zotero's connector API (handles webpage / report / non-journal item types correctly, where the upstream `_ITEM_TYPE_MAP` falls back to `"article"` and silently drops fields).
  - `scripts/_vendor_citation_writer.py` (vendored) — from `alisoroushmd/zotero-mcp` @ `ed5dfb71`, MIT license. See `NOTICE.md` and `LICENSE.zotero-mcp`.
  - `references/check_xref_symptoms.md` — `MISSING_DOCX` / `MISSING_BODY` / `MISMATCH` / `UNCITED` triage table.

- **Dependents updated** to point at the new location:
  - `skills/write-paper/SKILL.md` Phase 7.6 — old in-skill scripts replaced with `/manage-refs` invocations + visible deprecation note. Old paths `${CLAUDE_SKILL_DIR}/scripts/{check_citation_keys.py, check_xref.py, render_manuscript.sh}` and `${CLAUDE_SKILL_DIR}/references/citation_styles/` are retired in this release.
  - `skills/verify-refs/SKILL.md` — companion citation-key check now references `/manage-refs/scripts/check_citation_keys.py`.
  - `skills/self-review/SKILL.md` Phase 2.5b — cross-reference QC invocation now references `/manage-refs/scripts/check_xref.py`.

- **Global rules** updated to single-source the new entry point:
  - `~/.claude/rules/agent-skill-routing.md` — added `/manage-refs` rows for lifecycle, CSL render, citekey check, cross-reference QC, and CWYW injection; `/verify-refs` clarified as audit-only.
  - `~/.claude/rules/manuscript-references.md` — pandoc pipeline section repointed at `manage-refs/scripts/render_pandoc.sh`, with `check_xref.py` step added inline.

### Added — Senior MA reviewer harvest

Lessons from senior meta-analysis mentor circulation feedback promoted into global rules and skill checklists, so subsequent manuscript circulations in the same pipeline do not repeat the same comments.

- **Global rules (5 files)** under `~/.claude/rules/`:
  - `manuscript-style-classical.md` (new) — 11-item style policy: `## **METHODS**` heading, abstract sub-headers `**Objectives:**`, eligibility numbered list, no `§` symbol, no AI Disclosure paragraph in body, em-dash <25, Vancouver 6+ et al., ORCID one-per-line, table header punctuation, British/American per journal.
  - `senior-mentor-circulation.md` (new) — mandatory `8_Review_Comments/` folder layout, 1차 source preservation, 1:1 verification, mentor README (per-mentor preference accumulation).
  - `ai-drafted-document-policy.md` (new) — verbatim absorption forbidden when senior mentors attach AI-drafted documents; `_DO_NOT_USE_VERBATIM` filename suffix mandatory; trust hierarchy SSOT > mentor direct text > AI-draft. Motivation: 2026-04-12 Ishikawa 2017 denominator hallucination (5/70 vs 12/33 → real 35/68).
  - `data-integrity.md` — one-line augmentation cross-linking the AI-drafted policy.
  - `agent-skill-routing.md` — new "Cross-cutting 룰 (Manuscript / 회람)" table referencing the six rule files.

- **`/write-paper` Step 7.1 — Classical-style QC sub-step**:
  - `skills/write-paper/references/section_guides/step7_1_classical_qc.md` (new) — load-on-demand 7-grep checklist (`§` symbol, AI Disclosure paragraph, heading style, eligibility numbered list, Funding placeholder, PROSPERO chronology, em-dash overuse).
  - `skills/write-paper/SKILL.md` Step 7.1 — trigger table + load-on-demand pointer added.

- **`/humanize` Pattern 19–21**:
  - `skills/humanize/references/ai_patterns.md` — Pattern 19 (`§` section sign), Pattern 20 (Methods/Results self-reference parenthetical), Pattern 21 (AI Disclosure boilerplate in body) added with detection regex + rewrite guidance.
  - `skills/humanize/SKILL.md` — 18 → 21 patterns; section-specific focus extended to MA / SR Methods and Discussion.

- **`/meta-analysis` Phase 4.0 — AI-drafted starting document gate**:
  - `skills/meta-analysis/SKILL.md` — new sub-step at the top of Phase 4 (Data Extraction) requiring `_DO_NOT_USE_VERBATIM` filename suffix and source-PDF re-verification of every per-study N, denominator, event count, and effect estimate carried over from a senior mentor's AI-drafted directive. Trust hierarchy: SSOT > mentor direct text > AI-draft (never promote tier 3 to tier 2).
  - Cross-links `~/.claude/rules/ai-drafted-document-policy.md` (motivation: 2026-04-12 Ishikawa 2017 denominator hallucination caught at SSOT re-verification).

- **`/check-reporting prisma` Step 4d — PRISMA Figure 1 arithmetic & cross-reference audit**:
  - `skills/check-reporting/scripts/check_prisma_figure.py` (new) — extracts PRISMA numbers from manuscript body and Figure 1 source, runs 4 arithmetic equations (`screened = identified - duplicates`, etc.) and a body↔figure 1:1 cross-reference, emits `qc/prisma_figure_audit.json` + table. Exits 1 on any MISMATCH.
  - `skills/check-reporting/SKILL.md` Step 4d — invocation block + flagging policy (`[PRISMA-FIGURE]`, `fixable_by_ai: false`).
  - `skills/check-reporting/references/step4d_prisma_figure_audit.md` (new) — regex set, JSON schema, edge cases (multi-database, citation-searching strand, dual-reviewer screening, reports-vs-records terminology).

Resolves the meta-analysis project → medsci-skills handoff P1+P2.

### Added — Manuscript ↔ rendered DOCX cross-reference QC (`/write-paper` Step 7.6a + `/self-review` Phase 2.5d)

New 3-way audit catches the failure mode where in-text Table/Figure citations resolve to a different rendered caption because the build script carries its own legacy SSOT. Internal consistency (Phase 2.5) cannot detect it — both the prose and the build artifact echo their own divergent truths cleanly.

**Precedent:** in a STROBE cohort manuscript, the body cited "Supp Table S4 (sensitivity analysis)" but the rendered DOCX S4 was a different table; S1, S6, S7 mismatched and S8, S9 were cited but absent from the DOCX entirely. Caught only on co-author circulation review.

- `skills/write-paper/scripts/check_xref.py` — extracts (a) `(Supplementary )?(Table|Figure)\s+(S?\d+[A-Z]?)` in-text citations, (b) caption definitions from `## Tables` / `## Figures` / `## Supplementary {Tables,Figures}` body sections, (c) rendered DOCX caption paragraphs via python-docx. Emits `qc/xref_audit.json` with status codes `OK | MISSING_DOCX | MISSING_BODY | MISMATCH | UNCITED | NOT_CITED_NO_BODY`. Caption agreement via Jaccard ≥0.40. Panel-letter fallback (`Figure 2A` cite resolves to `Figure 2` caption). `--strict` exits 1 on any P0 finding.
- `/write-paper` Step 7.6a (new) — runs after Step 7.6 DOCX build, before Step 7.7 final gate. Submission gate; HALT pipeline on non-OK. Routing table for fixes by symptom (body update vs build-script update) — body caption is the SSOT, never the reverse.
- `/self-review` Phase 2.5d (new) — reuses the same script when a rendered DOCX exists. Translates findings to P0 Major Comments (category F, `fixable_by_ai: false`). Auto-fix forbidden in `--fix` mode (caption rewrites without rebuilding DOCX would only move the mismatch).

Resolves an internal improvement queue item (cross-reference QC, HIGH priority).

### Added — `/make-figures` flow diagram pipeline (R + DiagrammeR + rsvg)

New standardized flow-diagram generation for STROBE / CONSORT / PRISMA / STARD in a single R script, replacing the former D2 + matplotlib mix that caused repeated overlap, font, and DOCX-embed issues.

- `skills/make-figures/scripts/generate_flow_diagram.R` — CLI dispatcher: `--type {strobe|consort|prisma|stard} --config <yaml> --out <prefix>`. Reads a YAML node/edge spec, emits true vector PDF + 300 dpi PNG + 600 dpi PNG. Monochrome black outline on white fill, Arial, auto-overlap via Graphviz `dot` engine.
- `skills/make-figures/references/exemplar_diagrams/{strobe,consort,prisma,stard}/` — each directory now contains `template_input.yaml` + rendered `template_output.{pdf,png,_600.png}` so users can fork a concrete example.
- `skills/make-figures/references/exemplar_diagrams/strobe/` — new directory (previously missing alongside consort/prisma/stard).
- `skills/make-figures/references/exemplar_diagrams/README.md` — layout description extended to cover both "review anchors" (existing curator-curated PDFs) and "generation templates" (new).
- `skills/make-figures/SKILL.md` — "Flow diagram generation rule" rewritten to mandate the R pipeline as the single canonical tool. D2 recipe demoted to a legacy-fallback block. Tool Selection Guide table updated to route all four reporting-guideline flow diagrams through `generate_flow_diagram.R`.
- `skills/make-figures/references/figure_specs.md` — new "Flow Diagram Tool Selection" section documenting the stack choice, PRISMA 2020 compliance note, and rejection rationale for matplotlib / D2 / `consort` / `PRISMA2020` / Mermaid.

**System dependency:** `brew install librsvg` (macOS) or `apt-get install librsvg2-bin` (Linux). R packages: `DiagrammeR`, `DiagrammeRsvg`, `rsvg`, `yaml`.

**Validated end-to-end:** a STROBE cohort Figure 1 rebuilt with the new pipeline — single-color outline, no overlap, Arial rendered correctly for en-dash / bullet / `≤` / minus sign. Counts derived from a tracked cohort CSV. Legacy `create_figure1.py` and `figure1_flow.d2` preserved with `_legacy` suffix.

**Rollout:** retrofitted across multiple manuscripts spanning STROBE, STARD, PRISMA, PRISMA-DTA, and CONSORT-edu reporting guidelines.

- SKILL.md Flow-diagram section now documents the **per-project `create_figure1.R` pattern** (sprintf'd `dot` string + `stopifnot()` count reconciliation + multi-rank `{rank=same}` blocks) as the preferred route when the generic YAML dispatcher cannot express complex layouts.
- SKILL.md style rules hardened: **no HTML-like labels** (`label=<...>` with `<B>`/`<I>`/`&#8226;`) — plain quoted labels with `\l` bullets produce tighter, more readable structure than HTML ragged wrapping.

### Added — New skill `/academic-aio` + pipeline integration across README, write-paper, orchestrate

Medical AI paper optimization for AI search engines (Perplexity, ChatGPT web, Elicit,
Consensus, SciSpace) and RAG-based literature tools. Integrates TRIPOD+AI, CLAIM,
STARD-AI, TRIPOD-LLM, and DECIDE-AI reporting anchors with generative-engine-optimization
(GEO) principles from Aggarwal 2024 (arXiv:2311.09735). Scope covers title, abstract,
structured summary boxes (Key Points / Research in Context / Plain-Language Summary),
preprints, GitHub README, `CITATION.cff`, Zenodo, and Hugging Face model / dataset
cards. Explicit defense against LLM citation fabrication (Agarwal 2025, Nat Commun
doi:10.1038/s41467-025-58551-6, which reports up to 78–90% fabricated citations in
medical LLM answers). Produces a visible PASS/PARTIAL/FAIL checklist; never applies
edits silently (Communication Rules).

**Pipeline integration** (added in this release, not in the new skill itself):
- `README.md`: skill-table row added + main pipeline diagram branches
  `humanize → academic-aio` off the self-review / find-journal spine.
- `write-paper/SKILL.md` Skill Interactions table: new rows 7.5 (`/humanize`) and
  7.5a (`/academic-aio` opt-in `--aio`), running after `/self-review` Phase 7.4
  and before DOCX build (Phase 7.6).
- `orchestrate/SKILL.md`: (a) new multi-skill-workflow row "Medical-AI paper,
  AI-search visibility pass" with N4 + N9 nodes; (b) existing "Draft exists,
  prepare for submission" chain extended to `humanize → academic-aio (--aio)`;
  (c) new `--e2e` clause #8 specifying AIO is OFF by default in autonomous
  mode (AI-search visibility is a pre-submission, not a pre-draft, concern and
  autonomous silent rewrites would violate AIO's "never edit silently"
  contract) — opt-in via `--aio`, report always surfaced to user.
- Internal pipeline planning notes record the AIO-position rationale for 7.5a
  placement (after `check-reporting` so the Section 1.6 guideline anchor reflects
  real compliance; after `humanize` so the human-readability pass does not erase
  AIO edits; before DOCX build so the optimizations reach the final artifact)
  and the Anti-Hallucination division of labour with `search-lit` /
  `check-reporting` / `write-paper` / `humanize`.

**Anti-Hallucination block added to `/academic-aio` SKILL.md**: bars fabricated
citations / DOIs / arXiv IDs / reporting-guideline item numbers; bars invented
journal-specific summary-box rules (Lancet Digital Health "Research in context",
Radiology "Key Points", npj Digital Medicine); bars fabricated AI-search
discoverability metrics (Perplexity / Elicit / Consensus retrieval scores may
only be reported from recorded probes); bars auto-completion of CITATION.cff
and Zenodo author lists, ORCIDs, and affiliations. This closes the last
validator FAIL from the v2 content-integrity lint rollout.

**Skill count**: 32 → 33. Validator reports 265 PASS / 32 WARN / 0 FAIL after
these changes.

### Changed — Reference split for `/meta-analysis` Phase 4 & Phase 6 (R templates + KM/composite)

`/meta-analysis` SKILL.md had two oversized phases after the earlier Phase 9/10 split:
Phase 6 (Statistical Synthesis) ran 119 lines with full R code for DTA bivariate models,
intervention `metagen`/`metabin`, the dual-approach comparative + single-arm pooled
proportion decision table, practical R notes (method.tau, HK CI, zero-cell correction),
publication-bias test power, and sensitivity-analysis menu; Phase 4 (Data Extraction)
contained two specialised sub-procedures — KM curve reconstruction via WebPlotDigitizer
+ `IPDfromKM` (Guyot 2012) and composite-exposure disaggregation — that together ran
~40 lines. Both were moved to `references/phase6_statistical_synthesis.md` (148 lines)
and `references/phase4_km_composite.md` (58 lines), with SKILL.md bodies retaining a
one-table summary + load-on-demand pointer. Net impact: `/meta-analysis` 594 → 459
lines (−135, cumulative −281 from 740 pre-recovery-loop inlined state).

### Changed — Korean→English prose translation for `/ma-scout`, `/lit-sync`, `/grant-builder`, `/deidentify`

Four skills carried substantial Korean prose body text that tripped rule 9 of the v2
content-integrity lint (Korean outside code/tables/Communication Rules/frontmatter).
Translations preserve Korean domain terms in parenthetical references where they are
literal references to the Korean research system (Korean government agency names in
`/grant-builder`: 복지부=MOHW, 산자부=MOTIE, 중기부=MSS; Korean attachment names:
첨부1-3; Korean vault folder paths in `/lit-sync`: `02 연구/문헌/`, `02 연구/개념노트/`;
Obsidian note template headings in `/lit-sync` that must match the user's existing vault
convention: `## 서지 정보`, `## 핵심 내용`, `## 내 생각`, `## 관련 노트`). `/ma-scout`
also extracted the 72-line bilingual PROSPERO-ready README template block to
`references/project_readme_template.md` (includes Solo-Mode Adaptations for topic-first
mode without supervisor) and replaced the inlined block with a load-on-demand pointer.
Net impact: all four skills now pass lint rule 9 for SKILL.md body text; remaining
Korean is confined to frontmatter triggers (permitted), literal template content, and
Obsidian vault paths (the 32 outstanding WARNs are legitimate Korean-in-parenthesis
references that are not targeted by the rule).

### Changed — Reference split for `/meta-analysis` Phase 9/10, `/check-reporting` Step 4c, `/write-paper` Step 7.4a

The recently added recovery-loop phases were fully inlined in `SKILL.md` bodies,
inflating three skill files beyond what load-on-demand expects. Procedural detail was
extracted to new reference files (`meta-analysis/references/phase9_circulation.md`,
`phase10_recovery.md`, `check-reporting/references/step4c_registration_timing.md`,
`write-paper/references/section_guides/step7_4a_audit_recovery.md`) with SKILL.md bodies
retaining only the trigger table, routing table, and summary paragraph plus a
`Load-on-demand procedural detail` pointer. Net impact: `/meta-analysis` 740 → 594
lines (−146), `/check-reporting` 425 → 376 (−49), `/write-paper` 853 → 829 (−24). Pattern
follows the existing `checklists/QUADAS2.md` load-on-demand convention. All nine
content-integrity lints continue to pass.

### Added — `scripts/validate_skills.sh` v2 content-integrity lints + pre-commit hook

The validator previously checked frontmatter, size tiers, and reference integrity but
could not catch content regressions that had accumulated over prior sessions. v2 adds
four content-integrity rules scoped to shipped skill prose (`SKILL.md` plus
`references/**/*.md`, excluding `HANDOFF.md` and `TODO_*.md` meta-docs):
**Rule 6** blocks project-specific precedent identifiers (per-project IDs,
prior-citation slugs, ordinal-numbered paper labels) from leaking into shipped
skills; **Rule 7** blocks absolute personal home-directory paths in shipped
prose (scripts and exemplar `.meta.yaml` fixtures are out of scope); **Rule 8** flags dated precedent
blockquotes (`^> ... YYYY-MM-DD`) while allow-listing `Last updated:` / `Created:` /
`Updated:` / `Date:` meta-header prefixes; **Rule 9** warns on Korean prose in
`SKILL.md` body outside fenced code blocks, tables, blockquote examples, the
Communication Rules section, and frontmatter (Korean triggers remain permitted).
Rules 6–8 are FAIL-level; rule 9 is WARN-only pending per-skill translation
decisions. A `.git/hooks/pre-commit` hook runs the validator automatically when any
`skills/**/*.md` or the validator itself is staged, early-exiting otherwise to keep
non-skill commits fast.

### Changed — `/orchestrate` Dialogue Protocol is now the default interactive execution path

The prior interactive flow was a plain bulleted plan followed by "Shall I proceed with
step 1?" — a confirmation that surfaced no lock-in cost. The revised **Workflow Execution
— Dialogue Protocol** section makes per-fork decision-node rendering the primary control
flow: identify the node, render the template (context + numbered options + per-option
`unlocks` / `locks` / `recovery_cost`), wait for a numeric choice or a control word
(`back` / `pause` / `skip`), echo the lock in one line, invoke the matched skill, and
return for the next fork. The Multi-Skill Workflows table gained a **Nodes** column that
maps each scenario to the N1 – N9 node IDs. The `--e2e` Flag section now prescribes
node-by-node default application with per-node logging to `qc/_pipeline_log.md`, and
specifies that the PHI gate (N6) is the sole node that can HALT autonomous mode, while
Audit Recovery (N8) HALTs only when the routed recovery fails validation twice. The
Output Format multi-skill example was replaced with a worked N2 Paper Type rendering to
anchor downstream rendering style.

### Added — `/orchestrate` Dialogue Mode prototype (RPG-style decision nodes)

`/orchestrate` previously executed multi-skill pipelines with plan-then-confirm but
did not surface the downstream cost of each commitment (paper type, study design,
target journal timing, MA synthesis scope, audit recovery branch). The new
**Dialogue Mode** is the interactive default: at each major fork, the orchestrator
renders a decision node (context, numbered options, per-option `unlocks` / `locks` /
`recovery_cost`) and the user picks a number. `--autonomous` / `--e2e` bypasses the
rendering and uses each node's `default`, logging the choice to
`qc/_pipeline_log.md`. The prototype lists 9 primary nodes — entry classification,
paper type, study design (STARD/CONSORT/STROBE/TRIPOD+AI), target-journal timing
(commit-now vs. late-bind), MA synthesis depth (primary / +subgroups / +sensitivity /
+meta-regression), PHI Safety Gate, autonomy flag, Step 7.4a audit recovery branch,
and `/write-paper` section entry on re-entry — with rendering templates and
autonomous-default rationales. Load-on-demand reference at
`skills/orchestrate/references/dialogue_nodes.md`; `SKILL.md` body gains only a
one-paragraph pointer to preserve token economy.

### Added — `/meta-analysis` Phase 9 (Co-author Circulation) + Phase 10 (Self-Audit Recovery)

The pipeline previously stopped at Phase 8 (Reporting & Manuscript), leaving two operational
loops undocumented. **Phase 9** standardizes pre-submission circulation: thread-reply
continuity, attachment scope (body + change summary only; exclude GA / cover letter / COI
until journal is confirmed), recipient structure (corresponding + one senior methodologist
TO, co-authors CC), the 7-day deadline rule, and journal-undetermined framing. **Phase 10**
formalizes the v{N} → v{N+1} rebuild sprint when an audit uncovers structural data or
protocol-application errors — audit log, CSV re-verification, analysis re-run, manuscript
auto-sync, figure regeneration, change summary, protocol-registry amendment in parallel,
and the transparent re-circulation framing. Triggers include extraction ↔ source
mismatch, protocol-analysis disagreement, hand-typed script literal errors, and
consensus-record ↔ locked-dataset disagreement. Anti-patterns (hide & submit, reframe as
"minor revision", cover-letter-only disclosure) are documented as do-not.

### Added — `/write-paper` Step 7.4a Audit Recovery Branch

Phase 7 polish was a linear flow (draft → review → revise → submit) that silently proceeded
past structural self-review findings. Step 7.4a makes the recovery loop explicit: when
Step 7.4 returns a fatal `accuracy`, `data_fidelity`, `protocol_mismatch`, or
`numerical_claim` issue, an unresolved Step 7.3a primary-source disagreement, a persistent
`[VERIFY-CSV]` tag, or a registry ↔ analysis inconsistency, the pipeline halts Steps 7.5 –
7.6 and routes to the appropriate upstream recovery. For MA manuscripts this is
`/meta-analysis` Phase 10; for non-MA manuscripts with extraction errors, back to
`/write-paper` Phase 2; protocol amendments halt for human decision. On re-entry the
pipeline resumes at Step 7.3, not Step 7.1, because recovery may have introduced new
citations. Loop budget: one recovery cycle expected; a second cycle on the same manuscript
prompts a root-cause review of Phase 2 / 6 / 6b.

### Added — `/check-reporting` Step 4c Registration / Protocol Timing Consistency Check

The registration identifier alone is a single checklist item and passes even when the
manuscript is internally inconsistent about registration / amendment timing. Step 4c
audits five consistency items: registration identifier present in Methods/Abstract/
cover letter, registration date ↔ screening/extraction milestone order, amendment date ↔
Methods-described change agreement, cross-artifact agreement between Methods and the
registry record (e.g., PROSPERO PDF), and retrospective-registration disclosure when
the registration date post-dates extraction start. Findings carry the
`[REGISTRATION-TIMING]` label in Part C Action Items, with `fixable_by_ai: false` when
reconciliation requires an external amendment filing. A new `registration_timing` JSON
field is emitted in Part D. Applies to PRISMA 2020, PRISMA-DTA, PRISMA-P, MOOSE, CONSORT,
and SPIRIT. Common Gaps list updated to include amendment-date consistency as item #2.

### Added — Verified neurointervention/cerebrovascular journal profiles

- **JNIS (Journal of NeuroInterventional Surgery)** — compact + detail profiles built from user-supplied author-guidelines PDF (BMJ, SNIS). Covers double-anonymised review, ORCID mandate, BMJ Tier 3 data-sharing policy, Key Messages box requirement, AI policy aligned with BMJ/ICMJE.
- **Journal of Stroke** (Korean Stroke Society) — compact + detail profiles from user-supplied author-guidelines PDF. Full OA CC BY-NC 4.0 with no APC; Vancouver numbered references; structured 250-word abstract for Original Articles; mRS/mTICI/sICH definition requirements; AI policy defaults to ICMJE/WAME (no explicit journal-specific text).
- **Stroke (AHA/ASA)** — compact + detail profiles from user-supplied author-instructions PDFs. ISSN verified against ISSN Portal (print 0039-2499 / online 1524-4628, ISSN-L 0039-2499). Three-category science triage (Basic/Translational, Clinical, Population); structured 300-word abstract; Vancouver references listing first 10 authors + "et al."; 90-day revision window with mandatory Graphic Abstract at revision; explicit AI policy per AHA/ICMJE.

All three profiles follow the two-tier public-library format established by `INSI.md` and include a verification note citing the source author-guidelines PDF.

### Added — `/find-journal` Phase 3.6 Profile Coverage Advisory

Previously, when the public profile library had a known gap for the manuscript's field,
the ranking silently substituted adjacent journals and the user never learned that a
better-fitting target existed. The new Phase 3.6 scans `skills/find-journal/TODO_*_profiles.md`
files, matches their `## Field Keywords` block against the manuscript's themes, and appends
a Coverage Advisory block between the comparison note and the Mandatory Disclaimer when
a relevant TODO has still-missing journals. The advisory names the missing journals,
cites their publisher and 1-line rationale verbatim from the TODO file, and directs the
user to `/add-journal` with a PDF to close the gap per `POLICY.md`. No false alarms when
no TODO is relevant.

`TODO_neurointervention_profiles.md` updated with a `## Field Keywords` section so it
feeds the advisory. Future field TODO files should follow the same convention.

### Added — `/write-paper` Step 7.3a trigger 5 (reporting-quality checklist SRs)

Step 7.3a Numerical Claim Audit previously fired only on pooled estimates, comparative-arm
values, `[VERIFY-CSV]` tags, or post-v1 revisions. It missed the reporting-quality
systematic review pattern, where all headline numbers are derived by counting cells in an
items × studies checklist matrix (TRIPOD+AI, PROBAST+AI, CLAIM, PRISMA, STARD, CHARMS,
ARRIVE). The same failure class applies — hand-tallied totals drift from cell-level truth
while every downstream artifact echoes the wrong number.

Trigger 5 is now mandatory whenever the manuscript reports corpus-level, study-level, or
item-level PRESENT / PARTIAL / ABSENT / compliance counts or percentages from a checklist
synthesis. The procedure adds five steps specific to this pattern: per-study totals
recomputation, corpus-level Σ non-NA denominator, item-level roll-up, 3-way consistency
(manuscript ↔ per-study JSON ↔ summary document), and a reproducible audit script that
emits `numerical_claims_log.csv` and exits non-zero on any mismatch.

A companion rule is recorded in `~/.claude/rules/numerical-safety.md` so the gate
triggers even in non-skill workflows.

## [2.3.0] - 2026-04-19

### Added — Numerical Hallucination Prevention Layer

A real incident during a revision run exposed that the citation-safety pipeline did not have
a symmetric counterpart for numerical claims. Citations were verified end-to-end against
PubMed (0 fabricated refs), while a hand-typed `matrix()` in a revision-era R script silently
reversed a Fisher exact 2x2 ("3/45 vs 0/56, p=0.085" where the source said "0/45 vs 1/56,
p=0.37"). Every internal consistency check passed because every artifact echoed the same
wrong number. Detection required an explicitly requested second-pass audit with random
sampling against the primary paper.

To close that gap, four skills now enforce a common 3-layer (CSV ↔ analysis script ↔
manuscript) audit, with additional back-checking against the primary paper for revisions and
pooled estimates:

- **`/meta-analysis` Phase 6b — Post-Analysis Source Fidelity Audit (new).** After Phase 6
  statistical synthesis, mandates no hand-typed numerical matrices when a CSV exists,
  separate consensus-log rows for comparative-arm subsets, and a random 3-claim back-check
  (manuscript → R output → primary-source Table/Figure) before advancing to GRADE. A single
  mismatch is a P0 blocker.
- **`/self-review` Phase 2.5a — Numerical Source-Fidelity Audit (new).** Complements the
  existing Phase 2.5 internal consistency check with external validation: stratified random
  sampling of 5 claims, 3-layer traversal (manuscript ↔ CSV ↔ primary paper), and escalation
  of any mismatch to Major Comment. Revision-introduced numbers and comparative-arm specific
  values are the two highest-yield strata and are always sampled.
- **`/revise` Step 2.5 — Revision Numerical Lineage Check (new).** Any `/analyze-stats`
  re-run during revision must tag new numerical claims with `[VERIFY-CSV]`, read inputs from
  the locked extraction CSV, and maintain a response-document audit table that maps each new
  number to its source script:line + CSV coordinate + primary-source location. Prose
  generation is gated on the audit clearing.
- **`/write-paper` Step 7.3a — Numerical Claim Audit (new).** Sits alongside the existing
  citation verification step. Triggered whenever the manuscript contains pooled estimates,
  comparative-arm values, `[VERIFY-CSV]` tags, or is a post-v1 revision. Greps all analysis
  scripts for hand-typed numerical literals without CSV-coordinate comments and flags them
  as structural risks regardless of current correctness.

All four skills reference the revision-era Fisher-exact reversal pattern described above as
a concrete failure mode rather than an abstract risk. Complementary companion rules were
added to `~/.claude/rules/data-integrity.md` and a new `~/.claude/rules/numerical-safety.md`
so the gates trigger even in non-skill workflows.

## [2.2.1] - 2026-04-18

### Added

- **`/meta-analysis` Phase 3 multi-round screening structure**: Phase 3a now distinguishes Round 1 (single-reviewer initial screen), Round 2 (dual independent screen with Cohen's kappa), Round 3 (first-reviewer adjudication of disagreements), Round 4 (full-text), and PRISMA flow.
- **AI-assisted pre-screening template** (`meta-analysis/references/ai_pre_screening_template.py`): reusable script for compressing R3 adjudication. Generates AI suggestions only; first reviewer must independently confirm or overturn each. Includes Methods boilerplate citing model name and version. Companion priority-sort logic built in.

### Changed

- **`/meta-analysis` SKILL.md**: Phase 3 expanded from 17 to 39 lines (3a–3e). Maintains kappa requirement and adds explicit guidance for handling MAYBE-tagged records.

## [2.2.0] - 2026-04-18

### Added

- **5 new skills** (32 total): `humanize`, `author-strategy`, `peer-review`, `ma-scout`, `lit-sync`
  - **humanize**: 18-pattern AI writing detection and removal for academic manuscripts
  - **author-strategy**: PubMed author profile analysis with study type classification and strategy report
  - **peer-review**: Structured peer review drafting with journal-specific formatting (RYAI, INSI, EURE, AJR, KJR)
  - **ma-scout**: Meta-analysis topic discovery — professor-first or topic-first modes with PubMed E-utilities, PROSPERO check, and PICO scaffolding (732 lines, largest new skill)
  - **lit-sync**: Zotero + Obsidian reference sync pipeline with cross-cutting concept note extraction
- **Anti-hallucination clauses** added to all 32 skills. Domain-specific rules prevent fabricated variables, effect sizes, citations, and clinical definitions.
- **SKILL_TEMPLATE.md** (`docs/`) — canonical template for new skill creation with quality tier requirements
- **validate_skills.sh** (`scripts/`) — automated skill linter checking frontmatter, anti-hallucination, gates, line count tier, and reference integrity
- **3-country harmonization CSV** (`replicate-study/references/harmonization_3country.csv`) — KNHANES+NHANES+CHNS variable mapping (45 rows)

### Changed

- **cross-national**: Expanded from 2-country to 3-country support (KNHANES+NHANES+CHNS). Added ~100 lines of validated variable codings for KNHANES, NHANES, and CHNS with specific warnings (BMI cutoffs, hemoglobin units, survey weight handling). Added composite score replication warnings from LE8 validation.
- **batch-cohort**: Added physician-diagnosis requirement for outcome definitions (rule 8) and full 8-covariate default (rule 9). Expanded self-adjustment removal for education/income/MetS.
- **replicate-study**: Added 3-country harmonization reference.
- **fulltext-retrieval**: Fixed frontmatter (added missing `tools` and `model` fields).

### Infrastructure

- All 32 skills now pass `validate_skills.sh` with 0 FAIL.
- Quality tier distribution: 15 HIGH (300+ lines), 14 MID (150-300), 3 THIN (<150).

## [2.1.0] - 2026-04-15

### Added

- **find-cohort-gap**: New skill for systematic research gap discovery from cohort databases. 6-phase pipeline (cohort intake → PI profiling → intersection matrix → literature saturation scan → 6-Pattern scoring with comparison tables → feasibility gate → ranked one-pager proposals). Works with any cohort: NHIS, UK Biobank, institutional EMR, health checkup registries. Includes 4 reference files (pattern scoring rubric, cohort profile template, one-pager template, saturation query templates). Integrates with `/search-lit` for PubMed searches and feeds into `/design-study` → `/write-paper` pipeline.

## [2.0.0] - 2026-04-14

### Changed

- **Demos regenerated with `orchestrate --e2e` pipeline.** All 3 demos now produce a consistent artifact set: `analyze.{py,R}`, `_analysis_outputs.md`, `_pipeline_log.md`, `manuscript.md`, `manuscript_final.docx`, `reporting_checklist.md`, `review_comments.md`, `figures/_figure_manifest.md`, and study-type-specific tables and figures.
- Demo output structure flattened: `tables/` replaces `output/` for CSV files; manuscript and QC artifacts live at demo root.
- Previous demo scripts and outputs archived to `demo/_archive/` for reference.

### Added

- **Demo 1 (Wisconsin BC, STARD):** 19 artifacts. STARD flow diagram (D2), reporting checklist (82.1% compliance), self-review (74/100), submission-ready DOCX.
- **Demo 2 (BCG Vaccine, PRISMA):** 24 artifacts. R metafor analysis with forest plot, funnel plot, bubble plot, PRISMA flow diagram (D2), reporting checklist (77.8% compliance), self-review (72/100), submission-ready DOCX.
- **Demo 3 (NHANES Obesity, STROBE):** 23 artifacts. Python analysis with prevalence chart, OR forest plot, HbA1c distribution, age x BMI subgroup plot, STROBE flow diagram (D2), reporting checklist (81.8% compliance), self-review (75/100), submission-ready DOCX.
- `CHANGELOG.md` (this file).

### Pipeline artifacts (new in each demo)

| Artifact | Description |
|----------|-------------|
| `_pipeline_log.md` | 7-step execution trace with pass/fail status |
| `_figure_manifest.md` | Structured figure inventory for downstream consumption |
| `reporting_checklist.md` | Item-by-item guideline compliance assessment |
| `review_comments.md` | Self-review with Major/Minor classification and scores |
| `manuscript_final.docx` | Pandoc-built submission-ready Word document |

## [1.0.0] - 2026-04-08

Initial release with 22 skills and 3 demo pipelines.

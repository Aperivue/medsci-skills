# Changelog

## [Unreleased]

### Added

- **`/self-review` category C — power-aware null interpretation**: a new check that scores non-significant primary results (p > 0.05, 95% CI crossing the null) for whether the analysis is powered to *exclude* a clinically meaningful effect. An underpowered null is flagged as "not yet established" rather than "no effect," and the check watches for bilateral over-correction (a prior overclaim swinging to an equally unsupported negative claim during revision). Undocumented null = Minor; a null driving a clinical recommendation without power/CI-compatibility justification = Major. Backports a panel-only finding into the single-pass review (prose check, no new dependency).
- **Structural-zero / dose-duration covariate guards (`/analyze-stats`, `/clean-data`, `/define-variables`)**: a coupled source-side defense against the most common observational miscoding — a dose/duration variable anchored to a categorical exposure (pack-years under smoking status, grams/week under alcohol use). `/clean-data` gains a Stage-2 flag for *categorical-implied zeros* (a `never` record with a NULL dose is a contradiction, not missing data) plus a stdlib detector `scripts/check_structural_zero.py`; `/analyze-stats` gains a "Covariate Pitfalls" section warning against imputing structural zeros (MICE fabricates a non-zero dose for the unexposed) and against complete-case collapse (the unexposed stratum is silently dropped, shrinking n 40–60%), recommending adjustment on the categorical status with the continuous dose reserved for an exposed-only secondary analysis; `/define-variables` gains a matching failure mode requiring `IF status == 'never' THEN dose = 0` to be operationalized explicitly. Synthetic PII-free fixtures + regression test included.

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

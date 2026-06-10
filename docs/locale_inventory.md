# Locale Inventory

**Status: migration complete (PR1–PR4).** The English-canonical migration has landed — incidental
Korean prose is translated (PR2) and the Korean-default skills now default to English with opt-in
`*_ko` variants (PR3). The rows below are the **steady state**: 50 Korean-bearing files, each a
functional locale feature (A), a Korean-jurisdiction mode (A2), a bilingual trigger (D), or an
opt-in `*_ko`/locale variant. `check_locale_inventory.py --strict` is clean.

This file is the **auditable allowlist** for non-English (currently Korean) text under `skills/`.

Policy: skill mechanics and prose are English-canonical. Non-English is allowed **only** as a
labeled locale feature, a locale-jurisdiction mode, a bilingual trigger, or an opt-in `*_ko`
variant — and every such file must appear in the table below with a reason. See
[CONTRIBUTING.md](../CONTRIBUTING.md#language-policy) for the principle.

**Enforcement:** `scripts/check_locale_inventory.py` asserts that every file matched by
`grep -rl '[가-힣]' skills/` is listed here. A Korean-bearing file that is *missing* from this
table fails the check (CI). As translation/redesign PRs land, their rows are removed (the file no
longer contains Korean); the steady state is only the **KEEP** rows.

Buckets:
- **A** — locale feature: Korean is functional (locale data, language-specific parsing/examples, Korean PII detection). KEEP.
- **A2** — locale-jurisdiction mode: a Korean-domain workflow with English wrapper prose + preserved Korean artifact terms. KEEP.
- **B** — incidental prose: translate to English (PR2). Transitional row, removed when translated.
- **C** — Korean-default behavior/output: redesign to English-default + Korean opt-in `*_ko` variant (PR3). Transitional row.
- **D** — bilingual `triggers:` field (frontmatter): additive recognition aliases. KEEP.

> Note: several SKILL.md files carry both a **D** trigger line and **A** locale content; they are
> listed once under their KEEP rationale. Mixed B+C files are handled wholly in one PR (PR3) to
> avoid a single file straddling two PRs.

---

## KEEP — locale features (Bucket A)

| Path | Bucket | Why retained |
|---|---|---|
| `skills/deidentify/locales/kr.json` | A | Korean PHI locale data (RRN/phone/address patterns) — the feature. |
| `skills/deidentify/references/korean_phi_patterns.md` | A | Korean PHI pattern reference. |
| `skills/deidentify/references/hipaa_18_identifiers.md` | A | HIPAA ↔ Korean identifier mapping (성명/주민등록번호/개인정보보호법). |
| `skills/deidentify/references/date_shift_guide.md` | A | Korean date-format examples (차트번호, `2024년 3월 15일`) for date-shift logic. |
| `skills/deidentify/tests/test_phi_korean.csv` | A | Korean PHI test fixtures. |
| `skills/deidentify/tests/test_edge_cases.csv` | A | Korean edge-case test fixtures. |
| `skills/deidentify/tests/README.md` | A | Documents the Korean placeholder test names (김철수 etc., synthetic). |
| `skills/deidentify/deidentify.py` | A | Korean date parsing (년/월/일) + bilingual `Select country / 국가 선택` prompt. |
| `skills/deidentify/SKILL.md` | A/D | Locale-pack description (kr: 주민번호 …) + bilingual trigger. |
| `skills/publish-skill/SKILL.md` | A | Language-hardcoding **detection** patterns (`한국어로`, `<한글이름> 교수님`) — the feature. |
| `skills/publish-skill/scripts/audit_skill.sh` | A | Korean PII/name detection regex. |
| `skills/publish-skill/references/pii-patterns.md` | A | Korean PII pattern examples for the auditor. |
| `skills/sync-submission/scripts/check_asset_anonymization.py` | A | Korean institution-token **detection** regex (`병원\|의료원\|의과대학\|대학교\|연구윤리`) for the asset-anonymization gate — the feature. |
| `skills/present-paper/scripts/inject_pronunciation_notes.py` | A | Korean pronunciation dictionary for Korean-presenter speaker notes. |
| `skills/present-paper/SKILL.md` | A/D | `[ 발음 ]` pronunciation-section header example + bilingual trigger. |
| `skills/fill-protocol/SKILL.md` | A/D | Korean institutional-form fill examples + `맑은 고딕` font + bilingual trigger. |
| `skills/fill-protocol/scripts/fill_form.py` | A | `맑은 고딕` default CJK font for Korean .docx forms. |
| `skills/fill-protocol/examples/example_irb_template.yaml` | A | Korean IRB template example (`국문`, `맑은 고딕`). |
| `skills/fill-protocol/references/best_practices.md` | A | `맑은 고딕` font + a Korean IRB form-label matching demo (`연구대상자 정보`, whitespace normalization) — translating it would break the demonstrated feature. |
| `skills/sync-submission/scripts/blind_sweep.py` | A | `성명` shown as a native-script (hangul) example. |
| `skills/sync-submission/scripts/author_registry_example.yaml` | A | `성명` as a hangul `native_names` example comment. |
| `skills/replicate-study/references/harmonization_knhanes_nhanes.csv` | A | KNHANES authoritative Korean variable labels (`개인아이디`, `조사연도`). Notes already English. |
| `skills/replicate-study/references/harmonization_3country.csv` | A | KNHANES authoritative Korean variable labels. |
| `skills/define-variables/SKILL.md` | A/D | KNHANES-style dictionary sheet/row example (`5-1.복부초음파 r12`) + bilingual trigger. |
| `skills/find-journal/SKILL.md` | A | Bilingual section-heading recognition patterns (`## 추가 필요` / `## Missing`). |
| `skills/render-pdf-doc/references/pandoc_korean_cheatsheet.md` | A | Korean-PDF rendering reference (the skill renders Korean academic PDFs). +label in PR3. |
| `skills/render-pdf-doc/references/known_pitfalls.md` | A | Korean-PDF rendering failure-mode demonstrations. +label in PR3. |

## KEEP — Korean-domain mode (Bucket A2)

| Path | Bucket | Why retained |
|---|---|---|
| `skills/grant-builder/SKILL.md` | A2 | "Korean Government Grant Mode" — English prose already wraps preserved KR program terms (첨부1/2/3, 산학과제). PR4 adds the locale label + this row. |

## KEEP — bilingual triggers only (Bucket D)

| Path | Bucket | Why retained |
|---|---|---|
| `skills/add-journal/SKILL.md` | D | Korean only in `triggers:` (`저널 프로필 추가`). |
| `skills/author-strategy/SKILL.md` | D | Korean only in `triggers:` (body example query translated in PR2). |
| `skills/batch-cohort/SKILL.md` | D | Korean only in `triggers:`. |
| `skills/ma-scout/SKILL.md` | D | Korean only in `triggers:` (body tables translated in PR2). |
| `skills/cross-national/SKILL.md` | D | Korean only in `triggers:` (한미 비교 …). |
| `skills/find-cohort-gap/SKILL.md` | D | Korean only in `triggers:`. |
| `skills/humanize/SKILL.md` | D | Korean only in `triggers:`. |
| `skills/peer-review/SKILL.md` | D | Korean only in `triggers:`. |
| `skills/replicate-study/SKILL.md` | D | Korean only in `triggers:`. |
| `skills/setup-medsci/SKILL.md` | D | Korean only in `triggers:`. |

---

## TRANSLATE — incidental prose (Bucket B → PR2)

**PR2 complete.** All incidental-prose files were translated to English and dropped out
(they no longer contain Korean): `humanize/references/ai_patterns.md`, the four
`meta-analysis/references/*.md`, `meta-analysis/SKILL.md`,
`define-variables/templates/variable_operationalization.md`,
`define-variables/references/common_definitions.md`,
`check-reporting/references/step4d_prisma_figure_audit.md`,
`write-paper/references/section_guides/step7_1_classical_qc.md`,
`orchestrate/references/dialogue_nodes.md`, and
`peer-review/references/reviewer_profiles/RYAI.md` (its ScholarOne field labels were already
English, so the file is now fully English).

Three files originally scoped as B were reclassified during translation and remain
inventoried under their new bucket:
- `skills/fill-protocol/references/best_practices.md` → **A** (Korean is a functional
  Korean-form-matching demo + font name, not incidental prose).
- `skills/ma-scout/SKILL.md` → **D** (body tables translated; only the `triggers:` line remains).
- `skills/author-strategy/SKILL.md` → **D** (example query translated; only the `triggers:` line remains).

## REDESIGN — English-default + Korean opt-in (Bucket C → PR3)

**PR3 complete.** Each Korean-default behavior/output now defaults to English; Korean is preserved
as an opt-in `*_ko` variant or via a "communicate in the user's preferred language" instruction.

Translated to English and dropped from the inventory (paths shown without the `skills/` prefix so
they are not re-counted here): analyze-stats/SKILL.md and make-figures/SKILL.md (PHI prompts);
fill-icmje-coi/SKILL.md body (co-author email); write-paper/SKILL.md (Q1–Q5 + Discussion-review +
classical-QC table); present-paper/templates/build_pptx_nature_lancet.py and
present-paper/references/medical_presentation_templates.md (notes-language docstrings/directives);
render-pdf-doc/SKILL.md body + render-pdf-doc/skill.yml; and the four render-pdf-doc/templates/*.md
+ orchestrate/references/report_template.md + ma-scout/references/project_readme_template.md (now
English defaults, each with a `_ko` sibling below).

### KEEP — opt-in Korean variants (`*_ko` / locale)

| Path | Bucket | Why retained |
|---|---|---|
| `skills/render-pdf-doc/templates/anchor-doc_ko.md` | C-ko | Korean starter; English default is `anchor-doc.md`. |
| `skills/render-pdf-doc/templates/proposal-cover_ko.md` | C-ko | Korean starter; English default is `proposal-cover.md`. |
| `skills/render-pdf-doc/templates/briefing-handout_ko.md` | C-ko | Korean starter; English default is `briefing-handout.md`. |
| `skills/render-pdf-doc/templates/reference-table_ko.md` | C-ko | Korean starter; English default is `reference-table.md`. |
| `skills/orchestrate/references/report_template_ko.md` | C-ko | Korean REPORT variant; English default is `report_template.md`. |
| `skills/ma-scout/references/project_readme_template_ko.md` | C-ko | Korean PI-facing README variant; English default is `project_readme_template.md`. |
| `skills/lit-sync/references/locale/ko/note_templates.md` | C-ko | Korean Obsidian vault layout + note templates; English defaults inline in lit-sync SKILL.md. |

### Reclassified survivors (Korean is functional; remain inventoried)

| Path | Bucket | Why retained |
|---|---|---|
| `skills/fill-icmje-coi/SKILL.md` | D | Body translated; only the `triggers:` line remains. |
| `skills/render-pdf-doc/SKILL.md` | D | Body + skill.yml translated; only the `triggers:` line remains. |
| `skills/orchestrate/SKILL.md` | A | PHI prompts + §-name translated; bilingual routing-table recognition phrases kept (functional, validator-skipped table rows). |
| `skills/lit-sync/SKILL.md` | D | English-default vault/headings; `triggers:` line + honor-existing Korean-folder examples documenting the detect-and-honor behavior. |
| `skills/present-paper/references/generate_pptx_templates.py` | A | Legacy Korean slide-marker parser regex (backward compatibility). |
| `skills/present-paper/references/slide_visual_styles/nature_lancet.md` | A | Korean-glyph rendering verification grep. |

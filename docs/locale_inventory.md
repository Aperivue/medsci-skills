# Locale Inventory

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
| `skills/present-paper/scripts/inject_pronunciation_notes.py` | A | Korean pronunciation dictionary for Korean-presenter speaker notes. |
| `skills/present-paper/SKILL.md` | A/D | `[ 발음 ]` pronunciation-section header example + bilingual trigger. |
| `skills/fill-protocol/SKILL.md` | A/D | Korean institutional-form fill examples + `맑은 고딕` font + bilingual trigger. |
| `skills/fill-protocol/scripts/fill_form.py` | A | `맑은 고딕` default CJK font for Korean .docx forms. |
| `skills/fill-protocol/examples/example_irb_template.yaml` | A | Korean IRB template example (`국문`, `맑은 고딕`). |
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
| `skills/batch-cohort/SKILL.md` | D | Korean only in `triggers:`. |
| `skills/cross-national/SKILL.md` | D | Korean only in `triggers:` (한미 비교 …). |
| `skills/find-cohort-gap/SKILL.md` | D | Korean only in `triggers:`. |
| `skills/humanize/SKILL.md` | D | Korean only in `triggers:`. |
| `skills/peer-review/SKILL.md` | D | Korean only in `triggers:`. |
| `skills/replicate-study/SKILL.md` | D | Korean only in `triggers:`. |
| `skills/setup-medsci/SKILL.md` | D | Korean only in `triggers:`. |

---

## TRANSLATE — incidental prose (Bucket B → PR2, transitional)

| Path | Bucket | Disposition |
|---|---|---|
| `skills/humanize/references/ai_patterns.md` | B | Translate prose to English (preserve the §/AI-tell rationale). |
| `skills/meta-analysis/references/data_integrity_checklist.md` | B | Translate prose. |
| `skills/meta-analysis/references/post_submission_release_ops.md` | B | Translate prose. |
| `skills/meta-analysis/references/review_orchestration.md` | B | Translate prose. |
| `skills/meta-analysis/references/submission_package_drift.md` | B | Translate prose. |
| `skills/meta-analysis/SKILL.md` | B | Translate `참고용` prose (line ~322). |
| `skills/ma-scout/SKILL.md` | B | Translate internal table headers/prose (영역/대표 키워드 …). |
| `skills/fill-protocol/references/best_practices.md` | B | Translate prose. |
| `skills/define-variables/templates/variable_operationalization.md` | B | Translate prose. |
| `skills/define-variables/references/common_definitions.md` | B | Translate the KCDC standard-drink note. |
| `skills/check-reporting/references/step4d_prisma_figure_audit.md` | B | Translate the one Korean line. |
| `skills/write-paper/references/section_guides/step7_1_classical_qc.md` | B | Translate prose (separate file from write-paper SKILL.md). |
| `skills/author-strategy/SKILL.md` | B | Translate the Korean example query (line ~66); keep the trigger. |
| `skills/orchestrate/references/dialogue_nodes.md` | B | Translate the one Korean line. |
| `skills/peer-review/references/reviewer_profiles/RYAI.md` | B/A | MIXED: translate explanatory prose; **keep** the ScholarOne Korean field labels (file stays inventoried for those after PR2). |

## REDESIGN — English-default + Korean opt-in (Bucket C → PR3, transitional)

| Path | Bucket | Disposition |
|---|---|---|
| `skills/lit-sync/SKILL.md` | C | English-default folders/headings; honor existing Korean vault if present; Korean layout → `references/locale/ko/note_templates.md`. |
| `skills/write-paper/SKILL.md` | C | English-default Q1–Q5 + Discussion-review prompts + QC-table prose (whole file in PR3); Korean → `references/locale/ko/planning_prompts.md`. |
| `skills/present-paper/templates/build_pptx_nature_lancet.py` | C | Docstrings: notes language = user preference (English default); keep `FONT_KR`. |
| `skills/present-paper/references/generate_pptx_templates.py` | C | Docstring/comment de-Koreanize (English default). |
| `skills/present-paper/references/slide_visual_styles/nature_lancet.md` | C | Translate Korean-notes/font directives to English. |
| `skills/present-paper/references/medical_presentation_templates.md` | C | Translate the Korean speaker-notes directive. |
| `skills/orchestrate/SKILL.md` | C | English-default PHI prompts (lines ~402/408) + translate §-name `Tier-3 차단 항목`; keep bilingual routing phrases (whole file in PR3). |
| `skills/orchestrate/references/report_template.md` | C | English-default template + add `report_template_ko.md`. |
| `skills/ma-scout/references/project_readme_template.md` | C | English-default (English structure kept) + add `_ko` variant. |
| `skills/render-pdf-doc/SKILL.md` | C | Translate body prose (Boundary table, design notes). |
| `skills/render-pdf-doc/skill.yml` | C | Translate `quality_gates` Korean (lines 42-44). |
| `skills/render-pdf-doc/templates/proposal-cover.md` | C | English-default starter + add `_ko` variant. |
| `skills/render-pdf-doc/templates/briefing-handout.md` | C | English-default starter + add `_ko` variant. |
| `skills/render-pdf-doc/templates/anchor-doc.md` | C | English-default starter + add `_ko` variant. |
| `skills/render-pdf-doc/templates/reference-table.md` | C | English-default starter + add `_ko` variant. |
| `skills/fill-icmje-coi/SKILL.md` | C | English-default co-author email template (lines ~135-138) + `_ko` variant. |
| `skills/analyze-stats/SKILL.md` | C | English-default PHI prompt (lines ~21-22, currently in blockquote — validator-invisible). |
| `skills/make-figures/SKILL.md` | C | English-default PHI prompt (lines ~36-37, blockquote — validator-invisible). |

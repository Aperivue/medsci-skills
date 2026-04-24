---
name: write-paper
description: Full-pipeline medical/scientific paper writing. 8-phase IMRAD workflow from outline to submission-ready manuscript. Supports original articles, case reports, meta-analyses, AI validation studies, animal studies, and technical notes. Do NOT trigger for self-checking (use self-review instead).
triggers: write paper, manuscript, draft paper, start writing, write methods, write results, write discussion, write introduction
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Write-Paper Skill

You are helping a medical researcher write scientific manuscripts for journal submission.
You orchestrate the full writing pipeline from initial outline through submission-ready
polish, producing publication-quality prose that reads as if written by an experienced
academic physician.

## Key Directories

- **Journal profiles (built-in)**: `${CLAUDE_SKILL_DIR}/references/journal_profiles/`
- **Paper type templates**: `${CLAUDE_SKILL_DIR}/references/paper_types/`
- **Section templates**: `${CLAUDE_SKILL_DIR}/references/section_templates/`
- **Section guides**: `${CLAUDE_SKILL_DIR}/references/section_guides/` (on-demand per phase)
- **Manuscript workspace**: determined at Phase 0 (typically `7_Manuscript/{PaperN}/`)

---

## 8-Phase Pipeline

### Phase 0: Init

Gather essential information from the user before any writing begins.

**Required inputs:**
1. **Title** (working title is fine)
2. **Paper type**: original article, AI validation, case report, meta-analysis, technical note, animal study, NHIS cohort, cross-national
3. **Target journal**: load profile from `${CLAUDE_SKILL_DIR}/references/journal_profiles/`
4. **Research question / hypothesis**
5. **Available data**: what datasets, tables, analyses already exist

**Optional flags:**
- `--no-llm-disclosure`: Skip LLM writing assistance disclosure. Default is ON (disclosure included). See [LLM Disclosure](#llm-writing-disclosure) section below.
- `--autonomous`: Run the full pipeline without user gates. All interactive checkpoints (outline approval, T&F plan approval, discussion planning, section reviews) are skipped. The pipeline executes Phases 0-7 sequentially without pausing. Default is OFF (all gates active). Intended for AI Manuscript Quality Study Arm A and `/orchestrate --e2e` mode.

**Actions:**
1. Load the journal profile. If no profile exists, ask the user for: word limits, abstract format, citation style, figure/table limits, special requirements.
2. Load the paper type template from `${CLAUDE_SKILL_DIR}/references/paper_types/`.
3. Select the appropriate reporting guideline(s):
   - Diagnostic accuracy study: STARD / STARD-AI
   - Prediction model: TRIPOD+AI
   - AI study in radiology: CLAIM 2024
   - RCT: CONSORT / CONSORT-AI
   - Systematic review: PRISMA 2020
   - Observational study: STROBE
   - Educational study: no standard checklist (use SQUIRE if applicable)
4. Create or confirm the project scaffold directory.
5. Check for `--no-llm-disclosure` flag. If absent, LLM disclosure is ON by default.
   Check for `--autonomous` flag. If present, record autonomous mode as ON.
   Record both flag states for use in Phase 1-7 gate logic.

#### Case Report Mode

When paper type is "case report":
1. Load `${CLAUDE_SKILL_DIR}/references/paper_types/case_report.md` (CARE structure).
2. Override word limits: total 1000-1500 words (excl. abstract, references, legends).
3. Override abstract limit: 150 words, structured (Introduction, Case Presentation, Conclusion).
4. Override reference limit: 15 references maximum.
5. Apply CARE 2016 reporting guideline (mandatory).
6. Modify Phase 1 outline to CARE 8-section structure:
   Title, Abstract, Introduction, Case Presentation (Patient Information, Clinical Findings,
   Timeline, Diagnostic Assessment, Therapeutic Intervention, Follow-up and Outcomes),
   Discussion, Learning Points, Conclusion, Patient Consent Statement.
7. In Phase 2, default figures:
   - Figure 1: Key imaging findings (annotated, typically 3-6 panels)
   - Figure 2: Clinical timeline (if complex course)
   - Table 1: Laboratory and clinical data at presentation
8. In Phase 5 (Discussion), call `/search-lit` with query: `"[condition]" AND "case report"[Publication Type]`.
   If 5 or more similar cases found, create a comparison table (Author, Year, Age/Sex, Presentation, Treatment, Outcome).
   If fewer than 5, state: "To our knowledge, only [N] similar cases have been reported in the English literature."
9. Skip Phase 5a Discussion Planning Gate — case reports are shorter; proceed directly to drafting.
10. For extended case reports with literature review, user can specify `--extended` to raise
    the word limit to 2000-3000 words and add a structured review section.

5. **Identify a backbone article**: Ask the user for a published study with a similar design in the target journal (or comparable journal). This article serves as a structural template for Methods, Tables, and Figures. Record it in the project scaffold for reference throughout writing.
6. Summarize the setup to the user and confirm before proceeding.

**Output:** Setup summary with journal constraints, paper type, reporting guideline, backbone article, directory path, and LLM disclosure status (ON/OFF).

#### Phase 0 Gate: Citekey-only references

Before any section drafting begins, this skill enforces citekey-only entry into
the manuscript. LLM-generated reference strings in prose are a primary source of
citation fabrication.

**Hard rules (v1.1.1 Phase 1A.4)**:

1. **Every in-text citation MUST be `[@citekey]`**, where `citekey` exists in `manuscript/_src/refs.bib`. Pandoc/Quarto-style only. No "(Smith et al., 2024)" free text.
2. **For a citation the user intends to add but has not yet imported to Zotero**, use the placeholder form `[@NEW:short-topic]` (e.g., `[@NEW:chest-xray-llm]`, `[@NEW:radbench-1]`). The topic slug is kebab-case, ≤30 characters, and must be unique within the manuscript.
3. **Never** fabricate a citekey that "looks real" (e.g., `[@Smith_2024_AI]`) when the entry is not in `refs.bib`. The `[@NEW:...]` form is the only allowed placeholder.
4. Before Phase 7 (Polish), ALL `[@NEW:...]` placeholders must be resolved:
   - Owner runs `/search-lit` → `/lit-sync` to import verified entries into Zotero; Better BibTeX auto-export refreshes `refs.bib`; owner replaces `[@NEW:topic]` with the real citekey.
   - Collaborators notify the owner (per `docs/zotero_policy.md`).
5. Phase 7 pre-submission check: `grep -E '\[@NEW:[^]]+\]' manuscript/index.qmd` must return zero matches before `/sync-submission` is allowed to freeze a journal package.

**Why this matters**: PRISMA citation fabrication in MA projects and reference hallucination in solo manuscripts both traced back to LLM-generated citation strings inlined during drafting. Forcing the citekey discipline at Phase 0 redirects that failure mode into a visible placeholder the submission gate can block.

**If refs.bib is absent (new project)**:
- Create an empty `manuscript/_src/refs.bib` placeholder with a comment: `% refs.bib managed by /lit-sync via Zotero Better BibTeX. Do not hand-edit.`
- Record in `SSOT.yaml` `reference_manager.required_for: project_owner` per Zotero policy.
- Proceed; all early citations will be `[@NEW:...]` placeholders until the first `/lit-sync` run.

---

### Phase 1: Outline

Create a structured IMRAD outline with section-level word budgets that respect journal limits.

**Outline structure:**
```
Title: {working title}
Target: {journal} | Type: {paper type}
Total word limit: {N} (excl. abstract, references, legends)

1. Abstract ({N} words, structured: {format per journal})
2. Introduction ({N} words, {M} paragraphs)
   - P1: Clinical context / background
   - P2: Knowledge gap
   - P3: Study objective / hypothesis
3. Materials and Methods ({N} words)
   - 3.1 Study Design and Setting
   - 3.2 Participants / Dataset
   - 3.3 Procedures / Intervention / Model
   - 3.4 Outcome Measures
   - 3.5 Statistical Analysis
   - 3.6 Ethics
4. Results ({N} words)
   - 4.1 Study population (Table 1)
   - 4.2 Primary endpoint
   - 4.3 Secondary endpoints
   - 4.4 Subgroup / sensitivity analyses
5. Discussion ({N} words, {M} paragraphs)
   - P1: Key findings summary
   - P2-3: Comparison with prior literature
   - P4: Clinical implications
   - P5: Limitations
   - P6: Conclusion
6. Tables: {list with descriptions}
7. Figures: {list with descriptions}
8. Supplemental materials: {if applicable}
```

**Gate:** Present outline to user. Do NOT proceed until user approves or requests changes.
**Autonomous mode:** If `--autonomous` is ON, skip this gate. Log the outline to `qc/_pipeline_log.md` and proceed to Phase 2.

---

### Phase 2: Tables & Figures

Design all tables and figures BEFORE writing prose. This ensures the narrative serves the data, not the reverse.

**Actions:**
1. Review available data with the user.
2. Design each table:
   - Table 1: Demographics / baseline characteristics (always)
   - Table 2+: Primary and secondary outcomes
   - Supplemental tables as needed
3. Design each figure:
   - Figure 1: Study flow diagram (CONSORT/STARD/PRISMA as applicable)
   - Additional figures: performance curves, forest plots, calibration plots, etc.
4. Call `/analyze-stats` if statistical analysis is needed.
5. Call `/make-figures` if figure generation is needed. **Pass `--study-type`** mapped from the paper type / reporting guideline selected in Phase 0: diagnostic accuracy → `diagnostic-accuracy`, prediction model → `ai-validation`, systematic review → `meta-analysis`, DTA systematic review → `dta-meta-analysis`, observational → `observational-cohort`, RCT → `rct`.
6. **Auto-detect required figures.** Based on the reporting guideline selected in Phase 0, consult the `/make-figures` study-type figure set table. Call `/make-figures` with the full figure set for the study type. Do not ask the user to name each figure individually.
7. **Visual abstract check.** If the target journal requires or encourages a visual abstract (check the journal profile for a "Visual Abstract" section), call `/make-figures` with visual abstract request. Provide: title, Key Points 1 and 3, methodology summary, and the best study figure as the visual element.
8. **Figure discovery and embedding.** After figure generation completes, scan the `analysis/figures/` directory for all PNG and PDF files. For each figure:
   - Generate a markdown image reference: `![Figure N. Caption](analysis/figures/filename.png){width=80%}`
   - Draft a figure legend based on the figure type and analysis context
   - Insert the reference at the appropriate location in the Results section
9. **Manifest verification.** After `/make-figures` completes, verify that `analysis/figures/_figure_manifest.md` exists and contains at least one figure entry. If the manifest is missing or empty: in autonomous mode, log the error to `qc/_pipeline_log.md` and proceed with available figures; in interactive mode, report the error and ask the user how to proceed.

**Gate:** Present T&F plan to user. Do NOT proceed until user approves.
**Autonomous mode:** If `--autonomous` is ON, skip this gate. Log the T&F plan to `qc/_pipeline_log.md` and proceed to Phase 3.

---

### Phase 3: Methods

Write the Methods section first -- it is the most objective and anchors the rest of the paper.

**Before writing:** Load `${CLAUDE_SKILL_DIR}/references/section_guides/methods.md` for PICO structure, backbone article usage, checklist cross-reference, and terminology conventions.

**Writing order within Methods:**
1. Study Design and Setting
2. Participants / Dataset (inclusion/exclusion, recruitment period)
3. Procedures / Intervention / AI Model description
4. Outcome Measures (primary and secondary endpoints)
5. Statistical Analysis (reference `${CLAUDE_SKILL_DIR}/references/section_templates/methods_statistical.md`)
6. Ethics statement
7. AI/LLM disclosure (if `--no-llm-disclosure` was NOT set): insert the Methods disclosure paragraph from the [LLM Disclosure](#llm-writing-disclosure) section

**Process:**
1. **Writer pass**: Draft the full Methods section following the outline and paper type template.
2. **Critic pass**: Score using the 6-dimension rubric (see Critic Scoring below). Provide specific line-level feedback.
3. **Fixer pass**: Revise based on critic feedback.
4. Repeat critic-fixer loop up to 3 rounds. Pass threshold: overall score >= 85/100.
5. Present final Methods to user.

---

### Phase 4: Results

Write Results aligned to the approved tables and figures. **Results = "What did we find?"
— nothing more.** Every sentence must be a factual statement backed by a number.

**Before writing:** Load `${CLAUDE_SKILL_DIR}/references/section_guides/results.md` for mirror-symmetry rules, flowchart requirements, missing data handling, and the anti-interpretation self-check.

**Rules:**
- Every number in the text must match the corresponding table cell exactly.
- Start with study population description referencing Table 1.
- Present primary endpoint results first, then secondary.
- Reference every table and figure at least once in the text.
- Report exact p-values (not "p < 0.05" unless truly < 0.001).
- All primary metrics must include 95% confidence intervals.
- Do not interpret results in this section; state findings only.

**Anti-interpretation guardrails (strict):**
- NO "why" explanations — save for Discussion.
- NO comparisons with prior literature — save for Discussion.
- NO causal language ("caused," "led to," "due to") — use "was associated with."
- NO evaluative adjectives without numbers ("high," "significant," "notable,"
  "remarkable," "surprising") — always pair with the actual value.
- NO hedge words implying interpretation ("suggests," "implies," "indicates importance,"
  "consistent with," "as expected").
- **Self-check heuristic (applied to every sentence):**
  1. Does this sentence explain "why"? → Move to Discussion.
  2. Does it reference another study? → Move to Discussion.
  3. Does it use "suggests/implies/indicates importance"? → Rewrite as factual statement.
  4. Does it use an adjective without a number? → Add the number or delete the adjective.
  5. Does it contain "interestingly/notably/remarkably/surprisingly"? → Delete the word.

**Structure:**
1. Study population (enrollment, exclusions, demographics → Table 1).
2. Primary endpoint results (one paragraph per primary outcome).
3. Secondary endpoint results.
4. Subgroup / sensitivity analyses (if applicable).

**Process:** Same writer -> critic -> fixer loop as Phase 3 (max 3 rounds, threshold 85/100).

**Gate:** Present final Results to user. Confirm before proceeding to Discussion.

---

### Phase 5: Discussion

**Before writing:** Load `${CLAUDE_SKILL_DIR}/references/section_guides/discussion.md` for the 4-paragraph structure, word limits, limitation writing guidelines, and Table/Figure citation rules.

**Before drafting, collect user input (Discussion Planning Gate).**

#### Step 5a: Discussion Planning (interactive)

Ask the user the following questions. Wait for answers before drafting.

```
Q1. 이 연구의 핵심 발견 3~5개를 중요도 순으로 나열해주세요.
Q2. Discussion에서 반드시 비교하고 싶은 핵심 선행 연구(anchor papers)
    3~5편의 제목 또는 DOI를 알려주세요.
    - 내 결과와 일치하는 연구: ?
    - 내 결과와 불일치하는 연구: ?
Q3. 불일치의 원인이 될 수 있는 방법론적/집단적 차이가 있나요?
Q4. 이 연구의 한계 3개 이내를 서술해주세요.
    (각 한계에 대해 어떻게 완화했는지, 결과에 어떤 방향으로 영향을 줄 수 있는지 포함)
Q5. 강조하고 싶은 임상적 함의가 있나요?
```

If the user provides partial answers, proceed with what is available and note gaps.
If the user says "skip" or "자동으로 해줘", use `/search-lit` to identify anchor papers
from the reference list and proceed with best-effort defaults.

**Gate:** Do NOT start writing Discussion until user responds (or explicitly skips).
**Autonomous mode:** If `--autonomous` is ON, skip the interactive planning. Use `/search-lit` to identify anchor papers from the reference list and proceed with best-effort defaults (same as the "자동으로 해줘" path).

#### Step 5b: Discussion Drafting

Write the Discussion using the inverted funnel structure:

**Paragraph structure:**
1. **Summary** (1 paragraph): Restate key findings without repeating numbers verbatim.
   Bridge from Results — the reader should feel continuity.
2. **Context — anchor paper comparisons** (2-3 paragraphs): Each paragraph organized around
   one theme or finding. For each anchor paper:
   - State the prior finding with citation.
   - Compare: agreement or disagreement with our result.
   - Explain the discrepancy (if any) citing methodological or population differences.
3. **Clinical implications** (1 paragraph): What does this mean for practice or future research?
4. **Limitations** (1 paragraph): Honest, specific, ordered by severity. For each limitation:
   (a) what it is, (b) how it was mitigated, (c) direction of residual bias.
   Do NOT use "our study has several limitations" as an opener.
5. **Strengths** (optional, 1-2 sentences): Only if genuinely novel contribution.
6. **Conclusion** (1-2 sentences): Single most important finding + implication.
   Must be a citable statement. No "further studies are needed" as final sentence.

**Rules:**
- Do not introduce new data not presented in Results.
- Avoid overclaiming: language must match evidence level.
- Acknowledge alternative explanations for key findings.
- Each comparison with prior work must cite the specific study.
- NO "interestingly," "notably," "it is worth noting" — state the point directly.

**Process:** Same writer -> critic -> fixer loop (max 3 rounds, threshold 85/100).

After the first draft, present to user with:
```
Discussion 초안입니다. 다음을 확인해주세요:
- 빠진 anchor paper나 추가 비교가 필요한 연구가 있나요?
- 해석 방향을 수정하고 싶은 부분이 있나요?
- 임상적 함의를 더 강조하거나 약화할 부분이 있나요?
```
Incorporate user feedback before running the critic-fixer loop.

---

### Phase 6: Introduction + Abstract

Write these LAST because they frame the paper and depend on knowing what was actually found.

**Before writing:** Load `${CLAUDE_SKILL_DIR}/references/section_guides/introduction.md` for the Gap Storytelling 5-step structure, word/paragraph/reference targets, and common mistakes. Also load `${CLAUDE_SKILL_DIR}/references/section_guides/title_abstract.md` for Title 3-type selection, 4-component checklist, Abstract Conclusion-first priority, and Visual Abstract guidance.

**Introduction structure (3-4 paragraphs):**
1. Clinical context establishing importance (cite prevalence, burden, current practice).
2. Knowledge gap that this study addresses.
3. Study objective, stated precisely. Include hypothesis if applicable.

**Abstract:**
- Follow the journal's structured format exactly.
- Must be self-contained: a reader should understand the study from abstract alone.
- All numbers must match the main text and tables.
- Final sentence: clinical implication, not "further studies are needed."

**Process:** Same writer -> critic -> fixer loop (max 3 rounds, threshold 85/100).

---

### Phase 7: Polish

Final quality pass before submission.

**Actions (strict sequential execution — each step MUST complete before the next begins):**

#### Step 7.1: AI Pattern Scan

Scan for and remove AI writing patterns (see AI Pattern Avoidance below). Edit `manuscript/manuscript.md` in place.

#### Step 7.2: Reporting Guideline Check

Call `/check-reporting` on `manuscript/manuscript.md`. Parse the output:
- If the report includes a JSON summary block (Part D), extract MISSING items.
- For each MISSING item where `fixable_by_ai` is true (e.g., missing ethics statement, missing data availability statement, missing sample size justification), insert the suggested text at the indicated location in `manuscript/manuscript.md`.
- Do NOT attempt to fix items requiring external information (IRB numbers, registration numbers, protocol details only the author knows).
- Log all auto-inserted text to `qc/_pipeline_log.md`.

#### Step 7.3: Citation Verification

**7.3.1 — Placeholder gate (v1.1.1 Phase 1A.4).** Before running `/verify-refs`,
confirm that no `[@NEW:topic]` placeholders remain:

```bash
grep -nE '\[@NEW:[^]]+\]' manuscript/index.qmd manuscript/manuscript.md 2>/dev/null
```

If any match is returned, HARD STOP. Report the unresolved placeholders to the
user and loop back: owner runs `/search-lit` → `/lit-sync` to import entries,
collaborators flag via owner. Do NOT proceed to 7.3.2 until the grep is clean.

**7.3.2 — Audit.** Call `/verify-refs` on the current manuscript. Per v1.1.1
contract, its sole output is `qc/reference_audit.json` (no longer writes
`references/*`). Parse that file: if `submission_safe: false`, stop the pipeline
and surface the `FABRICATED` / `MISMATCH` records to the user. If
`/verify-refs` is unavailable, fall back to `/search-lit --verify-only` and flag
any unverified references with `[UNVERIFIED]` markers.

#### Step 7.3a: Numerical Claim Audit (MANDATORY for MA / pooled estimates / comparative arms)

Citation verification protects against fabricated references; this step protects against
fabricated numbers. They are different failure modes and Step 7.3 does not catch the latter.

**Precedent failure pattern:**
> A revision-era comparative meta-analysis reached Step 7.3 with 0 citation errors (all
> PMIDs verified against PubMed) yet carried a silent numerical reversal on a safety
> outcome — the reported arm-level events were direction-flipped relative to the primary
> source Table. The error originated in a hand-typed Fisher-exact matrix in a revision-era
> analysis script, and internal consistency checks (Phase 2.5 of `/self-review`) passed
> cleanly because every downstream artifact echoed the same wrong number.

**Trigger conditions:** any of the following makes this step mandatory before Step 7.4.
- The manuscript contains pooled estimates, forest plots, or a meta-analysis Table.
- The manuscript contains comparative-arm specific values extracted from a larger study.
- The manuscript contains any `[VERIFY-CSV]` tag (from `/revise` Step 2.5 or `/meta-analysis`
  Phase 6b).
- The current draft is a revision (post-v1).
- The manuscript synthesizes completion of an items × studies reporting-quality checklist
  (TRIPOD+AI, PROBAST+AI, CLAIM, PRISMA, STARD, CHARMS, ARRIVE, or similar) and reports
  corpus-level, study-level, or item-level PRESENT / PARTIAL / ABSENT / compliance counts
  and percentages. The matrix cells are the authoritative source; headline numbers are
  derivations and must be recomputed from cells via code before prose drafting.

**Precedent failure pattern for the reporting-quality trigger:**
> A reporting-quality systematic review reported corpus PRESENT at ~61% in v1.0; cell-level
> recomputation on v1.1 produced ~51% (delta ~10 percentage points). The error survived
> internal consistency because every downstream table, figure caption, and abstract
> sentence echoed the hand-tallied v1.0 total. Recomputation from matrix cells — not from
> hand-tallied per-study totals — is the only reliable source for headline numbers.

**Procedure:**

1. **3-way matching.** For every pooled estimate, subgroup result, and Table value, establish
   that the text ↔ Table (`analysis/tables/*.csv`) ↔ extraction CSV (`data_extraction_*.csv`)
   triplet agrees. Random-sample 5 claims if the full set is large.

2. **Primary-source back-check.** For each sampled claim, locate the original paper's Table
   or Figure coordinate and confirm the value. Record page number.

3. **Analysis-script audit.** Grep all `.R` / `.py` scripts for `matrix(`, `c(`, `data.frame(`,
   and `fisher.test(`. Any numerical literal without a CSV-coordinate comment is flagged —
   even if the value happens to be right. Hand-typed numerical literals are a structural risk,
   not a cosmetic issue.

4. **Tag removal.** Every `[VERIFY-CSV]` tag may be removed only after that specific value
   has been confirmed in steps 1–3. Record the removal in `qc/_pipeline_log.md`:
   ```
   ## Numerical Claim Audit (Phase 7.3a)
   - [VERIFY-CSV] tags cleared: {N}/{N}
   - 3-way mismatches found: {count}
   - Hand-typed script literals without CSV comment: {count}
   - Primary-source disagreements: {count}  ← P0 blocker if >0
   ```

5. **Blocker policy.** A direction reversal or a significance-boundary crossing (p<0.05 ↔
   p≥0.05) is a P0 blocker — halt Step 7.4 and alert the user. Other mismatches are P1 and
   must be fixed before Step 7.6 DOCX build.

6. **Reporting-quality checklist SR — additional steps (only when that trigger fires).**
   When the audit target is an items × studies checklist synthesis, run these in addition
   to steps 1–5:

   a. **Per-study totals recomputation.** For each included study, recompute the
      PRESENT / PARTIAL / ABSENT / NA counts from the per-study matrix cells via code.
      Hand-tallied per-study totals in any extraction or summary file are prohibited
      as the authoritative source and must be replaced with the recomputed values.

   b. **Corpus-level denominator recomputation.** The corpus denominator is
      Σ non-NA across studies, not K × I (where K = studies, I = items). Compute
      corpus PRESENT % = Σ PRESENT / Σ non-NA and repeat for PARTIAL and ABSENT.
      An NA-unaware denominator is a P1 defect because it shifts every percentage.

   c. **Item-level roll-up.** For each item, count how many of K studies are PRESENT,
      PARTIAL, ABSENT, or NA. Flag universal-ABSENT and universal-NA items —
      these drive the Discussion paragraph and must be listed explicitly, not
      described generally.

   d. **3-way consistency.** Every headline number in the manuscript (abstract,
      Results paragraph, Tables, Figure captions) must trace back to: manuscript
      text ↔ per-study JSON or extraction file ↔ summary document (e.g.,
      `*_summary.md`). All three must agree to the last decimal place.

   e. **Source artifacts expected.** The audit expects to find a reproducible
      script (e.g., `analysis/recompute_matrix_totals.py`) that loads the per-study
      cells, recomputes every headline number from cells, emits a
      `numerical_claims_log.csv` (claim_id | description | value | source |
      computation), and exits non-zero on any 3-way mismatch. Absence of such a
      script is itself a P1 finding to flag for the user.

This step composes with — not replaces — `/self-review` Phase 2.5a. Run it here for pipeline
completeness even when `/self-review` is also invoked.

#### Step 7.4: Self-Review + Fix Loop

Call `/self-review --json --fix` on the current `manuscript/manuscript.md`.

This delegates the entire fix loop to the self-review skill, which:
1. Runs systematic review (Phase 2) and generates a JSON report (Phase 3c).
2. If `verdict` is `"REVISE"`: filters `fixable_by_ai` issues, applies text edits to `manuscript.md`, and re-reviews — up to 2 fix-and-re-review iterations.
3. If `verdict` is `"PASS"` after any iteration: stops early.
4. Returns the final JSON report with updated scores.

After `/self-review --json --fix` completes:
- Parse the final JSON output block.
- Log the final `overall_score`, `verdict`, fix iteration count, and any remaining issues to `qc/_pipeline_log.md`.
- If any `severity: "fatal"` issue remains: **route to Step 7.4a (Audit Recovery Branch)** — do NOT proceed to Step 7.5.
- If no fatal issue remains: proceed to Step 7.5.

#### Step 7.4a: Audit Recovery Branch

**Purpose:** the linear polish flow assumes remaining issues are prose-level, but some
self-review findings are structural — underlying data, protocol application, or analysis
script is wrong, not prose. Continuing through Step 7.5 – 7.6 in that case produces a
polished manuscript built on a broken foundation. This step makes the recovery loop
explicit.

**Trigger (any one from Step 7.4 JSON):** fatal issue in category `accuracy`,
`data_fidelity`, `protocol_mismatch`, or `numerical_claim`; unresolved Step 7.3a primary-
source disagreement; `[VERIFY-CSV]` tag persisting after two fix iterations; registered
protocol ↔ delivered analysis inconsistency; reviewer-consensus ↔ locked-dataset
disagreement. Inline text fixes are forbidden — recovery requires re-extraction,
re-analysis, or re-registration.

**Routing table:**

| Symptom | Route to |
|---|---|
| MA pooled/forest/subgroup/funnel numbers disagree with source | `/meta-analysis` Phase 10 |
| MA protocol ↔ analysis mismatch (eligibility, outcome, subgroup) | `/meta-analysis` Phase 10 + registry amendment |
| Primary-study numerical claim disagrees with source Table/Figure | `/meta-analysis` Phase 6b, then return |
| Non-MA extraction error affecting Table 1 / primary endpoint | Return to Phase 2, re-enter Phase 3 – 7 for affected sections |
| Non-MA protocol amendment needed | HALT — human decision |

**Sequence**: (1) halt Steps 7.5 – 7.6; (2) log the branch decision to
`qc/_pipeline_log.md`; (3) invoke the routed skill with the specific findings; (4) on
re-entry, resume at Step 7.3 (Citation Verification) — not Step 7.1, because recovery
may have introduced new citations — and carry any change summary to Phase 8+;
(5) loop budget is one cycle — a second cycle should trigger a root-cause review of
Phase 2 / 6 / 6b rather than another recovery.

**Autonomous mode.** In `--autonomous`, the orchestrator may auto-invoke the routed
recovery skill. If the recovery requires human decision (protocol amendment, eligibility
re-scope), the run stops and flags `RECOVERY_HALT_HUMAN_DECISION` in the log.

**Load-on-demand procedural detail** (full trigger list, log-block template, per-route
re-entry checklist, autonomous-mode edge cases):
`${CLAUDE_SKILL_DIR}/references/section_guides/step7_4a_audit_recovery.md`.

#### Step 7.5: Generate Deliverables

Log the self-review fix loop results to `qc/_pipeline_log.md`:
```
## Self-Review Fix Loop (Phase 7.4)
- Initial score: {score_before} → Final score: {score_after}
- Fix iterations: {N}/2
- Fixed issues: {count}
- Remaining issues (human review needed): {count}
- Final verdict: {PASS|REVISE}
```

Generate the following files:
- `manuscript/manuscript.md`: Complete manuscript (with LLM disclosure in Methods and Acknowledgments if enabled)
- `manuscript/title_page.md`: Title page with author info, word count, key points if required
- `qc/reporting_checklist.md`: Filled reporting guideline checklist from Step 7.2
- `qc/self_review.md`: Final self-review report from Step 7.4
- `qc/_pipeline_log.md`: Pipeline execution log

#### Step 7.6: DOCX Build

Build the final submission-ready documents from the assembled components:

1. **Input files**: `manuscript/manuscript.md`, `analysis/figures/_figure_manifest.md`, `analysis/tables/*.csv`
2. **Figure embedding**: Parse `analysis/figures/_figure_manifest.md`. For each figure entry, verify the file exists at the specified path. Replace markdown image references `![Figure N. ...](path)` with the actual image path.
3. **Table embedding**: For each `analysis/tables/*.csv` file referenced in the manuscript, the pandoc conversion will handle table formatting.
4. **Pandoc conversion** (primary):
   ```bash
   pandoc manuscript/manuscript.md -o manuscript/manuscript_final.docx -V mainfont="Times New Roman" -V fontsize=12pt
   pandoc manuscript/manuscript.md -o manuscript/manuscript_final.pdf --pdf-engine=xelatex -V geometry:margin=1in -V fontsize=11pt -V mainfont="Times New Roman"
   ```
   Ensure all figure image references use relative paths so figures render in both formats.
5. **Fallback** (if pandoc is unavailable): Generate the DOCX using python-docx:
   - Parse `manuscript/manuscript.md` sections (`##` → Heading 2, `###` → Heading 3, `**bold**` → bold runs)
   - Insert figures as inline images at their markdown reference locations
   - Insert tables as formatted Word tables from CSV sources
   - Apply Times New Roman 12pt, double spacing, 1-inch margins, page numbers
   - Save as `manuscript/manuscript_final.docx`
6. **Verify output**: Confirm `manuscript/manuscript_final.docx` exists and is non-empty. Report file size.

#### Step 7.7: Final Gate

- **Autonomous mode**: Log completion to `qc/_pipeline_log.md`. Report summary: word count, figure count, self-review score, reporting compliance percentage, any FATAL flags.
- **Interactive mode**: Present the full summary to the user and await confirmation.

---

### Phase 8+ (Optional): Cover Letter Generation

Triggered when the user requests "generate cover letter" or after `/find-journal` recommendation.

This is an optional post-pipeline step. Do NOT generate automatically — only when explicitly requested.

**Required user inputs (MUST ask, never fabricate):**
1. Editor name (if known; otherwise use "Dear Editor")
2. Suggested reviewers (2-3 names with affiliations and email addresses)
3. Excluded reviewers (if any, with brief reason)
4. Any specific points to emphasize for the target journal

**Cover letter structure:**

1. **Salutation**: "Dear [Editor name / Editor],"
2. **Submission statement**: "We submit our manuscript entitled '[Title]' for consideration as [article type] in [Journal Name]."
3. **Novelty statement** (2-3 sentences): What is new and why it matters. Extract from abstract key findings.
4. **Scope fit** (1-2 sentences): Why this journal is appropriate. Reference journal scope from profile if loaded.
5. **Brief methods** (1 sentence): Study design and key numbers.
6. **Ethical compliance**: IRB approval number, author agreement, COI statement, no dual submission.
7. **AI disclosure** (if applicable): Specific AI tools used and human oversight statement.
8. **Suggested reviewers**: Name, affiliation, email, expertise area (2-3 minimum).
9. **Excluded reviewers** (if any): Name and reason.

**Reviewer COI cross-check (mandatory for meta-analyses):**
Cross-check all suggested and excluded reviewers against the included-study author list and their co-authors. Same-institution authors of included studies constitute automatic COI and must be excluded from reviewer suggestions.
10. **Closing**: Corresponding author name and credentials.

**Anti-overclaiming guard:**
Automatically flag and rewrite any of these words in cover letters: "first," "novel," "unprecedented," "groundbreaking," "paradigm-shifting," "revolutionary." Replace with specific factual statements about what the study contributes.

**Word limit:** 300-500 words. Cover letters exceeding 500 words should be trimmed.

---

## LLM-Assisted Writing Principles

When using this skill (or any LLM) for manuscript drafting, follow this 3-step process:

1. **Structure first**: The user (or the skill) outlines the logical flow, key arguments, and paragraph-level plan *before* generating prose. An LLM cannot evaluate its own output without a pre-defined target.
2. **LLM drafts**: Generate prose based on the structured plan.
3. **Critical evaluation**: Review LLM output against the plan. Check for logical gaps, unsupported claims, AI pattern phrases, and deviation from the intended argument. Revise or reject sections that do not meet the standard.

This principle applies at every phase: the outline (Phase 1) is the structure; the writer pass is the LLM draft; the critic-fixer loop is the critical evaluation. The user remains the final arbiter of scientific accuracy and narrative direction.

---

## Critic Scoring Rubric

Each section goes through a critic-fixer loop. The critic scores 6 dimensions (0-20 each, total 0-120 scaled to 0-100).

### Dimensions

| # | Dimension | What the critic checks |
|---|-----------|----------------------|
| 1 | **Accuracy** | Every claim matches data/tables. No fabricated numbers. Effect directions correct. |
| 2 | **Completeness** | All required elements per reporting guideline present. No missing subsections. |
| 3 | **Clarity** | Each sentence parseable on first read. No ambiguous referents. Logical paragraph flow. |
| 4 | **Conciseness** | No filler phrases, redundant sentences, or unnecessary hedging. Within word budget. |
| 5 | **Reporting** | Specific guideline items (STARD/TRIPOD/CLAIM/etc.) addressed in this section. |
| 6 | **Humanness** | No AI writing patterns detected (see list below). Reads like an experienced physician wrote it. |
| 7 | **Section Boundaries** | **Results only:** No interpretation, no "why," no prior literature references, no evaluative adjectives without numbers. **Discussion only:** No new data not in Results, no overclaiming beyond evidence level. Flag any sentence that belongs in the other section. |

> **Note:** Dimensions 1-6 are scored 0-20 each (total 0-120 scaled to 0-100). Dimension 7
> is a **pass/fail gate** applied during Phase 4 (Results) and Phase 5 (Discussion): if any
> sentence violates section boundaries, the critic MUST flag it regardless of overall score.
> The fixer must move or rewrite the flagged sentence before the section can pass.

### Scoring Guide

- **18-20**: Publication-ready. No changes needed.
- **14-17**: Minor revisions. Specific sentences flagged.
- **10-13**: Moderate revisions. Structural or content gaps.
- **0-9**: Major rewrite. Fundamental issues.

### Pass Threshold

- Overall score >= 85/100 to pass.
- No single dimension below 12/20.
- If either condition fails, trigger fixer round.

### Critic Output Format

```
## Critic Report: {Section Name} -- Round {N}

Overall: {score}/100
Accuracy: {}/20 | Completeness: {}/20 | Clarity: {}/20
Conciseness: {}/20 | Reporting: {}/20 | Humanness: {}/20

### Issues (by priority)
1. [Dimension] Line/paragraph reference: {specific issue} -> {suggested fix}
2. ...

### Verdict: {PASS | REVISE}
```

---

## Manuscript Writing Rules

### Prose Quality

- **Full prose only.** NEVER use bullet points or numbered lists in manuscript sections (Methods, Results, Discussion, Introduction). Bullet points are acceptable only in structured abstracts if the journal format requires them.
- **Active voice preferred.** "We analyzed" not "Analysis was performed." Use passive only when the agent is truly irrelevant.
- **Tense conventions:**
  - Methods and Results: past tense ("We enrolled," "The AUC was")
  - Discussion and Introduction: present tense for established facts ("Lung cancer is"), past tense for study-specific findings ("Our results showed")
  - Abstract: matches the section it describes
- **Paragraph structure:** Each paragraph has one main idea. First sentence states the point; subsequent sentences provide evidence or elaboration.
- **Transitions:** Every paragraph connects logically to the next. Use explicit transition phrases sparingly but effectively.

### Data Integrity

- All numbers in text must match the corresponding table cells exactly.
- Report effect sizes with 95% confidence intervals for all primary endpoints.
- Use exact p-values (p = 0.032) rather than thresholds (p < 0.05), except when p < 0.001.
- Percentages must match: if 23 of 150, write "23 (15.3%)" -- verify the math.
- Never round numbers differently between text and tables.

### AI Pattern Avoidance

The manuscript must NOT contain these patterns commonly flagged as AI-generated:

**Forbidden phrases:**
- "In conclusion" (use "In summary" or rephrase)
- "It is worth noting that"
- "It is important to note that"
- "Notably,"
- "Interestingly,"
- "Importantly,"
- "Furthermore," at sentence start (use "In addition," or restructure)
- "Moreover," at sentence start
- "plays a crucial role"
- "a comprehensive analysis"
- "delve into"
- "leverage" (use "use" or "apply")
- "utilize" (use "use")
- "in the realm of"
- "underscores the importance of"
- "sheds light on"
- "paves the way for"
- "a nuanced understanding"
- "the landscape of"
- "a paradigm shift"
- "robust" (unless describing a statistical method)

**Forbidden structural patterns:**
- Three-part list sentences ("X, Y, and Z" repeated across paragraphs)
- Excessive hedging chains ("may potentially be associated with possible")
- Mirror-structure paragraphs (same template repeated with different content)
- Grandstanding opening sentences ("In the rapidly evolving landscape of...")

**Preferred alternatives:**
- Vary sentence structure and length within paragraphs.
- Use specific, concrete language over abstract generalizations.
- Let data speak: "The AUC was 0.92" rather than "The model demonstrated remarkable performance."

### Journal Compliance

- Respect all word limits from the loaded journal profile.
- Follow the journal's structured abstract format exactly.
- Use the journal's citation style (Vancouver numbered for most radiology journals).
- Include all journal-specific required elements (e.g., "Key Points" for AJR, CLAIM checklist for RYAI AI studies).

---

## Skill Interactions

This skill orchestrates other skills at specific phases:

| Phase | Skill called | Purpose |
|-------|-------------|---------|
| 2 | `/analyze-stats` | Statistical analysis for tables |
| 2 | `/make-figures --study-type` | Figure generation with study-type auto-detection |
| 7.1 | (built-in) | AI pattern removal |
| 7.2 | `/check-reporting` | Reporting guideline compliance + auto-fix MISSING items |
| 7.3 | `/verify-refs` | Citation verification and reference artifact audit |
| 7.4 | `/self-review --json` | Self-review with auto-fix loop (max 2 iterations) |
| 7.4a | `/meta-analysis` Phase 10 (MA manuscripts) | Audit recovery branch — rebuild extraction/analysis/figures/body when self-review surfaces structural data or protocol issues |
| 7.5 | `/humanize` | AI-pattern density sweep (<2.0 / 1000 words) |
| 7.5a | `/academic-aio` (optional, off by default) | AI-search-engine and RAG visibility checklist — run after humanize so QC-confirmed claims and human-readable text anchor the PASS/PARTIAL/FAIL report. Opt-in via `--aio` or when preparing preprint / GitHub README / CITATION.cff / HF card alongside submission. Silent pipeline execution is explicitly prohibited by the skill's Communication Rules. |
| 7.6 | (built-in) | DOCX build from manuscript/manuscript.md + analysis/figures + analysis/tables |
| 8+ | `/find-journal` | Journal scope for cover letter (optional) |

If a called skill is not available, perform that step inline using the relevant section of this skill document as guidance.

---

## LLM Writing Disclosure

When LLM disclosure is enabled (default), the skill generates transparency statements
compliant with ICMJE 2025 and COPE guidelines. The user can disable this with `--no-llm-disclosure`.

### Why Default ON

Major journals (Nature, Lancet, Radiology, JAMA) and the ICMJE (2025 update) require
disclosure of AI writing assistance. Omitting disclosure risks rejection or retraction.
The default-on design protects the user; they can opt out for journals with no such policy
or when LLM assistance was minimal.

### Disclosure Locations (3 places)

#### 1. Methods Section — Last Paragraph

Insert at the end of the Methods section, after the ethics statement:

**Template (adapt to specifics):**
```
[AI-Assisted Writing Disclosure]
An artificial intelligence language model (Claude, Anthropic) was used to assist with
manuscript drafting, including structuring sections, refining prose, and verifying
internal consistency of reported statistics. All content was critically reviewed,
verified against source data, and approved by all authors. The AI tool was not involved
in study design, data collection, data analysis, or interpretation of results.
```

**Customization rules:**
- Replace "Claude, Anthropic" with the actual tool(s) used.
- List specific tasks the LLM performed (drafting, editing, literature search, statistical code).
- If the LLM was also used for data analysis (e.g., statistical code generation via
  `/analyze-stats`), state this explicitly: "was also used to generate statistical
  analysis code, which was reviewed and validated by [statistician/author]."
- Keep to 2-3 sentences. Do not over-explain.

#### 2. Acknowledgments Section

**Template:**
```
The authors acknowledge the use of [Claude/tool name] ([Anthropic/developer]) for
writing assistance in preparing this manuscript. The authors retain full responsibility
for the content.
```

#### 3. Cover Letter — AI Disclosure Paragraph (Phase 8+)

**Template:**
```
In accordance with [Journal Name]'s policy on AI-assisted writing, we disclose that
[Claude/tool name] was used to assist with manuscript preparation, specifically
[list tasks: drafting, language editing, statistical code review]. All authors have
reviewed and take responsibility for the final content. The AI tool was not listed
as an author and did not contribute to study conception, design, or data interpretation.
```

### What NOT to Disclose

- Do not disclose routine use of grammar checkers (Grammarly, Word spell-check) — these
  are not considered generative AI under current ICMJE guidance.
- Do not disclose use of reference managers (Zotero, EndNote) or statistical software
  (R, Python) unless the LLM generated the analysis code.

### Journal-Specific Overrides

When a journal profile is loaded in Phase 0, check for the `## AI Writing Disclosure Policy`
section in the profile. Tier 1 profiles now include structured fields:
- **Requirement level** (Required / Recommended / Not specified)
- **Permitted scope** (All tasks / Language editing only / Not permitted)
- **Disclosure location** (Methods / Acknowledgments / Cover letter / Submission form)
- **AI-generated images** (Allowed / Banned / Not specified)
- **Policy URL**

Use these fields to adjust disclosure language automatically. Key known policies:
- **Radiology/RSNA**: Required; language editing only; Methods + Acknowledgments; AI images banned.
- **RYAI/RSNA**: Required; language editing only; Methods + Acknowledgments; AI images banned.
- **JAMA/AMA**: Required; language editing only; Methods + Cover letter.
- **Lancet**: Required; language editing only ("readability and language"); Acknowledgments + prompts disclosed.
- **BMJ**: Required; all tasks permitted but must disclose; Methods + Acknowledgments; applies to text, images, data, diagrams.
- **Nature/Springer Nature**: Required; language editing only; Methods; AI images banned.
- **Science/AAAS**: Most restrictive. LLM use limited; treated as potential misconduct if undisclosed.

If the loaded journal profile has no AI Writing Disclosure Policy section, fall back to
ICMJE 2025 defaults (disclose in Methods + Acknowledgments, language editing scope).

---

## Error Handling

- If the user provides incomplete data for a table, flag specific missing values rather than inventing data.
- If word count exceeds the journal limit after a section draft, report the overage and suggest specific cuts.
- If the critic-fixer loop reaches 3 rounds without passing, present the best version to the user with the remaining issues listed, and ask for guidance.
- Never fabricate references. If a citation is needed, describe the type of reference needed and ask the user to provide it, or call `/search-lit` to find a real one.

## Resumption

If the user returns to a partially completed manuscript:
1. Check the workspace directory for existing drafts.
2. Identify which phase was last completed.
3. Summarize progress and ask the user where to resume.

## Anti-Hallucination

- **Never fabricate references.** All citations must be verified via `/search-lit` with confirmed DOI or PMID. Mark unverified references as `[UNVERIFIED - NEEDS MANUAL CHECK]`.
- **Never invent clinical definitions, diagnostic criteria, or guideline recommendations.** If uncertain, flag with `[VERIFY]` and ask the user.
- **Never fabricate numerical results** — compliance percentages, scores, effect sizes, or sample sizes must come from actual data or analysis output.
- If a reporting guideline item, journal policy, or clinical standard is uncertain, state the uncertainty rather than guessing.

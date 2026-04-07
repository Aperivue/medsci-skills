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
- **Manuscript workspace**: determined at Phase 0 (typically `7_Manuscript/{PaperN}/`)

---

## 8-Phase Pipeline

### Phase 0: Init

Gather essential information from the user before any writing begins.

**Required inputs:**
1. **Title** (working title is fine)
2. **Paper type**: original article, AI validation, case report, meta-analysis, technical note, animal study
3. **Target journal**: load profile from `${CLAUDE_SKILL_DIR}/references/journal_profiles/`
4. **Research question / hypothesis**
5. **Available data**: what datasets, tables, analyses already exist

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
5. Summarize the setup to the user and confirm before proceeding.

**Output:** Setup summary with journal constraints, paper type, reporting guideline, and directory path.

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
5. Call `/make-figures` if figure generation is needed.

**Gate:** Present T&F plan to user. Do NOT proceed until user approves.

---

### Phase 3: Methods

Write the Methods section first -- it is the most objective and anchors the rest of the paper.

**Writing order within Methods:**
1. Study Design and Setting
2. Participants / Dataset (inclusion/exclusion, recruitment period)
3. Procedures / Intervention / AI Model description
4. Outcome Measures (primary and secondary endpoints)
5. Statistical Analysis (reference `${CLAUDE_SKILL_DIR}/references/section_templates/methods_statistical.md`)
6. Ethics statement and AI disclosure

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

**Before writing, collect user input (Discussion Planning Gate).**

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

**Actions (in order):**
1. Scan for and remove AI writing patterns (see AI Pattern Avoidance below).
2. Call `/check-reporting` to verify reporting guideline compliance.
3. Call `/search-lit` to verify all citations are real and correctly referenced.
4. Call `/self-review` as a final pre-submission gate.
5. Generate the following deliverables:
   - Complete manuscript file
   - Title page (with author info, word count, key points if required)
   - Reporting guideline checklist (filled)
   - Cover letter draft

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
| 2 | `/make-figures` | Figure generation |
| 7 | (built-in) | AI pattern removal |
| 7 | `/check-reporting` | Reporting guideline compliance |
| 7 | `/search-lit` | Citation verification |
| 7 | `/self-review` | Final pre-submission check |

If a called skill is not available, perform that step inline using the relevant section of this skill document as guidance.

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

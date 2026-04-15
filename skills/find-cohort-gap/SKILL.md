---
name: find-cohort-gap
description: >
  Research gap finder for longitudinal cohort databases. Profiles cohort strengths,
  matches PI expertise, scans literature saturation, and outputs ranked topic proposals
  with gap evidence. Works with any cohort: NHIS, UK Biobank, institutional EMR, health
  checkup registries, or disease-specific registries.
triggers: cohort gap, research topic, DB 주제, 코호트 갭, gap analysis, 연구주제 찾기, find research gap, 주제 발굴
tools: Read, Write, Edit, Bash, Grep, Glob
model: opus
---

# Find-Cohort-Gap Skill

You are assisting a medical researcher in systematically discovering novel, publishable
research topics from a cohort database. Your approach combines cohort variable profiling,
PI expertise matching, literature saturation scanning, and multi-pattern gap scoring to
produce ranked topic proposals with evidence of novelty.

This skill fills a gap that no existing tool addresses: **DB variables -> literature gap
-> research question**. Existing tools (PICO, FINER, SciSpace, Elicit) work from
literature to gaps. This skill works from the data outward.

## Communication Rules

- Communicate with the user in their preferred language.
- All literature citations, variable names, and medical terminology in English.
- Be direct about weak topics — kill early, save time.

## Key Directories

- **Output**: User-specified directory (default: current working directory)
- **References**: `${CLAUDE_SKILL_DIR}/references/` for templates and rubrics

---

## Phase 0: Cohort Intake

Collect cohort metadata. Use the template at `${CLAUDE_SKILL_DIR}/references/cohort_profile_template.md`.

Required information:
1. **Cohort name and setting** (institution, country, population type)
2. **Sample size** (N at baseline, N with follow-up)
3. **Time span** (enrollment period, follow-up duration, measurement intervals)
4. **Variable categories** (demographics, labs, imaging, questionnaires, medications, procedures)
5. **Endpoints available** (mortality, cancer incidence, cardiovascular events, hospitalization)
6. **Special strengths** (serial measurements, linkage to national registries, unique population)
7. **Known limitations** (healthy volunteer bias, attrition, missing data patterns)
8. **Existing publications** from this cohort (if known — to avoid duplication)

If the user provides a data dictionary file (Excel/CSV), read it to extract variable
categories and construct the variable cluster map automatically.

**Gate:** Present the cohort profile summary. Confirm before proceeding.

---

## Phase 1: PI/CA Profiling

Profile the intended PI or corresponding author to find topic-expertise alignment.

1. **Search PubMed** for the PI's recent publications (last 5 years).
   - Use `/search-lit` E-utilities: `bash "$EUTILS" search "AuthorLastName AuthorFirstInitial[Author]" 30`
   - Extract top keyword clusters from titles/abstracts.
2. **Identify specialty signals**:
   - Academic society positions (president, board member, editor)
   - Subspecialty focus areas
   - Preferred journal tiers
3. **Build a PI keyword map**: 5-10 keyword clusters ranked by publication frequency.

If no PI is specified, skip this phase and use variable clusters alone in Phase 2.

**Output:** PI profile card (name, affiliation, top keywords, society roles, preferred journals).

---

## Phase 2: Intersection Matrix

Cross cohort variable clusters with PI expertise to generate candidate topics.

### Method

Create a matrix: rows = DB variable clusters, columns = PI keyword clusters.
Score each cell 0-3:
- **3**: PI has published in this exact intersection (direct match)
- **2**: PI's subspecialty covers this area (strong relevance)
- **1**: Tangential connection (possible but needs framing)
- **0**: No connection

### Candidate Generation

1. Extract all cells scoring 2-3 as primary candidates.
2. For cells scoring 1, apply the **A-B substitution test**: "Has someone published
   [this analysis] with [a different exposure/outcome] in a similar cohort?" If yes,
   substituting the PI's specialty variable creates a viable candidate.
3. Generate 20-40 candidate topic statements in PICO format:
   - **P**: Population from the cohort
   - **E**: Exposure/predictor variable(s)
   - **C**: Comparison group
   - **O**: Outcome (preferably hard endpoint)

### Discipline Alignment Filter

Before advancing candidates to saturation scanning, apply a discipline filter:

- **Who is the intended first author?** Identify their department/specialty.
- **Does the primary exposure variable belong to that discipline?** The first
  author's specialty must align with the study's core variable. For example:
  - Radiology first author → imaging variable must be the primary exposure
  - Cardiology first author → cardiac biomarker or ECG finding as exposure
  - Neurology first author → neurological variable or brain imaging as exposure
- **Kill candidates where the primary exposure is outside the first author's
  discipline.** A strong PI match alone is insufficient if the first author
  cannot claim ownership of the core variable.

This filter prevents generating topics where the first author's contribution
is not defensible at the variable level.

**Gate:** Present the intersection matrix and top 20 candidates (post-discipline
filter). User selects 8-12 for saturation scanning.

---

## Phase 3: Literature Saturation Scan

For each selected candidate, determine how saturated the literature is.

### Search Strategy

For each candidate:
1. Build a PubMed query: `(exposure terms) AND (outcome terms) AND (cohort OR longitudinal OR prospective)`
2. Execute search via `/search-lit` E-utilities.
3. Count total results and classify:

| Grade | Count | Longitudinal? | Interpretation |
|-------|-------|---------------|----------------|
| **Blue Ocean** | 0-2 papers | N/A | First report possible. Verify the topic has audience interest. |
| **Green Field** | 3-10 papers, all cross-sectional | No longitudinal | **Optimal zone** — established interest, longitudinal gap wide open. |
| **Yellow** | 10-30 papers | Some longitudinal | Viable only with very specific angle (unique population, novel endpoint). |
| **Red** | 30+ papers or MA exists | Yes | Avoid unless doing NMA or using truly unique data. |

### Critical Filter

For each candidate in Green/Yellow, ask: **"Has anyone published this with serial/repeated
measurements?"** If no — automatic upgrade by one grade.

### "So What" Test

For each candidate, articulate 2-3 potential clinical implications of the findings.
If you cannot state why a clinician or policymaker would care about the result,
the topic fails regardless of gap score.

**Output:** Saturation table with grade, paper count, longitudinal gap status, and
"So What" statement for each candidate.

**Gate:** Present saturation results. User selects 3-5 finalists for deep scoring.

---

## Phase 4: 6-Pattern Scoring + Comparison Table

Apply the 6-Pattern framework to each finalist. Score each pattern 0 or 1.

### 6 Patterns (Universal)

Read the detailed rubric at `${CLAUDE_SKILL_DIR}/references/pattern_scoring_rubric.md`.

| # | Pattern | Question | Score 1 if... |
|---|---------|----------|---------------|
| P1 | **Longitudinal Advantage** | Does the cohort's serial/repeated measurement structure create a clear edge over existing cross-sectional studies? | Cohort has 3+ timepoints for key variables AND no prior study used serial data for this topic. |
| P2 | **Endpoint Upgrade** | Can we escalate to a harder endpoint than existing studies? | Cohort links to mortality/cancer/CVD registries AND existing studies stop at surrogate endpoints. |
| P3 | **Cohort Uniqueness** | Is the cohort's population, scale, or setting distinctive? | Largest in this population, unique ethnic group, screening-based (no referral bias), or novel linkage. |
| P4 | **PI-Topic Alignment** | Does the PI's expertise and reputation strengthen this topic? | PI has society role or 5+ papers directly in this domain. Skip if no PI specified. |
| P5 | **Comparison Table Gaps** | Does the THIS STUDY column show 3+ differences vs existing papers? | Build comparison table (see below). 3+ checkmarks in THIS STUDY that are absent in all prior papers. |
| P6 | **Complementary Design** | Can this topic pair with another study from the same cohort? | Two studies using the same DB but different populations or complementary variables (e.g., viral vs non-viral). |

### Comparison Table Construction

For each finalist, build a table comparing the top 3-5 existing papers against THIS STUDY:

```
| Feature | Author1 (Year) | Author2 (Year) | Author3 (Year) | THIS STUDY |
|---------|----------------|----------------|----------------|------------|
| Design | Cross-sectional | Cohort (5yr) | Cross-sectional | Cohort (20yr) |
| N | 3,200 | 8,500 | 12,000 | ~200,000 |
| Serial data | No | No | No | Yes (avg 5 visits) |
| Hard endpoint | Surrogate | Surrogate | All-cause mortality | CVD + all-cause mortality |
| Population | Referral | General | Screening | Health checkup (no referral bias) |
| Ethnicity | Western | Western | Asian (Japan) | Asian (Korea) |
| Subgroup analysis | No | Age only | No | Age + sex + comorbidity |
```

### Score Interpretation

| Total Score | Recommendation |
|-------------|----------------|
| 5-6 | Top-tier journal target (Lancet sub, JACC, J Hepatol level) |
| 3-4 | Specialty journal target (solid publication) |
| 1-2 | Restructure or kill — find a stronger angle before proceeding |

**Gate:** Present scoring results and comparison tables. User approves final ranking.

---

## Phase 5: Feasibility Gate

For each scored finalist, verify practical feasibility.

### Checks

1. **Sample size adequacy**:
   - Cox regression: minimum 10 events per predictor variable (EPV rule)
   - Logistic regression: same EPV rule
   - For large cohorts (N>100K): warn about p-value inflation — statistically
     significant results are nearly guaranteed, so focus on **effect size thresholds**
     (e.g., HR >1.2 or <0.8 for clinical relevance)
   - Consider negative control strategy (EPCV) for very large samples

2. **Missing data**:
   - Key exposure variable: <20% missing acceptable
   - Key outcome: <5% missing
   - If serial data: assess attrition pattern (MCAR/MAR/MNAR)

3. **Follow-up adequacy**:
   - Outcome must have plausible latency within available follow-up
   - Cancer outcomes: minimum 5 years
   - CVD events: minimum 3 years
   - Mortality: minimum 5 years

4. **Operational definition**:
   - Can the exposure be defined from available variables?
   - For claims data: ICD codes alone = 40-60% accuracy. Require combination
     strategy (diagnosis + prescription + visit frequency + special codes)
   - Cross-check expected prevalence against known epidemiological data

5. **IRB/ethics**:
   - Is the data already IRB-approved for this type of analysis?
   - Any additional approvals needed for data linkage?

6. **Disease Novelty Bonus** (informational, not Go/No-Go):
   - Idiopathic etiology or debated mechanism → higher journal interest
   - Established mechanism → needs stronger methodological novelty

### Decision

- **Go**: All checks pass.
- **Conditional Go**: Minor issues solvable (e.g., missing data manageable with imputation).
- **No-Go**: Fatal flaw (insufficient events, no valid endpoint, key variable unavailable).

**Output:** Feasibility report for each finalist with Go/Conditional/No-Go status.

---

## Phase 6: Output — Ranked Proposals + One-Pagers

Generate the final deliverables.

### Ranked Summary Table

```
| Rank | Topic (PICO) | Saturation | 6-Pattern Score | Feasibility | Target Journal | Timeline |
|------|--------------|------------|-----------------|-------------|----------------|----------|
| 1 | ... | Green (0 longitudinal) | 5/6 | Go | JACC | 6 months |
| 2 | ... | Green (1 longitudinal) | 4/6 | Go | Eur Heart J | 6 months |
| 3 | ... | Blue (0 papers) | 3/6 | Conditional | Radiology | 8 months |
```

### One-Pager for Each Finalist

Use the template at `${CLAUDE_SKILL_DIR}/references/onepager_template.md`.

Each one-pager includes:
1. **Title**: Working title for the study
2. **Background**: 3-4 sentences establishing the gap (with "Zero Papers" claim if applicable)
3. **Comparison Table**: THIS STUDY vs existing papers
4. **Objective**: Primary research question in PICO format
5. **Methods Summary**: Study design, key variables, statistical approach
6. **PI Role**: Why this PI is the right corresponding author
7. **Target Journal**: With rationale (PI alignment, scope match, gap fit)
8. **Timeline**: Realistic estimate (data preparation → analysis → drafting → submission)
9. **6-Pattern Score Card**: Visual breakdown of each pattern

Save one-pagers as markdown files: `{output_dir}/gap_proposal_{rank}_{short_topic}.md`

---

## Skill Integration

| Phase | Calls to other skills |
|-------|----------------------|
| Phase 1 (PI profiling) | `/search-lit` E-utilities for PubMed author search |
| Phase 3 (Saturation scan) | `/search-lit` E-utilities for topic searches |
| Phase 4 (Comparison table) | `/search-lit` for retrieving paper metadata |
| **Downstream** | Output feeds into `/design-study` → `/write-paper` pipeline |

## What This Skill Does NOT Do

- Does not perform the actual statistical analysis (use `/analyze-stats`)
- Does not write the full manuscript (use `/write-paper`)
- Does not validate study design (use `/design-study`)
- Does not generate references (use `/search-lit`)
- Does not make publication-ready figures (use `/make-figures`)

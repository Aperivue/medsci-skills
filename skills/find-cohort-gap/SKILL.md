---
name: find-cohort-gap
description: Use when looking for research topics a longitudinal cohort database can answer (NHIS, UK Biobank, an institutional EMR or registry). Profiles the cohort, matches PI expertise, scans literature saturation and returns ranked topic proposals with gap evidence.
model: opus
metadata:
  triggers: "cohort gap, research topic, DB 주제, 코호트 갭, gap analysis, 연구주제 찾기, find research gap, 주제 발굴"
---

# Find-Cohort-Gap Skill

Output directory: user-specified (default: current working directory).

## Phase 0: Cohort Intake

The cohort does not have to be one this skill has heard of. Route on what the user
actually has.

| The user has… | Do this |
|---------------|---------|
| A **named public cohort** (NHIS, UK Biobank, KNHANES, …) | Fill the profile from published documentation. Cite the source for every field. |
| A **codebook / data dictionary / CSV export** of their own registry or EMR extract | Run the input adapter below. This is the common case — an institutional registry or single-centre export that no public documentation describes. |
| A **review, guideline, or preprint** defining the clinical domain | Attach it as domain context (`--context`), as a file or a URL. |

### Input adapter (local codebook / documents)

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/build_cohort_profile.py" \
  --codebook data_dictionary.csv \
  --context narrative_review.pdf --context https://example.org/guideline \
  --cohort-name "Institutional CT registry" --out-dir .
```

Formats: `.csv` / `.tsv` / `.json` / `.md` / `.txt` (stdlib), `.xlsx` (needs `openpyxl`),
`.pdf` (needs `pdftotext`). A `.csv` is auto-detected as a **codebook** (rows are
variables) or a **data export** (the header row is the variable list). Writes
`cohort_profile.md` + `cohort_profile.json` (+ `context_extract.md`).

**Do not read the codebook yourself and summarise it.** A paraphrased, merged, or invented
variable poisons every downstream claim — the intersection matrix, the feasibility gate, and
eventually the manuscript's Methods. The adapter enumerates variables verbatim with provenance
(`file:row`). Read `cohort_profile.md`; do not re-derive it.

The adapter infers, and shows its work for, the **variable cluster map**, **serial /
repeated-measure groups** (evidence for P1 Longitudinal Advantage), and **endpoint
candidates** (evidence for P2 Endpoint Upgrade). A variable matching no cluster keyword is
left `unclassified` — review those, since the lexicon is not exhaustive.

### What the adapter cannot know — ASK, never guess

A codebook does not state any of the following; each is emitted as `[UNKNOWN - ask the user]`:

1. **Sample size** (N at baseline, N with follow-up)
2. **Time span** (enrollment period, follow-up duration, measurement intervals)
3. **Known limitations** (healthy volunteer bias, attrition, missing-data patterns)
4. **Existing publications** from this cohort (to avoid duplicating them)
5. **IRB status and data-access route**

Collect these from the user before Phase 2, because a guessed N flows into the Phase 5
feasibility gate and makes it pass or fail for a reason unrelated to the cohort. Also confirm
the **setting** (institution type, country, population type) and any **special strengths**
the variable names cannot reveal — registry linkage, biobank availability, a distinctive
population.

**Gate:** Present the cohort profile summary, including the `[UNKNOWN]` list and the
unclassified variables. Confirm before proceeding.

## Phase 1: PI/CA Profiling

Profile the intended PI or corresponding author to find topic-expertise alignment. If no PI is
specified, skip this phase and use variable clusters alone in Phase 2.

1. **Search PubMed** for the PI's recent publications (last 5 years) with `/search-lit`'s
   E-utilities script:
   `bash "${CLAUDE_SKILL_DIR}/../search-lit/references/pubmed_eutils.sh" search "AuthorLastName AuthorFirstInitial[Author]" 30`
   Extract top keyword clusters from titles/abstracts.
2. **Identify specialty signals**: academic society positions (president, board member,
   editor), subspecialty focus areas, preferred journal tiers.
3. **Build a PI keyword map**: 5-10 keyword clusters ranked by publication frequency.

**Output:** PI profile card (name, affiliation, top keywords, society roles, preferred journals).

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
3. Generate 20-40 candidate topic statements in PICO format — **P** population from the
   cohort, **E** exposure/predictor variable(s), **C** comparison group, **O** outcome
   (preferably hard endpoint).

### Discipline Alignment Filter

Before saturation scanning, identify the intended first author's department/specialty. The
primary exposure variable must belong to that discipline (e.g., radiology first author →
imaging variable as the primary exposure). **Kill candidates where the primary exposure is
outside the first author's discipline** — a strong PI match alone is insufficient if the first
author cannot claim ownership of the core variable.

**Gate:** Present the intersection matrix and top 20 candidates (post-discipline
filter). User selects 8-12 for saturation scanning.

## Phase 3: Literature Saturation Scan

For each selected candidate, determine how saturated the literature is.

### Search Strategy

For each candidate:
1. Build a PubMed query: `(exposure terms) AND (outcome terms) AND (cohort OR longitudinal OR prospective)`
2. Execute search via `/search-lit` E-utilities.
3. Count total results, then ask the **Critical Filter** question — **"Has anyone published
   this with serial/repeated measurements?"** — and check whether a meta-analysis exists.
   Grade:

| Papers | Longitudinal papers | MA exists? | Grade | Interpretation |
|--------|---------------------|------------|-------|----------------|
| 0-2 | 0 | No | **Blue Ocean** | First report possible. Verify the topic has audience interest. |
| 3-10 | 0 | No | **Green Field** | **Optimal zone** — established interest, longitudinal gap wide open. |
| 10-30 | 0 | No | **Green Field** (upgraded from Yellow) | As above. |
| 3-30 | 1+ | No | **Yellow** | Viable only with very specific angle (unique population, novel endpoint). |
| 30+ | Any | No | **Yellow** (borderline Red) | As above. |
| Any | Any | Yes, outdated (>5 yr) or limited scope | **Yellow** | As above. |
| Any | Any | Yes, recent | **Red** | Avoid unless doing NMA or using truly unique data. |

### "So What" Test

For each candidate, articulate 2-3 potential clinical implications of the findings.
If you cannot state why a clinician or policymaker would care about the result,
the topic fails regardless of gap score.

**Output:** Saturation table with grade, paper count, longitudinal gap status, and
"So What" statement for each candidate.

**Gate:** Present saturation results. User selects 3-5 finalists for deep scoring.

## Phase 4: 6-Pattern Scoring + Comparison Table

Apply the 6-Pattern framework to each finalist. Score each pattern 0 or 1.

### 6 Patterns (Universal)

Read the detailed rubric at `${CLAUDE_SKILL_DIR}/references/pattern_scoring_rubric.md` and score
each finalist on **P1** Longitudinal Advantage, **P2** Endpoint Upgrade, **P3** Cohort Uniqueness,
**P4** PI-Topic Alignment (skip if no PI specified), **P5** Comparison Table Gaps (3+ features
unique to THIS STUDY in the table below), and **P6** Complementary Design.

### Comparison Table Construction

For each finalist, build a table comparing the top 3-5 existing papers against THIS STUDY,
one row per feature (design, N, serial data, hard endpoint, population, ethnicity, subgroup
analysis, …) — the rubric's P5 lists the construction steps and differentiator categories.
Cite existing papers only with a `/search-lit`-confirmed DOI or PMID; otherwise mark the
reference `[UNVERIFIED - NEEDS MANUAL CHECK]`.

### Score Interpretation

| Total Score | Recommendation |
|-------------|----------------|
| 5-6 | Top-tier journal target (Lancet sub, JACC, J Hepatol level) |
| 3-4 | Specialty journal target (solid publication) |
| 1-2 | Restructure or kill — find a stronger angle before proceeding |

**Gate:** Present scoring results and comparison tables. User approves final ranking.

## Phase 5: Feasibility Gate

For each scored finalist, verify practical feasibility.

### Checks

1. **Sample size adequacy**:
   - Cox and logistic regression: minimum 10 events per predictor variable (EPV rule)
   - For large cohorts (N>100K): warn about p-value inflation — statistically significant
     results are nearly guaranteed, so focus on **effect size thresholds** (e.g., HR >1.2
     or <0.8 for clinical relevance)
   - Consider negative control strategy (EPCV) for very large samples
2. **Missing data**: key exposure variable <20% missing acceptable; key outcome <5% missing;
   if serial data, assess the attrition pattern (MCAR/MAR/MNAR)
3. **Follow-up adequacy**: the outcome must have plausible latency within available
   follow-up — cancer outcomes minimum 5 years, CVD events minimum 3 years, mortality
   minimum 5 years
4. **Operational definition**:
   - Can the exposure be defined from available variables?
   - For claims data: ICD codes alone = 40-60% accuracy. Require combination
     strategy (diagnosis + prescription + visit frequency + special codes)
   - Cross-check expected prevalence against known epidemiological data
   - Flag any clinical definition, diagnostic criterion, or guideline claim you cannot
     source with `[VERIFY]` and ask the user.
5. **IRB/ethics**: is the data already IRB-approved for this type of analysis? Any
   additional approvals needed for data linkage?
6. **Disease Novelty Bonus** (informational, not Go/No-Go): idiopathic etiology or debated
   mechanism → higher journal interest; established mechanism → needs stronger
   methodological novelty

### Decision

- **Go**: All checks pass.
- **Conditional Go**: Minor issues solvable (e.g., missing data manageable with imputation).
- **No-Go**: Fatal flaw (insufficient events, no valid endpoint, key variable unavailable).

**Output:** Feasibility report for each finalist with Go/Conditional/No-Go status.

## Phase 6: Output — Ranked Proposals + One-Pagers

### Ranked Summary Table

```
| Rank | Topic (PICO) | Saturation | 6-Pattern Score | Feasibility | Target Journal | Timeline |
|------|--------------|------------|-----------------|-------------|----------------|----------|
| 1 | ... | Green (0 longitudinal) | 5/6 | Go | JACC | 6 months |
| 2 | ... | Blue (0 papers) | 3/6 | Conditional | Radiology | 8 months |
```

### One-Pager for Each Finalist

Fill every section of the template at `${CLAUDE_SKILL_DIR}/references/onepager_template.md`;
give the target journal with its rationale (PI alignment, scope match, gap fit). Save one-pagers
as markdown files: `{output_dir}/gap_proposal_{rank}_{short_topic}.md`

**Downstream:** output feeds into `/design-study` → `/write-paper`.

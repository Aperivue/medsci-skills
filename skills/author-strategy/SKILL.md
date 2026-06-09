---
name: author-strategy
description: PubMed author profile analysis. Author name → PubMed fetch → study type classification → visualization → strategy report.
triggers: author-strategy, 저자 분석, publication analysis, 다작 분석, 연구 전략 분석, author profile, reverse engineer strategy
tools: Read, Write, Edit, Bash, Glob, Grep
model: inherit
---

# /author-strategy — PubMed Author Strategy Analysis

## Purpose

Analyze a researcher's PubMed publication portfolio to reverse-engineer their research strategy. Produces a CSV dataset, 7 visualizations, and a strategy report.

## Prerequisites

- Python 3.10+ with `biopython`, `pandas`, `matplotlib`, `seaborn`
- Scripts: `${CLAUDE_SKILL_DIR}/fetch_pubmed.py`, `${CLAUDE_SKILL_DIR}/analyze_patterns.py`

## Workflow

### Step 1: Gather Input

Ask the user for:
1. **Author name** (PubMed format, e.g., "Kim DK" or "Lee KS")
2. **Last name** for position classification (auto-detected if ambiguous)
3. **Output directory** (default: `~/.local/cache/author-strategy/{AuthorName}/`)

### Step 2: Fetch PubMed Data

```bash
python "${CLAUDE_SKILL_DIR}/fetch_pubmed.py" "{Author Name}" \
  --last-name "{LastName}" \
  --output "{output_dir}/data/{name}_publications.csv" \
  --email "{user_email}"
```

Review the console summary (total count, study type distribution, author position).
If count is 0, suggest alternative name formats (e.g., "Yon DK" vs "Yon D" vs "Yon Dong Keon").

### Step 3: Generate Visualizations and Report

```bash
python "${CLAUDE_SKILL_DIR}/analyze_patterns.py" "{output_dir}/data/{name}_publications.csv" \
  --output-dir "{output_dir}/report/" \
  --author-name "{Author Name}"
```

This produces:
- 7 PNG charts (01-07)
- `analysis_report.md` with strategy breakdown

### Step 4: Interpret and Present

Read `analysis_report.md` and present to the user:

1. **Executive summary**: total publications, growth trajectory, high-tier rate
2. **Primary strategy**: what study type dominates and why
3. **Author position analysis**: leadership rate (1st + last) vs middle
4. **Topic clusters**: research focus areas
5. **ROI quadrant**: which strategies yield high-tier + leadership vs. volume only
6. **Replication opportunities**: which patterns are replicable with Claude Code + public databases

### Step 5: Optional — MA Gap Identification

If the user asks "what MA topics are feasible with this professor?":
- Cross-reference topic clusters with existing MA plans in memory
- Identify gaps where the professor has domain expertise but no MA published
- Output a prioritized list of MA proposals

## Study Type Classifier

The classifier is tuned for Korean epidemiology and public health researchers. Categories:

| Type | Detection Pattern |
|------|------------------|
| GBD | "global burden" or "gbd" in title/abstract |
| SR/MA | "systematic review" or "meta-analysis" |
| NHIS/Claims | "national health insurance", "nhis", "claims database", "nationwide cohort" |
| Cross-national | Country pairs or "cross-national"/"binational" |
| National survey | "knhanes", "nhanes", "kchs", "national survey" |
| Biobank | "biobank" |
| AI/ML | "machine learning", "deep learning", "artificial intelligence" |
| Clinical trial | "randomized" or publication type |
| Case report | "case report" |
| Letter/Commentary | Publication type = letter/comment/editorial |

**Known limitation**: The classifier may undercount NHIS studies when they appear in Cross-national or Other categories. The report notes this.

## Known Limitations

- The study type classifier is tuned for epidemiology and public health researchers. May undercount specialized study types for other fields.
- NHIS studies may be undercounted when they appear in cross-national or "other" categories.
- PubMed search requires an email for NCBI E-utilities (set via `--email` flag).

## Anti-Hallucination

- **Never fabricate publication counts, h-index, or journal metrics.** All numbers must come from PubMed API output.
- **Never invent study classifications.** If a paper cannot be classified, label it as "Other" rather than guessing.
- If PubMed returns 0 results, suggest alternative name formats rather than generating fake data.

## Output Structure

```
{output_dir}/
  data/
    {name}_publications.csv
  report/
    analysis_report.md
    01_yearly_stacked.png
    02_study_type_pie.png
    03_author_position.png
    04_journal_tier_heatmap.png
    05_topic_distribution.png
    06_growth_curve.png
    07_strategy_roi.png
```

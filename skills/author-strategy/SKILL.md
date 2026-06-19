---
name: author-strategy
description: PubMed author profile analysis. Author name → PubMed fetch → study-type classification → visualization → strategy report → optional trajectory-archetype classification.
triggers: author-strategy, 저자 분석, publication analysis, 다작 분석, 연구 전략 분석, author profile, reverse engineer strategy, trajectory archetype, career archetype
tools: Read, Write, Edit, Bash, Glob, Grep
model: inherit
---

# /author-strategy — PubMed Author Strategy Analysis

## Purpose

Analyze a researcher's PubMed publication portfolio to reverse-engineer their research strategy. Produces a CSV dataset, 7 visualizations, and a strategy report.

## Prerequisites

- Python 3.10+ with `biopython`, `pandas`, `matplotlib`, `seaborn`, and `pyyaml` (PyYAML is required by the archetype classifier and the rubric renderer)
- Scripts: `${CLAUDE_SKILL_DIR}/fetch_pubmed.py`, `${CLAUDE_SKILL_DIR}/analyze_patterns.py`, `${CLAUDE_SKILL_DIR}/pubmed_parse.py` (stdlib parser), `${CLAUDE_SKILL_DIR}/classify_archetypes.py`, `${CLAUDE_SKILL_DIR}/render_archetype_doc.py`
- Rubric: `${CLAUDE_SKILL_DIR}/references/trajectory_archetypes.yaml` (canonical) and `${CLAUDE_SKILL_DIR}/references/trajectory_archetypes.md` (generated)

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
3. **Author position analysis**: first/last positional rate vs middle (positional heuristic only — not leadership or corresponding-author metadata, which are unavailable here)
4. **Topic clusters**: research focus areas
5. **ROI quadrant**: which strategies yield high-tier + leadership vs. volume only
6. **Replication opportunities**: which patterns are replicable with Claude Code + public databases

### Step 5: Optional — MA Gap Identification

If the user asks "what MA topics are feasible with this professor?":
- Cross-reference topic clusters with existing MA plans in memory
- Identify gaps where the professor has domain expertise but no MA published
- Output a prioritized list of MA proposals

## Optional: Trajectory-Archetype Classification

A second, opt-in capability that classifies the author's trajectory into abstract
career archetypes (A1–A6 + a composite) as an **explainable, multi-label,
confidence-scored heuristic — not an objective verdict**. The rubric is the canonical
`references/trajectory_archetypes.yaml`. This path is **gated**: a surname alone does not
resolve an author, so the corpus must pass an explicit disambiguation review before it
can be classified.

### Step 6: Disambiguation Gate (required before classification)

Pass disambiguators so the target author is uniquely attributed (a surname alone is never
sufficient):

```bash
python "${CLAUDE_SKILL_DIR}/fetch_pubmed.py" "{Author Name}" \
  --initials "{Initials}" --orcid "{ORCID}" \
  --affiliation "{Institution}" --year-from "{YYYY}" --year-to "{YYYY}" \
  --output "{output_dir}/data/{name}_publications.csv" --email "{user_email}"
```

This writes the CSV, a `candidates.json` of affiliation/year candidate clusters, and a
`corpus_manifest.json` with `review_status: pending`. **Present the candidate clusters to
the user for review.** The user decides include/exclude. Only after the user has reviewed
the clusters do you finalize and approve the corpus (the `--approve` flag is a human gate
— never set it without explicit user review/approval):

```bash
python "${CLAUDE_SKILL_DIR}/fetch_pubmed.py" "{Author Name}" \
  --initials "{Initials}" --affiliation "{Institution}" \
  --include-pmids "{included.txt}" --exclude-pmids "{excluded.txt}" --approve \
  --output "{output_dir}/data/{name}_publications.csv" --email "{user_email}"
```

The manifest is cryptographically bound to the CSV (`csv_sha256` + `pmid_set_hash`); the
classifier refuses to run on an unapproved or mismatched corpus.

### Step 7: Run the Classifier and Present

```bash
python "${CLAUDE_SKILL_DIR}/classify_archetypes.py" \
  "{output_dir}/data/{name}_publications.csv" \
  --manifest "{output_dir}/data/corpus_manifest.json" \
  --rubric "${CLAUDE_SKILL_DIR}/references/trajectory_archetypes.yaml" \
  --output-dir "{output_dir}/report/"
```

Read `archetype_report.md` and present it to the user, **stating up front that the labels
are explainable heuristics, not objective classifications**. For each surfaced archetype,
show the score, confidence band, and the author's own evidence PMIDs. Honor the `[VERIFY]`
markers (h-index/citation/venue-tier are unavailable) and the A5 participation flag. List
the `insufficient evidence` archetypes too.

To retune the rubric, edit only the YAML and regenerate the narrative doc:

```bash
python "${CLAUDE_SKILL_DIR}/render_archetype_doc.py"        # regenerate the .md
python "${CLAUDE_SKILL_DIR}/render_archetype_doc.py" --check # CI/test sync gate
```

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
- **Archetype labels are explainable heuristics, not objective classifications.** Every label must carry a score, a confidence band, and evidence (the queried author's own PMIDs). Below the minimum sample or with conflicting signals, report `insufficient evidence` — never force a label.
- **Metadata + stored abstract only.** Signals are computed from PubMed metadata and the title/abstract text already fetched. Do not retrieve full text, follow external links, or resolve preprints. Signals that need citations, citation half-life, venue-impact tier, repository/preprint links, or corresponding-author role are `unavailable` and surface as `[VERIFY]` — never inferred.
- **Author position is a positional heuristic** (first/middle/last/unknown + real EqualContrib). Never present it as authoritative leadership or corresponding-author metadata.
- **Never resolve an author by surname alone.** Classification requires an approved, CSV-bound `corpus_manifest.json`; present candidate clusters for the user to confirm.

## Output Structure

```
{output_dir}/
  data/
    {name}_publications.csv
    candidates.json          # disambiguation candidate clusters (Step 6)
    corpus_manifest.json     # review_status + csv_sha256 + pmid_set_hash (Step 6)
  report/
    analysis_report.md
    01_yearly_stacked.png
    02_study_type_pie.png
    03_author_position.png
    04_journal_tier_heatmap.png
    05_topic_distribution.png
    06_growth_curve.png
    07_strategy_roi.png
    archetype_report.md      # trajectory-archetype classification (Step 7)
    archetype_results.json   # machine-readable labels + scores + evidence
```

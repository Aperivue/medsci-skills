---
name: author-strategy
description: Use when analyzing a researcher's publication record from PubMed. Fetches an author's papers, classifies study types and author position, charts the patterns and writes a strategy report, with an optional trajectory-archetype classification. Works from PubMed metadata only.
metadata:
  triggers: "author-strategy, 저자 분석, publication analysis, 다작 분석, 연구 전략 분석, author profile, reverse engineer strategy, trajectory archetype, career archetype"
---

# /author-strategy — PubMed Author Strategy Analysis

Work from PubMed metadata and the title/abstract text already fetched — nothing else. Do not
retrieve full text, follow external links, or resolve preprints. Signals that need citations,
citation half-life, venue-impact tier, repository/preprint links, or corresponding-author role are
`unavailable` and surface as `[VERIFY]` — never inferred.

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
4. **Email** for NCBI E-utilities (passed as `--email`)

### Step 2: Fetch PubMed Data

```bash
python "${CLAUDE_SKILL_DIR}/fetch_pubmed.py" "{Author Name}" \
  --last-name "{LastName}" \
  --output "{output_dir}/data/{name}_publications.csv" \
  --email "{user_email}"
```

Review the console summary (total count, study type distribution, author position).
If count is 0, suggest alternative name formats (e.g., "Kim DK" vs "Kim D" vs the full first
name) rather than generating data.

### Step 3: Generate Visualizations and Report

```bash
python "${CLAUDE_SKILL_DIR}/analyze_patterns.py" "{output_dir}/data/{name}_publications.csv" \
  --output-dir "{output_dir}/report/" \
  --author-name "{Author Name}"
```

This produces 7 PNG charts (01-07) and `analysis_report.md` with the strategy breakdown.

Study types come from the keyword rules in `pubmed_parse.py`, first match in this order: GBD,
SR/MA, NHIS/Claims, Cross-national, National survey, Biobank, AI/ML, Clinical trial, Case report,
Letter/Commentary; anything else is "Other". Present the script's labels as they are — never
reclassify a paper by guess.

### Step 4: Interpret and Present

Read `analysis_report.md` and present to the user; every count and rate comes from that
report or the fetched CSV, never from memory:

1. **Executive summary**: total publications, growth trajectory, most frequent journals (venue-impact tier is `unavailable` — never present a "high-tier" rate)
2. **Primary strategy**: what study type dominates and why
3. **Author position analysis**: first/last positional rate vs middle (positional heuristic only — not leadership or corresponding-author metadata, which are unavailable here)
4. **Topic clusters**: research focus areas
5. **ROI quadrant**: which study types combine volume with first/last positional rate (chart 07; no venue-tier axis)
6. **Replication opportunities**: which patterns are replicable with Claude Code + public databases

State the classifier's limits when they matter: it is tuned for Korean epidemiology and public
health researchers and may undercount specialized study types in other fields, and NHIS studies
that lack its keywords fall into "Other".

Known limits: a supplied `--orcid` or `--initials` that contradicts every same-surname author on
a paper yields `match_basis` `orcid-conflict` / `initials-conflict` and position `unknown` (a
namesake is never attributed). The `journal_tier` CSV column always reads `unavailable [VERIFY]`.
The A3 reporting-quality term list no longer contains `claim` (it matched "claims database"), so
papers naming only the CLAIM checklist do not count toward `dual_mode_corpus`.

### Step 5: Optional — MA Gap Identification

If the user asks "what MA topics are feasible with this professor?":
- Cross-reference topic clusters with the user's existing MA plans
- Identify gaps where the professor has domain expertise but no MA published
- Output a prioritized list of MA proposals

## Optional: Trajectory-Archetype Classification

An opt-in path that classifies the trajectory into abstract career archetypes (A1–A6 + a
composite) as an **explainable, multi-label, confidence-scored heuristic — not an objective
verdict**, using the canonical rubric `references/trajectory_archetypes.yaml`.

### Step 6: Disambiguation Gate (required before classification)

A surname alone never resolves an author. Pass disambiguators so the target author is uniquely
attributed:

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
the `insufficient evidence` archetypes too — below the minimum sample or with conflicting
signals, never force a label.

To retune the rubric, edit only the YAML and regenerate the narrative doc:

```bash
python "${CLAUDE_SKILL_DIR}/render_archetype_doc.py"        # regenerate the .md
python "${CLAUDE_SKILL_DIR}/render_archetype_doc.py" --check # CI/test sync gate
```

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
    04_journal_heatmap.png
    05_topic_distribution.png
    06_growth_curve.png
    07_strategy_roi.png
    archetype_report.md      # trajectory-archetype classification (Step 7)
    archetype_results.json   # machine-readable labels + scores + evidence
```

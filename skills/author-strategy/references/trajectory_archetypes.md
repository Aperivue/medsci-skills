<!-- GENERATED FILE — do not edit by hand.
     Source of truth: trajectory_archetypes.yaml
     Regenerate: python3 render_archetype_doc.py -->

# Trajectory-Archetype Rubric

Rubric version: **1.0.0**

Classification output is an **explainable, multi-label heuristic — NOT an objective verdict**. Each surfaced label carries a score, a confidence band, and evidence drawn from the queried author's OWN fetched PMIDs. Below the minimum sample, below the score threshold, or with a negative rule firing, the archetype is reported as `insufficient evidence`.

## Provenance tags

- `source-derived` — a raw PubMed record field (n_authors, year, pub_types, study_type).
- `rule-derived` — a threshold / share / fraction / term-match computed over raw fields.
- `unavailable` [VERIFY] — cannot be computed in the PubMed-only MVP (h-index, citation counts/half-life, venue-impact tier, repository/preprint links, cross-platform divergence). Weight 0; excluded from the score denominator; never fabricated.

## Scoring

- A signal is *computable for a dataset* iff its provenance is `source-derived` or `rule-derived` AND all its required columns are present.
- `score = (sum of weights of fired computable signals) / (sum of weights of all computable signals)`, clamped to [0, 1].
- `unavailable` signals never enter the numerator or denominator — they surface only as [VERIFY] notes.
- A **negative** rule firing suppresses the label (`insufficient evidence`) regardless of score.
- A label is surfaced iff: no negative fired, sample `n >= min_sample`, `score >= score_threshold`, and at least one computable signal fired.

## Confidence (capped at each archetype's `max_confidence_mvp`)

- **high** — >= 3 distinct computable signals fired AND `n >= min_sample`
- **med** — >= 2 distinct computable signals fired
- **low** — >= 1 computable signal fired

## Author position caveat

Author position is a positional heuristic (`first` / `middle` / `last` / `unknown`, plus real `EqualContrib` metadata when PubMed marks it). It is NOT authoritative leadership or corresponding-author metadata, which are `unavailable` in this MVP.

## Archetypes (multi-label; an author may score on several)

### A1 — Infrastructure builder

Datasets / benchmarks / ontologies / reusable resources.

_min_sample: 8 · score_threshold: 0.34 · max_confidence_mvp: high_

Signals:

- **resource_term_density** (`rule-derived`, weight 0.5) — At least 4 prominent papers whose titles name a reusable resource (dataset, benchmark, challenge, ontology, lexicon, schema, terminology).
- **standard_maintenance_terms** (`rule-derived`, weight 0.3) — Escalation toward maintained standards/terminology (schema -> ontology -> standard).
- **early_overview_reviews** (`rule-derived`, weight 0.2) — Repeated field-defining overview/basic-principles reviews near a field's inflection point.
- **citation_concentration_on_resources** (`unavailable` [VERIFY], weight 0.0) — Citation mass concentrated on a few resource papers; long citation half-life. _Pareto citation skew toward resource/benchmark works — needs citation data ([VERIFY])._
- **connector_coauthorship** (`unavailable` [VERIFY], weight 0.0) — Connector pattern across resource-producing groups. _Recurring cross-group co-authorship on others' resource papers — coarse, not in MVP record ([VERIFY])._

### A2 — Methodology rule-maker

Checklists / reporting standards / statistical guidance.

_min_sample: 6 · score_threshold: 0.34 · max_confidence_mvp: high_

Signals:

- **guideline_genre** (`rule-derived`, weight 0.45) — At least one consensus/guideline/reporting-standard/checklist-genre paper (the strong marker).
- **large_author_consortium** (`source-derived`, weight 0.2) — Hyper-multi-institution consortium authorship (unusually large author count).
- **methods_framework_titles** (`rule-derived`, weight 0.2) — Recurring methods/evaluation-framework titles.
- **normative_empirical_pairing** (`rule-derived`, weight 0.15) — A framework/guide paper followed within ~1-3 years by an audit quantifying field-wide non-compliance with it.
- **methods_section_citation_dominance** (`unavailable` [VERIFY], weight 0.0) — Citation profile concentrated in Methods sections rather than Discussion. _Citations dominated by Methods-section 'the way to do X' — needs citation context ([VERIFY])._

### A3 — Clinical-foundation to AI-pivot hybrid

Subspecialty clinical base shifting into AI/ML, often retaining a clinical-imaging through-line.

_min_sample: 8 · score_threshold: 0.34 · max_confidence_mvp: high_

Signals:

- **ai_term_presence** (`rule-derived`, weight 0.25) — AI/ML title/study-type terms become present (>= 10% of corpus).
- **dual_mode_corpus** (`rule-derived`, weight 0.3) — First/senior on both clinical-AI MODEL papers AND reproducibility/reporting-quality papers in the same domain (strong hybrid marker).
- **venue_drift_ai** (`rule-derived`, weight 0.25) — AI/ML terms absent in the early third of the timeline but recurring (>= 2) in the late third.
- **sustained_clinical_concurrent** (`rule-derived`, weight 0.2) — Clinical-imaging publications sustained concurrently with AI papers (hybrid, not defection): AI fraction between 10% and 90%.
- **mobility_preprint_citation_spike** (`unavailable` [VERIFY], weight 0.0) — Cross-border mobility, open-artifact release, preprint lead-time, mid-career citation spike. _Affiliation-country change, preprint-then-journal lag, modality citation shock — links/citations/preprint-match not in MVP ([VERIFY])._

Negatives (rule the archetype OUT):

- **pure_ai_no_clinical_floor** — ML-only from career start with no clinical floor (AI fraction == 100%) rules the archetype OUT.

### A4 — Systematic-review / meta-analysis volume engine

High-density SR/MA output across many clinical questions.

_min_sample: 6 · score_threshold: 0.4 · max_confidence_mvp: high_

Signals:

- **srma_fraction** (`source-derived`, weight 0.5) — SR/MA is >= 50% of the corpus (the primary marker).
- **srma_topic_breadth** (`rule-derived`, weight 0.25) — SR/MA spread across >= 4 distinct topic clusters (high topic entropy — proxy for method-monoculture across breadth).
- **how_to_paper** (`rule-derived`, weight 0.25) — A self-authored how-to/methods paper on conducting SR/MA (the 'factory manual' tell).
- **single_method_recurrence** (`unavailable` [VERIFY], weight 0.0) — Near-zero method entropy across high topic entropy. _One statistical method (e.g., bivariate/HSROC) recurring across organ systems — method labels not in PubMed metadata ([VERIFY])._
- **citation_if_decoupling** (`unavailable` [VERIFY], weight 0.0) — Citation/IF decoupling. _High h-index concentrated in mid-IF specialty journals — needs citation/IF data ([VERIFY])._

### A5 — Large-consortium participation pattern

Recurring membership in very-large-author consortium papers. NOT a citation or leadership claim.

_min_sample: 8 · score_threshold: 0.34 · max_confidence_mvp: med_

> **Flag.** Large author-count participation may reflect consortium MEMBERSHIP, not individual leadership or citation magnitude. In the PubMed-only MVP only the author-count pattern is computable; any citation-collapse / fractional-citation re-ranking is [VERIFY] and not asserted here.

Signals:

- **consortium_membership** (`source-derived`, weight 0.5) — Recurring membership (>= 2 papers) in very-large-author consortium papers (>= 50 authors).
- **consortium_corpus_share** (`rule-derived`, weight 0.5) — Hyper-authored papers are >= 10% of the corpus.
- **citation_share_of_consortium** (`unavailable` [VERIFY], weight 0.0) — Disproportionate citation share attributable to hyper-authored papers; the true individual signal lives in the lower first/last-author number. _Top papers' citation share + Scholar/WoS divergence + fractional (citations / author-count) re-rank collapse — needs citation data ([VERIFY])._

### A6 — Clinical-subspecialty + device/technique depth

Concentrated subspecialty device/technique/procedural depth, low AI presence.

_min_sample: 6 · score_threshold: 0.5 · max_confidence_mvp: med_

Signals:

- **device_term_density** (`rule-derived`, weight 0.6) — Concentrated device/technique/procedural title terms within one organ system (>= 4 papers).
- **low_ai_presence** (`rule-derived`, weight 0.4) — Low AI/ML title-term presence (<= 10% of corpus).

## Composite patterns (computed combinations, not independent labels)

### AX — Domain-clinical + AI-bridge hybrid

A primary clinical/procedural identity co-listed with a secondary computational identity.

- Requires all of: A3, A6
- Extra condition — On AI-cluster papers the clinical-domain author tends to be senior/last (supplies domain + data). Position is a heuristic, not authoritative leadership metadata.
- Fires only when A3 AND A6 both surface AND the target is last-author on >= 50% of AI-term papers.

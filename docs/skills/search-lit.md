<!-- AUTO-GENERATED from skills/search-lit/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# search-lit

> Use when finding papers or building a reference list. Searches PubMed, Semantic Scholar and bioRxiv/medRxiv, includes only references verified through an API, and generates BibTeX. Auditing an existing reference list is /verify-refs.

**Invoke:** `/search-lit` · **Model:** inherit

## When to use

`search-lit` activates on requests such as: literature search, find papers, citation, references, bibliography, PubMed search, related work.

## Quality Card

**Purpose** — Search PubMed, Semantic Scholar, and bioRxiv/medRxiv and generate API-verified BibTeX (anti-hallucination: every reference verified before inclusion).

**Safety boundaries**

- Never generates references from memory; unverified references are not silently included.
- Does not write to the manuscript refs.bib (that SSOT belongs to lit-sync).

**Known limitations**

- Depends on PubMed/Semantic Scholar availability; rate limits/outages reduce recall.
- Verification confirms existence/metadata, not topical relevance.
- A DOI whose resolved title matches its row is consistent with that row; it is not proof the record was extracted correctly. The check rules out one recurring way of being wrong, not all of them.

**Validation**

- `bash references/pubmed_eutils.sh <query>`
- `python3 scripts/check_doi_record_match.py --table <screening.tsv> --strict`
- `bash scripts/check_doi_record_match_challenge/verify.sh  # deterministic, network-free`
- `bash references/snowball_challenge/verify.sh  # deterministic, network-free`
- `/verify-refs --strict`

**Evidence** — `bundled_script`

## Bundled resources

**References** (`skills/search-lit/references/`):

- `embase_browser.md`
- `parse_pubmed.py`
- `pubmed_eutils.sh`
- `snowball.py`
- `snowball_challenge/` (7 files)

**Scripts** (`skills/search-lit/scripts/`):

- `check_doi_record_match.py`
- `check_doi_record_match_challenge/` (6 files)

## Source

Canonical definition: [`skills/search-lit/SKILL.md`](../../skills/search-lit/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*

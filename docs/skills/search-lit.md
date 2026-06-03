<!-- AUTO-GENERATED from skills/search-lit/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# search-lit

> Literature search and citation management for medical research. Searches PubMed, Semantic Scholar, and bioRxiv/medRxiv with verified citations. Anti-hallucination — every reference verified via API before inclusion. Generates BibTeX entries.

**Invoke:** `/search-lit` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

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

**Validation**

- `bash references/pubmed_eutils.sh <query>`
- `/verify-refs --strict`

**Evidence** — `bundled_script`

## Bundled resources

**References** (`skills/search-lit/references/`):

- `parse_pubmed.py`
- `pubmed_eutils.sh`

## Source

Canonical definition: [`skills/search-lit/SKILL.md`](../../skills/search-lit/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*

# Challenge card — Citation snowballing (search-lit Phase 2.5)

## Problem

Keyword/Boolean search alone misses relevant studies that are only reachable
through the **citation graph**. Recognized systematic-review practice
("snowballing" / "citation searching", PRISMA item 7) requires expanding a seed
set **backward** (references the seeds cite), **forward** (papers citing the
seeds), and **laterally** (algorithmically similar papers), then reporting how
many records that step contributed.

Before this gate, `search-lit` had only a lightweight "Related Papers" mode and
**no structured citation-searching workflow, no dedup against the existing
candidate pool, and no PRISMA citation-search count**.

## What the new gate does

`references/snowball.py` expands seed DOIs/PMIDs via the Semantic Scholar Graph
API (`/references`, `/citations`, `/recommendations`), deduplicates against the
existing `references/library.bib` pool (by DOI and normalized title), and emits
API-verified BibTeX candidates carrying `verified=false` +
`verified_by=semantic_scholar` (downstream `/verify-refs` confirms each). It
prints a PRISMA "records identified through citation searching" line.

Output is **appended** to the candidate pool; it never writes
`manuscript/_src/refs.bib` (that is `/lit-sync`'s sole path).

## Fixture (synthetic only — no real papers/PII)

- `fixture/DOI_10_0_seed1.{backward,forward,similar}.json` — recorded
  Semantic-Scholar-shaped responses for one synthetic seed.
- `fixture/library.bib` — an existing candidate pool containing one paper
  (`10.0/dup-backward`) that also appears in the backward results.

## Expected

- `expected/snowball.bib` — 4 new candidates (1 backward, 2 forward, 1 similar).
- The 2nd backward paper is **dropped** because its DOI already exists in the
  pool. PRISMA line: `5 raw (backward=1, forward=2, similar=1) ... 4 new`.

## Baseline vs new gate

| | Baseline (Related Papers mode) | New snowballing gate |
|---|---|---|
| Directions | forward-ish recommendations only | backward + forward + similar |
| Dedup vs pool | none | DOI + normalized title |
| PRISMA citation-search count | none | printed |
| Output | ad hoc | verified BibTeX appended to library.bib |

## Verifier (deterministic, no network)

```bash
bash verify.sh
```

Reads the recorded fixtures, runs `snowball.py --offline-fixture`, and diffs
against `expected/snowball.bib`. Exit 0 = match.

## Acknowledgement

The reproducible "fixture + expected + deterministic verifier" packaging is
inspired by public reproducible-audit layouts such as
[EinsteinArena](https://einsteinarena.com/) (design inspiration only; no code,
solutions, or data were copied).

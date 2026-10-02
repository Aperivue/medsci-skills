# Challenge card — acceptance-readiness pre-flight

**Tool under test:** `skills/find-journal/scripts/assess_acceptance_readiness.py`

## What it guards
`/find-journal` ranks journals by *scope fit*. But editors apply an earlier,
decisive filter: **importance/novelty + design-ceiling**. The #1 desk-rejection
driver is lack of novelty/importance (~52%), ahead of scope; and across editor
decisions an *unfixable* design-ceiling defect floors the outcome at REJECT no
matter how polished everything fixable is. This script supplies that missing
**acceptance-feasibility** axis as a deterministic lexical pre-flight so the skill
can gate the venue TIER a manuscript's design can credibly support.

It is advisory (a risk/ceiling band with reasons), never an acceptance probability,
and never auto-fixable.

## Fixtures
- `fixture_ceiling/manuscript.md` — seeded with one signal per category:
  cross-sectional + single-center + surrogate (FIB-4) + no-external-validation +
  pilot (DESIGN_CEILING ×5), single-vendor/single-scanner (UNFIXABLE_DEFECT),
  null/negative + incremental framing (IMPORTANCE_RISK ×2), and a
  management/surveillance claim (CLAIM_MISMATCH ×1). Expected: 9 flags, verdict
  `HIGH-IMPACT VENUE UNLIKELY WITHOUT A DESIGN CHANGE`.
- `fixture_clean/manuscript.md` — a multi-center, externally-validated, prospective
  design with a hard endpoint and a comparator. It *deliberately* contains the
  management/surveillance verbs ("we recommend … guide management … surveillance")
  but **no** ceiling trigger, so the gated CLAIM_MISMATCH must stay silent.
  Expected: 0 flags, verdict
  `NO LISTED SIGNAL MATCHED - NOT A DESIGN CLEARANCE; ASSESS DESIGN CEILING BY JUDGEMENT`
  (the negative fixture — proves no false positives).
- `fixture_methods_vocab/` — routine methods wording that used to fire
  (circular region of interest, marginal structural model, proxy/FIB-4 as covariates,
  technical feasibility). Expected: 0 flags.
- `fixture_references/` — design words appear only in the reference list. Expected:
  0 flags (the References section is not scanned).
- `fixture_refs_then_appendix/` — a section after References is scanned again.
  Expected: 1 single-center flag.
- `fixture_narrowed_positive/` — the narrowed patterns still fire on real signals
  (circular validation, proxy endpoint, feasibility study, marginal gain).
- `fixture_paraphrase/` — signals the lexical scan cannot match ("one institution",
  "has not been externally validated"). Expected: 0 flags and the empty verdict, which
  must say it is not a design clearance.
- Generated at run time: a .docx (zip), a PDF, a Latin-1 file and a file with NUL
  bytes must exit 2 with no report; a UTF-8 file with a BOM must scan normally.

## Pass criterion
`verify.sh` runs the tool on every fixture, diffs against the golden masters in
`expected/`, and checks the non-text exit codes. Exit 0 iff all pass. Deterministic
and network-free.

## Run
```
bash skills/find-journal/scripts/acceptance_readiness_challenge/verify.sh
```

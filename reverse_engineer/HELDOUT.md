# The held-out split — measuring whether this project is still converging

Every detector in this repo is tested against fixtures authored alongside it: a challenge card
proving it fires on a planted defect, and `check_detector_crossfire.py` proving it stays silent on
the demo manuscripts. Both are necessary. Neither is independent. In machine-learning terms they
are a **training set**, and a detector passing its own challenge card is a training accuracy of
100% — true, and uninformative about anything.

That leaves one question unanswerable, and it is the question that matters as the detector count
climbs: **is the stack getting better, or is it getting better at satisfying itself?**

An improvement loop whose generator and evaluator share a framing drifts toward the evaluator
rather than the goal — the measured quality rises while the unmeasured quality falls. The
counterweight is not another gate. Adding gates is what produces the drift. The counterweight is a
set of cases the gates were never allowed to learn from, scored periodically, whose trend can
contradict us.

## What the split is

| split | meaning |
|---|---|
| `train` (default) | May inform detectors, probes, exemplars, rubrics. The normal path. |
| `heldout` | **Measurement only.** `distill.py` denies every reuse mode for it — including `synthetic`, which every other known-license source is allowed. |

Denying `synthetic` looks over-strict until the claim is said out loud. A fire rate measured on
held-out papers asserts *"no detector was written knowing this paper."* Reading one to author a
fresh probe is exactly how a detector comes to know it. The reuse is non-derivative in copyright
terms and total in measurement terms — the license firewall and this firewall answer different
questions, and only this one answers "is the number still honest?"

`frozen_at` is required on every held-out record, because the claim is chronological: a freeze date
that precedes the detector is what makes it checkable rather than asserted.

## Building one

The papers are real, published, accepted open-access articles. They are **never committed** — they
live under `_corpus/heldout/`, which is gitignored, exactly like the rest of the corpus
(`LICENSING.md`). What gets published is the *number*, which is not copyrightable expression.

1. Acquire OA papers as usual (`acquire.py`), convert to `.md` under `_corpus/heldout/`.
   The filename stem must equal the manifest `record_id`.
2. In `_corpus/manifest.json`, set `split: "heldout"`, `frozen_at: "YYYY-MM-DD"`, and a
   `coverage` map declaring what design the paper *is*.
3. Never open them again except to label a fire.

Choose papers that **span designs**. Six papers that are all retrospective single-centre CT
detection studies are one pattern measured six times: a detector silent across them is silent on
that pattern, and the denominator is inflated sixfold. That is what `coverage` is for, and the
instrument reports concentration and identical profiles rather than trusting the count.

## Rendering the corpus faithfully (where the first measurement went wrong)

The corpus is the denominator. A converter that drops a section the detectors read does not produce
a missing signal — it produces a **fire**, and that fire is indistinguishable from a detector
defect. The first real run reported 12 fires; three rendering fixes later it reported 6, and **every
one of those removals was the parser, not the detectors**:

| what the renderer dropped | what fired | fire rate |
|---|---|---|
| everything but `<body>` | `check_disclosure_availability` on **12 of 12** papers | 0.031 |
| `<author-notes>`, `<back>` | JAMA / Elsevier put disclosures there | 0.018 |
| `<funding-group>`, `<custom-meta id="data-availability">` | PLOS puts them there and nowhere else | 0.015 |
| `<contrib-group>` (the byline) | `check_credit_integrity` cannot resolve initials without it | 0.015 |

The trap worth naming: **publishers disagree about where a disclosure lives**, so a renderer that
knows one publisher's location manufactures fires *for the other publishers' papers only* — a bias
correlated with journal rather than with quality, which is the worst kind a measurement corpus can
carry. Render title, byline, abstract, body, `author-notes`, `funding-group`, non-PMC
`custom-meta`, back matter and references before trusting a single number.

## First baseline (2026-07-25)

12 papers, 12 distinct design profiles, no concentration flagged. 33 detectors ran, 10 skipped
(unobserved, each named by what it needed). **389 pairs, 6 fires, fire rate 0.015.** 31 detectors
observed clean.

Labelled: **false-positive rate 0.800** (4 spurious / 5 decided, 1 unsure, coverage 100%). Two
causes, both structurally invisible to a fixture authored alongside its detector:

- **House-style vocabulary.** JAMA's "Data Sharing Statement" / "Funding/Support" / "Conflict of
  Interest Disclosures" and Elsevier's "Declaration of competing interest" all went unrecognised.
  A fixture uses the phrasing its detector expects, so the detector had never met a journal that
  words it differently.
- **Firing on prose when the target section is absent.** `check_credit_integrity` flagged the
  ordinary words "analysis" and "writing" as invalid CRediT terms in papers carrying **no CRediT
  statement at all**. A fixture always contains the block being validated; a real corpus does not.

One fire was real — a systematic review with no data-availability statement anywhere — which is
exactly why the rate is withheld until a human looks. The instrument found a genuine omission in an
accepted paper and three vocabulary bugs in our own stack, and could not have told them apart by
itself.

## A fire you act on spends the paper

This is the rule the first cycle produced, and it is the one most easily skipped.

The six fires above were investigated, and four turned out to be ours: house-style vocabulary and
a term scan running on sections that were never CRediT blocks. Fixing them dropped the same corpus
to **2 fires, fire rate 0.005, false-positive rate 0.000** — the loop closed for the first time.

That number is a **tuning score, not a held-out estimate.** Those twelve papers have now informed
detector changes; measuring the changed detectors on them again is scoring on the set they were
fitted to. The corpus did not stop being useful — it stopped being *unbiased*, and only for the
detectors it touched.

So the split has three parts, not two, and they are spent in this order:

| set | role | spent by |
|---|---|---|
| challenge-card fixtures | train | authored with the detector |
| **this corpus** | validation — find defects, fix them, re-measure | acting on a fire |
| a **fresh** frozen corpus | test — one unbiased number | reading it |

Acquiring the next freeze is cheap: the same PMC route, different DOIs, `frozen_at` on the day it
is sealed. Do that before quoting a false-positive rate as evidence of anything, and do not quote
this one as unbiased — it is the score of a fix on the cases that motivated it, which is exactly
the reading a reviewer would catch.

## Reading the output

```bash
python3 reverse_engineer/scripts/heldout_crossfire.py \
  --corpus _corpus/heldout --manifest _corpus/manifest.json \
  --worksheet _corpus/fires_to_label.csv --ledger _corpus/heldout_ledger.jsonl \
  --out _corpus/heldout_run.json
```

**Fire rate** (`fired_pairs / ran_pairs`) needs no judgment and means only "how often does the
stack speak on already-accepted work". Its *trend* is the signal: the corpus is frozen, so a rise
across runs is a change in the detectors. Detector count up and fire rate up together is the
overfitting signature — prune or label before adding more.

**False-positive rate** is withheld until a human labels the fires. A published paper is not a
defect-free paper; this project exists because reviewers miss things, so a fire may be exactly
right. Calling every fire a false positive would manufacture the alarming trend it claims to
detect. Label the worksheet (`real` / `spurious` / `unsure`) and the rate appears with its
coverage.

**Silent-when-run vs skipped** are reported separately and mean opposite things. A detector that
ran and stayed quiet is *observed* clean. A detector that never got a subject it could read is
*unobserved* — no evidence either way. The prune decision turns on exactly this distinction, and
harvesting project `qc/` directories cannot supply it: that only sees detectors somebody happened
to run. A frozen corpus observes all of them, every run.

The instrument never fails a build. It is an instrument, not a gate.

## What this is not yet

A buffer plus a ledger is the trivial version of a memory system. The mechanisms that make
biological consolidation work are richer, and two of them are not built here:

- **Interleaved replay with distillation.** Consolidation currently runs one way — episode becomes
  rule — and nothing replays old episodes against the newly consolidated state, so interference is
  never checked. The sharper half is distillation: many episodes should compress into *one* general
  detector. Promotion that adds one detector per episode is memorisation wearing the costume of
  learning, and the ratio (episodes resolved ÷ detectors added) is measurable.
- **Associative retrieval and editing.** Recall is currently exact-fingerprint matching, so a new
  episode either collides or looks novel. Retrieval from a partial cue, with the default action
  being to *edit an existing detector* rather than append a new one, is what would keep the slow
  store from growing linearly with experience.

Both are follow-on work, and both depend on this split existing first: without a set held out from
development, neither replay nor compression has anything independent to be scored against.

## Related

- `LICENSING.md` — the copyright firewall (a different question from this one)
- `scripts/heldout_crossfire.py` — the instrument
- `scripts/test_heldout_crossfire.sh` — its self-test (wired in `validate.yml`)
- `../scripts/check_detector_crossfire.py` — the training-set sibling, whose closing paragraph
  names the gap this file fills
- McClelland, McNaughton & O'Reilly (1995), *Psychological Review* 102(3):419-457 — complementary
  learning systems: why a fast episodic store and a slow statistical one need interleaved replay

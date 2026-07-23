# Evaluation refresh protocol — covering all 80 detectors

**Status: pre-registered protocol. No results exist yet.** Every number below is a target, a
budget, or a stopping rule fixed *before* any run. This document is written first on purpose:
the toolkit's own `estimand-provenance` discipline says an analysis plan chosen after seeing
results is a re-designation, not a derivation, and an evaluation of that discipline should not
violate it.

## 1. Why a refresh

The suite's size and its evaluation evidence are two separate facts, reported at different
versions (see [`MEDSCI_AUDIT.md`](../MEDSCI_AUDIT.md) § Evidence):

- **Current catalog: 80 detectors** across six families.
- **Canonical evaluation is v3.8-era.** The seeded-defect benchmark (**E1**) rests on 19
  `DefectSpec` rows / 17 offline injectors; the coverage inventory (**E7**) is n=21. Both
  predate most of the current catalog.
- Detectors added since are covered by **per-detector CI challenge cards**, which are
  *regression* tests, not a benchmark: they answer "does this still fire?" on every push, not
  "how does the suite behave, as a suite, at a pinned version?"

So the honest current claim is: an architecture-level benchmark on a then-current subset, plus
component-level regression on everything since. What is missing is a **system-level measurement
of the present suite**. That gap is the single largest remaining weakness in the evidence base,
and it is the one a methods reviewer will name first.

**Non-goal.** This does not replace or re-run the frozen canonical runs under
[`runs/canonical/`](runs/canonical/). Those are pinned to the published methods artifacts and
stay unchanged. This is a new, separately-versioned measurement.

## 2. What the existing design already gets right (and must be carried forward)

E1's [`DEFECT_RATIONALE.md`](h1_seeded_defects/DEFECT_RATIONALE.md) makes a methodological
commitment that is easy to lose in a "bigger benchmark" and must not be:

> Because fault injection has **no defined defect prevalence**, the benchmark reports **recall
> and the clean false-positive rate, not precision or sensitivity** — it is a *triggering*
> check, not a population estimate.

That is correct and binding. Injecting a defect and seeing the detector fire tells you the
detector triggers; it tells you nothing about how often that defect occurs in real manuscripts,
so no precision, PPV, or sensitivity can be computed from injection alone. **A refresh that
reports "sensitivity and specificity" from an injection corpus would be reporting numbers its
design cannot support.** The protocol therefore splits the question into three arms with
different evidentiary standing, and never blends their metrics into one headline.

Carried forward unchanged from E1: one defect at a time; deterministic injection (first match in
document order, no RNG); exactly one judged detector per injected copy, so attribution is
unambiguous; and every run reproducible from a pinned manifest.

## 3. Three arms

| Arm | Question | Corpus | Yields | Does **not** yield |
|-----|----------|--------|--------|--------------------|
| **A — E1-R** | Does each detector fire on the defect it exists to catch, and stay silent on a near-miss? | Synthetic injected + hard negatives | Per-detector **recall**, **clean-FP**, **hard-negative pass rate** | Precision, PPV, prevalence |
| **B — E10** | How noisy is the suite on a *clean* manuscript? | Clean realistic manuscripts | **Alert burden** per manuscript, per-detector share of alerts, adjudicated FP rate | Recall |
| **C — ledger** | On real manuscripts, what fraction of fires are worth acting on? | Real use, out-of-band | Aggregate per-detector **precision** with n | Recall; anything publishable at row level |

Arm B is the one that decides adoption. A detector suite with perfect recall that fires forty
times on a clean paper is unusable, and no amount of Arm A evidence fixes that. It is also the
arm the current evidence base has nothing on.

### Arm A — per-detector triggering (E1-R)

**Unit of analysis:** a `(detector, verdict)` pair, not a detector. A detector that emits three
distinct verdicts is three units; a verdict with no positive fixture is untested regardless of
how well its siblings do.

**Coverage requirement.** Every one of the 80 detectors carries:
1. **≥1 positive fixture per emitted verdict** — the defect is injected, that specific verdict
   must fire.
2. **≥1 hard negative** — a *near-miss* that a naive implementation would flag but that is
   correct, and on which the detector must stay silent. A blank file is not a hard negative.
3. **A clean-baseline run** — the un-injected input, on which the verdict must not fire.

Hard negatives are the addition over E1. They are where precision bugs actually live: the
`/verify-refs` defects that motivated recent releases (a Unicode hyphen in a surname read as a
fabricated author; a brace-protected surname read as a corporate author) were both near-miss
failures, not missing-recall failures.

**Family stratification.** The catalog is unbalanced by design — style/review 24, reporting
compliance 15, data preparation 15, numerical/cohort 11, confounding/scope/estimand 7,
citation/reference 8. Reporting is **per family and per detector**; no single pooled recall
figure is reported as the headline, because pooling lets a large easy family mask a small hard
one.

**Metrics.** Per `(detector, verdict)`: recall ∈ {0,1} (deterministic — the ground truth is the
injection); clean-FP ∈ {0,1}; hard-negative pass ∈ {0,1}. Aggregated per family as counts, not
percentages, when n < 20.

**No adjudication needed.** Ground truth is the injection itself. This is Arm A's strength and
the reason it is the cheap arm.

### Arm B — alert burden on clean manuscripts (E10)

**Corpus.** Manuscripts that are believed defect-free and are *realistic* — full IMRAD length,
real tables, real reference lists. Two sources, both licence-checked and synthetic-or-public
only (see § 5): purpose-built synthetic manuscripts spanning the study designs the suite
targets, and open-access published articles whose licence permits redistribution.

**Applicability gating is mandatory.** Many detectors are genre-gated (a Perspective-structure
check must not be scored against an RCT; a slide-deck check must not be scored against a
manuscript). Each corpus item declares which detectors are *applicable*; a non-applicable
detector that stays silent is not a true negative and is excluded from that item's denominator.
Failing to do this would manufacture a flattering burden figure.

**Metrics.** Alerts per manuscript (median, IQR, max) split by severity; the fraction of clean
manuscripts with ≥1 Major alert; each detector's share of total alerts (the "top offender"
ranking); and the adjudicated false-positive rate among fires.

**Pre-specified burden budget.** A clean manuscript should draw **0 Major alerts** and a median
of **≤ 3 Minor** alerts. A detector responsible for more than **20 %** of all alerts across the
clean corpus is flagged for review regardless of its Arm A recall. These thresholds are fixed
now so that a disappointing result cannot be re-described as acceptable later.

**Adjudication — and the honest constraint.** "Clean" is an assumption, not a fact: an alert on
a supposedly clean manuscript may be a true positive the corpus builder missed. Every alert is
therefore adjudicated as *true defect* / *false positive* / *ambiguous* by **two independent
adjudicators**, disagreements resolved by a third, with agreement (Cohen's κ) reported.

**This is the binding constraint on the whole protocol, and it is not a tooling problem.** The
project currently has one maintainer, who is also the detector author. Self-adjudication of
one's own detectors is exactly the self-confirming loop the architecture exists to avoid — an
author judging whether his own gate was right inherits the blind spot that produced it. Arm B
therefore **cannot be completed credibly without at least one external adjudicator**, and this
protocol should not be run to completion until one is recruited (see
[`MAINTAINERS.md`](../MAINTAINERS.md) § Clinical Reviewers, an already-defined role that is
currently unfilled). Running Arm B solo and reporting the numbers would be a worse outcome than
not running it.

### Arm C — real-manuscript disposition ledger (out-of-band)

The only source of genuine precision on real inputs is what happened when a detector fired on a
real manuscript and a human decided whether to act. Those labels accumulate during ordinary use
as `real` / `spurious` / `unsure` dispositions.

**This arm lives outside this repository and always will.** Real manuscripts carry
unpublished-work, collaborator, and institutional detail; the raw ledger is never committed,
mirrored, or included in a release payload. Only **aggregate per-detector precision with its n**
is publishable, and only once n is large enough that a single project cannot be re-identified
from the pattern. Arm C is reported as supporting evidence, never as the headline, because its
sampling frame is "manuscripts this author happened to work on."

## 4. Bootstrapping from what already exists

Arm A does not start from zero. Every detector already ships a CI challenge card with a positive
case and a negative control. The first work item is therefore an **inventory, not an authoring
sprint**:

- **Stage 0 — inventory.** For each of the 80 detectors, mechanically determine: verdicts
  emitted; positive fixtures present; whether the existing negative control is a *hard* negative
  or merely an empty/trivial input. Output: a per-detector gap table. Largely automatable from
  the existing challenge-card wiring and `metadata/detectors_catalog.json`.
- **Stage 1 — fill gaps.** Author only the missing positives and hard negatives found in Stage 0.
- **Stage 2 — run Arm A** at a pinned version; emit the manifest in § 6.
- **Stage 3 — build the clean corpus and run Arm B.** Gated on an external adjudicator (§ 3).
- **Stage 4 — report** per family, with Arm C aggregates as supporting evidence.

Stages 0–2 are solo-completable. Stage 3 is not. Publishing Stages 0–2 alone is a legitimate
partial result provided it is described as triggering coverage and not as accuracy.

## 5. Corpus provenance and the synthetic-only firewall

- **No patient data, ever** — no PHI, no clinical vignettes derived from real encounters.
- **No private manuscript content** — no unpublished collaborator work, no manuscript IDs, no
  institution-identifying context. This is the same firewall the repo's PII gates enforce; the
  benchmark corpus is not an exception to it.
- **Public articles** are included only where the licence permits redistribution, recorded per
  item with source URL, licence, and retrieval date.
- **Synthetic manuscripts** record their generator and the design they represent.
- Every corpus item is content-hashed; the corpus is versioned as a unit.

## 6. Pinning, manifest, and what invalidates a run

A run is meaningless without knowing what was measured. Each run emits
`runs/<UTC-date>_<arm>/manifest.json` recording: repo commit SHA; `detector_count` and the
per-family id lists from `metadata/detectors_catalog.json`; Python version and OS; corpus
version and per-item hashes; and the protocol version (this file's commit).

A run is **invalidated** — not amended — by any change to the detector catalog or the corpus.
Adding a detector does not retroactively join a completed run; it schedules the next one. This
is deliberate: a benchmark that silently absorbs new detectors reports a number that no single
version of the software ever produced.

## 7. Pre-specified consequences

Fixed now, so the analysis is not shopped afterwards:

| Finding | Consequence |
|---|---|
| Recall = 0 on a detector's own injected defect | Bug. Fix before the next release. |
| Fires on its hard negative | Precision bug. Fix, or downgrade `maturity` to `experimental`. |
| > 20 % share of clean-corpus alerts | Review for over-firing; tighten or gate by genre. |
| Zero fires across the clean corpus **and** no real-world dispositions | Prune candidate — a gate nobody has ever seen fire is unverified surface, not coverage. |
| A verdict with no positive fixture after Stage 1 | Not reported as covered. Absence is stated, not implied. |

The last row is the one that keeps the report honest: **coverage claims are made per verdict,
and anything untested is named as untested.**

## 8. Relationship to CI

Challenge cards and this benchmark answer different questions and neither replaces the other.
Challenge cards run on every push and protect against regression; they are a *tripwire*. This
protocol runs at a pinned version and measures the suite as a system; it is a *measurement*.
Where Stage 1 authors a new hard negative, that fixture is wired into CI as well — so the
benchmark's investment compounds into the regression suite rather than sitting in a one-off
evaluation directory.

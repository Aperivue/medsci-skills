# Venue-tier acceptance recipe — clinical DL / AI-validation studies (design-time)

This is **not** another quality checklist. `design-study` already covers the comparator,
leakage, metric, and reader-study-ceiling decisions (see Phase 3, the Frequent Failure Modes,
and `reader_elicitation_design.md`). This reference answers a **different** question, and answers
it *before data collection*:

> For the study you can **actually run** given your data, labels, and compute, **which venue tier
> will accept it — and which single design move most raises the acceptance probability at the tier
> above it?**

It is reverse-engineered from **accepted open-access papers** (cited by DOI below), and it is a
design-time decision aid, not a post-hoc rescue.

## The decoupling principle (why this is a design decision, not a writing one)

Acceptance of a clinical DL / AI-validation study is set at **design time** by three things — the
**comparator**, the **validation reach**, and the **scope-vs-venue** match — not by how well the
manuscript is written. A structurally single-centre, internal-only study cannot out-write its way
into a flagship; venue-fit is **decoupled from quality** (an internal-only study can be excellent
and still land only at a focused venue). The corollary: pick the tier your design can support, or
pay for one specific "clearing move" to reach the next tier — *before* you collect data, because
none of these moves can be added post hoc.

## The acceptance ladder — design profile → venue tier → the clearing move

| The design you can actually run | Lands at (tier) | The clearing move that got it accepted | Accepted OA exemplar |
|---|---|---|---|
| **Single-centre, internal validation**, but a disciplined **clinical-endpoint** comparator + independent **blinded** readers against an independent reference standard | Focused clinical-radiology (**KJR / AJNR / Eur Radiol**) | Replace the image-metric endpoint with a **clinical diagnostic endpoint**, and read it with **≥2 blinded readers vs an independent reference standard** — the reader discipline substitutes for external data | TLE MRI deep-learning reconstruction, *KJR* 2024 (`10.3348/kjr.2023.0842`, CC BY-NC): 3-arm comparator (routine vs thin-slice vs thin-slice+DLR), 2 blinded neuroradiologists on 351 shuffled studies, EEG/surgical reference, pre-specified subgroup — accepted single-centre on comparator + reader rigour |
| **Focused single-organ / biomarker task**, multi-centre development + a **genuine external** set with an **honestly reported drop**, reporting-guideline named, ideally **open weights/data** | SpringerOpen methods (**Insights into Imaging / European Radiology Experimental**) | Add a **genuine external** test set (different sites/scanners) and **report the degradation**; name the fitting guideline (**CLEAR + METRICS** for radiomics, **STARD / TRIPOD+AI** for diagnostic models); release weights/data | Endometrial-subtype radiomics-DL, *Insights into Imaging* 2025 (`10.1186/s13244-025-01966-y`, CC BY): 3-site, combined external (macro-AUC 0.79→0.74), **nested** clinical→radiomics→DL comparator, CLEAR+METRICS · Inner-ear U-Net, *Eur Radiol Exp* 2024 (`10.1186/s41747-024-00508-3`, CC BY): 4-centre / 3-vendor train → held-out **5th-vendor** external (DSC 0.89→0.83), open weights + data |
| **Full ladder** — multi-centre dev → **multiple external** sets → **reader study** (accuracy **and** reading time) → prospective cohort; **or** a reader study as the centrepiece with washout + specialty/experience subgroups | Flagship / methods-flagship (**npj Digital Medicine / Radiology / Lancet Digital Health**) | Add a **reader study that measures clinical impact** (MRMC/crossover, washout, blinding, readers across experience/specialty, accuracy + reading-time) on top of external validation — the flagship bar is *"the model changes what a clinician does, and for whom"* | PCN CT model, *npj Digital Medicine* 2025 (`10.1038/s41746-025-01970-y`, CC BY): 4-hospital dev + **3 external sets** + 8-reader MRMC crossover (AUC 0.786→0.845, reading time down) + prospective 3-month-follow-up cohort · Pelvic-radiograph AI-support, *npj Digital Medicine* 2025 (`10.1038/s41746-025-01923-5`, CC BY-NC-ND): 26-physician, 3-session (no-AI / alert / heatmap) **washout** reader study as the centrepiece, specialty subgroups |

*Read the exemplars as design patterns, not templates; the DOIs let you inspect the real designs.*

## The five design levers, ranked by acceptance impact

Distilled across the accepted batch above — the recurring decisions that separated them from a
predictable reject:

1. **External / multi-site validation with an honest drop is the single biggest lever.** Every
   top-tier accept tested on data from sites/scanners *outside* development and **reported the
   degradation openly** (0.89→0.83 DSC; 0.79→0.74 AUC). A disclosed generalization gap earns more
   trust than a suspiciously flat external number. Internal-only studies survive only when a very
   strong reader design carries them.
2. **A comparator that is the real clinical alternative, not a strawman.** Accepts benchmark
   against *current practice* — radiologist double-reading, the conventional reconstruction, or a
   **nested** clinical→radiomics→DL ladder that isolates the marginal value of the DL component.
   "Model vs nothing" reads as promotional (see also Phase 3 *incremental value* in SKILL.md).
3. **A reader study that measures clinical impact, not standalone AUC.** MRMC / crossover designs
   with **washout, blinding, multiple readers across experience/specialty, and reading-time +
   accuracy endpoints** recur across the batch. Showing the model changes clinician behaviour (and
   for whom, via subgroups) is what lifts a paper above a leaderboard result. Design mechanics live
   in `reader_elicitation_design.md`; route AI-vs-human benchmarks to `/design-ai-benchmarking`.
4. **Scope matched to the venue tier** (the ladder above). Mismatching an underpowered single-centre
   study to a flagship is a predictable reject; a focused, honest single-organ study is a clean
   accept at a methods venue.
5. **Explicit reporting-guideline conformance + reproducibility artifacts.** Accepts *name* their
   framework (STARD / TRIPOD+AI for diagnostic-accuracy models; CLEAR + METRICS for radiomics)
   rather than gesturing at "standard methods" — it pre-empts the methods-rigour objection. Where
   the cohort is modest, **releasing weights + data + code** is itself the acceptance argument, and
   substitutes for scale at the methods venues.

## Using this at design time (the decision)

Before you collect data:

1. **Name honestly the design you can run** (data reach, label source, whether an external cohort
   and readers are obtainable).
2. **Read its tier** off the ladder.
3. **Decide**: submit at that tier, or invest the **one clearing move** to reach the next tier. The
   cheapest ladder rungs, in order, are usually: *(a) add a genuine external set → (b) add a reader
   study measuring clinical impact → (c) add a prospective cohort.*
4. Do **not** push a structurally-ceilinged design at a higher tier expecting to out-write it —
   that is the cascade-reject trap. If the ceiling is real, either lower the venue or pay for the
   clearing move at design time.

## What this does NOT replace

- **Comparator / incremental-value / endpoint-scope** design quality → Phase 3 of this skill.
- **Reader-study internals** (rubric axes, calibration probes, the six ceiling decisions) →
  `reader_elicitation_design.md`; **AI-vs-human-expert** benchmark → `/design-ai-benchmarking`.
- **The journal shortlist itself** (scope fit, AI-policy, APC) → `/find-journal`.

This reference is the **design → acceptance-tier bridge** you consult *before* those — it turns "is
my study good?" into "which tier is my study *for*, and what one move moves it up?"

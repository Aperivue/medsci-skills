# Reader / expert-elicitation study design

Load-on-demand companion to `/design-study` Phase 2, section E. Read it when the study
elicits expert ratings — a reader study, an annotation panel, or an AI-output evaluation.
A design with no human-rater arm needs none of it.

It covers rubric design (decoupled axes, anchored Likert points, pre-specified discriminant
validity), planted calibration probes, operational rigor, the human-as-**operator** arm for
interactive / promptable AI, and the six design-stage ceiling decisions for a perceptual /
reader AI study — the ones that fix the acceptance ceiling before a single reader sees an
image, and that no amount of good execution can lift afterwards.

When the study elicits expert ratings (reader study, annotation panel, AI-output evaluation), check
the following before data collection.

**Rubric design**
- **Decouple the axes.** Each rated dimension should measure one construct. Keep "is the finding
  valid/correct" separate from "is it novel", "is it feasible to measure", "does it add value over
  current tools", and "would it change action". A candidate can be high-validity yet low-added-value
  ("real but redundant"); a single blended score hides this.
- **Anchor every Likert point** with a short verbal descriptor; pilot the anchors with at least one
  reviewer before locking.
- **Pre-specify discriminant validity**: hypothesize which dimensions should correlate vs be
  orthogonal, then report the full inter-dimension correlation matrix to confirm the rubric measures
  distinct constructs.

**Calibration probes (planted control items)**
Insert a small number of deliberate control items, blinded and randomized across raters (record who
received which, e.g. a `probe_arm` flag), to (i) anchor the scale, (ii) measure rater drift and
fatigue, and (iii) audit the rubric and pipeline itself. Four useful flavors:
- **Positive control / "too-good" item** — a known-strong or near-tautological item; tests whether
  raters equate "largest effect" with "best", and whether an upstream construct-independence gate works.
- **Known-bad negative control** — an engineered defect (fabricated reference, missing key statistic);
  expected to score low.
- **Instability item** — an estimate that reverses or fails to replicate on holdout; tests caveat handling.
- **Mechanism-contradiction item** — an empirical direction that opposes the proposed mechanism.

Use the control items as a **rater-competence check** — report each rater's hit rate on known-good vs
known-bad controls — not as reliability evidence. ICC scales with the spread between items, and
controls are extreme by construction, so an ICC on a handful of controls is high whatever the raters'
reliability on real items (same raters and noise: ICC(2,1) 0.89 on four controls, 0.16 on 40 real
items). Report reliability (ICC with its form stated and a 95% CI, or Krippendorff's α for ordinal
ratings) on a representative anchor set of real items (Koo & Li, *J Chiropr Med* 2016; de Vet et
al., *J Clin Epidemiol* 2006).

**Operational rigor**
- Randomize item order **per reviewer** (not one global seed); analyze order and fatigue effects.
- Collect reviewer metadata (years of experience, prior AI-evaluation experience, subspecialty) for
  descriptive reporting.
- Define a structured export schema (per-item ratings, free-text justifications, follow-ups, timing) up front.
- Require each item to be judged standalone; discourage cross-item references in free-text, which
  signal non-independent rating.
- **An unsettled category boundary.** Fix the primary definition of each dichotomy the raters
  apply (typical vs atypical, in scope vs out of scope), and any alternative definition, before
  the confirmatory read; choosing among definitions after seeing the results is a selection the
  agreement statistics cannot undo. If the boundary is still open, explore it in a pilot. A form
  that records the boundary-defining attributes for only one verdict leaves the other verdict's
  cases with no record of why, so moving the boundary through them means re-reading them. Record
  the boundary-defining attributes per reader and case, before adjudication, for every case on the
  side(s) a boundary move could come from
  (both sides if unknown), and label agreement computed by re-applying another definition to the
  recorded attributes as such.
- **Record which instrument version produced each record.** If the version a rating, labelling or
  survey tool writes into its records does not change when the tool's content changes, that field
  alone cannot establish whether the instrument changed during collection. Each submitted record
  must identify the instrument version the rater actually used (the form as loaded, not the
  server's version at submission), by an identifier that changes
  whenever the instrument's content changes.

**Human-as-operator arm (interactive / promptable AI).** The reader-study patterns above assume the
human is a *rater / reference* judging outputs. Interactive / promptable segmentation (SAM2, MedSAM2,
nnInteractive) inverts this: the human is the *operator* who places the prompts, so the measured object
is the human-operated system's **accuracy + interaction count + time + learning curve**, not a rating.
Design for it explicitly:
- Define the operator population and their onboarding; a **learning curve** (performance vs case index)
  is a first-class outcome, not noise to average away.
- Fix the prompting protocol (allowed prompt types, stopping rule, target Dice) identically to any
  simulated-prompting arm so the two are comparable — **protocol fidelity**, checked in `/model-assessment`.
- Pre-specify the interaction and timing metrics; their deterministic reporting gate is
  `/model-assessment --task interactive`. (A design document is free-form prose, so the deterministic
  anchor for these items sits at the reporting stage, not on the protocol text.)

For an AI-system-versus-human-expert benchmark specifically, route to `/design-ai-benchmarking`, which
extends this subsection with arm definition, LLM-as-judge versus human-as-judge adjudication, and a
structured export schema.

**Perceptual / reader AI study — design-stage ceiling gate**

For a reader/observer/perceptual or diagnostic-accuracy AI study (visual Turing test, AI-vs-human
detection, image-provenance/deepfake, observer study), the acceptance ceiling is fixed **at design
time, not at analysis time** — excellent execution cannot lift a ceiling baked into the comparator,
the estimand, or the reader cohort. Walk these six before data lock and, for each, take the
higher-ambition option or record an explicit, defensible reason not to (set each at the impact level
of the journal you actually want):

1. **Comparator realism (biggest lever).** A curated teaching-repository "authentic" arm scopes the
   claim to "teaching-quality", not clinical. Use consecutive, de-identified clinical-acquisition
   images (the real PACS spectrum), or add a clinical-spectrum validation arm.
2. **Format / non-content confound matching.** Match every non-content attribute (aspect ratio,
   resolution, compression, color profile) across arms by construction, and pre-specify a
   confound-classifier ceiling check (format-only AUC must be ≪ reader AUC) as a *primary* gate.
3. **Synthetic / index-arm denominator (survivorship).** Pre-specify how failed/low-quality
   generations are counted; report the full generation denominator rather than evaluating only the
   convincing survivors.
4. **Reader independence and breadth.** Recruit readers independent of the model's development and the reference
   standard, and record each reader's role; collect reader characteristics; blind readers to the hypothesis where feasible.
   Define the target reader population first; recruit across sites (or countries) when the claim
   is meant to hold across institutions. Decide the
   claim's scope for readers and for cases separately: a fixed set (this named panel, this
   benchmark case set) or a defined population. The analysis reflects sampling variation only on
   the axes being generalised, a result on a fixed axis is reported as conditional on that set,
   and recruitment breadth follows that scope. When a named panel scores a property of the model
   or system, state its composition, training and disagreement-resolution rule; high agreement
   does not reveal a bias the whole panel shares.
5. **Estimand and power (match decision 4).** Define the primary endpoint and contrast on the
   reader and case scope set in decision 4, and size the study for it (power for a test, interval
   width for an estimate); when the scope is the reader-AND-case generalization, make it the **primary** estimand from the start, so the two-way interval — not a number conditional on the fixed reader pool —
   supports the headline claim. Fix the analysis model at the same time, once the outcome type, link,
   reader/case sampling, estimand (conditional on the random effects, or population-average) and any
   weights are defined: for a reader-and-case estimand conditional on the random effects, a mixed model with crossed reader and case random
   effects (a GLMM for a binary outcome) is the natural primary analysis. A GEE (or a marginalized
   mixed model) estimates a population-average quantity — the primary model when that is the
   pre-specified estimand. Whether it matches the conditional effect depends on the link and the
   random-effects structure, so a GEE used as a robustness check states which quantity it estimates
   rather than assuming agreement. Either way the variance must handle reader AND case dependence —
   clustering on reader alone ignores the cases every reader shares.
   Fix the estimand weights at design, and record the reason if the model changes.
6. **Novelty positioning vs scoop, and venue-fit.** Scan for close prior work at design time; if a
   flagship precedent exists, make the differentiation categorical (new modality class, clinical
   spectrum, outcome linkage), not incremental; pick the venue whose audience values the likely
   result (a rigorous null fits a methodology-forward journal better than an impact-first one).

The meta-rule: set the comparator, the confound-matching, the reader cohort, and the estimand at the
target journal's impact level **before** data collection — do not plan to out-write a structural
ceiling in revision.

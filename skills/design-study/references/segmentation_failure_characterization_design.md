# Is the segmentation usable — designing past the mean Dice

For a segmentation study whose claim is **clinical usability** rather than benchmark accuracy, the
decisive design question is not which metric you report but **what counts as a failure, who decides,
and whether the reader can see the tail**. A mean DSC of 0.90 with a 5% catastrophic tail and a
uniform 0.90 are different clinical objects, and the mean cannot tell you which one you have.
Reverse-engineered from accepted open-access papers (cited by DOI as design facts). These are
**design-time** decisions: an acceptability rate cannot be recovered from a finished experiment that
never asked a clinician, and a failure taxonomy assigned after seeing the failures is a description,
not a finding. Distinct from `/model-evaluation` (which metric, computed correctly) and
`/uncertainty-imaging` (per-case uncertainty, abstention, risk–coverage).

## The failure the reviewer expects

*"Mean DSC 0.87 across 40 organs-at-risk, therefore ready for clinical use."* — one aggregate number,
no per-case distribution, no clinician judgement, no statement of what a failure would have looked
like. The reviewer's objection is not that 0.87 is low. It is that **0.87 is silent on the question
being claimed**, and the study has no instrument that could have answered it.

How wide that silence is, measured: in a seven-site evaluation of one auto-contouring pipeline,
physician-rated *use-as-is* rates ranged from **89% (head/neck normal tissue) to 40% (head/neck CTV)
to 44% (postmastectomy breast)** — with **the same software** *(JCO Glob Oncol 2024
`10.1200/GO.23.00376`, CC BY: 5-point Likert, 31 radiation oncologists across 16 institutions and 6
countries, ≥3 independent raters per case)*. A single pooled accuracy figure over those structures
would have reported a usable system and concealed that a third of it was not.

## Design the usability question (decide before you run anything)

- **Pre-specify the failure taxonomy.** Name the classes before you look: *boundary drift* (right
  structure, wrong edge), *missed structure* (absent output), *hallucinated structure* (output where
  no structure exists), and *catastrophic / anatomically impossible* (a contour no clinician could
  have drawn). These fail differently in the clinic and a single overlap score maps all four onto one
  axis. Assigning classes after seeing the errors makes the taxonomy a summary of *this* run rather
  than a measurement instrument.
- **Define the acceptability endpoint, the judge, and the adjudication rule.** State the scale, who
  applies it, how many raters see each case, and how disagreement resolves — *before* data. A
  structured scale is what makes the rate reproducible: the JCO evaluation's 5 points (*unusable /
  major edits / minor edits required / stylistic only / use as-is*) yield a number another group can
  reproduce. The contrast is instructive: an otherwise careful head-and-neck validation assessed
  acceptability through **eight physicians' satisfaction categories with no structured scale**,
  concluding the contours needed "no edits of major clinical significance" *(Front Oncol 2023
  `10.3389/fonc.2023.1137803`, CC BY)*. That conclusion may well be right, and it is **not a rate** —
  nobody can reproduce it, meta-analyse it, or size a future study against it.
- **Report the tail, not only the centre.** Commit in advance to the **per-case distribution**, the
  **worst-case percentile**, and the **count of catastrophic failures** alongside the mean. "Only 4
  of 777 structures fell below DSC 0.5" *(Front Oncol 2023, above)* is a tail statement and belongs
  in the design, because a study that never records it cannot produce it later.
- **Treat edit effort as its own endpoint, paired and disaggregated.** If the claim is that the model
  saves work, measure the work: editing time on the **same cases** against manual-from-scratch, per
  structure and per site. The disaggregation is not decoration — a seven-centre evaluation reporting
  an overall **46% time saving** also found **no significant saving for lymph-node levels IA, IB,
  III, IVA and IVB**, with some centres taking **longer to edit than to contour manually** *(npj
  Digit Med 2025 `10.1038/s41746-025-01624-z`, CC BY-NC-ND — learn-only)*. The pooled 46% is true and
  would have hidden every one of those.
- **Stratify failures by what predicts them.** Decide up front which case attributes the failure rate
  will be broken down by — structure size, contrast phase, pathology present, scanner or site — so
  the study can say *where* the model fails rather than only *how often*. Small structures and target
  volumes are where the acceptability rates above collapse; a design that pools them cannot show it.

## Two traps specific to this endpoint

- **The acceptability question determines the answer.** *Use-as-is* and *acceptable after minor
  edits* are different endpoints, and the gap between them is large: 44% → 91% (breast), 40% → 93%
  (head/neck CTV) *(JCO Glob Oncol 2024)*. Both are legitimate; naming which one the headline claim
  rests on is mandatory, and reporting the permissive one while implying the strict one is the
  overclaim reviewers catch.
- **A high global score can coexist with a clinically unusable case.** Overlap computed over a whole
  volume is dominated by the easy interior, so a contour can score well in 3-D while carrying errors
  on the slices that matter. Design the per-case (and where relevant per-slice) read so that such a
  case is *visible* rather than averaged away.

## What this does NOT replace

**Which metric and how it is computed** (Dice + a boundary metric, per structure) →
`/model-evaluation`; **per-case uncertainty, abstention, and risk–coverage failure detection** →
`/uncertainty-imaging`; **split leakage, tuning-on-test, internal vs external** → `/model-validation`;
**comparing several models fairly** → `multi_model_comparison_design.md`; **sizing the acceptability
rate, the failure-rate bound, and the edit-time contrast** → `calc-sample-size`
`references/segmentation_acceptability_sample_size.md` (Test 17); **showing the distribution and its
tail** → `make-figures` `exemplar_plots/segmentation_failure_panel.md`.

This is the **usability decision** for a segmentation study — the one that turns "the mean Dice was
high" into "clinicians accepted N% of cases as-is, these are the failures, and this is where they
fall". Decide it before data collection.

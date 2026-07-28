# Compare several models head-to-head — design the comparison to be fair

For a study whose contribution is **comparing several models / architectures against each other** on
the same task (CNN vs Transformer vs a foundation-model backbone; N segmentation networks; N fusion
strategies), the single decision that most determines acceptance is **not which model wins — it is
whether the comparison is fair**. Reverse-engineered from accepted open-access papers (cited by DOI as
design facts). It is a **design-time** decision: none of the fairness controls below can be added after
you have run the models. Distinct from `combine_models_ablation_design.md` (an ablation *of one* model
built from parts) and `/design-ai-benchmarking` (AI *versus a human-expert panel*) — this is
**model-vs-model**.

## The failure the reviewer expects

*"Our model beat ResNet, DenseNet, and a transformer."* — with borrowed baseline numbers, only the
home model tuned, one accuracy per cell and no paired test, this is a **"we win" leaderboard**, and it
is the **rejected** pattern. Its purest published form: baselines copied from a benchmark's
documentation (never re-run under matched conditions) while only the authors' own model had its
learning-rate / batch-size / epochs configured, reported as a bare accuracy table with no CIs
*(Sci Rep 2024 `10.1038/s41598-024-63094-9`, included in the corpus as the negative control)*. The
operational proof that this matters: when CNN- vs Transformer- vs Mamba-segmentation is re-run under
**matched** conditions with an adequately-tuned baseline, most claimed architecture "wins" **evaporate**
*(nnU-Net Revisited, arXiv:2404.09556, CC BY — the field's fair-benchmarking argument; the MICCAI 2024
proceedings version `10.1007/978-3-031-72114-4_47` is © Springer, so reuse the arXiv copy)*.

## Design the comparison to be fair (decide before you run anything)

- **One dataset, one frozen patient-level split, one preprocessing pipeline — pushed through every
  model.** Fix the split and preprocessing *once* and reuse them identically; no model gets cleaner
  data, its own resampling, or a private augmentation policy. This is the reviewer's first question.
  *(liver multi-phase MRI, Sci Rep 2025 `10.1038/s41598-025-07084-5`: one N4/z-score/registration
  pipeline and one nested-CV stratification across nnU-Net, ResEnc nnU-Net, and Swin UNETR; mandibular
  canal CBCT, Int Dental J 2026 `10.1016/j.identj.2026.109427`: one fixed 128/20/25 split + identical
  clip/augmentation across UNETR / Swin UNETR / 3D UX-Net.)*
- **A strong, self-configuring reference baseline — not a hobbled U-Net.** If the reference model is
  under-tuned, the whole comparison is void. Instantiate the baseline through **nnU-Net / nnUNetv2** and
  configure the strongest competitor as carefully as your own. *(tooth CBCT, Head & Face Med 2025
  `10.1186/s13005-025-00555-0` [CC BY-NC-ND]: the "3D U-Net" arm is nnUNetv2, self-configuring; nnU-Net
  Revisited names a weak baseline as the mechanism that manufactures novel-method wins.)*
- **Match the training / HPO / compute budget across models — the #1 fairness threat — or disclose the
  gap.** "New ≠ better; the new model was just tuned harder / given more VRAM / trained longer." Either
  **match** the iteration budget *(mandibular canal, tooth: same 30k / 150-epoch budget for all)* or,
  where hardware forbids parity, **disclose the disparity in the open** *(liver: 8.5 vs 28 vs 40 GB VRAM,
  ~11 vs ~32 training-days, stated plainly)* — never silently tune only the home model. nnU-Net Revisited
  makes matched compute a first-class requirement.
- **Report variance over a single run.** A single-run leaderboard ranks by *skill + luck*: train over
  **multiple seeds** and report the spread, so the ranking is shown to be stable rather than a lucky
  draw. nnU-Net Revisited names **inter-publication variance** (the same baseline spanning a wide DSC
  range across papers) as the reason one-number leaderboards are untrustworthy. This is the control the
  accepted papers most often **still omit** — a place a new study can clear the current bar.
- **Pre-specify the primary metric and the primary comparison.** Name — before data — the one metric and
  the one contrast (proposed vs the strong baseline) the claim rests on. Choosing the metric or facet
  where you happen to win, after seeing the results, is cherry-picking; a multi-facet win is credible
  only when the primary was fixed in advance.

## Commit to a paired delta, not a side-by-side table

Run all models on the **same cases** so the between-model difference can be **tested**, not eyeballed.
The accepted comparisons pair and test: **Friedman + pairwise Wilcoxon signed-rank + Bonferroni** for
bounded, non-normal per-case Dice *(tooth)*, **repeated-measures ANOVA + post-hoc** *(mandibular canal)*,
**DeLong + Benjamini–Hochberg** for a paired ΔAUC *(spondylitis MRI, Eur J Med Res 2025
`10.1186/s40001-025-03731-9`)*. Two features recur: the test respects the **paired** structure, and
**multiplicity is corrected** when many pairs are compared. Deciding to pair is a design choice — you
cannot pair after collecting the arms separately. (Size this delta with `calc-sample-size` Test 16;
present it with the leaderboard figure below.)

## Rank honestly — a ranking is not a significance test

Put uncertainty on every model (a CI, or at least a tested delta) and **resist over-ranking** — but
rank against the right object: the **paired Δ and its CI**, not the overlap of two marginal CIs. Two
marginal intervals can overlap heavily while the paired Δ excludes zero, because the covariance the
paired test uses is invisible in the marginals; non-overlap implies a difference, overlap implies
nothing either way. Models inside the critical difference are **not separated by the test** — leave
them unranked rather than reporting a demonstrated tie. Disaggregate
(per-structure / per-class) and show **where the winning model still fails** — the honest negative
(a structure that collapses for all models, a fusion strategy at chance) is an acceptance asset, not a
liability. A corollary the corpus surfaced: a CI must be **believable for the N** — an implausibly tight
interval on a small test set is a red flag, not reassurance.

## What this does NOT replace

- **metric selection** (Dice + a boundary metric; AUROC + AUPRC) → `/model-evaluation`; **validation
  design + the split-leakage gate** → `/model-validation`; **sizing the between-model delta** →
  `calc-sample-size` `references/multi_model_comparison_sample_size.md` (Test 16); **presenting the
  comparison** → `make-figures` `exemplar_plots/model_comparison_leaderboard.md` + `analyze-stats`
  `table-standards/table-types/model_comparison.md`; **which architecture to consider at all** →
  `/architecture-zoo`; **a model built by combining / adapting one set of parts** →
  `combine_models_ablation_design.md`.

This is the **fair-comparison decision** for a model-vs-model study — the one that turns "our model won"
into "the comparison was fair, and our model won". Decide it before data collection.

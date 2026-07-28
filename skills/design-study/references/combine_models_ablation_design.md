# Combine / adapt / fine-tune existing models — design the comparator as an ablation

For a study whose model is built by **combining, adapting, or fine-tuning existing models** —
nnU-Net, TotalSegmentator, SAM / MedSAM, a pretrained backbone (the models `/architecture-zoo`
helps you choose) — the single decision that most determines acceptance is the **comparator**: you
must show that the combination / adaptation **earns its complexity**. Reverse-engineered from
accepted open-access papers (cited by DOI as design facts). It extends the Phase-3 *fine-tuning
contribution baseline* note (framed there for NLP/LLM) to imaging combine-existing studies, and it
is a **design-time** decision — none of these contrasts can be added after data collection.

## The failure the reviewer expects

*"Our combined model achieved Dice 0.90."* — with no decomposition, the reviewer cannot tell whether
the combination did anything; maybe the best single component alone scores 0.89. A single headline
number for a multi-component model is the **rejected** pattern. The accepted pattern **isolates what
the combination adds**.

## Design the ablation ladder (register the baselines before data collection)

Pre-specify the baselines the combined model must beat — each on the **same test set**, a
**patient-level** split, with a **paired CI** on the difference:

- **Un-adapted / off-the-shelf base** — the foundation model *without* your fine-tuning, or the
  pretrained backbone *without* your head. Proves the **adaptation** helps, not just the base.
  *(PCaSAM, npj Digital Medicine 2025 `10.1038/s41746-025-01756-2`: the fine-tuned model beats the
  un-adapted generalist foundation model and other baselines.)*
- **Best single component** — if you combine A + B, beat the better of A-alone / B-alone. Proves the
  **combination** helps. *(Embed-MedSAM, npj DM 2025 `10.1038/s41746-025-01881-y`: +≈16% Dice over
  the second-best model; VIBESegmentator, Eur Radiol 2025 `10.1007/s00330-025-12035-9`: positioned
  against the off-the-shelf tools — TotalSegmentator + spine + body-composition — it was seeded
  from.)*
- **Direct-train vs transfer** — if you fine-tune a pretrained model, compare against **training the
  same architecture from scratch** on your data. Isolates the pretrained component's contribution.
  *(Medulloblastoma nnU-Net, Radiology: AI 2024 — direct-train vs adult-glioma-pretrained-then-
  fine-tuned as the whole point of the study.)*
- **Nested incremental value** for a clinical/radiomics/DL combination (clinical → +radiomics → +DL
  → integrated) is the same discipline on tabular+imaging features — see Phase 3 *incremental value*
  and `analyze-stats` `incremental_value` table-type.

## Ground the gain in the clinical deliverable

A modest Dice / AUC delta reads as consequential only when tied to the endpoint clinicians use:
a **downstream clinical metric** *(PCaSAM: PI-RADS AUC on the external set)* or a **volume-agreement
statistic** — ICC / Bland–Altman / Lin's concordance *(CRLM total tumor volume, Eur Radiol Exp 2023
`10.1186/s41747-023-00383-4`, ICC 0.98; orbital-lymphoma volumetry, Neuroradiology 2024
`10.1007/s00234-024-03429-5`)* — not the segmentation metric alone.

## The leakage trap specific to reusing pretrained models

The base model you reuse may have been **developed on data that overlaps your test set** — the
`/model-sourcing` trap (evaluating on the benchmark the base was trained or tuned on, so the arm
reads like validation while being closer to a training-set score). **Pin the base-model
revision** and check its training corpus against your external set before you trust the number.
nnU-Net's self-configuration is attractive precisely because hyperparameters are set from the
**training data's fingerprint**, not tuned on the reported test folds.

## Reproducibility is part of the design for a combine-existing study

Reviewers of a "we built on X" paper expect to be able to run it. Decide **up front** to open
weights / code and to pin the base-model revision (`/architecture-zoo` records the licence — mind
non-commercial base weights such as nnInteractive / ConvNeXt V2 / most medical FMs).

## What this does NOT replace

- **metric selection** (Dice + a boundary/agreement metric) → `/model-evaluation`; **validation
  design + the split-leakage gate** → `/model-validation`; **which venue tier** the design lands at
  → `venue_accept_recipe.md`; **the model choice + its licence** → `/architecture-zoo` +
  `/model-sourcing`.

This is the **comparator-design decision** for a combine-existing-models study — the one that turns
"our model scored X" into "the combination is *why* it scored X". Decide it before data collection.

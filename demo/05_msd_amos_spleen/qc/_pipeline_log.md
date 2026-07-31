# Pipeline log — Demo 5 (MSD Task09 → AMOS22 spleen ladder)

Nine days on a GPU cluster plus a manuscript pass. Unlike Demos 1–3 this was not one
`orchestrate --e2e` invocation: the imaging stages are site-bound and were driven by hand, and the
friction that produced is the point of the demo (`FRICTION.md`). This log records what ran, what it
produced, and what failed.

## Stage 0–1 — profile, then split

| Step | Skill / script | Output | Result |
|---|---|---|---|
| Profile MSD Task09 | `/profile-imaging` | `qc/dataset_profile_msd.json` | **1 Major — `TEST_SET_UNLABELLED`**: the shipped test split carries no ground truth, so it cannot yield Dice. Acted on: the held-out set was carved from labelled data instead. |
| Profile AMOS22 | `/profile-imaging` (re-run with `--target-label 1`) | `qc/amos22_dataset_profile_spleen.json` | **2 Major + 1 Minor.** `LABEL_EMPTY` on `amos_0057`, `amos_0115`, `amos_0541`; `TEST_SET_UNLABELLED` on the 240-case test split; **`INTENSITY_SCALE_INCONSISTENT` (Minor)** — "500/600 cases bottom out near air and the rest do not". The last one names the property that later broke rung 3. **It was not acted on.** |
| Build split | `pipeline/build_split.py` | `splits/split_assignment.csv`, `splits/split_seed.txt` | 41 labelled → 32 train / 9 held-out, seed 42 |
| Split-leakage gate | `/model-validation` `check_split_leakage.py --strict` | `qc/split_leakage.json` | **OK** — 41 rows, 41 subjects, 0 overlap, seed recorded |

## Stage 2 — preprocessing declared, and its counterfactual

| Step | Output | Result |
|---|---|---|
| Declare the real manifest | `manifests/preprocessing_manifest.json` | 4 transforms, all `fit_scope: train`, `stage: after_split` |
| Preprocessing-leakage gate | `qc/preprocessing_leakage.json` | **OK** |
| Declare the naive counterfactual | `manifests/preprocessing_manifest_naive.json` | the obvious way of using nnU-Net: every case in `nnUNet_raw`, split afterwards |
| Same gate, counterfactual | `qc/preprocessing_leakage_naive.json` | **3 × `PREPROCESS_BEFORE_SPLIT` (Major)** — the gate must fail here, and `reproduce.sh` asserts that it does |

## Stage 3–5 — sourcing, training, inference

nnU-Net v2 vetted by hand (`/model-sourcing`); the benchmark-provenance conflict was found here and
is disclosed in the manuscript. Training: 5 folds × 100 epochs, `3d_fullres`, `nnUNet_compile=f`
(the compiler refuses compute capability < 7.0). Inference: 5-fold ensemble, nnU-Net defaults with
mirroring TTA, on all three arms — confirmed from the run logs, not from intent.

**Three jobs died before anything ran** (see `FRICTION.md`): a Triton refusal on a Pascal GPU, a
node-local container store, and a node with no route to the registry. Later, two silent failures:
absolute symlinks invisible inside the prediction container (nnU-Net reported "0 cases" and **exited
0**), and a per-node Python path difference that killed the evaluation step twice — the second time
*after* rung 3's predictions had already been computed on a GPU.

## Stage 6 — evaluation

| Arm | Command | Result |
|---|---|---|
| rung 1 | `evaluate_segmentation.py --arm rung1_msd_heldout` | 9 evaluated, 9 scored |
| rung 2 | same, `--arm rung2_amos_ct` | 300 evaluated, 298 scored, 2 target-free (**both predicted a spleen that is not there**), 28 empty predictions |
| rung 3 | same, `--arm rung3_amos_mri` (CPU-only job after the dependency fix) | 60 evaluated, 59 scored, 1 target-free, 20 empty predictions |
| normalisation evidence | `normalizer_modality_evidence.py`, **both** external arms | the control arm is what made the mechanism a measurement rather than an anecdote |
| metric unit tests | `test_evaluate_segmentation.py` | **18/18 pass** on synthetic volumes with answers derived on paper |

## Stage 7 — analysis, figures, manuscript

`analysis/make_tables.py` → 5 tables; `analysis/make_figs.py` + `pipeline/aggregate_results.py` +
the shipped `/make-figures` R pipeline → 5 figures (`analysis/figures/_figure_manifest.md`).
`make_tables.py` and `aggregate_results.py` compute the headline medians by **independent code
paths** and agree to the last reported digit.

References: 13 entries, every one resolved by DOI against CrossRef/PubMed. A fuzzy bibliographic
query returned the **wrong paper for two of the first four** attempts and those results were
discarded; three further candidates could not be resolved and were **not cited**. One entry (the
AMOS Zenodo deposit) was removed from the bibliography because its creator string is unpunctuated,
which every parser mis-splits — the DOI is cited in Data-availability instead. `verify-refs`: 13/13
OK.

Reporting: CLAIM 2024, 44 items, assessed individually — `qc/reporting_checklist.md`. 23 PRESENT,
10 PARTIAL, 7 MISSING, 4 N/A. The MISSING rows are left visible; four of them cannot be closed from
the public data.

## Stage 8 — self-review panel, one round

`/self-review --panel` with a **cross-substrate** roster (the manuscript was drafted by Claude, so a
Claude-only panel would inherit its blind spots). Full record: `qc/self_review.md`.

**The Codex reviewer returned a Reject, and was substantially right.** Eight Major findings were
accepted and applied, including three that changed what the paper claims: rung 3 is a *constructed*
test rather than a discovered failure; the causal attribution exceeded the design; and one authored
example cannot support general claims about tooling. Two of the author's own statements were shown
to be false against the shipped artifacts — an Abstract sentence contradicted by Table 2, and a
"registered in advance" claim the repository cannot substantiate.

Two Claude subagents died mid-run (API errors, then a stalled resume). `check_panel_diversity
--strict` fired `PANEL_UNDERRETURN` for exactly that reason, which is recorded rather than worked
around; the statistics lens was re-probed on the other substrate and returned two further findings.

## Stage 9 — lock

`manifest.lock.json` fingerprints the 14 artifacts every reported number derives from
(`version_dataset.py verify --strict`: **14/14 match**). It is not yet wired into CI — the repository's
demo-manifest CI step covers Demos 1–3 only, and extending it is a gate change left for the
maintainer.

## What is not in this log

No presentation, no DOCX-to-portal packaging, no journal selection. This is a demonstration write-up,
not a submission.

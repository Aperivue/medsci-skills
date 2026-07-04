# Challenge card — model-scaffold (the build → validate chain)

## Problem
A clinician-researcher wants to *build* a medical-imaging model, not just validate one
an engineer handed over. But a hand-rolled training repo is where the metric-inflating
mistakes start: an image-level (not patient-level) split, an unrecorded seed, dropout
left on at inference, training that accidentally touches the test set. These are
exactly the defects `/model-validation` (Phase 1) catches *after the fact*. This skill
prevents them *at generation time*.

## What the gate does
`scripts/scaffold.py` stamps out a **runnable PyTorch segmentation repo** with the
reproducibility guarantees baked in **by construction**:
- a **patient-level, seed-locked split** written as an auditable artifact
  (`splits/split_assignment.csv` + `split_seed.txt`) — disjoint by construction, so it
  passes `/model-validation`'s `check_split_leakage.py`;
- a `train.py` that seeds every RNG + sets cuDNN deterministic + builds the training
  loader from the **train split only**, and an `evaluate.py` that infers under
  `model.eval()` + `torch.no_grad()` — so it passes this skill's
  `check_training_hygiene.py`;
- `model.py` (a small configurable U-Net), `dataset.py` (reads the frozen split, never
  re-splits), `losses.py`, `config.yaml`, `requirements.txt`, `REPRODUCIBILITY.md`, and
  a `methods_stub.md` with `[VERIFY]` placeholders (no fabricated numbers).

It **integrates** MONAI / nnU-Net / TorchIO (referenced in the generated requirements),
it does not reimplement them. The generated repo is what the user runs on a GPU; the
gates here only verify the **network-free** parts.

## Fixture (synthetic only — no real images, no PII)
- `fixture/manifest.csv` — 12 synthetic patients (1–2 images each).
- `expected/split_assignment.csv` — the deterministic patient-level split for seed 42.

## Expected (`verify.sh`, network-free)
1. `scaffold.py` emits the repo; the split matches `expected/split_assignment.csv` and
   is **patient-disjoint** (proven inline) with seed 42 recorded.
2. every emitted `.py` is valid Python.
3. the emitted repo **passes `check_training_hygiene.py --strict`** (clean).
4. **torch tier (self-skipping):** if torch is installed, `model.py` builds, the forward
   output shape is `(2,1,32,32)`, gradients flow, and the loss is reproducible under a
   fixed seed. If torch is absent it prints `SKIP` and exits 0 — runnability is a
   documented local check, **never** claimed as CI coverage.
5. **breadth + fine-tuning provenance:** all six tasks (segmentation, classification,
   detection, synthesis, ssl, **finetune**) scaffold to the same task-independent frozen
   split with hygiene-clean code. For `finetune`, the repo also carries a pretrained-weight
   provenance record (`PRETRAINED.md` + a `pretrained:` block in `config.yaml`); stripping
   that record makes `check_training_hygiene` fire `PRETRAINED_PROVENANCE_MISSING` (Minor) —
   the gate has teeth against a hand-rolled fine-tune whose starting checkpoint is unrecorded.

This is the build → validate chain executed end to end: a generated repo whose split a
Phase-1 gate would clear and whose training code this phase's gate clears.

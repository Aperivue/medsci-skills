---
name: explainability
description: >
  Produce or audit the interpretability/explainability analysis of a medical-imaging model —
  Grad-CAM / Grad-CAM++ / attention-rollout / saliency / integrated-gradients — so it clears the rigor
  bar a reviewer expects: mandatory Adebayo sanity checks (model- and data-randomisation), a
  quantitative localisation metric against ground truth (IoU / pointing game / Dice) instead of eyeballed
  examples, a cohort-level result rather than cherry-picked cases, and attribution framing rather than
  "proof the model is correct". Emits an explainability-report manifest and a deterministic rigor gate.
  Integrates captum / pytorch-grad-cam; it does not reimplement them, and never runs a model on real
  patient data.
triggers: explainability, interpretability, saliency, saliency map, grad-cam, gradcam, grad-cam++, attention map, attention rollout, integrated gradients, captum, pytorch-grad-cam, heatmap, class activation map, CAM, feature attribution, sanity check, Adebayo, model randomization, localization metric, pointing game, IoU with ground truth, XAI, explainable AI, model looks at, faithfulness
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Explainability Skill

## Purpose

A saliency / Grad-CAM heat-map is the **most over-interpreted artifact** in medical-imaging AI: a
colourful map over the lesion is routinely presented as proof the model "looks at the right thing."
Adebayo et al. (*NeurIPS* 2018) showed many saliency methods produce visually convincing maps that are
**independent of the model's learned weights and of the labels** — so they explain nothing. This skill
produces an explainability analysis that clears the rigor bar, and audits an existing one, so the map
is trustworthy before it reaches a manuscript (CLAIM 2024 / TRIPOD+AI interpretability items).

It sits alongside evaluation in the lane: `/architecture-zoo` → `/preprocess-imaging` →
`/model-scaffold` → `/model-validation` → `/model-evaluation` + **explainability** →
`/write-paper` + `/check-reporting`. It **integrates** captum / pytorch-grad-cam (referenced in the
plan); it does not reimplement them and never runs a model on real patient data.

## When to use
- You produced (or are about to produce) saliency / Grad-CAM / attention maps and want them reported
  to the standard a reviewer expects.
- You want to audit an explainability analysis for the four failure modes below.

## When NOT to use
- Discrimination / calibration metrics → `/model-evaluation` then `/analyze-stats`.
- Split or preprocessing leakage → `/model-validation` / `/preprocess-imaging`.
- LLM/MLLM faithfulness & hallucination → `/mllm-eval`.
- Reimplementing captum / pytorch-grad-cam → out of scope (this skill wires and audits them).

## The four failure modes (what the gate enforces)
1. **Saliency as validation.** A map is *attribution*, not proof the model is correct or that the
   relationship is causal. Frame it as "where signal is attributed", never as "the model is right".
2. **No sanity check.** Run the Adebayo **model-randomisation** and **data-randomisation** tests. A map
   that survives neither is uninterpretable; both axes are the minimum bar.
3. **No quantitative localisation.** If you claim the map localises the finding, measure it — IoU /
   pointing game / Dice against ground-truth masks — do not eyeball a few examples.
4. **Cherry-picked examples.** Report a cohort-level result, not a handful of hand-picked cases.

## Workflow

### Phase 1 — Produce the maps (integrate, don't reimplement)
Choose the method for the architecture (`references/explainability_guide.md`): Grad-CAM / Grad-CAM++
for CNNs, attention-rollout for ViTs, integrated-gradients / SHAP for attribution. Wire captum or
pytorch-grad-cam; do not write a new CAM implementation.

### Phase 2 — Sanity-check and quantify
- Run the **model-parameter randomisation** and **data (label) randomisation** tests (Adebayo 2018);
  a faithful map degrades when the model/labels are randomised.
- Compute a **quantitative localisation metric** against ground-truth masks (IoU / pointing game /
  Dice) over the cohort — not a visual impression.

### Phase 3 — Emit the explainability-report manifest
```json
{
  "method": "grad-cam++",
  "n_examples": 200,
  "cohort_level": true,
  "localization_metric": "iou",
  "localization_value": 0.63,
  "sanity_checks": ["model_randomization", "data_randomization"],
  "interpretation": "localization"
}
```
`interpretation`: `attribution` / `localization` / `faithfulness` (descriptive) — never
`validation` / `causal` (overclaim).

### Phase 4 — Gate the report (deterministic)
```bash
python3 scripts/check_explainability_report.py --manifest explainability_report.json --strict
```
Verdicts: `SALIENCY_AS_VALIDATION`, `NO_SANITY_CHECK`, `NO_LOCALIZATION_METRIC` (Major);
`INSUFFICIENT_SANITY`, `CHERRY_PICKED_EXAMPLES`, `MISSING_METHOD` (Minor). The verdict is reproduced
by rule on the manifest, never asserted from prose.

## Integration
- **`/model-evaluation`** — explainability accompanies the held-out metrics as a secondary analysis.
- **`/self-review`** `ai_overclaiming` / `image_synthesis` probes audit saliency overclaiming in a
  finished manuscript; this skill *produces* the rigorous analysis they look for.
- **`/check-reporting`** — the manifest documents the CLAIM 2024 / TRIPOD+AI interpretability items.

## Anti-Hallucination

- **Never fabricate saliency maps, localisation metrics, or sanity-check results.** Every value in the
  manifest comes from the researcher's executed XAI code — never invented. This skill designs and
  audits the analysis; it does not run a model on real patient data.
- **Never present a saliency map as proof of model correctness or causation.** A map is attribution;
  claiming it validates the model is the overclaim this skill exists to prevent (`SALIENCY_AS_VALIDATION`).
- **Never report an explainability-audit "pass" without running `check_explainability_report.py`.** The
  rigor verdict is reproduced deterministically, never asserted from prose.
- **Integrate, don't reimplement.** Reference captum / pytorch-grad-cam; do not write a new CAM /
  attribution implementation or claim results for one.

## Reproducible challenge
`scripts/check_explainability_report_challenge/` ships a synthetic weak/strong report pair with a
network-free `verify.sh` wired into the skill's validation commands.

<!-- AUTO-GENERATED from skills/explainability/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# explainability

> Produce or audit the interpretability/explainability analysis of a medical-imaging model — Grad-CAM / Grad-CAM++ / attention-rollout / saliency / integrated-gradients — so it clears the rigor bar a reviewer expects: mandatory Adebayo sanity checks (model- and data-randomisation), a quantitative localisation metric against ground truth (IoU / pointing game / Dice) instead of eyeballed examples, a cohort-level result rather than cherry-picked cases, and attribution framing rather than "proof the model is correct". Emits an explainability-report manifest and a deterministic rigor gate. Integrates captum / pytorch-grad-cam; it does not reimplement them, and never runs a model on real patient data.

**Invoke:** `/explainability` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`explainability` activates on requests such as: explainability, interpretability, saliency, saliency map, grad-cam, gradcam, grad-cam++, attention map, attention rollout, integrated gradients, captum, pytorch-grad-cam, heatmap, class activation map, CAM, feature attribution, sanity check, Adebayo, model randomization, localization metric, pointing game, IoU with ground truth, XAI, explainable AI, model looks at, faithfulness.

## Quality Card

**Purpose** — Stop the most over-interpreted artifact in medical-imaging AI — a saliency/Grad-CAM heat-map presented as proof the model 'looks at the right thing' — from reaching a manuscript without sanity checks, a quantitative localisation metric, a cohort-level result, and attribution (not validation) framing.

**Safety boundaries**

- Advisory plus deterministic-audit only: never alters maps, metrics, or sanity-check results.
- The rigor verdict is reproduced by a stdlib script (rule on the report manifest), never asserted from prose.
- Integrates captum / pytorch-grad-cam by reference; it does not reimplement them and never runs a model on real patient data.

**Known limitations**

- Audits the declared report manifest, not the executed XAI code; a mislabelled interpretation or an unrun sanity check recorded as run can hide a real gap.
- A clean explainability audit is necessary, not sufficient — discrimination, calibration, and validation-design gates still apply.

**Validation**

- `python3 scripts/check_explainability_report.py --manifest <explainability_report.json> --strict`
- `bash scripts/check_explainability_report_challenge/verify.sh  # deterministic, network-free`

**Evidence** — `ci_validator`

## Bundled resources

**References** (`skills/explainability/references/`):

- `explainability_guide.md`

**Scripts** (`skills/explainability/scripts/`):

- `check_explainability_report.py`
- `check_explainability_report_challenge/` (6 files)

## Source

Canonical definition: [`skills/explainability/SKILL.md`](../../skills/explainability/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*

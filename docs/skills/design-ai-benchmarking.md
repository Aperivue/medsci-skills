<!-- AUTO-GENERATED from skills/design-ai-benchmarking/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# design-ai-benchmarking

> Use when designing a study that benchmarks AI systems against a human-expert panel, before data collection. Plans the arms, decoupled rubrics with anchors, planted calibration probes, reviewer panel, inter-rater reliability targets and LLM-as-judge versus human adjudication.

**Invoke:** `/design-ai-benchmarking` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`design-ai-benchmarking` activates on requests such as: AI benchmarking, AI vs human expert, reader study design, expert panel evaluation, LLM-as-judge, AI evaluation rubric, model benchmark design, human baseline comparison, AI-output rating, evaluation rubric design.

## Quality Card

**Purpose** — Surface design and validity risks specific to AI-vs-human-expert benchmarks (rubric coupling, scale calibration, rater independence, judge choice) before data collection begins.

**Safety boundaries**

- Advisory only: writes decision notes plus rubric/schema artifacts, never ratings or analysis results.
- Calibration probes and reference labels are planted or adjudicated, never fabricated to fit a hypothesis.

**Known limitations**

- A design review reduces but cannot eliminate evaluation bias; it does not guarantee a valid benchmark.
- No standalone demo; rubric and panel decisions require domain-expert judgement.

**Validation**

- `carry the rubric and export schema into analyze-stats for ICC/agreement, then check-reporting (STARD-AI / CLAIM / TRIPOD+AI)`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/design-ai-benchmarking/references/`):

- `anchor_rotate_reader_allocation.md`
- `benchmark_export_schema.json`
- `elicitation_rubric_template.md`

## Source

Canonical definition: [`skills/design-ai-benchmarking/SKILL.md`](../../skills/design-ai-benchmarking/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*

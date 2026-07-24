---
name: model-sourcing
description: >
  Vet the concrete third-party model a study will be built on — this repository, this revision,
  this checkpoint — not the architecture family. Records a model dossier (source and version pin,
  licence and the file it was read from, intended use, pretrained-weight provenance, model task
  vs study task, reported validation, what the model was developed on, your evaluation arms) and
  gates it deterministically. Catches what a licence check and a citation count cannot: an
  evaluation arm sitting on the benchmark the model was developed or tuned on, so the arm reads
  like validation while being closer to a training-set score. Also an evaluation set inside a
  pretraining corpus, an unstated or use-incompatible licence, an unpinned revision, and a
  hardware claim never executed. It vets an artifact; it never downloads or runs one.
triggers: source a model, vet a model, pick a model, model provenance, model dossier, pretrained weights, checkpoint, HuggingFace model, GitHub model, model licence, weight provenance, is this model independent, benchmark overlap, trained on my test set, data contamination, model version pin, third-party model, can I use this model
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Model-Sourcing Skill

## Purpose

`/architecture-zoo` answers a literature question — which family of model suits this task. That
question has a stable answer. The next question does not: *which concrete artifact do I run?*
A repository, a revision, a checkpoint. That is a provenance question, and the two facts a
careful researcher usually checks are the two that cannot answer it.

The licence tells you whether you may use it. The citation count tells you whether others did.
Neither tells you **whether the number you are about to report means what you will say it means.**

The failure this skill exists for is the quietest one in the lane. A method developed and tuned
against a benchmark family gets evaluated by the next person *on that same family*, and the
resulting figure reads like validation while sitting much closer to a training-set score. Nothing
in the repository says so. The licence is clean, the paper is peer-reviewed and highly cited, the
task matches, the code runs on your GPU. The conflict lives in the **relationship** between two
facts that are documented in different places — what the model was developed on, and what you are
about to evaluate it on — and it becomes visible only when they are written down side by side.

Writing them down side by side is what the dossier is for.

## When to use
- You have a concrete candidate (a GitHub repo, a Hugging Face checkpoint, a paper's released
  weights) and are about to build a study on it.
- You are writing the Methods paragraph that says which model you used, and it has to survive a
  reviewer asking what it was trained on.
- You inherited a pipeline whose model came from somewhere nobody recorded.

## When NOT to use
- Choosing an architecture *family* → `/architecture-zoo` (archetypes and the task-to-architecture
  logic; deliberately not a live leaderboard).
- Building the training repo → `/model-scaffold`. Designing the validation study →
  `/model-validation`. Computing held-out metrics → `/model-evaluation`.
- Documenting a model **you** built → `/model-card` (Model Card + Datasheet).
- Auditing your own dataset before modelling → `/profile-imaging`.
- Evaluating an LLM/multimodal system on a clinical task → `/mllm-eval` (which owns
  pretraining-contamination of public benchmarks for that setting).

## Workflow

### Step 1 — write the dossier

One JSON file recording what is *known*, with unknowns left unstated rather than guessed:

```json
{
  "model": "OrganSeg-3D v2.5.1",
  "source": {"kind": "github", "url": "...", "version": "v2.5.1", "commit": "abc1234"},
  "licence": {"spdx": "Apache-2.0", "verified_from": "LICENSE at commit abc1234"},
  "intended_use": "research",
  "weights": {"pretrained": false},
  "task": {"model": "3d_ct_organ_segmentation", "study": "3d_ct_organ_segmentation"},
  "reported_validation": [{"dataset": "ExampleBench", "metric": "Dice", "source": "J Ex 2021"}],
  "developed_on": ["ExampleBench"],
  "evaluation_arms": [{"name": "external", "dataset": "OtherCohort-2026"}],
  "hardware": {"claimed": "any CUDA GPU", "verified_on": "GTX 1080 Ti", "verified": true}
}
```

Each field is read from the artifact, not from memory: the licence from the `LICENSE` file at the
pinned commit (a README badge is not the licence), `developed_on` from the paper's own account of
where the method was built and tuned, `hardware.verified` only after it has actually run.

`developed_on` is the field people skip, and it is the one the gate needs. A method that won a
challenge was tuned on that challenge.

### Step 2 — gate it

```bash
python3 scripts/check_model_provenance.py --dossier model_dossier.json \
    --out qc/model_provenance.json --strict
```

Stdlib-only, network-free — no repository is fetched and no licence resolved online, so the audit
re-runs anywhere the JSON travels. Verdicts:

| Verdict | Severity | Fires when |
|---|---|---|
| `BENCHMARK_PROVENANCE_CONFLICT` | Major | an evaluation arm uses a dataset the model was developed or tuned on |
| `EVAL_DATA_IN_TRAINING` | Major | an evaluation arm's dataset is inside the pretraining corpus |
| `LICENCE_UNSTATED` | Major | no licence recorded — which is not the same as a permissive one |
| `LICENCE_INCOMPATIBLE` | Major | a non-commercial / research-only licence under commercial or deployment intent |
| `WEIGHTS_PROVENANCE_UNKNOWN` | Major | pretrained weights whose training corpus is not stated |
| `TASK_MISMATCH` | Minor | the model's task is not the study's task |
| `NO_VERSION_PIN` | Minor | no commit, tag or revision |
| `VALIDATION_UNREPORTED` | Minor | no reported validation (dataset + metric + source) |
| `HARDWARE_UNVERIFIED` | Minor | hardware support claimed but never executed |
| `LICENCE_UNVERIFIED` | Minor | a licence is named but the file it was read from is not |

**The gate flags a relationship, not a reputation.** A dossier that declares
`developed_on: ExampleBench` passes cleanly as long as no evaluation arm uses ExampleBench.
Being developed on a benchmark is not a defect; evaluating on it and calling that independent is.
The clean fixture exists to prove exactly that distinction.

Dataset names are matched as **token sequences** with a small family-alias table, so
`MSD Task09 Spleen` matches `MSD` and `MS Cohort 2026` does not. Matching never falls back to
substring search.

### Step 3 — turn a Major into a study decision

A `BENCHMARK_PROVENANCE_CONFLICT` is rarely a reason to abandon the model — it is usually the
best-engineered option precisely because it was tuned hard. It is a reason to change **what the
arm is claimed to establish**:

1. Report that arm as a demonstration that the pipeline runs end to end, not as evidence the
   method works.
2. Put the evidential weight on an arm whose data **post-dates** the model, and say so with dates.
3. State the conflict in Methods and Limitations rather than leaving a reviewer to find it.

An `EVAL_DATA_IN_TRAINING` is different in kind: that arm produces a training-set score and cannot
be reported as validation at all.

Carry the dossier forward — `/model-validation` (arm design), `/model-evaluation` (what each arm
may claim), `/model-card` (provenance section), `/write-paper` (Methods + Limitations).

## Outputs

- `model_dossier.json` — the provenance record downstream skills and the Methods section read.
- `qc/model_provenance.json` — deterministic audit with verdicts.
- The arm-by-arm decision from Step 3, written into the study record.

## Anti-Hallucination

- **Never infer a fact the dossier does not state.** An unstated licence is `LICENCE_UNSTATED`,
  never "probably MIT"; an unstated pretraining corpus is a Major finding, never an assumption.
- **Never record a licence from a badge, a model card summary, or memory** — only from the licence
  file at the pinned revision, and record which file that was.
- **Never mark hardware verified without executing it.** A support matrix and what the stack
  actually runs is a different claim; a CUDA capability the compiler accepts may still be refused
  by a compiler in the same stack.
- **Never report an arm as independent validation when the gate flags a provenance conflict.**
- If a provenance fact cannot be established from the artifact, leave it unstated and let the
  gate say so.

## Deterministic gate

`scripts/check_model_provenance.py` — 10 verdicts by set arithmetic over the dossier, stdlib-only
and network-free. Reproducible challenge:
`bash ${CLAUDE_SKILL_DIR}/scripts/check_model_provenance_challenge/verify.sh`.
Regression suite: `bash ${CLAUDE_SKILL_DIR}/tests/test_model_provenance.sh`.

## Boundaries

```
architecture-zoo (which family?) -> model-sourcing (this skill: which artifact, and what may its
  numbers claim?) -> profile-imaging / preprocess-imaging -> model-scaffold -> model-validation
  -> model-evaluation -> model-card -> write-paper
```

<!-- AUTO-GENERATED from skills/model-sourcing/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# model-sourcing

> Vet the concrete third-party model a study will be built on — this repository, this revision, this checkpoint — not the architecture family. Records a model dossier (source and version pin, licence and the file it was read from, intended use, pretrained-weight provenance, model task vs study task, reported validation, what the model was developed on, your evaluation arms) and gates it deterministically. Catches what a licence check and a citation count cannot: an evaluation arm sitting on the benchmark the model was developed or tuned on, so the arm reads like validation while being closer to a training-set score. Also an evaluation set inside a pretraining corpus, an unstated or use-incompatible licence, an unpinned revision, and a hardware claim never executed. It vets an artifact; it never downloads or runs one.

**Invoke:** `/model-sourcing` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`model-sourcing` activates on requests such as: source a model, vet a model, pick a model, model provenance, model dossier, pretrained weights, checkpoint, HuggingFace model, GitHub model, model licence, weight provenance, is this model independent, benchmark overlap, trained on my test set, data contamination, model version pin, third-party model, can I use this model.

## Quality Card

**Purpose** — Establish what a third-party model's numbers are allowed to claim, before a study is built on it — by writing the provenance facts that live in different documents into one record and auditing the relationships between them, chiefly whether an evaluation arm sits on the benchmark the model was developed against.

**Safety boundaries**

- Audit only: never downloads, executes, fine-tunes, or benchmarks a model, and never fetches a repository or resolves a licence over the network.
- Every verdict is decided by set arithmetic over the dossier JSON; an unstated fact yields a finding rather than an inferred value.
- Stdlib-only, so the audit reproduces anywhere the dossier travels.

**Known limitations**

- The dossier is taken at face value: the gate cannot tell that a stated licence is wrong or that `developed_on` is incomplete, so the reading of the artifact is the researcher's responsibility and the gate audits the consequences.
- Dataset matching is token-sequence based with a small family-alias table; two names for the same corpus that share no leading token (a private cohort renamed between papers) will not be matched.
- A clean dossier is necessary, not sufficient: split disjointness (model-validation), preprocessing leakage (preprocess-imaging) and metric choice (model-evaluation) are separate gates.

**Validation**

- `python3 scripts/check_model_provenance.py --dossier <dossier.json> --strict`
- `bash scripts/check_model_provenance_challenge/verify.sh  # deterministic, network-free`
- `bash tests/test_model_provenance.sh`

**Evidence** — `ci_validator`

## Bundled resources

**Scripts** (`skills/model-sourcing/scripts/`):

- `check_model_provenance.py`
- `check_model_provenance_challenge/` (8 files)

## Source

Canonical definition: [`skills/model-sourcing/SKILL.md`](../../skills/model-sourcing/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*

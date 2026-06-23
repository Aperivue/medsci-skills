<!-- AUTO-GENERATED from skills/self-review/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# self-review

> Pre-submission self-review for the user's own manuscripts, applying a reviewer perspective. Systematic check across 10 categories with research-type branching. Outputs Anticipated Major/Minor Comments with severity framing and optional R0 numbering for /revise pipeline integration.

**Invoke:** `/self-review` · **Tools:** Read, Write, Edit, Grep, Glob · **Model:** inherit

## When to use

`self-review` activates on requests such as: self-review, pre-submission check, check my paper, reviewer perspective, manuscript self-check.

## Quality Card

**Purpose** — Pre-submission self-review of the user's own manuscript from a reviewer's perspective across 10 categories, with severity-framed anticipated comments.

**Safety boundaries**

- Reviews the user's own manuscript only; not for reviewing external (journal-assigned) manuscripts.
- Does not silently fix non-AI-fixable issues; it flags them for the author.

**Known limitations**

- Anticipates likely reviewer comments; cannot predict a specific reviewer's focus.
- Advisory; produces recommendations, not manuscript edits.

**Validation**

- `python3 scripts/check_reviewer_team_consistency.py`
- `python3 scripts/check_domain_probe_sync.py --strict`
- `bash tests/test_panel_mode.sh`
- `bash tests/test_reference_adequacy.sh`
- `feed R0-numbered output into /revise`

**Evidence** — `demo`

## Bundled resources

**References** (`skills/self-review/references/`):

- `domain-probes/` (12 files)
- `exemplar_findings/` (8 files)
- `panel_review_template.md`

**Scripts** (`skills/self-review/scripts/`):

- `check_artifact_coverage.py`
- `check_claim_artifact.py`
- `check_classical_style.py`
- `check_cohort_arithmetic.py`
- `check_confounding_completeness.py`
- `check_panel_diversity.py`
- `check_paren_spans.py`
- `check_reference_adequacy.py`
- `check_reviewer_team_consistency.py`
- `check_scope_coherence.py`
- `check_supplement_hygiene.py`

## Source

Canonical definition: [`skills/self-review/SKILL.md`](../../skills/self-review/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*

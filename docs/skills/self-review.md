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
- `bash tests/test_editorial_impression.sh`
- `bash tests/test_rounded_delta.sh`
- `bash tests/test_figure_citation.sh`
- `bash tests/test_emphasis_density.sh`
- `bash tests/test_cv_leakage.sh`
- `python3 scripts/check_table_percentages.py --manuscript <manuscript.md> --strict  # recompute n (%) cells vs column denominator`
- `bash scripts/check_table_percentages_challenge/verify.sh  # deterministic, network-free`
- `feed R0-numbered output into /revise`

**Evidence** — `demo`

## Bundled resources

**References** (`skills/self-review/references/`):

- `domain-probes/` (22 files)
- `exemplar_findings/` (8 files)
- `panel_review_template.md`
- `phases/` (1 file)

**Scripts** (`skills/self-review/scripts/`):

- `check_artifact_coverage.py`
- `check_binning_consistency.py`
- `check_citation_order.py`
- `check_claim_artifact.py`
- `check_classical_style.py`
- `check_cohort_arithmetic.py`
- `check_confounding_completeness.py`
- `check_cv_leakage.py`
- `check_editorial_impression.py`
- `check_emphasis_density.py`
- `check_figure_citation.py`
- `check_null_calibration.py`
- `check_panel_diversity.py`
- `check_paren_spans.py`
- `check_reference_adequacy.py`
- `check_reviewer_team_consistency.py`
- `check_rounded_delta.py`
- `check_scope_coherence.py`
- `check_supplement_hygiene.py`
- `check_table_percentages.py`
- `check_table_percentages_challenge/` (6 files)

## Source

Canonical definition: [`skills/self-review/SKILL.md`](../../skills/self-review/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*

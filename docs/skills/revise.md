<!-- AUTO-GENERATED from skills/revise/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# revise

> Parse peer reviewer comments and generate a structured Response to Reviewers document with tracked manuscript changes. Classifies comments as MAJOR/MINOR/REBUTTAL, coordinates new analyses with /analyze-stats and /make-figures, and produces cover letter for editor.

**Invoke:** `/revise` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`revise` activates on requests such as: revise paper, respond to reviewers, revision letter, reviewer comments, major revision, minor revision, resubmit, R1 revision, revision round, response letter, point-by-point response.

## Quality Card

**Purpose** — Parse reviewer comments and generate a structured Response to Reviewers with tracked manuscript changes and an editor cover letter.

**Safety boundaries**

- Valid reviewer points are not argued away as rebuttal without user approval.
- Does not reference original page/line numbers after the manuscript has been revised.

**Known limitations**

- Coordinates new analyses/figures via other skills but does not itself produce statistics.
- No standalone demo; depends on the actual reviewer comments supplied.
- check_response_claims verifies only anchored claims (quoted added text, added citations); paraphrased edits are not machine-verifiable and are not flagged.

**Validation**

- `confirm every reviewer comment maps to a point-by-point response`
- `/verify-refs --strict on new citations`
- `python3 scripts/check_response_claims.py --response revision/response_to_reviewers.md --manuscript manuscript/manuscript.md --strict`
- `bash tests/test_response_claims.sh`
- `python3 scripts/check_density_complaint.py --comments revision/decision_letter.md --previous manuscript/manuscript_R0.md --revised manuscript/manuscript.md --strict`
- `bash scripts/density_complaint_challenge/verify.sh`

**Evidence** — `bundled_script`

## Bundled resources

**References** (`skills/revise/references/`):

- `r2r_voice.md`

**Scripts** (`skills/revise/scripts/`):

- `check_density_complaint.py`
- `check_response_claims.py`
- `density_complaint_challenge/` (5 files)

## Source

Canonical definition: [`skills/revise/SKILL.md`](../../skills/revise/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*

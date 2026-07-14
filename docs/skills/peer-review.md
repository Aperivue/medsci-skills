<!-- AUTO-GENERATED from skills/peer-review/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# peer-review

> Peer review assistant for medical journals. Generates structured review drafts with journal-specific formatting. Constructive developmental tone with systematic manuscript analysis.

**Invoke:** `/peer-review` · **Tools:** Read, Write, Edit, Grep, Glob · **Model:** inherit

## When to use

`peer-review` activates on requests such as: peer review, manuscript review, review paper, reviewer comments, 리뷰, 논문 리뷰, review invitation, journal review.

## Quality Card

**Purpose** — Draft a structured peer-review for a journal-assigned manuscript following the MedSci peer-review guideline (v2.5), with journal-specific formatting.

**Safety boundaries**

- Reviews assigned external manuscripts only; never edits the user's own manuscript.
- References are not generated from memory.

**Known limitations**

- A review is one reviewer's judgement, not an editorial decision.
- No standalone demo; quality depends on the manuscript supplied.
- The injection scan catches formatting-hidden text (colour/size/position/render-mode/metadata) deterministically; a phrase in visible prose is flagged for a human, not auto-removed.

**Validation**

- `confirm the draft addresses each section against the guideline rubric`
- `python3 scripts/check_domain_probe_sync.py --strict`
- `python3 scripts/scan_pdf_layers.py <manuscript.pdf> | python3 scripts/check_pdf_injection.py - --strict  # hidden-text / prompt-injection guard (extractor needs PyMuPDF)`
- `bash scripts/check_pdf_injection_challenge/verify.sh  # deterministic, network-free, PyMuPDF-free`

**Evidence** — `ci_validator`

## Bundled resources

**References** (`skills/peer-review/references/`):

- `aczel_2021_reviewer2_patterns.md`
- `domain-probes/` (23 files)
- `exemplar_reviews/` (7 files)
- `narrative_review_audit.md`
- `review_draft_template.md`
- `reviewer_calibration/` (2 files)
- `reviewer_profiles/` (6 files)

**Scripts** (`skills/peer-review/scripts/`):

- `check_pdf_injection.py`
- `check_pdf_injection_challenge/` (6 files)
- `check_review_request_types.py`
- `check_review_request_types_challenge/` (6 files)
- `check_self_improvement_claims.py`
- `scan_pdf_layers.py`

## Source

Canonical definition: [`skills/peer-review/SKILL.md`](../../skills/peer-review/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*

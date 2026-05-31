# Seed Issues

Copy-paste-ready issues a maintainer can file on GitHub to seed the contributor funnel.
These are drafts — paste the body into a new issue and apply the suggested labels. They
are intentionally scoped so a first-time contributor can pick one up.

---

## 1. Auto-generate per-skill docs from `SKILL.md` (+ CI drift gate)

**Labels:** `good first issue`, `documentation`, `enhancement`

**Body:**

Per-skill documentation currently lives only inside each `skills/<skill>/SKILL.md`. A
hand-maintained parallel copy under `docs/skills/` would drift, so we want it generated.

Build a small, deterministic, stdlib-only generator:

- `scripts/gen_skill_docs.py` reads the YAML frontmatter of every `skills/<skill>/SKILL.md`
  (`name`, `description`, `triggers`, `tools`, `model`) and writes one
  `docs/skills/<skill>.md` index page per skill, plus a `docs/skills/README.md` index
  linking them all.
- The page should link back to the source `SKILL.md` and list the skill's reference
  files if present.
- Add a `--check` mode that fails (non-zero exit) when the generated output is stale
  relative to the current `SKILL.md` files, and wire it into `.github/workflows/validate.yml`
  so doc drift fails CI — the same pattern as `scripts/validate_catalog_consistency.py`.

Acceptance:
- Running the generator produces `docs/skills/<skill>.md` for all skills.
- `--check` passes immediately after generation and fails after an unsynced `SKILL.md` edit.
- No personal paths, names, or PII in generated output (it is sourced from public SKILL.md).

---

## 2. Polish the 10 core skills' `SKILL.md` for first-time readers

**Labels:** `help wanted`, `documentation`

**Body:**

The most-used skills should each open with a crisp "what it does / when to use / when NOT
to use / minimal example" so a new clinician can orient in under a minute. Pick one skill,
tighten its `SKILL.md` opening, and confirm the validators still pass
(`bash scripts/validate_skills.sh`). One skill per PR keeps reviews small.

Core skills to polish (claim one in a comment):

- [ ] orchestrate
- [ ] write-paper
- [ ] analyze-stats
- [ ] make-figures
- [ ] check-reporting
- [ ] verify-refs
- [ ] meta-analysis
- [ ] revise
- [ ] peer-review
- [ ] sync-submission

Acceptance:
- The skill's `SKILL.md` clearly states purpose, when to use, when not to use, and a
  minimal example.
- `bash scripts/validate_skills.sh` and `python3 scripts/validate_skill_contracts.py` pass.

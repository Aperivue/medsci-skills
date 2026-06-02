# Seed Issues

Copy-paste-ready issues a maintainer can file on GitHub to seed the contributor funnel.
These are drafts — paste the body into a new issue and apply the suggested labels. They
are intentionally scoped so a first-time contributor can pick one up.

---

> The "auto-generate per-skill docs" issue that previously lived here has been implemented:
> `scripts/gen_skill_docs.py` generates `docs/skills/` and CI gates it via `--check`.

## 1. Polish the 10 core skills' `SKILL.md` for first-time readers

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

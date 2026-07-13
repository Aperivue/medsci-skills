<!-- AUTO-GENERATED from skills/contribute/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# contribute

> Offer your local changes back to the project — a journal profile you added, a checklist item you fixed, a skill you adapted to your department — as a pull request or an issue, without ever typing a git command. Detects what you changed against the installed version, scans it for patient data and identifiers, shows you every line, and sends nothing until you confirm. Also files feedback: a detector that fired wrongly, a step that failed on your file.

**Invoke:** `/contribute` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** sonnet

## When to use

`contribute` activates on requests such as: contribute, 기여, send my changes, share my edit, report a false positive, feedback, my journal is missing, open a PR, pull request, 오탐 신고, report a bug.

## Quality Card

**Purpose** — Let a clinician who has never opened a pull request give their change back to the project, without ever typing a git command and without leaking a patient.

**Safety boundaries**

- Nothing leaves the machine until the author has seen every line that would leave it and confirmed.
- Patient-level data and credentials are blockers: the line is deleted, not argued with.
- The safety scan is an aid, never a certificate — the skill says so to the user, every time.
- Touches only the installed skills; never the user's manuscripts or data.
- Reminders are opt-in and off by default; the setting governs reminders only and cannot weaken the safety scan.
- The star note is shown once, ever, and never repeated; it explains what a star is rather than asking for one.

**Known limitations**

- No pattern list recognises every patient name or every hospital; the scan narrows what the author must check, it does not replace the check.
- A pull request needs the GitHub CLI; without it the contribution still reaches the project as an issue.
- A modified file is sent whole (the shipped original is not kept on disk — only its hash), so the maintainer diffs it.

**Validation**

- `bash tests/test_contribution_safety.sh`
- `python3 scripts/find_local_changes.py --target claude`

**Evidence** — `bundled_script`

## Bundled resources

**Scripts** (`skills/contribute/scripts/`):

- `check_contribution_safety.py`
- `contribution_prefs.py`
- `find_local_changes.py`
- `star_repo.py`
- `submit_contribution.py`

## Source

Canonical definition: [`skills/contribute/SKILL.md`](../../skills/contribute/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*

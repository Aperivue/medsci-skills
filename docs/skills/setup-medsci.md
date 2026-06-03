<!-- AUTO-GENERATED from skills/setup-medsci/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# setup-medsci

> Diagnostic checklist for the MedSci Skills runtime. Verifies Python, R, Node, Claude Code, Git, Zotero, and configured MCP servers, and prints a pass/fail table with links to the right setup doc for any missing component. Read-only — does not install anything.

**Invoke:** `/setup-medsci` · **Tools:** Bash, Read · **Model:** inherit

## When to use

`setup-medsci` activates on requests such as: setup, install, environment, diagnostic, check setup, why doesn't this work, missing python, missing R, MCP not connected, 환경 설정, 설치 점검.

## Quality Card

**Purpose** — Check and prepare the local toolchain (Python/R/CLI deps) needed to run the skills.

**Safety boundaries**

- Confirms before destructive or system-wide changes; surfaces what is missing.
- Operates locally; does not transmit machine state.

**Known limitations**

- Environment coverage is best-effort across OSes; some hosts need manual steps.
- No standalone demo; an operational utility.

**Validation**

- `re-run the setup check and confirm all dependencies report present`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/setup-medsci/references/`):

- `setup-checklist.md`

## Source

Canonical definition: [`skills/setup-medsci/SKILL.md`](../../skills/setup-medsci/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*

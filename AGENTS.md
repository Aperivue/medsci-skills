# Working in this repository (Codex and other agents)

`CLAUDE.md` carries the same instruction for Claude Code, with its history. Codex reads this file,
not that one, so the fence is repeated here.

## `_corpus/` — do not read it, do not run anything against it

`_corpus/` is gitignored and may exist in a maintainer's working tree. Its `heldout/` papers are a
frozen test set: a number measured on them means *no detector was written knowing these papers*, and
reading one in order to write or justify a change is how a detector comes to know it.

- Do not open files under `_corpus/`.
- Do not run a detector, `grep`, `find`, or any scan across it. Name directories (`skills/`,
  `scripts/`, `tests/`) instead of scanning the repository root, or exclude it explicitly
  (`--exclude-dir=_corpus`).
- Do not cite a number derived from it as evidence for changing a detector.
- If a task seems to require it, stop and ask. It almost certainly does not.

## Everything else

`CONTRIBUTING.md` is the entry point: what to run before pushing (CI is the merge gate), the
worktree discipline, and what a change is expected to ship with.

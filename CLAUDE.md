# Working in this repository

## `_corpus/heldout/` — do not read, do not run anything against it

**This is the one instruction in this file that cannot be recovered from if you get it wrong.**

`_corpus/heldout/` holds a frozen set of real published papers whose entire purpose is to be
material **no detector was written knowing about**. Its protocol
(`reverse_engineer/HELDOUT.md`) states the spend rule directly:

| set | role | spent by |
|---|---|---|
| challenge-card fixtures | train | authored with the detector |
| the current corpus | validation | **acting on a fire** |
| a fresh frozen corpus | test — one unbiased number | **reading it** |

Reading is not a neutral act here. A fire rate measured on these papers asserts *"no detector was
written knowing this paper"*; reading one in order to author or justify a change is exactly how a
detector comes to know it. The protocol's own instruction is **"Never open them again except to
label a fire."**

So, when working anywhere in this repository:

- **Do not open** `_corpus/heldout/*.md`.
- **Do not run** a detector, a grep, or a scan across `_corpus/`.
- **Do not cite** a number derived from it as evidence for changing a detector.
- If a task seems to require it, stop and ask. It almost certainly does not.

`_corpus/` is gitignored, so `git status` will never show a change there and a clone will not carry
it. Neither fact protects it: **anything scanning the working tree sees it.** That is not
hypothetical — on 2026-07-31 an audit was launched against "the repository", three of its agents
reached `_corpus/heldout/`, and one ran a detector across the corpus and opened two of the papers.
The finding it produced was quarantined and not acted on, and the corpus in place was already spent,
so nothing measurable was lost. The next corpus is the one that reading destroys, and this file
exists because the fence was in a prompt instead of in the repository.

## Merging your own pull requests

The maintainer has authorized Claude to merge a pull request it opened, **without asking**, when all
of these hold: CI is green on the current head, there is no merge conflict, no review thread is open,
and the change is one of:

- a CI, test or tooling fix (workflows, `scripts/`, `tests/`, challenge-card `verify.sh` plumbing);
- a correction of a stated count, link or other fact in documentation;
- bookkeeping (distribution manifest, generated docs and catalogs, CHANGELOG entries);
- a refactor that changes no output a user sees.

Squash-merge, then say what was merged. **Ask first** for anything else, and always for:

- a change to what a detector flags or clears, or to its message — that is what a user is told about
  their manuscript;
- a change to a medical or research claim, or to a reporting checklist (`MAINTAINERS.md` requires
  founder review);
- a release, a version bump or a tag;
- anything touching `_corpus/`.

When a pull request mixes the two, it is the second kind.

## Everything else

`CONTRIBUTING.md` is the entry point: what to run before pushing (CI is the merge gate), the
worktree discipline, and what a change is expected to ship with.

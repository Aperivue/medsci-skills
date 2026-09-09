# Context-Engineering Alignment for Claude 5 Models — Design

**Date:** 2026-09-09
**Status:** approved (design); implementation planned per change-type
**Source material:** [`context-engineering-claude5.md`](../../../context-engineering-claude5.md) —
summary of *The New Rules of Context Engineering for Claude 5 Generation Models*

## Motivation

The upstream guidance is that newer models are over-constrained by prompt material written for
older ones: redundant instruction, front-loaded context, and repeated general exhortation cost
context without changing behavior. Anthropic removed >80% of Claude Code's system prompt with no
performance loss. This repository ships 55 `SKILL.md` files (~19,500 lines total) that are the
prompt surface for every skill, so the same audit applies here.

## Locked decisions

These were settled before design and constrain every change below.

1. **PR granularity — one *change type* per PR, cutting across skills.** Not one PR per skill.
   A PR applies a single kind of edit (e.g. "delete redundant generic anti-hallucination bullets")
   to the files that need it.
2. **Pilot before mass application.** Each change type lands first on a 2-file pilot, verified
   green against the full CI mirror, before extending to the remaining files.
3. **The "trust the model's judgment instead of strict rules" recommendation is OUT OF SCOPE for
   safety and determinism surfaces.** This repository's deterministic gates, anti-hallucination
   enforcement, `capabilities.yml` ownership, and `--strict` detector semantics are the product,
   not legacy over-constraint. Nothing in this program relaxes a gate, downgrades a severity, or
   converts a deterministic check into model judgment. The upstream advice is applied only to
   *documentation and explanation style*.
4. **No runtime cross-skill sharing.** Per [`docs/dedup_audit.md`](../../dedup_audit.md), skills are
   strictly self-contained: they ship standalone via `/publish-skill` and a skill folder must work
   when lifted out of the repo. Consolidation, where wanted, uses build-time vendoring — never a
   shared file that an installed skill would reach outside its own directory.

## Prior art found during design (and what it changed)

- **`scripts/check_domain_probe_sync.py` is already a general vendoring gate** — table-driven
  (`VENDOR_SETS`), self-discovering (it hashes every file under `skills/` and fails on content
  appearing in 2+ skills that is not declared), with `--strict` / `--sync` / `--root` modes. Any
  future consolidation in this program registers a set there rather than adding a second mechanism.
  It operates on whole files by sha256, so a *fragment inside* `SKILL.md` is not in its scope.
- **`docs/SKILL_TEMPLATE.md`** specifies the `## Anti-Hallucination` section as carrying
  **domain-specific** rules, and its publishing checklist says so explicitly. The identical generic
  block now present in 11 skills is therefore drift *away* from the template, not the template's
  intent.
- **`scripts/validate_skills.sh:171`** requires only that the `## Anti-Hallucination` *heading*
  exist. Bullet content is not gated, so trimming bullets keeps the gate green.

**Rejected alternatives.** Extracting the shared block into a per-skill vendored
`references/anti_hallucination_core.md` declared in `VENDOR_SETS` (adds 11 files and an indirection
hop for two bullets), and extending the vendoring gate to marker-delimited fragments (new
capability, disproportionate to two bullets). Both were rejected as machinery exceeding the
problem. The residual inline duplication of the two *convention-bearing* bullets is accepted as
the deliberate price of skill portability — the same conclusion `docs/dedup_audit.md` reached for
duplicated code idioms.

## Change type 1 — trim redundant generic anti-hallucination bullets

### Problem

Eleven `SKILL.md` files carry a byte-identical four-bullet `## Anti-Hallucination` block. Two of
those bullets carry repository-specific, non-obvious convention:

- the `/search-lit`-verified DOI/PMID routing and the `[UNVERIFIED - NEEDS MANUAL CHECK]` marker;
- the `[VERIFY]` marker for unverified clinical definitions, criteria, and guideline claims.

The other two are general exhortation that a Claude 5-generation model does not need repeated per
skill, and that no downstream skill or gate consumes:

- `**Never fabricate numerical results** — compliance percentages, scores, effect sizes, or sample
  sizes must come from actual data or analysis output.`
- `If a reporting guideline item, journal policy, or clinical standard is uncertain, state the
  uncertainty rather than guessing.`

### Change

Delete those two bullets from each affected file. Keep the heading, keep the two marker-convention
bullets, and keep every skill-specific bullet already present below them untouched.

**Deliberately unchanged:** the marker-convention bullets stay inline and duplicated across skills.
Portability requires the convention to be present in each standalone skill, and two stable bullets
do not justify a vendored file or a fragment-level gate.

### Affected files (11)

`check-reporting`, `grant-builder`, `find-cohort-gap`, `write-protocol`, `fill-protocol`,
`design-study`, `present-paper` (second block), `make-figures`, `revise`, `write-paper` (second
block), `self-review`.

`self-review`'s first bullet additionally documents its Phase 2.5c enforcement; that sentence is
preserved.

### Explicitly out of scope for this change type

Skills whose anti-hallucination block is *not* the identical generic one — `calc-sample-size`,
`design-ai-benchmarking` (a good example of the domain-specific rules the template asks for),
`present-paper`'s first block, `write-paper:702`, and the prose in
`write-paper/references/phase7_integrity_audits.md`. These differ in substance; editing them is a
content judgment, not a deduplication, and does not belong in a mechanical trim PR.

### Sequencing

- **PR 1 (pilot):** `check-reporting` and `grant-builder`. Purpose is to prove the change is
  gate-clean and to establish the regeneration flow, on a diff small enough to read.
- **PR 2:** the remaining nine files, same edit.

### Verification

CI is the authoritative gate for this program. The local toolchain on the authoring machine is
only partly able to mirror it, and the limits are load-bearing rather than incidental:

```bash
python scripts/gen_skill_docs.py --check   # runnable locally; green today
```

- **`python3` does not exist on this machine** — it resolves to the Microsoft Store alias stub. The
  interpreter is `python` (3.13.9). `scripts/run_ci_mirror.sh` calls `python3` internally and so
  cannot run locally without a shim; `scripts/validate_skills.sh` additionally requires `exiftool`,
  which is absent.
- **`gen_distribution_manifest.py` must NOT be run in write mode locally.** `core.autocrlf=true`
  with no `.gitattributes` means the working tree is CRLF while committed blobs are LF. The
  generator hashes working-tree bytes, so a local write-mode run rewrites all **1264** shipped-file
  hashes to CRLF values and breaks the self-updater's download verification. Its `--check` is
  therefore structurally red here and carries no signal.
- Consequently, a PR in this program edits shipped files without refreshing `metadata/`, and the
  `Distribution manifests in sync` check is **expected red** — the path `CONTRIBUTING.md` documents
  for contributors who cannot run the generator. Each PR body says so and asks the maintainer to
  refresh on an LF checkout.
- `docs/skills/` pages are generated from frontmatter, `skill.yml`, and bundled-resource listings,
  and do not embed `## Anti-Hallucination` body text, so prose edits inside that section produce no
  `docs/skills/` diff. Where a change type *does* reach the generated pages, run
  `python scripts/gen_skill_docs.py` and commit the regenerated output with the change.

Per-change-type assertions (exact grep counts before and after) live in the implementation plan
rather than here.

## Backlog — later change types, each its own PR

Listed for sequencing only; each needs its own design pass before implementation.

1. **Obvious-prose diet.** Trim per-skill preamble that restates what the skill's own structure
   already conveys.
2. **`skill.yml` structuring.** Move flag/output descriptions that exist as prose in `SKILL.md`
   into the structured contract, where the schema already has a field for them.
3. **Progressive-disclosure extension.** Several large `SKILL.md` files already defer detail via
   read-on-demand reference tables (`self-review` is the reference implementation). Extend the
   pattern to large files that still front-load.

## Risks

- **Breadth.** The prompt surface is the product; a careless mass edit degrades skill behavior.
  Mitigated by one change type per PR, a 2-file pilot each, and the CI mirror as the gate.
- **Generated-artifact drift.** `SKILL.md` edits propagate to `docs/skills/` and to the
  distribution manifests. Mitigated by running `gen_skill_docs.py --check` in every PR and by
  declaring the manifest refresh in the PR body, since it cannot be generated correctly from a CRLF
  working tree.
- **Over-application of upstream advice.** The upstream guidance targets over-constrained system
  prompts, not safety-critical deterministic gates. Locked decision 3 is the fence; any change that
  would relax a gate is out of scope by construction.

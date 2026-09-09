# Anti-Hallucination Boilerplate Trim — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete the two general-exhortation bullets from the `## Anti-Hallucination` block that is duplicated verbatim across 11 `SKILL.md` files, keeping the two repository-convention bullets and every skill-specific bullet intact.

**Architecture:** A pure prose deletion applied by a stdlib Python line filter that asserts exactly two removals per file. No new scripts, no new CI gates, no vendoring mechanism. Change type 1 of the program in the spec; the remaining change types get their own plans.

**Tech Stack:** Python 3.13 (stdlib only, invoked as `python` on this machine), git, `gh` CLI. Existing repo gates: `scripts/gen_skill_docs.py`, `scripts/gen_distribution_manifest.py`, `scripts/validate_skills.sh`, `scripts/run_ci_mirror.sh`.

**Spec:** [`docs/superpowers/specs/2026-09-09-context-engineering-alignment-design.md`](../specs/2026-09-09-context-engineering-alignment-design.md)

## Global Constraints

- **Never relax a gate.** No change in this plan may alter a severity, a `--strict` semantic, a deterministic check, or an anti-hallucination *enforcement* path. Only redundant explanatory prose is removed. (Spec, locked decision 3.)
- **Keep the `## Anti-Hallucination` heading in every file.** `scripts/validate_skills.sh:171` greps for the heading and fails the skill without it. Bullet content is not gated.
- **Keep both convention bullets** — the `/search-lit`-verified DOI/PMID routing with `[UNVERIFIED - NEEDS MANUAL CHECK]`, and the `[VERIFY]` marker bullet. These carry repository-specific convention and stay inline and duplicated by design (spec: portability).
- **NEVER run `python scripts/gen_distribution_manifest.py` in write mode on this machine.** `core.autocrlf=true` with no `.gitattributes`, so the working tree is CRLF while committed blobs are LF. The generator hashes working-tree bytes, so a local write-mode run rewrites **1264** shipped-file hashes to CRLF values and breaks the self-updater's download verification. `--check` is therefore structurally red locally and must be ignored; CI (Linux, LF) is the authority.
- **The working tree is CRLF.** Regex `$` anchors do not match after a line's text (a `\r` sits before the newline), and multi-line literal edits are fragile. Do line-based edits with the Python filter given in the tasks, not multi-line string replacement.
- **Local interpreter is `python`, not `python3`.** `python3` resolves to the Microsoft Store alias stub and fails. `scripts/run_ci_mirror.sh` calls `python3` internally and therefore cannot run here without a shim; `scripts/validate_skills.sh` requires `exiftool`, also absent. Local verification is limited to `gen_skill_docs.py --check` plus the grep assertions in each task; CI is the authoritative gate.
- **Fork workflow.** `origin` is `embed-Rayn/medsci-skills` (the user's fork); `upstream` is `Aperivue/medsci-skills`. PRs target `upstream` `main`. The user is a contributor, not the maintainer, so a red `Distribution manifests in sync` check is expected and is handled by a note in the PR body — this is the path `CONTRIBUTING.md` documents, not a failure.
- **Pushing and opening PRs are shared-state actions.** Stop and get explicit user confirmation before `git push` and before `gh pr create`.

## The exact edit

Two lines are deleted. Both appear exactly once per target file (verified by count).

Deleted:

```text
- **Never fabricate numerical results** — compliance percentages, scores, effect sizes, or sample sizes must come from actual data or analysis output.
- If a reporting guideline item, journal policy, or clinical standard is uncertain, state the uncertainty rather than guessing.
```

Kept (unchanged, in every file):

```text
- **Never fabricate references.** All citations must be verified via `/search-lit` with confirmed DOI or PMID. Mark unverified references as `[UNVERIFIED - NEEDS MANUAL CHECK]`.
- **Never invent clinical definitions, diagnostic criteria, or guideline recommendations.** If uncertain, flag with `[VERIFY]` and ask the user.
```

`skills/self-review/SKILL.md`'s first bullet carries an extra sentence about its Phase 2.5c enforcement; the filter matches whole lines, so that bullet is untouched.

**Do not touch `skills/academic-aio/SKILL.md`.** A loose grep for `state the uncertainty rather than guessing` returns 12 files, but academic-aio's variant reads *"If a compliance item, journal policy, or AI-search platform behavior is uncertain…"* inside a fully domain-specific block — the customization the template asks for, not boilerplate. The filter's exact-string match excludes it automatically; do not "fix" it.

---

### Task 1: Pilot trim — `check-reporting` and `grant-builder`

**Files:**
- Modify: `skills/check-reporting/SKILL.md:561-562`
- Modify: `skills/grant-builder/SKILL.md:250-251`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: the `trim_ah_bullets.py` filter body reproduced in Task 2, and a verified-clean precedent for the same edit on nine more files.

- [ ] **Step 1: Record the baseline counts (the assertion this task inverts)**

Run:

```bash
git status --short
python scripts/gen_skill_docs.py --check
```

Expected: `git status --short` prints nothing (clean tree; stash or commit anything present before proceeding). `gen_skill_docs.py --check` prints `OK: docs/skills/ in sync (59 skill pages + index).`

Then record the pre-edit state:

```bash
grep -c "Never fabricate numerical results" skills/check-reporting/SKILL.md skills/grant-builder/SKILL.md
grep -c "state the uncertainty rather than guessing" skills/check-reporting/SKILL.md skills/grant-builder/SKILL.md
```

Expected: each file reports `1` for both patterns (four `:1` lines total).

- [ ] **Step 2: Create the feature branch**

```bash
git checkout -b trim-generic-anti-hallucination-bullets-pilot
```

- [ ] **Step 3: Apply the deletion with the line filter**

Run this exactly as written (CRLF-safe: it splits on `\n` and compares with the trailing `\r` stripped, then rejoins unchanged bytes):

```bash
python - <<'PY'
import pathlib

TARGETS = [
    "skills/check-reporting/SKILL.md",
    "skills/grant-builder/SKILL.md",
]
# ASCII prefixes, deliberately: the full bullet contains an em dash (U+2014), and
# matching on it would make the filter hostage to the encoding this heredoc is
# decoded with. Both prefixes are unique per file, and academic-aio's variant
# starts "- If a compliance item," so it cannot match.
DROP_PREFIXES = (
    "- **Never fabricate numerical results**",
    "- If a reporting guideline item, journal policy, or clinical standard is uncertain",
)

for target in TARGETS:
    path = pathlib.Path(target)
    text = path.read_bytes().decode("utf-8")
    lines = text.split("\n")
    kept = [
        line for line in lines
        if not line.rstrip("\r").startswith(DROP_PREFIXES)
    ]
    removed = len(lines) - len(kept)
    assert removed == 2, f"{target}: expected 2 removals, got {removed}"
    path.write_bytes("\n".join(kept).encode("utf-8"))
    print(f"ok {target}: removed {removed}")
PY
```

Expected output:

```text
ok skills/check-reporting/SKILL.md: removed 2
ok skills/grant-builder/SKILL.md: removed 2
```

If an assertion fires, nothing was written for that file — re-read the file and reconcile against "The exact edit" above before retrying.

- [ ] **Step 4: Verify the deletion and that nothing else moved**

```bash
grep -c "Never fabricate numerical results" skills/check-reporting/SKILL.md skills/grant-builder/SKILL.md
```

Expected: `0` for both files (grep exits 1 when nothing matches — that is the pass condition here).

```bash
grep -c "Anti-Hallucination" skills/check-reporting/SKILL.md skills/grant-builder/SKILL.md
grep -c "UNVERIFIED - NEEDS MANUAL CHECK" skills/check-reporting/SKILL.md skills/grant-builder/SKILL.md
grep -c "flag with \`\[VERIFY\]\`" skills/check-reporting/SKILL.md skills/grant-builder/SKILL.md
```

Expected: `1` for each file on all three patterns — heading present, both convention bullets present.

```bash
git diff --stat
```

Expected: exactly 2 files changed, 4 deletions, 0 insertions.

```bash
git diff
```

Expected: only the two bullet lines removed per file; no line-ending churn, no reflowed neighbours. **If the diff shows whole files rewritten, stop** — that is CRLF damage; run `git checkout -- skills/` and re-read Step 3.

- [ ] **Step 5: Confirm the generated docs gate is still green**

```bash
python scripts/gen_skill_docs.py --check
```

Expected: `OK: docs/skills/ in sync (59 skill pages + index).`

The per-skill pages under `docs/skills/` are generated from frontmatter, `skill.yml`, and bundled-resource listings and do **not** embed the Anti-Hallucination body text (verified), so this edit produces no `docs/skills/` diff. If the check reports drift, run `python scripts/gen_skill_docs.py` and commit the regenerated pages with the change.

Do **not** run `gen_distribution_manifest.py` — see Global Constraints.

- [ ] **Step 6: Commit**

```bash
git add skills/check-reporting/SKILL.md skills/grant-builder/SKILL.md
git commit -m "$(cat <<'EOF'
docs(skills): drop redundant generic anti-hallucination bullets (pilot)

The numerical-results and state-the-uncertainty bullets are general
exhortation duplicated verbatim across 11 skills; no gate or downstream
skill consumes them, and docs/SKILL_TEMPLATE.md asks this section to carry
domain-specific rules instead. For check-reporting the second bullet is
already covered concretely by its own N/A-with-justification rule.

The two convention-bearing bullets stay inline in each skill: the
/search-lit routing and the [UNVERIFIED] / [VERIFY] markers must travel
with a standalone skill (docs/dedup_audit.md).

Pilot scope: two files, to prove the edit is gate-clean before the
remaining nine.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 7: Push and open the PR — CONFIRM WITH THE USER FIRST**

Do not run these until the user explicitly approves the push.

```bash
git push -u origin trim-generic-anti-hallucination-bullets-pilot
gh pr create --repo Aperivue/medsci-skills --base main \
  --head embed-Rayn:trim-generic-anti-hallucination-bullets-pilot \
  --title "docs(skills): drop redundant generic anti-hallucination bullets (pilot: 2 skills)" \
  --body "$(cat <<'EOF'
## Summary

- Deletes two general-exhortation bullets from the `## Anti-Hallucination` block in `check-reporting` and `grant-builder`: the `Never fabricate numerical results` bullet and the `state the uncertainty rather than guessing` bullet.
- Both are duplicated verbatim across 11 skills, are consumed by no gate or downstream skill, and run against `docs/SKILL_TEMPLATE.md`, which specifies this section as carrying **domain-specific** rules.
- The two convention-bearing bullets are kept inline in each skill (the `/search-lit` DOI/PMID routing and the `[UNVERIFIED - NEEDS MANUAL CHECK]` / `[VERIFY]` markers). Per `docs/dedup_audit.md` a skill must work when lifted out of the repo, so that convention is deliberately not centralized.
- Pilot scope: 2 of 11 files. The remaining nine follow in a separate PR once this is green.

Context: this is change type 1 of the alignment described in `docs/superpowers/specs/2026-09-09-context-engineering-alignment-design.md`. No gate, severity, or deterministic check is touched.

## Test plan

- [ ] `python3 scripts/gen_skill_docs.py --check` — green (this edit does not reach the generated pages)
- [ ] `## Anti-Hallucination` heading still present in both files (`scripts/validate_skills.sh:171` requires it)
- [ ] Both convention bullets still present in both files
- [ ] `git diff --stat` is 2 files / 4 deletions / 0 insertions
- [ ] CI `validate` job green apart from the manifest check noted below

## Note on the `Distribution manifests in sync` check

Expected red: this PR edits shipped files, so their hashes change and `metadata/` needs a refresh. I could not run `scripts/gen_distribution_manifest.py` — my working tree is CRLF (`core.autocrlf=true`, no `.gitattributes`), and a write-mode run there would rewrite all 1264 shipped-file hashes to CRLF values and break the self-updater. Please refresh the manifest on an LF checkout before merging, per the `CONTRIBUTING.md` note.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Expected: the PR URL is printed. Report it to the user.

---

### Task 2: Extend the trim to the remaining nine skills

Start only after Task 1's PR is green in CI (apart from the documented manifest check).

**Files:**
- Modify: `skills/find-cohort-gap/SKILL.md:349-350`
- Modify: `skills/write-protocol/SKILL.md:242-243`
- Modify: `skills/fill-protocol/SKILL.md:247-248`
- Modify: `skills/design-study/SKILL.md:277-278`
- Modify: `skills/present-paper/SKILL.md:1050-1051`
- Modify: `skills/make-figures/SKILL.md:929-930`
- Modify: `skills/revise/SKILL.md:566-567`
- Modify: `skills/write-paper/SKILL.md:715-716`
- Modify: `skills/self-review/SKILL.md:865-866`

Line numbers are from the pre-edit tree and are advisory; the filter matches by content.

**Interfaces:**
- Consumes: the filter body from Task 1, Step 3, with a different `TARGETS` list.
- Produces: no code artifact; completes change type 1.

- [ ] **Step 1: Branch from an up-to-date `main`**

```bash
git checkout main
git fetch upstream
git merge --ff-only upstream/main
git checkout -b trim-generic-anti-hallucination-bullets-rest
```

If `--ff-only` refuses, stop and report — do not rebase or reset without asking.

- [ ] **Step 2: Record the baseline counts**

```bash
grep -rc "Never fabricate numerical results" skills --include=SKILL.md | grep -v ":0"
```

Expected: 9 files each reporting `1` — the nine listed above. `check-reporting` and `grant-builder` are absent because Task 1 already cleaned them. If either reappears, Task 1 was reverted; stop and report.

- [ ] **Step 3: Apply the deletion**

```bash
python - <<'PY'
import pathlib

TARGETS = [
    "skills/find-cohort-gap/SKILL.md",
    "skills/write-protocol/SKILL.md",
    "skills/fill-protocol/SKILL.md",
    "skills/design-study/SKILL.md",
    "skills/present-paper/SKILL.md",
    "skills/make-figures/SKILL.md",
    "skills/revise/SKILL.md",
    "skills/write-paper/SKILL.md",
    "skills/self-review/SKILL.md",
]
# ASCII prefixes, for the same reason as Task 1: no dependence on how the em dash
# in the full bullet is decoded. academic-aio's variant starts "- If a compliance
# item," and therefore cannot match.
DROP_PREFIXES = (
    "- **Never fabricate numerical results**",
    "- If a reporting guideline item, journal policy, or clinical standard is uncertain",
)

for target in TARGETS:
    path = pathlib.Path(target)
    text = path.read_bytes().decode("utf-8")
    lines = text.split("\n")
    kept = [
        line for line in lines
        if not line.rstrip("\r").startswith(DROP_PREFIXES)
    ]
    removed = len(lines) - len(kept)
    assert removed == 2, f"{target}: expected 2 removals, got {removed}"
    path.write_bytes("\n".join(kept).encode("utf-8"))
    print(f"ok {target}: removed {removed}")
PY
```

Expected: nine `ok … removed 2` lines.

- [ ] **Step 4: Verify**

```bash
grep -rc "Never fabricate numerical results" skills --include=SKILL.md | grep -v ":0" || echo "NONE REMAINING"
```

Expected: `NONE REMAINING`.

```bash
grep -rc "state the uncertainty rather than guessing" skills --include=SKILL.md | grep -v ":0"
```

Expected: exactly one file — `skills/academic-aio/SKILL.md:1`. That is its domain-specific variant and must survive. Any other file here is a mistake.

```bash
git diff --stat
```

Expected: 9 files changed, 18 deletions, 0 insertions.

```bash
grep -c "Anti-Hallucination" skills/self-review/SKILL.md skills/write-paper/SKILL.md skills/present-paper/SKILL.md
```

Expected: `1` for `self-review`, and `1` each for `write-paper` and `present-paper` — those two keep a single heading with a second, domain-specific bullet list above it that this edit does not touch.

```bash
git diff -- skills/self-review/SKILL.md
```

Expected: only two lines removed; the Phase 2.5c sentence in the first bullet is intact.

- [ ] **Step 5: Confirm the generated docs gate**

```bash
python scripts/gen_skill_docs.py --check
```

Expected: `OK: docs/skills/ in sync (59 skill pages + index).` If it reports drift, run `python scripts/gen_skill_docs.py` and commit the regenerated pages.

- [ ] **Step 6: Commit**

```bash
git add skills/find-cohort-gap/SKILL.md skills/write-protocol/SKILL.md \
  skills/fill-protocol/SKILL.md skills/design-study/SKILL.md \
  skills/present-paper/SKILL.md skills/make-figures/SKILL.md \
  skills/revise/SKILL.md skills/write-paper/SKILL.md skills/self-review/SKILL.md
git commit -m "$(cat <<'EOF'
docs(skills): drop redundant generic anti-hallucination bullets (remaining 9)

Completes the trim piloted on check-reporting and grant-builder. Same two
general-exhortation bullets, same rationale: no gate or downstream skill
consumes them, and docs/SKILL_TEMPLATE.md asks this section for
domain-specific rules.

academic-aio is deliberately untouched — its closing bullet is a
domain-specific variant, not the shared boilerplate.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 7: Push and open the PR — CONFIRM WITH THE USER FIRST**

```bash
git push -u origin trim-generic-anti-hallucination-bullets-rest
gh pr create --repo Aperivue/medsci-skills --base main \
  --head embed-Rayn:trim-generic-anti-hallucination-bullets-rest \
  --title "docs(skills): drop redundant generic anti-hallucination bullets (remaining 9 skills)" \
  --body "$(cat <<'EOF'
## Summary

- Completes the trim piloted for `check-reporting` and `grant-builder`: removes the same two general-exhortation bullets from the remaining nine skills that carried the identical block — `find-cohort-gap`, `write-protocol`, `fill-protocol`, `design-study`, `present-paper`, `make-figures`, `revise`, `write-paper`, `self-review`.
- The two convention-bearing bullets stay inline in every skill; `self-review`'s Phase 2.5c enforcement sentence is preserved.
- `academic-aio` is intentionally untouched: its closing bullet is a domain-specific variant, not the shared boilerplate.

Context: change type 1 of `docs/superpowers/specs/2026-09-09-context-engineering-alignment-design.md`. No gate, severity, or deterministic check is touched.

## Test plan

- [ ] No `SKILL.md` still contains the `Never fabricate numerical results` bullet
- [ ] `state the uncertainty rather than guessing` remains in exactly one file — `academic-aio` (its own variant)
- [ ] `## Anti-Hallucination` heading present in all nine files
- [ ] `git diff --stat` is 9 files / 18 deletions / 0 insertions
- [ ] `python3 scripts/gen_skill_docs.py --check` green
- [ ] CI `validate` job green apart from the manifest check noted below

## Note on the `Distribution manifests in sync` check

Expected red, same as the pilot PR: shipped-file hashes change and `metadata/` needs a refresh, which I cannot generate from a CRLF working tree without corrupting all 1264 entries. Please refresh it on an LF checkout before merging.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Expected: the PR URL is printed. Report it to the user.

---

## Optional Task 0: make hash-based gates runnable locally

Not required by Tasks 1-2 and **not** to be done without explicit user approval — it re-checks-out the whole working tree.

The working tree is CRLF while committed blobs are LF, which makes every hash-based gate (`gen_distribution_manifest.py`, `check_precedent.py`, `verify_package_integrity.py`) structurally red locally. Normalizing the tree to LF fixes that permanently:

- [ ] **Step 1: Confirm the tree is clean**

```bash
git status --short
```

Expected: no output. If anything is listed, stop — commit or `git stash -u` first.

- [ ] **Step 2: Switch to LF and renormalize**

```bash
git config core.autocrlf input
git add --renormalize .
git status --short
```

Expected: `git status --short` lists modified files only if the index needed renormalizing; if it does, review the diff before committing anything, and do not commit renormalized line endings as part of a content PR — that belongs in its own change and needs maintainer agreement.

- [ ] **Step 3: Re-verify**

```bash
python scripts/gen_distribution_manifest.py --check
```

Expected: `OK` rather than `DISTRIBUTION_MANIFEST_DRIFT`. If it still reports 1264 changed files, the tree did not renormalize; revert with `git config core.autocrlf true` and leave the manifest to CI.

Also worth installing so `scripts/validate_skills.sh` and `scripts/run_ci_mirror.sh` can run: `exiftool`, `pandoc`, `poppler`, and a real `python3` on PATH.

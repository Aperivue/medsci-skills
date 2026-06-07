---
name: publish-skill
description: >
  Convert a personal agent skill into a distributable, open-source-ready skill.
  Runs PII audit, generalization, license compatibility check, cross-platform adapter review, and packaging workflow.
triggers: publish skill, distribute skill, open-source skill, package skill, universalize skill
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Skill: publish-skill

Convert a personal agent skill into a clean, distributable, open-source-ready skill package. This skill walks through a 7-phase pipeline that audits for personally identifiable information, generalizes language and role assumptions, verifies license compatibility, checks cross-platform adapter needs, and prepares the final package for commit.

## Communication Rules

- Communicate with the user in their preferred language
- Use English for technical terms (PII, MIT, CC BY, GPL, YAML frontmatter)
- Present audit findings in structured tables

---

## Phase 0: Init and Identify Source

### Required Inputs

Collect from the user:

1. **Source skill path**: directory containing the personal skill (e.g., `~/.claude/skills/my-skill/` or `~/.agents/skills/my-skill/`)
2. **Target package path**: directory of the distributable package (e.g., `~/workspace/<your-package>/`)
3. **Target license**: license of the package (default: MIT)

### Actions

1. Read `SKILL.md` from the source skill directory
2. Inventory all files recursively (`ls -R`)
3. Classify skill type:
   - **Standalone**: self-contained skill with no agent delegation
   - **Orchestrator**: delegates to sub-agents (NOT suitable for distribution without refactoring)
   - **Wrapper**: thin wrapper around another tool/API
4. Present inventory table to the user:

```
| File | Lines | Type | Notes |
|------|-------|------|-------|
```

**Gate**: User confirms source skill and target package before proceeding.

---

## Phase 0.5: Skill-Worthiness Gate

Before spending effort on PII scrubbing and generalization, confirm the workflow is
worth distributing *as a skill* at all. A skill earns its place by encoding a reusable
decision heuristic, a hard-won constraint, or a verification step — not a snippet anyone
could reconstruct in five minutes. Apply all three gates; **any "no" (or "yes" on the
inverse) stops publication** in favor of documentation or a memory note instead.

| Gate | Question | Pass condition |
|------|----------|----------------|
| **Uniqueness** | Could a competent user get the same result by searching the web for ~5 minutes, or by asking a general assistant with no skill installed? | **No** |
| **Specificity** | Does it encode a workflow, decision heuristic, constraint, or convention specific to this domain or a recurring task — rather than a generic code snippet or a standard-library example? | **Yes** |
| **Effort** | Did discovering it take real debugging, study design, operational effort, or a reviewer-anticipation lesson (a pitfall, a verification step, a domain convention)? | **Yes** |

Favor skills that encode reviewer-anticipation, reporting-guideline constraints,
verification gates, and decision trees over thin wrappers or one-off snippets. This is
the publish-time analogue of the "reusable pattern vs one-off hack" distinction: a
workflow that fails the gate is better captured as a doc or a memory note than shipped as
a skill that dilutes the catalog.

**Gate**: If any of the three fails, recommend documentation/memory instead and stop. If
the value is real but the skill delegates to private agents, route through Phase 1's
orchestrator finding (refactor to standalone first). Only a clear three-way pass proceeds.

---

## Phase 1: Originality Check

Verify the skill is original work suitable for open-source distribution.

### Checks

1. **External source**: Is this skill adapted from another package or author? Check for attribution headers, license blocks, or "based on" comments.
2. **Third-party content**: Do any files in `references/` come from external sources (published guidelines, textbooks, standards bodies)?
3. **Competitive sensitivity**: Does the skill reveal proprietary business logic or competitive advantage that should remain private?

### Decision Matrix

| Finding | Action |
|---------|--------|
| Fully original | Proceed to Phase 2 |
| Adapted with compatible license | Add attribution header, proceed |
| Contains non-compatible third-party content | Flag for removal or URL manifest conversion |
| Orchestrator with private agent references | STOP -- requires refactoring to standalone first |
| Competitive/proprietary logic | STOP -- not suitable for open-source |

---

## Phase 2: PII De-identification Audit

**Zero tolerance**: the skill must have exactly 0 PII matches before proceeding.

### Pre-scan Setup

Before running, ask the user for everything that should also count as a PII hit but is unique to them:
- Their name(s) in all languages and romanizations (a placeholder shape: `<First Last>|<native-script name>`)
- Their institutional affiliation(s) (a placeholder shape: `<Institution>|<Hospital>`)
- Any collaborator surnames that may appear in drafts or filenames

Combine the inputs into a single `grep -E` alternation pattern (pipe-separated).

### Automated Scan

Run the bundled audit script. The first argument is the skill directory; the second is the user-specific alternation pattern from Pre-scan Setup.

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/audit_skill.sh <source_skill_path> \
    "<First Last>|<native-script name>|<Institution>|<Hospital>"
```

The script runs nine categories that mirror the medsci-skills monorepo linter (`scripts/validate_skills.sh`):

1. **Hardcoded paths** (`/Users/<name>/`, `/home/<name>/`, `~/Documents`, `~/Desktop`, `~/Downloads`, `~/Projects`)
2. **Email addresses** (any address-shaped string)
3. **IP addresses / internal URLs** (`*.internal`, `*.local`, `*.corp`)
4. **Institutional references** (SNUH / AMC / SMC / KAIST / SNU / ASAN / MGH / Mayo Clinic / Johns Hopkins / Samsung Medical / Severance / Asan Medical)
5. **Academic roles with names** (`professor <Surname>`, `Prof. <Surname>`, `Dr. <Surname>`, `PGY[0-9]`, `<한글이름> 교수님`)
6. **Language hardcoding** ("in Korean", "한국어로", "in Japanese", "in Chinese")
7. **Location specifics** (Seoul / Busan / Daegu / Tokyo / Beijing / Shanghai / Boston / Stanford and Korean variants)
8. **Blockquote dated precedent** (`> YYYY-MM-DD ...` lines that reveal an internal review timeline)
9. **Author-style filenames** (`<Surname>{Year}_*` pattern, e.g., `<Surname>2025_<Journal>_Fig01.png`; allow-list excludes generic tokens like `Issue2024_`, `Sample2025_`)
10. **Binary EXIF metadata** (DOCX / PPTX / XLSX / PDF / PNG / JPG / TIFF — scanned via `exiftool` when installed; skipped silently otherwise with an install hint)

False-positive guard: text scans use `grep --binary-files=without-match` so byte-stream collisions inside `.pyc`, `.png`, or `.docx` files do not trigger findings. `__pycache__/` is also explicitly skipped.

### Cross-validation

For categories the script flags, also manually verify with the Grep tool against `${CLAUDE_SKILL_DIR}/references/pii-patterns.md`. Pay particular attention to:

- Names not in the EXTRA_PATTERNS argument (e.g., a co-author who appeared only in one early draft)
- Domain-specific institutional acronyms (your institution may not be in the default list)
- Project-specific identifiers like `CK-NN`, `MA-NN`, dated cohort names

### Output Format

Present all findings in a remediation table:

```
| # | File:Line | Category | Match | Suggested Fix |
|---|-----------|----------|-------|---------------|
```

**Gate**: User reviews all findings. Fix each one. Re-run audit. Proceed only when 0 hits confirmed.

---

## Phase 3: Generalization

Transform personal assumptions into universal defaults.

### Language

- Replace: `"in Korean"` / `"한국어로"` / `"Korean language"` → `"in the user's preferred language"`
- Replace: `"communicate in [specific language]"` → `"Communicate with the user in their preferred language"`
- Keep: multilingual trigger keywords in the `triggers:` field (these aid discovery)

### Role

- Replace: `"radiology researcher"` → `"medical researcher"` (if the skill is domain-general)
- Replace: `"professor"` / `"fellow"` → `"researcher"` or `"user"` (context-dependent)
- Keep: domain-specific terms that define the skill's scope (e.g., "diagnostic accuracy" is fine)

### Paths

- Replace: hardcoded absolute paths → `${CLAUDE_SKILL_DIR}` for bundled reference files
- Replace: `~/Documents/...` → user-provided output directory
- Keep: relative paths within the skill directory structure

### Environment

- Remove: assumptions about specific OS (macOS, Linux)
- Remove: assumptions about specific editors or IDEs
- Remove: references to personal infrastructure (agents, other personal skills)
- Keep: tool requirements listed in frontmatter `tools:` field

### Interoperability

- Check: does the skill reference other skills by name (e.g., "route to `analyze-stats`")?
- If referenced skill exists in target package: keep the reference
- If referenced skill does NOT exist in target package: make it optional with fallback instructions

### Output

Show a unified diff of all generalization changes for user review.

---

## Phase 4: License Compatibility Check

Verify all bundled files are compatible with the target package license.

### Scan Process

For each file in the skill's `references/` and `scripts/` directories:

1. Check for license headers or declarations within the file
2. Check for LICENSE files in the same directory
3. If the file contains content from a known standard (reporting guidelines, clinical scores, etc.), identify the source and its license

### Compatibility Matrix

Reference `${CLAUDE_SKILL_DIR}/references/license-compatibility-matrix.md` for the full matrix.

**Quick reference for MIT target:**

| Source License | Can Bundle? | Action |
|---------------|------------|--------|
| CC0 / Public Domain | Yes | No changes needed |
| CC BY 4.0 / 3.0 | Yes | Add attribution header |
| MIT / BSD / Apache 2.0 | Yes | Include license notice |
| CC BY-NC | No | Convert to URL reference |
| CC BY-NC-ND | No | Convert to URL reference |
| CC BY-SA | No | Copyleft risk -- convert to URL reference |
| GPL v2/v3 | No | Mark as optional external dependency |
| Unknown / Proprietary | No | Assume incompatible -- remove or get permission |

### URL Manifest Pattern

For non-compatible content, convert from bundled file to a URL manifest:

```markdown
## [Checklist Name]

This checklist is not bundled due to license restrictions ([License Type]).

**Official source**: [URL]
**How to use**: Download the checklist from the official source and place it in
`references/` before using this skill's reporting check feature.
```

### Output

Present license audit table:

```
| File | Source | License | Compatible? | Action |
|------|--------|---------|------------|--------|
```

---

## Phase 5: Validate and Test

### Structural Validation

1. **YAML frontmatter**: Parse and verify all required fields (name, description, tools)
2. **File references**: Every `${CLAUDE_SKILL_DIR}/...` path resolves to an actual file
3. **Script executability**: Scripts in `scripts/` have appropriate shebangs
4. **Line count**: SKILL.md should be under 500 lines for optimal loading
5. **Description quality**: Description should start with a verb and include trigger keywords

### Final PII Re-check

Run `audit_skill.sh` one final time. Must return exit code 0.

### Cross-Platform Adapter Review

Check whether the skill can run in common desktop-agent environments:

| Platform | Check |
|---|---|
| Claude Code | No hardcoded dependency on private `~/.claude` paths unless documented. |
| Codex | `SKILL.md` is self-contained and installable under `~/.agents/skills/`. |
| Cursor | A short `.cursor/rules/*.mdc` adapter can point to the canonical `SKILL.md`. |
| Windows | Commands avoid Unix-only assumptions or provide PowerShell/Python alternatives. |
| macOS/Linux | Shell examples use portable paths where possible. |

If the package is intended for a workshop or classroom, prepare direct-download
ZIPs rather than asking users to navigate GitHub manually:

```text
https://github.com/{owner}/{repo}/releases/latest/download/{package}-classroom-windows.zip
https://github.com/{owner}/{repo}/releases/latest/download/{package}-classroom-macos.zip
```

### README Entry Draft

Generate a table row matching the target package's README format:

```markdown
| **{skill-name}** | {One-sentence description of what the skill does.} |
```

### User Testing

Instruct the user to:

1. Copy the cleaned skill to a test location: `cp -r <cleaned_skill> ~/.claude/skills/<skill-name>`
2. Restart Claude Code
3. Test the skill triggers by typing `/<skill-name>` or relevant trigger phrases
4. Verify all phases work end-to-end on a sample input

**Gate**: User confirms testing is complete.

---

## Phase 6: Package and Commit

### Copy to Target Package

```bash
cp -r <cleaned_skill_path> <target_package>/skills/<skill-name>/
```

### Update README

Apply the README entry drafted in Phase 5:
- Add row to the appropriate table (Available Now / Coming Soon)
- Update pipeline diagram if the skill adds a new stage
- Update skill count if mentioned in prose

### Generate Commit Commands

Present the exact commands but do NOT auto-execute push:

```bash
cd <target_package>
git add skills/<skill-name>/
git add README.md
git diff --cached   # User reviews
git commit -m "Add <skill-name>: <one-line description>"
```

**Gate**: User reviews `git diff --cached` and explicitly approves the commit. Push is always manual.

### Post-Publish

Remind the user to:
- Update any memory files tracking package status
- Add the skill to any marketplace listings if applicable
- Test installation from a clean clone: `git clone <repo> && cp -r <repo>/skills/<skill-name> ~/.claude/skills/`
- For classroom distribution, create or update GitHub Release ZIP assets and test direct download links.

### Classroom Package Checklist (if applicable)

- [ ] Full skill set is installed once; lesson tasks use only 1-2 skills at a time
- [ ] Windows ZIP includes `installers/install-windows.cmd`
- [ ] macOS ZIP includes `installers/install-macos.command`
- [ ] `README_FIRST.md` explains unzip -> double-click -> restart -> test prompt
- [ ] Email announcement uses direct GitHub Release download links
- [ ] WSL is documented as an advanced option, not a default requirement
- [ ] First prompts avoid full end-to-end orchestration

---

## What This Skill Does NOT Do

- Never auto-executes `git push` -- push is always manual
- Never modifies the source skill in place -- works on a copy or the target directory
- Never makes judgment calls on competitive sensitivity -- always asks the user
- Never bundles content with incompatible licenses -- converts to URL references
- Never assumes a specific package license -- asks in Phase 0
- Never skips the PII audit -- zero tolerance is enforced at Phase 2 and Phase 5

## Anti-Hallucination

- **Never fabricate file paths, URLs, DOIs, or package names.** Verify existence before recommending.
- **Never invent journal metadata, impact factors, or submission policies** without verification at the journal's website.
- If a tool, package, or resource does not exist or you are unsure, say so explicitly rather than guessing.

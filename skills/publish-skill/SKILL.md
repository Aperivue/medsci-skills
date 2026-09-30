---
name: publish-skill
description: Use when turning a personal agent skill into an open-source, distributable one. Runs a PII audit, generalizes personal details, checks licence compatibility, reviews cross-platform adapters and walks through packaging.
model: inherit
metadata:
  triggers: "publish skill, distribute skill, open-source skill, package skill, universalize skill"
---

# Skill: publish-skill

## Phase 0: Init and Identify Source

### Required Inputs

Collect from the user:

1. **Source skill path**: directory containing the personal skill (e.g., `~/.claude/skills/my-skill/` or `~/.agents/skills/my-skill/`)
2. **Target package path**: directory of the distributable package (e.g., `~/workspace/<your-package>/`)
3. **Target license**: license of the package — ask; offer MIT as the default, never assume it

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

Make every later fix on a working copy (`<cleaned_skill_path>` below) or in the target directory.
NEVER modify the source skill in place, because it is the user's working original.

**Gate**: User confirms source skill and target package before proceeding.

---

## Phase 0.5: Skill-Worthiness Gate

Before spending effort on PII scrubbing and generalization, confirm the workflow is worth
distributing *as a skill* at all. Apply all three gates:

| Gate | Question | Pass condition |
|------|----------|----------------|
| **Uniqueness** | Could a competent user get the same result by searching the web for ~5 minutes, or by asking a general assistant with no skill installed? | **No** |
| **Specificity** | Does it encode a workflow, decision heuristic, constraint, or convention specific to this domain or a recurring task — rather than a generic code snippet or a standard-library example? | **Yes** |
| **Effort** | Did discovering it take real debugging, study design, operational effort, or a reviewer-anticipation lesson (a pitfall, a verification step, a domain convention)? | **Yes** |

**Gate**: Any "no" (or "yes" on the inverse) stops publication — recommend documentation or a
memory note instead. If the value is real but the skill delegates to private agents, route through
Phase 1's orchestrator finding (refactor to standalone first). Only a clear three-way pass proceeds.

---

## Phase 1: Originality Check

### Checks

1. **External source**: Is this skill adapted from another package or author? Check for attribution headers, license blocks, or "based on" comments.
2. **Third-party content**: Do any files in `references/` come from external sources (published guidelines, textbooks, standards bodies)?
3. **Competitive sensitivity**: Does the skill reveal proprietary business logic or competitive advantage that should remain private? Ask the user; never make this judgment call yourself.

### Decision Matrix

| Finding | Action |
|---------|--------|
| Fully original | Proceed to Phase 2 |
| Adapted with compatible license | Add attribution header, proceed |
| Contains non-compatible third-party content | Flag for removal or URL reference conversion |
| Orchestrator with private agent references | STOP -- requires refactoring to standalone first |
| Competitive/proprietary logic | STOP -- not suitable for open-source |

---

## Phase 2: PII De-identification Audit

**Zero tolerance**: the skill must have exactly 0 PII matches before proceeding.

### Pre-scan Setup

Before running, ask the user for everything unique to them that should also count as a PII hit:
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

The script scans ten categories, plus the user pattern:

1. **Hardcoded paths** (`/Users/<name>/`, `/home/<name>/`, `~/Documents`, `~/Desktop`, `~/Downloads`, `~/Projects`)
2. **Email addresses** (any address-shaped string)
3. **IP addresses / internal URLs** (`*.internal`, `*.local`, `*.corp`)
4. **Institutional references** (SNUH / AMC / SMC / KAIST / SNU / ASAN / MGH / UCSF / Mayo Clinic / Johns Hopkins / Samsung Medical / Severance / Asan Medical)
5. **Academic roles with names** (`professor <Surname>`, `Prof. <Surname>`, `Dr. <Surname>`, `PGY[0-9]`, `<한글이름> 교수님`)
6. **Language hardcoding** ("in Korean", "한국어로", "in Japanese", "in Chinese")
7. **Location specifics** (Seoul / Busan / Daegu / Tokyo / Beijing / Shanghai / Boston / Stanford and Korean variants)
8. **Blockquote dated precedent** (`> YYYY-MM-DD ...` lines that reveal an internal review timeline)
9. **Author-style filenames** (`<Surname>{Year}_*` pattern, e.g., `<Surname>2025_<Journal>_Fig01.png`; allow-list excludes generic tokens like `Issue2024_`, `Sample2025_`)
10. **Binary EXIF metadata** (DOCX / PPTX / XLSX / PDF / PNG / JPG / TIFF — scanned via `exiftool` when installed; skipped otherwise, with an install hint)

### Cross-validation

For categories the script flags, also verify manually with the Grep tool against `${CLAUDE_SKILL_DIR}/references/pii-patterns.md`. Pay particular attention to:

- Names not in the extra-patterns argument (e.g., a co-author who appeared only in one early draft)
- Domain-specific institutional acronyms (your institution may not be in the default list)
- Project-specific identifiers like `CK-NN`, `MA-NN`, dated cohort names

### Output Format

Present all findings in a remediation table:

```
| # | File:Line | Category | Match | Suggested Fix |
|---|-----------|----------|-------|---------------|
```

**Gate**: User reviews all findings. Fix each one in the working copy. Re-run the audit on the working copy. Proceed only when 0 hits are confirmed.

---

## Phase 3: Generalization

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

For each file in the skill's `references/` and `scripts/` directories:

1. Check for license headers or declarations within the file
2. Check for LICENSE files in the same directory
3. If the file contains content from a known standard (reporting guidelines, clinical scores, etc.), identify the source and its license

Classify each file with `${CLAUDE_SKILL_DIR}/references/license-compatibility-matrix.md` (written
for an MIT target; it also lists common checklist and package licenses). Bundle compatible content
with the attribution header or license notice it requires; convert non-compatible content to the
matrix's URL Reference Pattern; mark GPL/LGPL tools as optional external dependencies; treat an
unknown license as incompatible (remove, or get permission).

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

Run `audit_skill.sh` one final time on the cleaned skill. Must return exit code 0.

### Cross-Platform Adapter Review

Check whether the skill can run in common desktop-agent environments:

| Platform | Check |
|---|---|
| Claude Code | No hardcoded dependency on private `~/.claude` paths unless documented. |
| Codex | `SKILL.md` is self-contained and installable under `~/.agents/skills/`. |
| Cursor | A short `.cursor/rules/*.mdc` adapter can point to the canonical `SKILL.md`. |
| Windows | Commands avoid Unix-only assumptions or provide PowerShell/Python alternatives. |
| macOS/Linux | Shell examples use portable paths where possible. |

If the package is intended for a workshop or classroom, read
`${CLAUDE_SKILL_DIR}/references/classroom-distribution.md` and follow it (direct-download ZIPs,
release assets, classroom checklist).

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
- Add the skill to any marketplace listings if applicable
- Test installation from a clean clone: `git clone <repo> && cp -r <repo>/skills/<skill-name> ~/.claude/skills/`
- For classroom distribution, finish the release steps in `references/classroom-distribution.md`.

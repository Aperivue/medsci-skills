---
name: add-journal
description: >
  Add a new journal to the MedSci Skills profile database. Extracts metadata from
  author guidelines, generates write-paper (detailed) and find-journal (compact)
  profiles in canonical format with quality gates.
triggers: add journal, new journal, create journal profile, journal profile 추가
tools: Read, Write, Edit, Grep, Glob
model: inherit
---

# Add Journal Skill

You are helping a medical researcher add a new journal to the MedSci Skills profile database.
You generate two reference profiles per journal -- a detailed write-paper profile (~100-150 lines)
and a compact find-journal profile (~30 lines) -- using the journal's author guidelines as
the primary data source.

## Communication Rules

- Communicate with the user in their preferred language.
- Journal names, profile content, and URLs are always in English.
- Medical terminology and field names are always in English.
- Section headings within profiles must exactly match the canonical format defined below.

## Key Directories

- **Write-paper profiles:** `${CLAUDE_SKILL_DIR}/../write-paper/references/journal_profiles/`
- **Find-journal profiles:** `${CLAUDE_SKILL_DIR}/../find-journal/references/journal_profiles/`

---

## Phase 0: Input Collection

### Required
1. **Journal name** -- full official name (e.g., "Journal of Clinical Oncology")

### Strongly Encouraged
2. **Author Guidelines URL** -- primary data source for metadata extraction

### Optional
3. **Field focus** -- e.g., cardiology, oncology, surgery, general medicine, medical education, methodology
4. **Tier estimate** -- Q1 / Q2 / Q3 (user's best guess)
5. **ISSN** -- if known

If the user provides only a journal name without a URL, ask for the Author Guidelines URL
before proceeding. The guidelines page is the single most important data source for accurate
profile generation.

---

## Phase 1: Duplicate Check

Before any data extraction, check whether the journal already exists:

1. **Glob both directories:**
   ```
   ${CLAUDE_SKILL_DIR}/../write-paper/references/journal_profiles/*.md
   ${CLAUDE_SKILL_DIR}/../find-journal/references/journal_profiles/*.md
   ```

2. **Filename match:** Normalize the journal name (spaces to underscores, remove special characters)
   and check for an exact filename match.

3. **Abbreviation match:** Grep existing profiles for the journal's common abbreviation
   (e.g., "JCO" for Journal of Clinical Oncology).

### If found:
- Report which directory/directories already have the profile, with file paths.
- If present in only one directory, offer to create the missing counterpart.
- If present in both, offer to update the existing profiles or abort.
- Do NOT proceed to Phase 2 without user direction.

### If not found:
- Confirm to user: "No existing profile found. Proceeding with data extraction."

---

## Phase 2: Data Extraction

### Path A: WebFetch Available

1. Attempt to fetch the Author Guidelines URL.
2. Parse the page for metadata fields listed in the extraction checklist below.
3. If the page is insufficient (login-gated, JavaScript-heavy, or sparse), fall back to Path B.

### Path B: User-Provided Content

1. Ask the user to paste the Author Guidelines content (or key sections).
2. Accept pasted content and extract metadata from it.

### Extraction Checklist

Extract the following. Mark any field that cannot be determined as `[TODO: verify at journal site]`.

**For write-paper profile:**

| Field | Example |
|-------|---------|
| Full name | Journal of Clinical Oncology |
| Abbreviation | J Clin Oncol |
| Publisher | Wolters Kluwer (ASCO) |
| ISSN (print/online) | 0732-183X / 1527-7755 |
| Frequency | 36 issues/year |
| Impact Factor (with year) | ~45.3 (JCR 2023) |
| OA model | Hybrid |
| Acceptance rate | ~10-15% |
| Peer review type | Single-blind, 2-3 reviewers |
| Manuscript types with limits | Table: type, word limit, abstract, references, figures |
| Abstract format | Structured/unstructured, headings, word limit |
| Required sections | For Original Article |
| Statistical requirements | p-value format, CI, effect sizes |
| Figure specs | DPI, format, color, max count |
| Cover letter requirements | What to include |

**For find-journal profile:**

| Field | Example |
|-------|---------|
| Scope paragraph | 1-2 sentence scope description |
| Scope keywords | Comma-separated, 15-20 keywords |
| Article types | List of accepted types |
| Classification | Tier (Q1/Q2), OA, Field |

### --- Gate 1: Metadata Confirmation ---

Present extracted metadata as a structured summary. Ask the user:

1. "Is this information accurate? Any corrections?"
2. "What are the common rejection reasons for this journal?" (if not extractable)
3. "How would you position this journal relative to similar journals in the field?"

Do NOT proceed to Phase 3 until user confirms or provides corrections.

---

## Phase 3: Profile Generation

### 3.1 Load Reference Template

Read ONE existing write-paper profile from a similar field as a format reference:

| Field | Template to Load |
|-------|-----------------|
| Radiology | `Radiology.md` or `European_Radiology.md` |
| General medicine | `The_BMJ.md` or `JAMA.md` |
| Medical education | `Medical_Education.md` or `BMC_Medical_Education.md` |
| AI / digital health | `npj_Digital_Medicine.md` or `JMIR.md` |
| IR / interventional | `CVIR.md` or `JVIR.md` |
| Surgery | `Annals_of_Internal_Medicine.md` |
| Other | `The_BMJ.md` (safest general template) |

Also read ONE existing find-journal profile from any field for the compact format reference.

### 3.2 Generate Write-Paper Profile

Follow the canonical 10-section order exactly:

```markdown
# Journal Profile: {Full Name}

## Journal Identity

- **Full name**: {name}
- **Abbreviation**: {abbrev}
- **Publisher**: {publisher}
- **ISSN**: {print} (print), {online} (online)
- **Frequency**: {frequency}
- **Impact Factor**: ~{IF} (JCR {year})
- **Open Access**: {OA model}
- **Acceptance rate**: ~{rate}
- **Peer review**: {type}

## Manuscript Types and Word Limits

| Type | Body Word Limit | Abstract | References | Figures/Tables |
|------|----------------|----------|------------|----------------|
| Original Article | {limit} | {limit} | {limit} | {limit} |
| ... | ... | ... | ... | ... |

---

## Abstract Requirements

{Structured or unstructured. Show format as code block if structured.}

---

## Required Sections (Original Article)

1. **Introduction**
2. **Methods**
   - {subsections}
3. **Results**
4. **Discussion**
5. **{Other required sections if any}**

---

## Statistical Reporting

- {p-value format}
- {CI requirements}
- {Effect size requirements}
- {Software identification requirement}
- {Journal-specific statistical requirements}

---

## Figures

- **Maximum**: {N figures/tables}
- **Resolution**: {DPI} minimum
- **Format**: {accepted formats}
- **Color**: {policy}

---

## Common Rejection Reasons

1. {reason}
2. {reason}
3. {reason}
4. {reason}
5. {reason}

---

## Cover Letter

Should include:
- {requirements}

---

## Author Guidelines URL

{URL}

---

## Positioning

{When to submit here. When NOT to submit here.}

| Dimension | {This Journal} | {Competitor 1} | {Competitor 2} |
|-----------|---------------|----------------|----------------|
| Society | ... | ... | ... |
| Scope | ... | ... | ... |
| Impact factor | ... | ... | ... |
| Emphasis | ... | ... | ... |
```

### 3.3 Generate Find-Journal Profile

Follow the canonical 5-section format exactly:

```markdown
# {Full Name}

## Identity
- **Abbreviation:** {abbrev}
- **Publisher:** {publisher}
- **ISSN:** {print} / {online}
- **Homepage:** {URL}
- **Author guidelines:** {URL}

## Scope
{1-2 sentence scope description.}

## Scope Keywords
{comma-separated keywords, 15-20 terms}

## Article Types Accepted
- Original Article
- Review Article
- ...

## Classification
- **Tier:** {Q1/Q2}
- **Open Access:** {Full OA / Hybrid / Subscription}
- **Field:** {field}

## Special Notes
{2-3 sentences on positioning, unique aspects, society affiliation.}
```

### --- Gate 2: Profile Review ---

Present BOTH complete draft profiles to the user. Ask:

1. "Review these profiles. Any corrections needed?"
2. "Is the Scope paragraph accurate?"
3. "Are the Common Rejection Reasons realistic?"

Do NOT write files until user approves both profiles.

---

## Phase 4: Write Files and Update Counts

### 4.1 Determine Filename

Convert journal name to filename: spaces to underscores, remove special characters.

Examples:
- "Journal of Clinical Oncology" -> `Journal_of_Clinical_Oncology.md`
- "JACC" -> `JACC.md`
- "The Lancet Oncology" -> `The_Lancet_Oncology.md`
- "JAMA Network Open" -> `JAMA_Network_Open.md`

### 4.2 Write Profile Files

1. Write the write-paper profile to:
   `${CLAUDE_SKILL_DIR}/../write-paper/references/journal_profiles/{filename}.md`

2. Write the find-journal profile to:
   `${CLAUDE_SKILL_DIR}/../find-journal/references/journal_profiles/{filename}.md`

### 4.3 Update Profile Counts

After writing, count the actual files in both directories using Glob:

```
Glob: ${CLAUDE_SKILL_DIR}/../write-paper/references/journal_profiles/*.md
Glob: ${CLAUDE_SKILL_DIR}/../find-journal/references/journal_profiles/*.md
```

Compute total = find-journal count + write-paper count.

Update **all** count references in these files:

**`find-journal/SKILL.md`** -- update every occurrence of the old counts:
- Frontmatter `description:` line (total count)
- Body paragraph referencing total count
- Key Directories section (local count, write-paper count)
- Phase 3.1 "yields N profiles total (X + Y)"
- Case Report Mode section (total count)
- Error Handling section (total count)

Use Grep to find all numeric count references before updating. Use `replace_all` when
the same number appears multiple times.

**`README.md`** -- update:
- "Depth per skill" row: "(N journal profiles, ...)"
- find-journal row in Available Now table: "against N journal scope profiles"

### 4.4 Confirmation

Report to user:
- Files written (paths)
- New counts: find-journal local, write-paper, total
- Files updated with new counts
- Reminder: "Run `git add -A && git commit` to commit changes"

---

## Batch Mode

When the user wants to add multiple journals in one session:

1. Collect all journal names and URLs upfront.
2. Run Phase 1 (duplicate check) for all journals first.
3. For each journal, run Phases 2-3 individually with gates.
4. Write all files in a single Phase 4 pass (one count update at the end).

This avoids updating counts N times for N journals.

---

## Quality Standards

### Never Fabricate

- Impact Factor, acceptance rate, APC, ISSN, or peer review timelines.
- Mark unknown values as `[TODO: verify at journal site]`.
- Use approximate ranges (e.g., "~15-20%") only when the source supports it.

### Statistical Reporting Section Is Mandatory

Every write-paper profile MUST include a Statistical Reporting section. If the journal's
author guidelines do not specify statistical requirements, use these defaults and note
they should be verified:

- Report exact p-values to 2-3 significant figures; use p < 0.001 below that threshold.
- 95% CI for primary outcomes.
- Effect sizes with clinically meaningful units.
- Statistical software and version must be identified.

### Positioning Section Should Compare

The Positioning section should include a comparison table against 2-3 similar journals,
covering: society affiliation, scope emphasis, impact factor range, and distinguishing features.

---

## Error Handling

- If WebFetch fails or is unavailable: ask user to paste content. Never fail silently.
- If author guidelines page is login-gated: ask user to paste accessible portions.
- If insufficient information for a required field: mark as `[TODO: verify at journal site]`.
- If journal exists in one directory but not the other: create only the missing profile.
- If user provides conflicting information: present the conflict and ask for resolution.
- Never fabricate metrics -- mark unknown values explicitly.

---

## Skill Interactions

| Context | Skill | Interaction |
|---------|-------|-------------|
| After adding | find-journal | New profile immediately available for journal matching |
| After adding | write-paper | New profile available as target journal for manuscript formatting |
| Verification | search-lit | Can verify journal exists in PubMed/NLM catalog if needed |

---

## What This Skill Does NOT Do

- Does not scrape paywalled content or bypass access restrictions.
- Does not auto-commit changes to git.
- Does not modify existing profiles without user confirmation.
- Does not validate whether a journal is predatory (recommend user check Beall's list or DOAJ).

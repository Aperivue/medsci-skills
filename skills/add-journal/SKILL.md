---
name: add-journal
description: Use when a target journal has no profile yet. Reads the journal's author guidelines and writes a detailed /write-paper profile plus a compact /find-journal profile, public or user-local private, in the canonical format with quality gates.
model: inherit
metadata:
  triggers: "add journal, new journal, create journal profile, journal profile 추가"
---

# Add Journal Skill

Generate two profiles per journal from its author guidelines: a detailed write-paper profile
(~100-150 lines) and a compact find-journal profile (~30 lines). Write profile content in English;
the library is shared.

## Key Directories

Profiles live in one of two tiers. Pick the target in Phase 0, before any extraction.

- **Public** (shipped; must meet the verification bar in
  `${CLAUDE_SKILL_DIR}/../find-journal/POLICY.md`):
  - write-paper: `${CLAUDE_SKILL_DIR}/../write-paper/references/journal_profiles/`
  - find-journal: `${CLAUDE_SKILL_DIR}/../find-journal/references/journal_profiles/`
- **User-local private** (per-user, never pushed to git):
  - write-paper: `$HOME/.claude/private-journal-profiles/write-paper/`
  - find-journal: `$HOME/.claude/private-journal-profiles/find-journal/`

POLICY.md also documents promotion from private to public.

---

## Phase 0: Input Collection

- **Required:** full official journal name; target tier (`public` or `private`).
- **Strongly encouraged:** Author Guidelines URL. If the user gives only a name, ask for this URL
  before proceeding; it is the primary data source.
- **Optional:** field focus (used in 3.1), tier estimate (Q1/Q2/Q3), ISSN.

This skill does not judge whether a journal is legitimate. For an unfamiliar publisher, check DOAJ
membership (for open-access titles) and indexing before writing a profile, and tell the user.

### Public vs. Private target selection

If the user does not state the target tier, ASK before proceeding.

- **Default to `private`** for any journal outside the user's stated area of deep expertise.
  Private profiles need not clear the public bar line by line, but the journal's own Author
  Guidelines page must still be the primary source: no inference from adjacent journals, no AI
  policy copied from the publisher family.
- **`public` only when all of these hold:**
  1. The user intends to contribute the profile upstream.
  2. The user has opened the journal's homepage and author guidelines page and can attest to each
     field against the live source, or can paste the relevant sections.
  3. AI policy wording is transcribed from the journal's or publisher's own policy page, not
     inferred from a sibling journal.
  4. The user has completed or will complete the promotion checklist in
     `../find-journal/POLICY.md` before commit.

If the target is `public` but the user cannot attest to (2) and (3), switch the target to
`private` and say that promotion can happen later once the checklist is cleared.

---

## Phase 1: Duplicate Check

Before any extraction:

1. Glob all four directories:
   ```
   ${CLAUDE_SKILL_DIR}/../write-paper/references/journal_profiles/*.md
   ${CLAUDE_SKILL_DIR}/../find-journal/references/journal_profiles/*.md
   $HOME/.claude/private-journal-profiles/write-paper/*.md
   $HOME/.claude/private-journal-profiles/find-journal/*.md
   ```
2. Check for an exact filename match on the normalized name (4.1 rules).
3. Grep existing profiles for the journal's common abbreviation (e.g., "JCO").

If found, report the paths. If present in only one directory, offer to create only the missing
counterpart; if in both, offer to update or abort. Do NOT proceed to Phase 2 without user
direction.

---

## Phase 2: Data Extraction

- **Path A (WebFetch available):** fetch the Author Guidelines URL and parse it. If the page is
  login-gated, JavaScript-heavy, or sparse, fall back to Path B.
- **Path B:** ask the user to paste the Author Guidelines content (or key sections). Never fail
  silently when a fetch fails.

### Extraction Checklist

Mark any field that cannot be determined as `[TODO: verify at journal site]`.

**For the write-paper profile:** full name; abbreviation; publisher; ISSN (print/online);
frequency; Impact Factor with its JCR year; OA model; acceptance rate; peer-review type; manuscript
types with word, abstract, reference and figure limits; abstract format (structured or not,
headings, word limit); required sections for an Original Article; statistical requirements
(p-value format, CI, effect sizes); figure specs (DPI, format, color, max count); cover letter
requirements.

**For the find-journal profile:** a 1-2 sentence scope paragraph; 15-20 comma-separated scope
keywords; accepted article types; classification (tier Q1/Q2, OA, field).

### --- Gate 1: Metadata Confirmation ---

Present the extracted metadata as a structured summary. Ask:

1. "Is this information accurate? Any corrections?"
2. "What are the common rejection reasons for this journal?" (if not extractable)
3. "How would you position this journal relative to similar journals in the field?"

If the user's information conflicts with the source, present the conflict and ask. Do NOT proceed
to Phase 3 until the user confirms or corrects.

---

## Phase 3: Profile Generation

### 3.1 Load Reference Template

Read ONE existing write-paper profile from a similar field as a format reference:

| Field | Template to Load |
|-------|-----------------|
| Radiology | `Radiology.md` or `European_Radiology.md` |
| General medicine | `The_BMJ.md` or `JAMA.md` |
| Medical education | `JMIR_Medical_Education.md` |
| AI / digital health | `npj_Digital_Medicine.md` or `JMIR.md` |
| IR / interventional | `CVIR.md` or `JVIR.md` |
| Surgery | `Annals_of_Internal_Medicine.md` |
| Other | `The_BMJ.md` (safest general template) |

Also read ONE existing find-journal profile for the compact format.

### 3.2 Generate Write-Paper Profile

The detailed profile `/write-paper` loads when drafting for this journal. Read
`${CLAUDE_SKILL_DIR}/references/write_paper_profile_template.md` when writing it and fill the
literal template.

**Follow the canonical 11-section order exactly.** `/write-paper` Phase 7 and `/find-journal` read
these profiles positionally — a reordered, renamed, or omitted section silently degrades both:

1. **Journal Identity** — full name, abbreviation, publisher, ISSN, frequency, impact factor, OA
   model, acceptance rate, peer-review type
2. **Manuscript Types and Word Limits**
3. **Abstract Requirements** — word cap and heading structure
4. **Required Sections (Original Article)**
5. **Statistical Reporting** — MANDATORY. If the guidelines specify nothing, use these defaults
   and mark them `[TODO: verify at journal site]`: exact p-values to 2-3 significant figures
   (p < 0.001 below that); 95% CI for primary outcomes; effect sizes in clinically meaningful
   units; statistical software and version identified.
6. **Figures**
7. **Common Rejection Reasons**
8. **Cover Letter**
9. **AI Writing Disclosure Policy** — permitted scope, disclosure location, AI-generated-image
   stance, and the policy URL
10. **Author Guidelines URL**
11. **Positioning** — when to submit here, when *not* to, and a comparison table against 2-3
    similar journals (society, scope emphasis, impact factor range, distinguishing features)

**Fill rules.** Never guess a value. NEVER invent an Impact Factor, acceptance rate, APC, ISSN,
peer-review timeline, word limit or abstract structure, because an invented value propagates
straight into a drafted manuscript: mark it `[TODO: verify at journal site]` instead. Use an
approximate range (e.g., "~15-20%") only when the source supports it. Where the journal publishes no
dedicated AI policy, cite the publisher-level policy and say so explicitly.

### 3.3 Generate Find-Journal Profile

Follow the canonical format exactly:

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
{2-3 sentences on positioning, unique aspects, society affiliation.} AI policy: {1-line summary from write-paper profile's AI Writing Disclosure Policy section — e.g., "language editing only, dual disclosure required, AI images banned." or "follows ICMJE — disclose AI use in Methods."}
```

### --- Gate 2: Profile Review ---

Present BOTH complete draft profiles. Ask:

1. "Review these profiles. Any corrections needed?"
2. "Is the Scope paragraph accurate?"
3. "Are the Common Rejection Reasons realistic?"

Do NOT write files until the user approves both profiles.

---

## Phase 4: Write Files and Update Counts

### 4.1 Determine Filename

Spaces to underscores, special characters removed: "Journal of Clinical Oncology" ->
`Journal_of_Clinical_Oncology.md`; "JACC" -> `JACC.md`; "JAMA Network Open" ->
`JAMA_Network_Open.md`.

### 4.2 Write Profile Files

Write the write-paper profile and the find-journal profile, each as `{filename}.md`, into the
directory pair chosen in Phase 0 (Key Directories). For `private`, create the two private
directories if missing. Do NOT write private profiles anywhere inside the medsci-skills git tree.

### 4.3 Update Profile Counts

Do not edit `SKILL.md`, `README.md` or any other file to update a profile count: counts are
derived from disk at runtime, and private profiles are never counted.

### 4.4 Confirmation

Report the target tier and the paths written, then:
- `public`: remind the user to commit the two profile files (staged by path) with a message
  recording which pages were opened and on what date, as POLICY.md requires.
- `private`: "Files are local-only in your private profiles directory (outside this repo) — do not
  commit to the public repo."

---

## Batch Mode

For several journals in one session:

1. Collect all journal names and URLs upfront.
2. Run Phase 1 (duplicate check) for all journals first.
3. Run Phases 2-3 per journal, with both gates.
4. Write all files in a single Phase 4 pass.

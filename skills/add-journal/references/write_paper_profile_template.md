# Write-paper journal profile — canonical template

Load-on-demand companion to `/add-journal` Step 3.2. SKILL.md keeps the canonical
11-section order and the fill rules; this file is the literal template to copy.

Read it when you are actually writing a `write-paper` profile. Follow the 11-section
order exactly — `/write-paper` Phase 7 and `/find-journal` both read these files
positionally, so a reordered or renamed section silently degrades them.

Follow the canonical 11-section order exactly:

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

## AI Writing Disclosure Policy

- **Requirement level:** {Required / Recommended / Not specified — follows ICMJE recommendations}
- **Permitted scope:** {Language editing only / All tasks / describe specific policy}
- **Disclosure location:** {Methods / Acknowledgments / Cover letter / Submission form}
- **AI-generated images:** {Banned / Must be declared / Not specified}
- **Policy URL:** {URL to journal's AI policy page, or author guidelines URL if no dedicated page}

<!-- Use WebFetch to check the journal's Author Guidelines for AI policy.
     If no specific AI policy found, use ICMJE default:
     - Requirement level: Not specified — follows ICMJE recommendations
     - Permitted scope: Language editing only — per ICMJE 2025
     - Disclosure location: Methods
     - AI-generated images: Not specified
     - Policy URL: [author guidelines URL] (no dedicated AI policy page)
     Add [VERIFY] tag if uncertain about any field. -->

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

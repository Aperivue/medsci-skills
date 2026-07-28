# Step 5 — Report templates (Parts A–D)

Load-on-demand companion to `/check-reporting` Step 5. SKILL.md keeps the
NOT-FOR-SUBMISSION rule, the part list, and the JSON field contract; this file carries
the four literal output templates — Part A (summary), Part B (item-by-item checklist),
Part C (action items), and Part D (the machine-readable JSON block).

Read it when you are writing the report. Everything here is an output format: none of it
informs the audit itself.

**The banner is not optional.** The report MUST begin with the NOT-FOR-SUBMISSION comment
as its very first line — this is an internal working audit, never the official journal
checklist an author fills in and uploads.

Produce a structured compliance report in two parts.

This report is an **internal working audit** — it carries auto-fix annotations, a
machine-readable JSON block (`compliance_pct`, `fixable_by_ai`, …), and Action
Items. It is **NOT** the official reporting checklist a journal expects (that is
the blank guideline form with `Item | Recommendation | Reported in page/section`,
which the authors fill in). Never submit this report as the submission checklist.
To make the file self-identifying so it cannot be reused by filename into a later
submission package, **the report MUST begin with the NOT-FOR-SUBMISSION banner
below** as its very first line. (`/sync-submission`'s `check_checklist_dump_leak`
gate also catches this dump if it ever lands in a submission directory.)

#### Part A: Summary

```
<!-- INTERNAL AUDIT — NOT FOR SUBMISSION. This is the /check-reporting working
report, not the official journal checklist. Do not upload to a submission portal. -->

## Reporting Guideline Compliance Report

Manuscript: {title}
Target manuscript file: {manuscript filename, e.g. manuscript_v8.md}
Target version: {version token from the filename or frontmatter, e.g. v8}
Guideline: {name and version}
Date: {YYYY-MM-DD}
Assessed by: Claude (automated pre-screening)

### Summary

| Status | Count | Percentage |
|--------|-------|------------|
| PRESENT | {n} | {%} |
| PARTIAL | {n} | {%} |
| MISSING | {n} | {%} |
| N/A | {n} | {%} |
| **Total** | **{n}** | **100%** |

Overall compliance: {PRESENT count}/{applicable count} ({%})

Critical items (Step 4f): {present}/{total} present.{ if any missing: " Critical gap — " + each MISSING critical item with the section it belongs in. This, not the percentage, is the headline.}
```

#### Part B: Item-by-Item Checklist

```
### Detailed Checklist

| # | Section | Item | Status | Location | Notes |
|---|---------|------|--------|----------|-------|
| 1 | Title/Abstract | {item text} | PRESENT | Title | {notes} |
| 2 | Introduction | {item text} | MISSING | -- | {suggestion} |
| ... | ... | ... | ... | ... | ... |
```

#### Part C: Action Items (for MISSING and PARTIAL)

```
### Action Items (Priority Order)

1. **[MISSING] Item {N}: {item name}**
   - Required: {what needs to be added}
   - Suggested location: {section, paragraph}
   - Example text: "{draft sentence or phrase}"

2. **[PARTIAL] Item {N}: {item name}**
   - Current: {what was found}
   - Needed: {what additional detail is required}
   - Suggested revision: "{draft revision}"
```

Order action items by:
1. Items most journals enforce strictly (e.g., ethics approval, registration, sample size)
2. Items in the Methods section (easiest to fix)
3. Items in other sections

#### Part D: Machine-Readable JSON Summary

Append a fenced JSON block at the end of the report. This enables `/write-paper` Phase 7 and `/orchestrate` to parse compliance results programmatically. This block **MUST** be present when invoked with `--json` flag or when called from `/write-paper` Phase 7. It SHOULD also be present in standard invocations (appended after Part C).

```json
{
  "check_reporting_version": "1.1",
  "manuscript_title": "...",
  "target_manuscript": "manuscript_v8.md",
  "target_version": "v8",
  "source_sha256": "<first 12 hex chars of sha256 of the manuscript file bytes>",
  "guideline": "STARD-AI",
  "guideline_version": "2025",
  "date": "YYYY-MM-DD",
  "total_items": 40,
  "present": 32,
  "partial": 4,
  "missing": 3,
  "na": 1,
  "compliance_pct": 88.9,
  "action_items": [
    {
      "item_number": 12,
      "section": "Methods",
      "item_name": "Sample size justification",
      "status": "MISSING",
      "suggested_location": "Methods, after participant description",
      "suggested_fix": "Add: 'The sample size was determined based on [rationale]. A minimum of [N] cases was required to achieve [target] precision for the primary endpoint.'",
      "fixable_by_ai": true
    },
    {
      "item_number": 7,
      "section": "Methods",
      "item_name": "Blinding of index test to reference standard",
      "status": "PARTIAL",
      "current_text": "Readers were blinded",
      "needed": "Specify what readers were blinded to (reference standard results, clinical information, other reader results)",
      "suggested_fix": "Expand to: 'Readers interpreted [index test] images blinded to the reference standard results, clinical information, and other readers' assessments.'",
      "fixable_by_ai": true
    }
  ]
}
```

**Field definitions:**
- `compliance_pct`: `present / (total_items - na) * 100`, rounded to one decimal
- `action_items`: Array of MISSING and PARTIAL items only (PRESENT and N/A excluded)
- `fixable_by_ai`: `true` if the fix involves inserting or expanding text with information available in the manuscript or inferable from context; `false` if it requires external information (e.g., registration number, IRB approval number, specific protocol details only the author knows)
- `suggested_fix`: Concrete draft text that can be inserted or used to expand an existing sentence

---

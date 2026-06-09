# Step 7.1 Extension — Classical Manuscript Style QC

A grep-based checklist that automatically verifies the global rule `~/.claude/rules/manuscript-style-classical.md` (11 items) for senior-MA-reviewer readiness. Run alongside the Step 7.1 AI Pattern Scan.

**Why**: Senior MA mentors routinely flag the § symbol, AI Disclosure boilerplate, prose-form eligibility criteria, em-dash overuse, and AI-style headings as "AI patterns." A manuscript-level automated grep blocks these in advance.

## Automated checks (run together at Phase 7.1 entry)

```bash
MD=manuscript/manuscript.md

# 1. Enforce 0 occurrences of the § symbol
N=$(grep -c "§" "$MD" || true)
[ "$N" -eq 0 ] || echo "FAIL: § symbol ${N} occurrence(s) — remove all or replace with (Methods)/(Results)"

# 2. No AI Disclosure paragraph in the body (only on the journal form / cover letter)
grep -inE "artificial intelligence disclosure|generative ai was not used|ai acknowledg(e)?ment" "$MD" \
    && echo "FAIL: AI Disclosure paragraph present in the body — move it to the cover letter / submission form"

# 3. Heading style — five main sections in uppercase + bold
for H in METHODS RESULTS DISCUSSION INTRODUCTION CONCLUSION; do
    grep -qE "^## \*\*${H}\*\*" "$MD" || echo "WARN: '## **${H}**' heading missing (or a variant)"
done

# 4. Eligibility / Inclusion criteria — numbered list recommended
grep -A 3 -inE "^#{2,4}.*(eligibility|inclusion criteria|exclusion criteria)" "$MD" \
    | grep -qE "\([0-9]+\)|^[0-9]+\." \
    || echo "WARN: Eligibility/Inclusion criteria may be prose — consider converting to a '(1)... (2)...' numbered list"

# 5. No grant-ID placeholder in the Funding section
grep -inE "grant\s*(id|number)?\s*[:#]\s*(TBD|TODO|XXX|\[insert\]|\[grant)" "$MD" \
    && echo "FAIL: Funding grant-ID placeholder remains — ask the senior author to enter it directly"

# 6. No PROSPERO chronology in the body (only the registration number, one line, is allowed)
grep -inE "prospero.*(amendment|chronology|lodged|registered on \d{4}-\d{2}-\d{2}.*amended)" "$MD" \
    && echo "FAIL: PROSPERO chronology / amendment lodging present in the body — move it to the supplementary"

# 7. Em-dash overuse (< 25 per manuscript recommended)
N=$(grep -o "—" "$MD" | wc -l | tr -d ' ')
[ "$N" -lt 25 ] || echo "WARN: ${N} em-dashes (>=25) — an AI-generation signal; redistribute with commas/colons"

# 8. 0 hand-typed reference-list entries
# Per the manuscript-references.md rule, in-text citations may only be [@bibkey] or [N].
# If the References section has hand-typed entries, the build artifact (.docx) must be verified — delegate to Step 7.6a.
```

## Pass criteria

- FAIL = 0 (must fix).
- WARN ≤ 2 (may be acknowledged after user review).
- Record the result in `qc/_pipeline_log.md` with a timestamp + the raw output.

## Responsibility boundary

This step performs **automated grep only**. The following are separate steps:
- Body rewrite for Patterns 19–21 (§, self-reference, AI Disclosure boilerplate) → `/humanize`
- Hand-typed reference verification → Step 7.6a `check_xref.py` (after the DOCX build)
- PRISMA arithmetic consistency → `/check-reporting prisma` Step 4d
- Entering the actual Funding grant-ID value → direct circulation to the senior author

## Related

- Global rule: `~/.claude/rules/manuscript-style-classical.md` (motivation for the 11 items)
- Circulation workflow: `~/.claude/rules/senior-mentor-circulation.md`
- AI-draft handling: `~/.claude/rules/ai-drafted-document-policy.md`
- No hand-typed references: `~/.claude/rules/manuscript-references.md`
- Related skills: `/humanize` (Patterns 19–21), `/check-reporting prisma` (Step 4d)

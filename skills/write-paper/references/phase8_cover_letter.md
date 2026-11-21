# Phase 8+ — Cover letter generation

Load-on-demand companion to `/write-paper` Phase 8+. Read it only when the user asks for a
cover letter; never generate one automatically.

**Required user inputs (MUST ask, never fabricate):**
1. Editor name (if known; otherwise use "Dear Editor")
2. Suggested reviewers, as the journal requires or the user decides — see "Suggested reviewers" below
3. Excluded reviewers (if any, with brief reason)
4. Any specific points to emphasize for the target journal

**Cover letter structure:**

1. **Salutation**: "Dear [Editor name / Editor],"
2. **Submission statement**: "We submit our manuscript entitled '[Title]' for consideration as [article type] in [Journal Name]."
3. **Novelty statement** (2-3 sentences): What is new and why it matters. Extract from abstract key findings.
4. **Scope fit** (1-2 sentences): Why this journal is appropriate. Reference journal scope from profile if loaded.
5. **Brief methods** (1 sentence): Study design and key numbers.
6. **Ethical compliance**: IRB approval number, author agreement, COI statement, no dual submission.
7. **AI disclosure** (if applicable): Specific AI tools used and human oversight statement.
8. **Suggested reviewers** (as the journal requires or invites): Name, affiliation, confirmed email, expertise area.
9. **Excluded reviewers** (if any): Name and reason.
10. **Closing**: Corresponding author name and credentials.

**Suggested reviewers — the journal's rule first:**
Check the journal's current instructions for how many reviewers it requires or allows, where they are entered (letter or portal) and its conflict criteria, and follow them. Only when suggestions are optional is leaving them out a decision, made with the user. The manuscript's cited literature is a starting point for finding candidates, not a requirement. Present only candidates who clear the journal's conflict criteria and the cross-check below, for the user to confirm. Give an email address only when the source ties it explicitly to that person (their own corresponding-author line or an official institutional page); if it cannot be confirmed, give none.

**Reviewer COI cross-check (mandatory for meta-analyses):**
Cross-check all suggested and excluded reviewers against the included-study author list and their co-authors. Same-institution authors of included studies constitute automatic COI and must be excluded from reviewer suggestions.

**Anti-overclaiming guard:**
Automatically flag and rewrite any of these words in cover letters: "first," "novel," "unprecedented," "groundbreaking," "paradigm-shifting," "revolutionary." Replace with specific factual statements about what the study contributes.

**Word limit:** 300-500 words. Cover letters exceeding 500 words should be trimmed.

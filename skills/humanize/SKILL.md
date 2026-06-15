---
name: humanize
description: Detect and remove AI writing patterns from academic manuscripts and response-to-reviewers letters. Scans for 24 common AI-generated text patterns and rewrites flagged passages to sound naturally human-written while preserving technical accuracy.
triggers: humanize, AI patterns, AI 문체, remove AI writing, make it sound natural, 자연스럽게, de-AI
tools: Read, Write, Edit, Grep, Glob
model: inherit
---

# Humanize Skill

You are assisting a medical researcher in detecting and removing AI writing patterns from
academic manuscripts. Your goal: make the text read as if an experienced academic physician
wrote it, while preserving every technical claim, number, and citation.

## Communication Rules

- Communicate with the user in Korean (matching their working language).
- All manuscript edits are in English.
- Medical terminology is always in English, even in Korean communication.

## Reference Files

- **Pattern reference**: `${CLAUDE_SKILL_DIR}/references/ai_patterns.md` -- full 24-pattern list with expanded examples for medical/radiology manuscripts (Pattern 19–21 are senior-MA-reviewer red flags; Pattern 22–24 are response-to-reviewers letter patterns)
- **Source material**: Based on matsuikentaro1/humanizer_academic and Wikipedia: Signs of AI writing

Always read the pattern reference file at the start of a humanize session.

---

## Workflow

### Phase 1: Scan

Read the manuscript section(s) provided by the user and scan for all 24 patterns. For
response-to-reviewers letters and cover letters, prioritise patterns 22-24.

**For each pattern found:**
1. Record the pattern number and name.
2. Count occurrences.
3. Extract the exact passage from the text.
4. Note the location (paragraph number or line range).

**Output: Pattern Frequency Table**

```
## AI Pattern Scan Report

Section: {section name}
Word count: {N}

| # | Pattern | Count | Severity | Example from text |
|---|---------|-------|----------|-------------------|
| 1 | Significance inflation | 3 | HIGH | "...pivotal role in diagnostic imaging..." |
| 7 | AI vocabulary words | 5 | HIGH | "Additionally,...", "crucial finding..." |
| 8 | Copula avoidance | 2 | MEDIUM | "...serves as the gold standard..." |
| ... | ... | ... | ... | ... |

Patterns not detected: 2, 4, 9, 14, 15

Total AI pattern instances: {N}
AI pattern density: {N per 1000 words}
```

### Phase 2: Report

Present findings to the user with actionable summary.

**Severity levels:**
- **HIGH** (>3 occurrences): Likely to trigger AI detection tools. Fix immediately.
- **MEDIUM** (1-3 occurrences): Noticeable to careful readers. Should fix.
- **LOW** (0 occurrences): Clean for this pattern.

**AI Pattern Score:**
- Count total pattern instances across all 24 categories.
- Compute density: instances per 1000 words.
- Target: < 2.0 instances per 1000 words.

**Gate:** Present the report and ask the user which patterns to fix. Default: fix all HIGH and MEDIUM.

### Phase 3: Fix

Rewrite flagged passages following these rules:

1. **Preserve technical accuracy.** Every number, statistic, p-value, confidence interval, and
   clinical fact must remain identical.
2. **Preserve citation density.** Do not remove or relocate citations.
3. **Preserve formal academic register.** Do not make the text casual or conversational.
4. **Do not force casualness.** The target voice is an experienced radiologist writing for peers
   in a top-tier journal -- not a blog post.
5. **Keep domain-specific terminology intact.** "Convolutional neural network," "apparent diffusion
   coefficient," "Fleiss' kappa" stay as-is.
6. **Never introduce new claims** or remove existing ones.
7. **Vary sentence structure.** Mix short declarative sentences (8-12 words) with longer ones
   (25-35 words). Avoid uniform length.
8. **Use active voice** where natural. "We analyzed" rather than "Analysis was performed."

**Fix strategies per pattern category:**

| Category | Strategy |
|----------|----------|
| Content patterns (1-6) | Delete vague claims; replace with specific data or citations |
| Language patterns (7-12) | Substitute with plain academic English; simplify verb constructions |
| Style patterns (13-15) | Adjust formatting and punctuation |
| Filler and hedging (16-18) | Delete filler; calibrate hedging to match evidence level |

**Output:** Present the rewritten text with changes highlighted using diff format or tracked changes.

### Phase 4: Verify

Re-scan the rewritten text using the same 24 patterns.

**Output: Verification Report**

```
## Verification Report

| Metric | Before | After |
|--------|--------|-------|
| Total instances | 23 | 4 |
| Density (per 1000 words) | 8.2 | 1.4 |
| HIGH severity patterns | 3 | 0 |
| MEDIUM severity patterns | 5 | 2 |

Remaining issues:
- Pattern 17 (hedging): 2 instances remain -- appropriate for the evidence level.

Verdict: PASS (density < 2.0)
```

If the density remains above 2.0, run another fix-verify cycle (max 3 rounds).

---

## The 24 Detection Patterns

### Content Patterns

| # | Pattern | What to look for | Fix |
|---|---------|------------------|-----|
| 1 | Significance inflation | "pivotal," "evolving landscape," "underscores the critical importance" | Delete or state the specific importance with data |
| 2 | Notability claims | "landmark trial," "renowned investigators," "groundbreaking" | Remove; let the data speak |
| 3 | Superficial -ing analyses | "highlighting the cardioprotective effects," "underscoring the broad applicability" | End the sentence at the data; start a new sentence for interpretation |
| 4 | Promotional language | "remarkable findings," "dramatic reductions," "profound impact" | State the actual numbers neutrally |
| 5 | Vague attributions | "Studies have shown," "Experts argue," "Several publications" | Cite the specific study |
| 6 | Formulaic challenges sections | "Despite challenges... future outlook... continues to provide" | State specific limitations factually |

### Language Patterns

| # | Pattern | What to look for | Fix |
|---|---------|------------------|-----|
| 7 | AI vocabulary words | Additionally, crucial, delve, enhance, fostering, pivotal, showcase, tapestry, underscore, landscape (abstract) | Delete or replace with plain English |
| 8 | Copula avoidance | "serves as," "stands as," "represents a" | Use "is" |
| 9 | Negative parallelisms | "not only X but also Y" | "X and Y" |
| 10 | Rule of three overuse | Forcing ideas into groups of three repeatedly | Use natural grouping (2, 4, 5 items) |
| 11 | Synonym cycling | patients/participants/subjects/individuals | Pick one term, use consistently |
| 12 | False ranges | "from improved renal function to enhanced cardiac outcomes" | List the specific outcomes directly |

### Style Patterns

| # | Pattern | What to look for | Fix |
|---|---------|------------------|-----|
| 13 | Em dash overuse | More than 2 em dashes per page | Use parentheses or restructure. **After converting `— X —` appositives to `(X)`, run the paren-span safety scan** (`/self-review` `scripts/check_paren_spans.py`): a bulk conversion can pair two *unrelated* dashes across a sentence boundary and wrap a whole sentence (or an ordinal "Sixth, …" limitation) inside one parenthesis — paren-balanced but broken, so a balance check misses it. Operate per-sentence; never match across `. ` |
| 14 | Title case in headings | "Statistical Analysis And Primary Endpoints" | Sentence case per journal style |
| 15 | Curly quotation marks | Curly quotes from ChatGPT | Straight quotes |

### Filler and Hedging

| # | Pattern | What to look for | Fix |
|---|---------|------------------|-----|
| 16 | Filler phrases | "It is important to note that," "In order to," "Due to the fact that" | Delete the filler; state the content directly |
| 17 | Excessive hedging | "may potentially suggest the possibility" | Choose the appropriate certainty level: "suggests" |
| 18 | Generic positive conclusions | "The future looks bright," "continues to reshape," "paves the way" | State the specific next step or implication |

### Senior MA Reviewer Patterns

| # | Pattern | What to look for | Fix |
|---|---------|------------------|-----|
| 19 | § (section sign) marker | "as in §2.3", "(see §Discussion)", "§Results" | Delete or replace with section name ("Methods", "Results") — `grep -c "§"` = 0 |
| 20 | Methods/Results self-reference parenthetical | "(Methods §X)", "(Results §3.1)", "(Methods, Section 2.3)" | Drop the parenthetical or shorten to "(see Methods)" |
| 21 | AI Disclosure boilerplate (body) | "## Artificial Intelligence Disclosure", "Generative AI was not used to create..." in manuscript body | Remove from body → place in cover letter / submission form only (per `~/.claude/rules/journal-ai-image-policies.md`) |

### Response-Letter Patterns (R2R)

Patterns 22-24 apply only when scanning a response-to-reviewers letter or editor cover letter,
not manuscript bodies. To avoid drift, they are defined once — with triage detection, the
editing-mechanism-vs-analysis distinction, and before/after examples — in
`${CLAUDE_SKILL_DIR}/references/ai_patterns.md` (Response-Letter Patterns section). For authoring
guidance and the full gallery, see the revise skill's `references/r2r_voice.md`.

---

## Section-Specific Focus

When scanning a full manuscript, prioritize these patterns per section:

| Section | Priority Patterns | Reason |
|---------|------------------|--------|
| Abstract | ALL (1-21) | Most visible section; most scrutinized for AI patterns |
| Introduction | 1, 2, 5, 7, 12 | AI inflates background importance and uses vague attributions |
| Methods | 8, 16 | Methods should be straightforward; copula avoidance and filler are common |
| Results | 3, 4, 6, 10, 11 | AI adds interpretive -ing clauses and promotional language to results |
| Discussion | 1, 5, 6, 17, 18 | AI produces formulaic discussions with excessive hedging |
| Conclusion | 1, 18 | AI generates generic positive conclusions |
| Methods (MA / SR) | 19, 20, 21 | § markers, self-reference parentheticals, AI Disclosure boilerplate are senior-MA-reviewer red flags |
| Discussion (MA / SR) | 19, 20 | Self-reference parentheticals especially common when discussing methods |
| Body (any) | 21 | AI Disclosure belongs in cover letter / submission form, not manuscript body |
| Response to Reviewers / cover letter | 22, 23, 24 (+ 13, 16, 19) | Editing-mechanism narration, internal draft line numbers, and tooling leaks are the dominant tells in machine-drafted rebuttals (see ai_patterns.md R2R section) |

---

## Interaction with Other Skills

| Calling skill | When this skill is invoked |
|---------------|---------------------------|
| `/write-paper` | Phase 7 (Polish) -- automatic scan before submission |
| `/peer-review` | When reviewing one's own manuscript for AI patterns |
| `/revise` | When drafting response-to-reviewers letters and cover letters -- patterns 22-24 are the enforced gate before submission |

When called by another skill, return the verification report so the calling skill can check
the pass/fail status.

---

## What This Skill Does NOT Do

- Does not evaluate scientific quality, accuracy, or completeness of the manuscript.
- Does not add new content or citations.
- Does not assess journal compliance or formatting.
- Does not translate between languages.
- Only removes AI patterns; does not perform general copy-editing.

## Anti-Hallucination

- **Never introduce new claims or citations** during rewriting. Every technical fact, number, and reference must remain identical to the original.
- **Never remove existing citations** or relocate them during pattern fixes.
- **Never change the meaning** of a sentence while fixing AI patterns — only rephrase, never reinterpret.
- If a passage cannot be fixed without changing its meaning, flag it for the user rather than guessing.

---

## Gates

| Gate | Severity | Trigger | Action on fail |
|---|---|---|---|
| AI-pattern density target | ADVISORY | density > 2.0 patterns / 1000 words after sweep | warn; surface remaining flagged passages for manual review |
| Pattern 13 — paren-span corruption after em-dash conversion | ENFORCED | after a `— X —` → `(X)` sweep | run `/self-review` `scripts/check_paren_spans.py --strict`; `PAREN_SPAN_ORDINAL` / `PAREN_SPAN_SENTENCE` means a conversion wrapped a sentence/ordinal inside parens — fix before finalizing |
| Pattern 19 — `§` symbol | ENFORCED (senior MA reviewer prep) | `grep -c "§" manuscript.md` > 0 | auto-strip; verify post-rewrite count == 0 |
| Pattern 20 — `(see Methods §X)` self-reference | ENFORCED | match found | rewrite to direct section name reference |
| Pattern 21 — AI Disclosure paragraph in body | ENFORCED | "Generative AI was not used..." paragraph in manuscript body | move to cover letter or remove |
| Patterns 22-24 — R2R editing-mechanism / draft line-number / tooling leak | TRIAGE (response letters); `§` = 0 hard | detection greps in ai_patterns.md R2R section surface candidates | review each hit (analysis narration, quoted additions, revised-manuscript page/line are NOT tells); rewrite confirmed tells to substantive prose |
| Citation preservation invariant | ENFORCED | any pre-existing `[@bibkey]` removed by rewrite | revert that single rewrite; flag for user |
| Numerical preservation invariant | ENFORCED | any number changed by rewrite | revert; flag for user |

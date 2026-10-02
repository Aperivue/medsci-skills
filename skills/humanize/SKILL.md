---
name: humanize
description: Use when a manuscript or response-to-reviewers letter reads as AI-written. Scans for 27 AI writing patterns and rewrites flagged passages, preserving technical accuracy and bounding how much text changes. Not general copy-editing; that is /polish-language.
metadata:
  triggers: "humanize, AI patterns, AI 문체, remove AI writing, make it sound natural, 자연스럽게, de-AI"
---

# Humanize Skill

This skill only removes AI patterns; it does not perform general copy-editing, evaluate
scientific quality, check journal formatting, or translate.

Read `${CLAUDE_SKILL_DIR}/references/ai_patterns.md` at the start of every session, before
scanning: the definitions, watch words, examples, detection greps, per-pattern fixes and the
section-by-section priorities for all 27 patterns live only there.

---

## Workflow

### Phase 1: Scan

Scan the section(s) the user provides for all 27 patterns. For response-to-reviewers letters and
cover letters, prioritise Patterns 22-24. For a full manuscript, follow the per-section priorities
in `ai_patterns.md` (Section-Specific Application Guide). For each pattern found, record its number
and name, the count, the exact passage, and its location (paragraph number or line range).

**Output: Pattern Frequency Table**

```
## AI Pattern Scan Report

Section: {section name}
Word count: {N}

| # | Pattern | Count | Severity | Example from text |
|---|---------|-------|----------|-------------------|
| 1 | Significance inflation | 3 | HIGH | "...pivotal role in diagnostic imaging..." |
| ... | ... | ... | ... | ... |

Patterns not detected: 2, 4, 9, 14, 15

Total AI pattern instances: {N}
AI pattern density: {N per 1000 words}
```

### Phase 2: Report

- Severity per pattern: **HIGH** (>3 occurrences), **MEDIUM** (1-3), **LOW** (0, clean).
- Density: total instances across all 27 patterns per 1000 words. Target: < 2.0.

**Gate:** Present the report and ask the user which patterns to fix. Default: fix all HIGH and MEDIUM.

### Phase 3: Fix

Rewrite flagged passages with each pattern's fix from `ai_patterns.md`, under these rules:

1. **Preserve technical accuracy.** Every number, statistic, p-value, confidence interval, and
   clinical fact must remain identical.
2. **Preserve citations.** Never add, remove, or relocate a citation.
3. **Keep the formal academic register** of an experienced radiologist writing for peers in a
   top-tier journal. Never make the text casual or conversational.
4. **Keep domain-specific terminology intact.** "Convolutional neural network," "apparent diffusion
   coefficient," "Fleiss' kappa" stay as-is.
5. **Never introduce new claims, remove existing ones, or change a sentence's meaning** — rephrase,
   never reinterpret. If a passage cannot be fixed without changing its meaning, leave it and flag
   it for the user.
6. **Use active voice** where natural: "We analyzed" rather than "Analysis was performed."
7. **Vary sentence structure.** Mix short declarative sentences (8-12 words) with longer ones
   (25-35 words). A de-AI pass tends to *flatten* rhythm — it shortens the long sentences and pads
   the short ones toward a comfortable middle, which is itself a tell.
   `scripts/check_sentence_variety.py` verifies this rule in Phase 4.
8. **Thin out antithesis and cleft constructions (Pattern 27, the M2 heuristic).** For each "X
   rather than Y", "not X but Y" or "X, not Y", apply the negative-form test: delete the negative
   half and rewrite the clause in the positive. If a fact disappears, the contrast was functional —
   keep it; if nothing disappears, it was decoration — cut it. Judge by the manuscript's overall
   rate, not instance by instance, and keep two or three for emphasis. Rewrite clefts ("What … is
   …", "It is … that …") in plain subject-verb order ("What matters is X" → "X matters").
   `scripts/check_rhetorical_density.py` (in `/self-review`) measures this in Phase 4.

**Output:** Present the rewritten text with changes highlighted using diff format or tracked changes.

### Phase 4: Verify

**Keep the pre-rewrite text.** Before editing in place, copy the original somewhere the fidelity
check can read it (`cp manuscript.md /tmp/pre_humanize.md`). Without it Phase 4 can only re-scan
for patterns — it cannot tell whether the rewrite preserved numbers and citations.

Run both deterministic checks, then re-scan the rewritten text using the same 27 patterns.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_rewrite_fidelity.py" \
    --before /tmp/pre_humanize.md --after manuscript.md \
    --out qc/rewrite_fidelity.json --strict
python3 "${CLAUDE_SKILL_DIR}/scripts/check_sentence_variety.py" \
    --manuscript manuscript.md --out qc/sentence_variety.json
```

`NUMBER_DRIFT`, `NUMBER_REASSIGNED`, `CITATION_DROP` or `CITATION_MOVED` means the rewrite broke an
invariant — revert that passage, redo it, and flag it for the user. `EDIT_FOOTPRINT_HIGH` is advisory: Patterns 6 and 18 replace whole
paragraphs by design, so a correct pass over an inflated draft can exceed 60% of words changed.
Read the diff and confirm the author's argument survived rather than assuming the percentage is a
defect.

**Known limits:** the fidelity gate does not check an added or removed negation, a number written
in words, a changed unit, or a direction word next to a non-percentage. A clean exit does not
clear these; read the diff for them.

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

If the density remains above 2.0, run another fix-verify cycle (max 3 rounds). When called by
another skill, return the verification report so the calling skill can check the pass/fail status.

---

## The 27 Detection Patterns

All 27 are defined in `references/ai_patterns.md`. Two carry rules to apply exactly as written:

| # | Pattern | What to look for | Fix |
|---|---------|------------------|-----|
| 13 | Em dash overuse | More than 2 em dashes per 1000 words (the `/self-review` classical-style gate fails a manuscript above 25 prose em-dashes) | Use parentheses or restructure. **After converting `— X —` appositives to `(X)`, run the paren-span safety scan** (`python3 "${CLAUDE_SKILL_DIR}/../self-review/scripts/check_paren_spans.py"`): a bulk conversion can pair two *unrelated* dashes across a sentence boundary and wrap a whole sentence (or an ordinal "Sixth, …" limitation) inside one parenthesis — paren-balanced but broken, so a balance check misses it. Operate per-sentence; never match across `. ` |
| 21 | AI Disclosure boilerplate (body) | "## Artificial Intelligence Disclosure", "Generative AI was not used to create..." in manuscript body | Put it where the target journal asks (the journal profile's `Disclosure location`): Methods or Acknowledgments for some journals, cover letter, title page or submission form only for others. Do not delete a disclosure the journal requires in the body |

Patterns 22-24 apply only to response-to-reviewers letters and editor cover letters, not
manuscript bodies. They are defined once in `ai_patterns.md` (Response-Letter Patterns); for
authoring guidance, see the revise skill's `references/r2r_voice.md`.

---

## Gates

| Gate | Severity | Trigger | Action on fail |
|---|---|---|---|
| AI-pattern density target | ADVISORY | density > 2.0 patterns / 1000 words after sweep | warn; surface remaining flagged passages for manual review |
| Pattern 13 — paren-span corruption after em-dash conversion | ENFORCED | after a `— X —` → `(X)` sweep | run `python3 "${CLAUDE_SKILL_DIR}/../self-review/scripts/check_paren_spans.py" --strict`; `PAREN_SPAN_ORDINAL` / `PAREN_SPAN_SENTENCE` means a conversion wrapped a sentence/ordinal inside parens — fix before finalizing |
| Pattern 19 — `§` symbol | ENFORCED (senior MA reviewer prep) | `grep -c "§" manuscript.md` > 0 | auto-strip; verify post-rewrite count == 0 |
| Pattern 20 — `(see Methods §X)` self-reference | ENFORCED | match found | rewrite to direct section name reference |
| Pattern 21 — AI disclosure in the wrong place | ENFORCED | an AI-use disclosure in the body of a journal that wants it elsewhere, or repeated in several places | move it to where the target journal asks (journal profile); never reword a required disclosure to hide the tool |
| Pattern 26 — aphorism density | ENFORCED | negative-definition rate AND short-declarative share both over threshold | run `python3 "${CLAUDE_SKILL_DIR}/../self-review/scripts/check_aphorism_density.py" --manuscript manuscript.md`; `APHORISM_DENSITY` (Minor) means the prose is a run of epigrams with the explanatory sentences compressed out — absorb most of them into the neighbouring sentence and write the explanation back, keeping two or three for emphasis; do NOT simply delete them, which shortens the prose further |
| Pattern 27 — antithesis / cleft density | ENFORCED | "rather than" / "not X but Y" / "X, not Y" or "What … is …" / "It is … that …" over a per-1000 threshold AND raw-count floor | run `python3 "${CLAUDE_SKILL_DIR}/../self-review/scripts/check_rhetorical_density.py" --manuscript manuscript.md`; `ANTITHESIS_DENSITY` / `CLEFT_DENSITY` (both Minor) — apply Fix rule 8 (the M2 test). A lone functional "rather than" or "instead of" never fires |
| Pattern 25 — inline-emphasis over-use | ENFORCED | italic-emphasis density over threshold after allowlist | run `python3 "${CLAUDE_SKILL_DIR}/../self-review/scripts/check_emphasis_density.py" --manuscript manuscript.md`; `EMPHASIS_OVERUSE` (Minor) means strip inline italics (keep only stat symbols / Latin / gene-species); whole-clause italics are the strongest tell |
| Patterns 22-24 — R2R editing-mechanism / draft line-number / tooling leak | TRIAGE (response letters); `§` = 0 hard | detection greps in ai_patterns.md R2R section surface candidates | review each hit (analysis narration, quoted additions, revised-manuscript page/line are NOT tells); rewrite confirmed tells to substantive prose |
| Citation preservation invariant | ENFORCED | a citation item (each key of a multi-key or locator Pandoc citation, or a numeric marker) removed or changed, or moved out of the sentence of the word it was attached to while that word kept its place | `scripts/check_rewrite_fidelity.py --before <pre> --after <post> --strict` → `CITATION_DROP` / `CITATION_MOVED` (Major); revert that single rewrite and flag for the user |
| Numerical preservation invariant | ENFORCED | a numeric token's count changed (sign, inequality sign and %-direction are part of the token; writing a sign out in words also fires), or values traded places while the words around them stayed | same script → `NUMBER_DRIFT` / `NUMBER_REASSIGNED` (Major); revert and flag. Known limits: a negation, a number written in words, a unit, or a direction word next to a non-percentage is not checked — read the diff for these |
| Rewrite footprint | ADVISORY | fraction of word tokens changed exceeds `--warn-pct` (default 70) | `EDIT_FOOTPRINT_HIGH` (Minor) — never blocks; read the diff (Phase 4) |
| Fix rule 7 — sentence-length uniformity | ADVISORY | prose has no short (≤12 words) or no long (≥25 words) sentences | `scripts/check_sentence_variety.py --manuscript <file>` → `SENTENCE_UNIFORM` (Minor); break up or combine sentences until both bands exist. Silent below 15 sentences |

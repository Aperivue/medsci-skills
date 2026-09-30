---
name: polish-language
description: Use when a manuscript needs a copy-edit for consistency and non-native English clarity. Flags abbreviation, US/UK spelling, en-dash range, P/p, hyphenation, number-style and unit-spacing issues, then polishes style only. AI-tell removal is /humanize.
triggers: polish language, copy-edit, consistency check, ESL, non-native English, house style, abbreviation consistency, en-dash, US UK spelling, proofread manuscript, 일관성 검사, 교정
tools: Read, Write, Edit, Grep, Glob, Bash
model: inherit
---

# Polish-Language Skill

Tighten a manuscript's **mechanical language consistency and clarity** before circulation or
submission — the copy-editor pass content-focused skills skip. The author is often a non-native
(ESL) English writer, so clarity edits keep the formal academic register and never touch facts.
Manuscript edits are in English.

This skill **never** rewrites scientific claims, changes numeric values, edits citations, or
judges study quality; it standardizes house style and improves sentence-level clarity, with
explicit user approval for every edit. Out of scope: AI-tell removal (`humanize`, which does not
do general copy-editing), drafting or restructuring (`write-paper`), reporting-guideline items
(`check-reporting`), AI-search optimization (`academic-aio`), reference formatting and citation
integrity (`manage-refs`, `verify-refs`), and translation.

**Input**: a manuscript or section (Markdown / plain text). **Output**: (1) the deterministic
consistency report, and (2) — only after a user gate — a clarity-polished revision with a change
log limited to style.

## Workflow

### Phase 1: Deterministic consistency lint (no LLM judgement)

Run the bundled linter — it reports, never edits:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/lint_consistency.py" path/to/manuscript.md
# add --strict to exit non-zero when any issue is found (CI / pre-submission gate)
```

It flags eight families, each with line numbers and a per-category + total count:

1. **Abbreviations** — used-before-defined, defined-but-unused, defined-twice,
   used-but-never-defined (define-once discipline).
2. **Spelling** — mixed US/UK variants (analyze/analyse, tumor/tumour, …); reports the minority
   side against the document's dominant variant.
3. **Numeric ranges** — hyphen between numbers where an en-dash belongs (`5-10` → `5–10`).
4. **p-values** — mixed `P`/`p` case; impossible `P = 0.000`.
5. **Hyphenation / terminology** — variant forms of one term (follow-up / followup / "follow up").
6. **Small numbers** — single digits 1–9 written as digits in prose.
7. **Units** — missing space between value and unit (`5mg` → `5 mg`).
8. **Thousands separator (title vs body)** — a float title writes a number with a period
   separator (`3.681`) that the body writes with a comma (`3,681`).

Present the report to the user. The linter output is the source of truth for what is
mechanically wrong: do not invent further "issues" from memory, and label anything else you
notice as an editorial suggestion, not a linter finding. The fixed rules do not settle every
grammar or journal preference, so triage flags in context.

### Phase 1b: Figure-SOURCE locale drift

Text baked into a figure never reaches Phase 1, so a UK word typed into a PowerPoint panel or
plotting script ships in a US manuscript unseen. Scan the figure **sources** (no OCR):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/lint_figure_locale.py" --manuscript path/to/manuscript.md --figures-dir figures/
# --spelling us|uk forces the target; otherwise it reads a `spelling:` front-matter field,
# then falls back to the body's own US/UK majority. --strict exits non-zero on any drift.
```

It reads `<a:t>` runs inside `*.pptx` slide XML and the text of `*.py` / `*.R` plotting scripts,
with the same US↔UK families as Phase 1. `FIGURE_LOCALE_DRIFT` is **Minor** — copy-edit the
source before the raster is re-exported. A missing figures directory is not an error; it exits 0
with nothing judged.

### Phase 2: Triage with the user (gate)

Walk the user through the report. Some flags are author choices (a journal may mandate UK
spelling, or digits for all numbers). **User approval is required** before any edit — confirm
per category which to apply and which to keep. Record the decisions; do not auto-apply.

### Phase 3: Apply mechanical fixes (style-only)

For each **approved** category, apply the deterministic fix with `Edit`:
- standardize spelling to the chosen variant,
- replace numeric-range hyphens with en-dashes,
- normalize `P`/`p` and fix `P = 0.000` to the reported inequality,
- unify hyphenation, spell out small numbers, add value/unit spaces,
- define each abbreviation once at first use; remove redundant redefinitions.

Re-run `lint_consistency.py` after editing — the count should drop to the issues the user chose
to keep. This re-run is the verification gate; never claim a fix without it.

### Phase 4: ESL clarity polish (optional, gated, style-only)

If the user requests a clarity pass, improve readability sentence by sentence while preserving
meaning, register, numbers, and citations:
- split run-on sentences; fix article (a/an/the) and preposition usage;
- correct subject–verb agreement and awkward non-native phrasings;
- prefer active voice only where it does not change emphasis or claims.

Show each proposed change as a before/after diff and get **user review** before writing. Numbers,
p-values, effect sizes, units, citations, and claims are copied verbatim; an edit that would
change any of them is out of scope — skip it. Never merge, add, or drop a scientific claim,
number, or reference. If a sentence's meaning is even slightly uncertain, leave it and ask; do
not invent domain facts to smooth a sentence. Every applied change must trace to a linter flag
or a user-approved clarity suggestion in the change log.

## Reproducible challenge card

Deterministic and network-free (synthetic manuscript with seeded defects +
`expected/report.txt`):

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/lint_challenge/verify.sh"   # PASS = 11 seeded issues across 8 categories + 2 clean controls
```

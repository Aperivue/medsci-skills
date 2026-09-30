---
name: find-journal
description: Use when choosing where to submit a manuscript. Matches the abstract against curated journal profiles and returns ranked picks with scope fit, AI-disclosure policy, an acceptance-readiness pre-flight and a reject-fallback cascade. Impact and APC figures may be stale.
model: inherit
metadata:
  triggers: "find journal, recommend journal, where to submit, which journal, journal selection, target journal, journal match"
---

# Find Journal Skill

## Phase 1: Input Collection

### Required Inputs
1. **Abstract text** or key findings summary
2. **Study type**: original research, meta-analysis, case report, technical note, review, letter, AI validation, diagnostic accuracy, etc.

### Optional Inputs
3. **Preferred tier**: Q1 / Q1-Q2 / any (default: any)
4. **OA preference**: Full OA / Hybrid OK / No preference (default: no preference)
5. **Field focus**: radiology, medical AI, clinical specialty, methodology, education, general medicine
6. **Journals to exclude**: journals that have already rejected this manuscript

If only an abstract is given, infer the study type from it. When called from `/write-paper` or
another skill, take the abstract and study type from the calling context and skip these questions.

---

## Phase 2: Theme Extraction

From the abstract or key findings, extract: disease/condition; modality/technique; methodology
(e.g., retrospective cohort, diagnostic accuracy, systematic review, RCT); population; and
innovation type (new algorithm, clinical validation, workflow improvement, educational tool).

---

## Phase 2.5: Acceptance-Readiness & Design-Ceiling Pre-flight

Editors screen importance/novelty and the design ceiling before scope fit (lack of
novelty/importance is the top desk-rejection cause). This phase estimates that first filter, so
the skill does not recommend a venue whose bar the design cannot clear. It is advisory, and its
flags are **not auto-fixable**: the author decides.

### 2.5.1 Run the deterministic pre-flight (preferred)

If a manuscript or abstract file is available, run:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/assess_acceptance_readiness.py <manuscript_or_abstract.md>
# add --json for a machine-readable report
```

It returns flags in four categories — DESIGN_CEILING, UNFIXABLE_DEFECT,
IMPORTANCE_RISK, CLAIM_MISMATCH — and a ceiling verdict
(`NO STRUCTURAL CEILING …` / `IMPORTANCE-FRAMING REVIEW …` /
`SPECIALTY / TOLERANT-VENUE OR DESIGN FIX …` / `HIGH-IMPACT VENUE UNLIKELY …`).

### 2.5.2 If only pasted text is available

Read `${CLAUDE_SKILL_DIR}/references/acceptance_signals_schema.md` §3 (taxonomy and verdict
bands), apply the same taxonomy to the pasted text with judgement, and assign the same ceiling
verdict.

### 2.5.3 Carry the verdict forward

Record the ceiling verdict and its top flags for Phase 3.2 Axis 2 and for the Phase 4
Acceptance-Readiness Summary and Cascade plan. Do not block the recommendation on a ceiling:
route to a venue the design can clear, or recommend a design change or presubmission inquiry.

---

## Phase 3: Profile Loading and Matching (2-Pass)

### 3.1 Pass 1: Load Compact Profiles

Read both tiers and merge them into one profile set:

```
# Public (shipped with the skill)
${CLAUDE_SKILL_DIR}/references/journal_profiles/*.md

# User-local private (optional, may be empty or absent)
$HOME/.claude/private-journal-profiles/find-journal/*.md
```

On a filename collision the private copy wins (user override). If either directory is missing or
empty, continue with the other and say which tier was unavailable. Count the profiles actually
loaded after the merge and state the total in the output — never hard-code the count.

From each profile parse Scope, Scope Keywords, Article Types Accepted, Classification (Tier, OA,
Field), Special Notes (includes a 1-line AI policy summary), and the optional **Acceptance
Signals** block (format: `${CLAUDE_SKILL_DIR}/references/acceptance_signals_schema.md` §1).

Do NOT read write-paper profiles in this pass — they are 4-5x larger and carry formatting detail
irrelevant to matching.

### 3.2 Two-Axis Scoring (scope fit × acceptance feasibility)

Score each journal on two independent axes: scope fit ("does this journal cover my topic?") and
acceptance feasibility ("can this manuscript's design and importance clear this journal's bar?").
Keep them separate — a perfect scope match can still desk-reject the design.

**Axis 1 — Scope fit.** Compute a composite scope-fit score:

| Factor | Weight | Description |
|--------|--------|-------------|
| Scope alignment | 40% | How well the manuscript's themes match the journal's scope and keywords |
| Study type fit | 25% | Whether the journal accepts this article type and values this methodology |
| Tier match | 20% | Alignment with user's preferred tier (if specified) |
| OA match | 10% | Alignment with user's OA preference (if specified) |
| Special fit | 5% | Bonus for unique alignment with journal's Special Notes |

**Axis 2 — Acceptance feasibility.** Weigh the Phase 2.5 ceiling verdict against each journal's
Acceptance Signals (selectivity band, desk-reject triggers, design expectations); for a profile
without that block, use its Special Notes plus the Phase 2.5 taxonomy. Assign **High / Medium /
Low**:
- **Low / ceiling-mismatch** when the journal's bar is one the manuscript's ceiling cannot clear
  (e.g., a `highly-selective` venue that desk-rejects single-center surrogate-endpoint designs,
  and the manuscript is exactly that).
- **High** when no ceiling signal collides with the journal's stated bar.

Report a band with reasons, NEVER an acceptance probability, because no acceptance-rate data
source exists and a number would be false precision (schema §4).

### 3.3 Filtering

Before scoring, exclude journals on the user's exclusion list and journals that do not accept the
manuscript's study type (e.g., a case report to a journal that only takes original research). If
no journal survives, relax the filters — OA constraint first, then tier — and re-score.

### 3.4 Ranking

Rank primarily by the Axis-1 scope-fit score, then apply Axis 2:
- **Demote** (or, if the mismatch is severe, drop below a better-feasibility peer) any journal
  whose acceptance feasibility is Low / ceiling-mismatch.
- **Never silently demote** — always carry the reason so Phase 4 can surface it.
- Select the top 5 by the feasibility-adjusted order. If a strong scope match is demoted for
  feasibility, still mention it in the comparison note with the mismatch spelled out (the author
  may choose to fix the design rather than change venue).

### 3.5 Pass 2: Enrich Top-5

For each top-5 journal, look for a detailed write-paper profile in both tiers (private wins on
collision):

```
# Public
${CLAUDE_SKILL_DIR}/../write-paper/references/journal_profiles/{journal_filename}

# User-local private
$HOME/.claude/private-journal-profiles/write-paper/{journal_filename}
```

If found, take from it: manuscript types and word limits, abstract format, statistical reporting
requirements, the full 5-field AI Writing Disclosure Policy, common rejection reasons, and
Acceptance Signals (these sharpen the Axis-2 call and the cascade plan). If none is found or the
directory is not accessible, use the compact profile only.

---

## Phase 4: Output

Every journal fact you print (URLs, article types, OA model, AI policy) comes from the loaded
profile or from the journal's own website; never invent journal metadata, an impact factor, an
APC or a submission policy.

For each of the top 5 recommended journals, present:

```
### Rank [N]: [Journal Name] ([Tier])

**Scope fit:** [2-3 sentences explaining why this manuscript matches this journal's scope.
Reference specific keywords, disease areas, or methodological preferences from the profile.]

**Article types accepted:** [relevant types from profile]

**Open Access:** [Full OA / Hybrid / Subscription]

**Acceptance feasibility:** [High / Medium / Low] — [1 line: how the manuscript's
Phase 2.5 ceiling meets this journal's bar; spell out any mismatch, e.g., "scope fit
High, but this highly-selective venue desk-rejects single-center surrogate-endpoint
designs — add external validation or target a selective/accessible venue"]

**Homepage:** [URL]
**Author guidelines:** [URL]

**AI disclosure:** [Required / Recommended / Not specified] — [brief summary of permitted scope and disclosure location, if available in profile]
```

After all 5, add a 2-3 sentence comparison note on the key tradeoffs between the top choices
(e.g., scope breadth vs. specialty depth, tier vs. acceptance feasibility). Then add the two
blocks below, then the Mandatory Disclaimer.

### Acceptance-Readiness Summary

```
---
### Acceptance-Readiness Summary

**Ceiling verdict:** [from Phase 2.5]
**Top flags:** [the 2-4 most consequential design-ceiling / unfixable / importance flags, each with its 1-line reason]
**Implication for venue tier:** [1-2 sentences — e.g., "An unfixable single-center +
surrogate-endpoint ceiling makes flagship venues unlikely without external validation;
the recommendations above are routed to venues this design can clear."]

_Advisory only — a risk band, not an acceptance prediction; flags are not auto-fixable._
```

### Cascade plan

```
---
### Cascade plan (primary → reject-fallback)

1. **Primary:** [top recommendation] — [why first]
2. **If rejected:** [fallback 1] — [same-publisher transfer if applicable, else one tier
   down / different scope angle]. An editor's transfer offer within the same publisher
   is usually worth taking: the manuscript skips a fresh desk screen.
3. **Then:** [fallback 2]

[If the Phase 2.5 risk is IMPORTANCE rather than design, recommend a **presubmission
inquiry** to the primary target before full submission — it lets the editor quick-assess
contribution/fit and saves a desk-reject cycle.]

[If a confidential corresponding-author editor-bar overlay exists in
`$HOME/.claude/private-journal-profiles/find-journal/`, its notes have already been
merged into the per-journal feasibility calls above.]
```

---

## Mandatory Disclaimer

Always append this disclaimer at the bottom of every recommendation output:

```
---
**Important Disclaimer**

Impact Factor, APC fees, acceptance rates, and turnaround times change frequently
and are subject to copyright restrictions. Please verify current values directly
at each journal's homepage before making your submission decision.

Recommended verification sources:
- Journal Citation Reports (JCR) via institutional access: for Impact Factor
- Journal homepage -> Author Guidelines: for current APC and formatting requirements
- Clarivate Master Journal List: for indexing status
```

---

## Special Modes

### Post-Rejection Mode

When the manuscript was rejected by a specific journal:

1. Exclude the rejecting journal.
2. **Distinguish the rejection type — it changes the advice:**
   - **Desk-reject (no peer review)** — usually an importance/novelty or design-ceiling
     verdict, not a fixable-revision signal. Re-run Phase 2.5; if a ceiling or importance flag
     is present, the next same-tier venue will likely desk-reject again. Route **one or two
     tiers down** (or to a tolerant/`accessible` venue), or advise the design/importance fix
     first, and consider a **presubmission inquiry**.
   - **Post-peer-review reject** — prefer a **same-publisher transfer** (Springer Nature
     Transfer Desk / Elsevier Article Transfer Service / Wiley / Nature Portfolio) that carries
     the referee reports; otherwise same tier or one down, with the fatal flaw addressed.
3. If rejected from Q1 other than by a ceiling/importance desk-reject, recommend a mix of Q1
   (different scope angle) and strong Q2.
4. In each scope-fit explanation, note how the recommendation differs from the rejected
   journal's focus.
5. Suggest scope adjustments — or, when Phase 2.5 found a ceiling, design changes — that might
   improve feasibility for the new target.

### Case Report Mode

When the study type is case report, prioritize journals known for valuing educational or rare
cases. If fewer than 5 profiled journals accept case reports, say so and suggest the user
consider case-report-specific journals outside the profile set.

### Submission Directory Scaffolding

When the user selects a target journal, create `submission/{journal_short}/` (lowercase with
underscores, e.g., `radiology_ai`, `european_radiology`, `ajr`) and report the path so
`/write-paper` Phase 8+ and `/peer-review` know where to write:

```
submission/
└── {journal_short}/          # e.g., radiology_ai/
    ├── cover_letter.md       # Generated by /write-paper Phase 8+
    ├── checklist.md          # Journal-specific submission checklist
    └── peer_review.md        # Generated by /peer-review (journal scope-aware)
```

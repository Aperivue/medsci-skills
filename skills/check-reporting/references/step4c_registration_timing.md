# Step 4c Reference — Registration / Protocol Timing Consistency Check

Load this reference when running Step 4c during `/check-reporting`. The SKILL.md body
carries only the scope + trigger summary; full item-by-item procedure lives here.

## Applies To

Systematic reviews, meta-analyses, and intervention studies with prospective registration
(PRISMA 2020, PRISMA-DTA, PRISMA-P, MOOSE, CONSORT, SPIRIT).

## Motivation

The registration identifier itself is a single checklist item in most guidelines, so it
can pass the Step 4 audit even when the manuscript is internally inconsistent about
*when* the registration or its amendments occurred relative to the analysis. Reviewers
and editors scrutinize this timing — an undisclosed post-hoc amendment is a common
rejection trigger.

## Items to Check

### 1. Registration identifier present

Confirm the registration number (e.g., PROSPERO CRD####, ClinicalTrials.gov NCT####) is
cited in Methods, the Abstract, and (where required) the cover letter.

### 2. Initial registration date vs. manuscript milestone dates

Extract from the manuscript:
- Search start / end date (e.g., "databases were searched from 2010-01-01 to 2025-12-31").
- Screening / data extraction completion date (often in the PRISMA flow caption or in
  Methods).
- If the Methods states an explicit registration date, that date must predate — or at
  minimum not contradict — the screening/extraction milestone. A registration date
  *after* data extraction completion must be disclosed as retrospective and justified.

### 3. Amendment date(s) consistency

If the manuscript references an amendment to the registered protocol:
- The amendment date must appear in Methods (typical phrasing: "The registered protocol
  was amended on YYYY-MM-DD to …").
- The described amendment content must match what Methods actually reports (e.g., an
  eligibility refinement, subgroup reassignment, outcome addition). A Methods-stated
  amendment that does not correspond to any visible methods change is a red flag.
- If the amendment post-dates the analysis lock, Methods must state that the analysis
  was re-run after the amendment — otherwise the amendment is a post-hoc rationalization.
- The amendment date must not post-date the manuscript submission date (when the latter
  is known from the cover letter or file metadata).

### 4. Cross-artifact agreement

When the author provides the registry record (PROSPERO PDF, ClinicalTrials.gov export)
as a supplement or accompanying document:
- Primary outcome(s), eligibility criteria, and analysis plan described in Methods must
  agree with the registry entry, or explicit amendment citations must reconcile any
  difference.
- A silent discrepancy between registry and Methods is a `[REGISTRATION-TIMING]`
  finding, reported in Part C with `fixable_by_ai: false` (requires author action — file
  an amendment or correct Methods text).

### 5. Retrospective registration disclosure

If any evidence suggests the registration was filed after data extraction began
(registration date later than the reported extraction start, or the registry record's
"current stage" indicates post-extraction filing), Methods must contain a disclosure
paragraph. The absence of such disclosure in a retrospective-registered review is a
`[REGISTRATION-TIMING]` finding.

## Flagging Rules

- Any failure among items 1 – 5 is reported in Part C Action Items with the label
  `[REGISTRATION-TIMING]`.
- Mark `fixable_by_ai: false` when reconciliation requires an external amendment filing
  or an author-supplied date.
- Mark `fixable_by_ai: true` only when the fix is a Methods-text insertion of a known
  registration identifier or amendment date already disclosed elsewhere in the
  manuscript.

## JSON Field (Part D)

Include a `registration_timing` object when this step runs:

```json
"registration_timing": {
  "registry": "PROSPERO",
  "registration_id": "CRD########",
  "initial_registration_date": "YYYY-MM-DD or null",
  "amendments": [
    { "date": "YYYY-MM-DD", "described_change": "..." }
  ],
  "timing_consistency": "CONSISTENT | DISCREPANCY | INCOMPLETE",
  "findings": ["free-text list of specific issues"]
}
```

# MA-Scout Project README Template (PROSPERO-ready)

Load this reference when `/ma-scout` Phase 4 (Folder & README Scaffolding) creates a
new topic folder. English section headings and PICO/PIRD structure keep the README aligned
with downstream `/meta-analysis` and `/search-lit` expectations.

This is the English default. For a supervisor / professor-facing Korean README, use
`project_readme_template_ko.md` (same structure, Korean prompts for the PI-facing fields).

Copy the block below into `{topic_folder}/README.md` and fill in the curly-brace fields.

````markdown
# {Topic Title} — {MA Type} Meta-analysis ({Supervisor name})

## Overview
- Supervisor: {Supervisor name} ({affiliation history})
- Supervisor's area: Pillar {N} — {area name}
- Status: Planning
- Priority: rank {N}
- Created: {YYYY-MM-DD}

## Research Question
### PICO/PIRD
- **P**opulation: {specific patient group, disease, setting}
- **I**ndex test / Intervention: {test or intervention}
- **C**omparator / Reference standard: {comparator or reference standard}
- **O**utcome: {DTA: Se/Sp/AUC, Prognostic: HR/OR, adverse events, etc.}

### One-line RQ
{the complete research question in one sentence}

## Key Gap
- Existing MAs: {N} ({details, most recent year, scope limitations})
- Consensus/Scholar Gateway cross-check: {result summary}
- medRxiv/bioRxiv preprint MA: {yes/no}
- Registered PROSPERO protocol: {yes (CRD#) / no}
- {specific gap explanation — why a new MA is needed}

## Professor's Authority
- {number of related publications, 1-2 representative papers, distinctive contribution}
- {why this supervisor is well-suited to this topic}

## Preliminary Search ({date})
### Search Strategy (PubMed)
```
{the actual PubMed query used — the E-utilities esearch query verbatim}
```
- Total hits: {N} (raw)
- DTA/outcome extractable (estimated): {N} (×0.15-0.30 discount)
- Existing MAs: {N} (narrow) / {N} (including broad SRs)
- Consensus search result: {whether any additional papers were found}
- bioRxiv/medRxiv: {N} preprints

### Embase Search Strategy (Draft)
```
{draft Embase query — including Emtree terms}
```
(draft before execution — verify when Embase access is available)

## Target Journal
| Rank | Journal | IF | MA acceptance rate | Turnaround | Notes |
|------|---------|-----|--------------------|-----------|-------|
| 1st | {journal} | {IF} | {high/medium} | {months} | {rationale} |
| 2nd | {journal} | {IF} | {high/medium} | {months} | {rationale} |

## Timeline (backwards-planned)
| Stage | Estimated time | Prerequisite |
|-------|----------------|--------------|
| Supervisor proposal | {YYYY-MM} | {condition} |
| PROSPERO registration | +1 week | Supervisor approval |
| Search complete | +2 weeks | PROSPERO registration |
| Screening complete | +3 weeks | 2nd reviewer secured |
| Data extraction | +4 weeks | Screening consensus |
| Analysis + draft | +6 weeks | Data lock |
| Supervisor review | +8 weeks | Draft complete |
| Submission | +10 weeks | Supervisor approval |

## Data Sources Used
- PubMed E-utilities: ✅ (esearch count + efetch metadata)
- Consensus MCP: ✅/❌
- Scholar Gateway: ✅/❌
- bioRxiv/medRxiv: ✅/❌
- PROSPERO: ✅
````

## Solo-Mode Adaptations (no supervisor)

When a user runs `/ma-scout` in topic-first mode (T-Phase 5) without a supervisor assignment,
substitute:
- `## Overview` — replace `Supervisor:` with `Lead: {user_name}` or `Lead: {user_name} + {co-author}`,
  and the `Supervisor's area` row with `Domain: {subspecialty}`.
- `## Professor's Authority` — rename to `## Team Expertise` and describe the user's credentials and
  prior publications that justify leading this MA, plus the co-author's if any.
- `## Timeline` — drop the supervisor-proposal step and start directly at PROSPERO registration:

| Stage | Estimated time | Prerequisite |
|-------|----------------|--------------|
| PROSPERO registration | {YYYY-MM} | Topic confirmed |
| Search complete | +1 week | PROSPERO registration |
| Screening complete | +2 weeks | 2nd reviewer secured |
| Data extraction | +3 weeks | Screening consensus |
| Analysis + draft | +5 weeks | Data lock |
| Co-author review | +7 weeks | Draft complete |
| Submission | +8 weeks | Final approval |

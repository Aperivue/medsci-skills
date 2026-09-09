---
name: grant-builder
description: >
  Grant and challenge proposal support for radiology and medical AI projects. Structures significance,
  innovation, approach, milestones, and consortium roles while keeping claims evidence-based and executable.
triggers: grant, proposal, aims page, grant proposal, significance, innovation, approach, milestones, 산학과제, 산학협력, 과제계획서, 연구계획서, 연구비 신청, 첨부3
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Grant-Builder Skill

## Purpose

This skill supports competitive proposal writing for:

- national R&D grants
- multi-institution consortia
- challenge proposals
- internal pilot funding
- translational medical AI project plans
- **Korean government grants** (산학협력 / 연구계획서 — MOHW 복지부, MOTIE 산자부, MSS 중기부, and regional industry-academia programs)

It is optimized for projects where clinical relevance, multi-site coordination, and executable milestones matter as much as technical novelty.

---

## Korean Government Grant Mode (산학과제 / 연구계획서)

When the user requests a Korean industry-academia grant (산학과제) or research plan
(연구계획서), apply the adaptations below. Korean program terms are preserved in
parentheses because they are the literal form used on the funding agency's template.

### Document Structure (three-attachment format)

Most Korean grants follow a standardized three-attachment format:
- **Attachment 1 (첨부1, 기본정보)**: project title, participating institutions,
  investigator CVs, publication / patent record.
- **Attachment 2 (첨부2, 매칭확인서)**: per-institution cost-share confirmation,
  typically finalized after a kickoff meeting between the institutions.
- **Attachment 3 (첨부3, 연구계획서)**: the 10-page research plan — structure below.

### Attachment 3 Standard Structure

```
1. Significance & Aims (약 2p)
   - clinical problem with quantitative framing
   - domestic + international trends (3–5 year literature / guideline window)
   - differentiation of the proposed work

2. Research Content & Methods (약 4p)
   - staged roadmap (Phase 1 – N with time ranges)
   - pipeline schematic (mandatory when an AI pipeline is in scope)
   - per-subproject institution and personnel assignment

3. Team Capability (약 1p)
   - expertise + representative record (SCI papers, patents) per investigator
   - cross-institution synergy (hospital = data / clinical; university = algorithm)

4. Expected Outcomes & Utilization (약 2p)
   - quantitative targets: SCI papers, patents
   - qualitative targets: clinical impact, standardization contribution
   - linkage to follow-on larger grants (positioning as a seed)

5. Budget Plan (약 1p)
   - RA salaries, computing equipment, consumables, academic activities, indirect costs
```

### Writing Tips for Small-Scale Grants (< KRW 30 million)

- Write for a non-specialist reviewer — assume the evaluator is not in your subfield.
- Emphasize feasibility over technical novelty.
- Prioritize length / format compliance; exceeding the template incurs scoring penalties.
- Include preliminary data or pilot results whenever available.
- Keep quantitative targets conservative — undershooting a committed target is punished
  more than overdelivering on a modest one.

---

## Communication Rules

- Communicate with the user in their preferred language.
- Proposal prose should be in the language required by the target call.
- Avoid hype. Emphasize unmet need, feasibility, differentiation, and deliverables.

---

## Core Outputs

Depending on the request, produce one or more of:

- project concept summary
- `Significance`
- `Innovation`
- `Approach`
- specific aims
- work packages
- milestone table
- role split by institution
- evaluation framework
- reviewer-risk memo

---

## Workflow

### Phase 1: Decode the funding call

Extract:
- funding body
- call theme
- eligibility constraints
- deliverable expectations
- timeline
- evaluation criteria

If no call text is available, infer a generic academic-medical AI proposal structure and label assumptions.

### Phase 2: Frame the problem

Define:
- clinical pain point
- current workflow limitation
- why existing AI or standard care is insufficient
- who benefits if the project succeeds

**Gate:** Present the problem framing (clinical pain point, gap, proposed solution) to the
user. Confirm before building proposal sections — a misframed problem produces an
unfundable proposal.

### Phase 3: Build the proposal spine

Always articulate:
- problem
- gap
- proposed solution
- why this team can execute it
- measurable outputs

### Phase 4: Convert to proposal sections

#### Significance

Must answer:
- why this matters clinically
- why this matters now
- why the proposed solution is worth funding

#### Innovation

Should focus on:
- what is genuinely different
- why the integration is new
- why the novelty is useful, not just technical

#### Approach

Should define:
- dataset and participating sites
- model or workflow components
- validation plan
- benchmark/comparator
- failure analysis
- risk mitigation

### Phase 5: Execution plan

Generate:
- milestones by quarter or year
- institution-level responsibilities
- dependencies and handoffs
- required infrastructure

---

## Default Structure

```text
## Proposal Summary
Title: ...
Goal: ...
Clinical problem: ...

### Significance
...

### Innovation
...

### Approach
Aim 1. ...
Aim 2. ...
Aim 3. ...

### Milestones
- ...

### Consortium roles
- ...

### Major risks and mitigations
- ...
```

---

## Evaluation Heuristics

Before finalizing, check:

1. Is the clinical need explicit and credible?
2. Is the novelty more than "we will use AI"?
3. Are the aims linked to measurable outputs?
4. Is the validation plan convincing?
5. Is the multi-site structure realistic?
6. Are compute, annotation, and regulatory needs acknowledged?
7. Does each institution have a distinct role?

---

## Common Weaknesses To Flag

- novelty described without clinical consequence
- vague benchmark or success criterion
- no external validation or deployment path
- too many aims for the timeline
- consortium members listed but not functionally integrated
- proposal sounds like a paper, not a funded program

---

## Handoff Rules

- route to `search-lit` to support significance and prior-art positioning
- route to `design-study` if the evaluation framework is weak
- route to `write-paper` only when the proposal requires publication-style narrative sections

---

## What This Skill Does NOT Do

- It does not fabricate budget details
- It does not promise datasets, partners, or infrastructure not evidenced by the user
- It does not replace institutional administrative review

## Anti-Hallucination

- **Never fabricate references.** All citations must be verified via `/search-lit` with confirmed DOI or PMID. Mark unverified references as `[UNVERIFIED - NEEDS MANUAL CHECK]`.
- **Never invent clinical definitions, diagnostic criteria, or guideline recommendations.** If uncertain, flag with `[VERIFY]` and ask the user.

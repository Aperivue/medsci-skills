---
name: grant-builder
description: Use when drafting a grant or challenge proposal for a radiology or medical AI project, including a Korean government industry-academia plan. Structures significance, innovation, approach, aims, milestones and consortium roles, keeping claims evidence-based and executable.
triggers: grant, proposal, aims page, grant proposal, significance, innovation, approach, milestones, 산학과제, 산학협력, 과제계획서, 연구계획서, 연구비 신청, 첨부3
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Grant-Builder Skill

Write proposal prose in the language the target call requires. Produce whichever parts the request
needs: concept summary, Significance, Innovation, Approach, specific aims, work packages, milestone
table, role split by institution, evaluation framework, reviewer-risk memo.

## Korean Government Grant Mode

When the user requests a Korean industry-academia grant (산학과제) or research plan (연구계획서) —
e.g., MOHW, MOTIE, MSS or regional industry-academia programs — apply the adaptations below.
Korean program terms are preserved in parentheses because they are the literal form used on the
funding agency's template.

### Document Structure (three-attachment format)

| Attachment | Contents |
|---|---|
| 1 (첨부1, 기본정보) | project title, participating institutions, investigator CVs, publication / patent record |
| 2 (첨부2, 매칭확인서) | per-institution cost-share confirmation, typically finalized after a kickoff meeting between the institutions |
| 3 (첨부3, 연구계획서) | the 10-page research plan — structure below |

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

### Small-Scale Grants (< KRW 30 million)

- Write for a non-specialist reviewer; assume the evaluator is not in your subfield.
- Emphasize feasibility over technical novelty.
- Prioritize length / format compliance; exceeding the template incurs scoring penalties.
- Include preliminary data or pilot results whenever available.
- Keep quantitative targets conservative — undershooting a committed target is punished more than
  overdelivering on a modest one.

---

## Workflow

### Phase 1: Decode the funding call

Extract funding body, call theme, eligibility constraints, deliverable expectations, timeline and
evaluation criteria. If no call text is available, infer a generic academic-medical AI proposal
structure and label the assumptions.

### Phase 2: Frame the problem

Define the clinical pain point, the current workflow limitation, why existing AI or standard care is
insufficient, and who benefits if the project succeeds.

**Gate:** Present the problem framing (clinical pain point, gap, proposed solution) to the user.
Confirm before building proposal sections — a misframed problem produces an unfundable proposal.

### Phase 3: Build the proposal spine

Always articulate: problem, gap, proposed solution, why this team can execute it, measurable
outputs.

### Phase 4: Convert to proposal sections

- **Significance** must answer why this matters clinically, why now, and why the proposed solution
  is worth funding.
- **Innovation**: what is genuinely different, why the integration is new, why the novelty is
  useful and not just technical.
- **Approach**: dataset and participating sites, model or workflow components, validation plan,
  benchmark/comparator, failure analysis, risk mitigation.

Route to `search-lit` to support significance and prior-art positioning; cite a reference only with
a `/search-lit`-confirmed DOI or PMID, otherwise mark it `[UNVERIFIED - NEEDS MANUAL CHECK]`. Mark
any unconfirmed clinical definition, diagnostic criterion or guideline recommendation `[VERIFY]` and
ask the user. Route to `design-study` if the evaluation framework is weak, and to `write-paper` only
when the proposal requires publication-style narrative sections.

### Phase 5: Execution plan

Generate milestones by quarter or year, institution-level responsibilities, dependencies and
handoffs, and required infrastructure. Do not fabricate budget details, and do not promise datasets,
partners or infrastructure the user has not evidenced.

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

## Before Finalizing

Check, and flag any failure to the user:

1. Is the clinical need explicit and credible?
2. Is the novelty more than "we will use AI", with a clinical consequence?
3. Are the aims linked to measurable outputs with a concrete benchmark or success criterion?
4. Is the validation plan convincing, including external validation or a deployment path?
5. Is the multi-site structure realistic, with each institution in a distinct, functionally
   integrated role?
6. Are compute, annotation, and regulatory needs acknowledged?
7. Are there too many aims for the timeline?
8. Does it read as a funded program rather than a paper?

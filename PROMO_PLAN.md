# MedSci Skills Promotion Plan

Status date: 2026-05-23

## Current Snapshot

- GitHub: 105 stars, 30 forks, 9 open issues.
- Traffic window: 2026-05-08 to 2026-05-21.
- Views: 2,489 total / 844 unique.
- Clones: 3,227 total / 456 unique.
- Top referrers: Threads 402, GitHub 325, Google 288, Reddit 126, ChatGPT 58, Aperivue 28.
- Current public surface: 40 skills, three public end-to-end demos, Zenodo concept DOI `10.5281/zenodo.20155321`.

## Tier 1: Community Visibility

### Awesome Lists

`awesome-claude-code`: no existing medsci-skills PR found in the checked search. Do not create a PR in this cycle. Next cycle task: re-check the maintainer policy, then submit a small one-line addition with the DOI and demo links.

Candidate lists to inspect before outreach:

| Candidate | URL | Likely route | Fit |
|---|---|---|---|
| Awesome Claude | https://github.com/ai-for-developers/awesome-claude | Pull request titled `Add: MedSci Skills` | Good fit for Claude/agent-skill ecosystem visibility. |
| Awesome LLM Apps | https://github.com/Shubhamsaboo/awesome-llm-apps | Issue or pull request after checking contribution conventions | Possible fit only if framed as runnable research workflow templates, not a generic link. |
| Awesome Healthcare AI | https://github.com/medtorch/awesome-healthcare-ai | Pull request to relevant tools/resources section | Good medical AI audience fit; emphasize research workflow and reporting compliance. |
| Awesome AI for Science | https://github.com/ai-boost/awesome-ai-for-science | Pull request to research workbench or medical AI section | Good science-tooling fit; keep entry concise and evidence-backed. |

### Reddit Draft Outlines

PII policy: no manuscript IDs, no unpublished study names, no author names, no project-specific identifiers, and no PMID lists in post bodies or comments. Run the PII gate before posting.

#### r/ClaudeAI

Title: `I built 40 Claude Code skills for medical research workflows, with public demos and validators`

Body outline:

- One-sentence problem: medical research work involves many brittle handoffs from literature search to manuscript and submission.
- What is shipped: 40 Claude Code skills, three public demo pipelines, validator checks, citation/DOI metadata.
- Why Claude-specific: skills package repeatable procedures, guardrails, and routing patterns rather than one-off prompts.
- Invite feedback on install friction, skill structure, and missing workflows.

First comment:

```text
Repo: https://github.com/Aperivue/medsci-skills
DOI: https://doi.org/10.5281/zenodo.20155321
Best starting points: README demos, /setup-medsci, /verify-refs, /meta-analysis, /check-reporting.
```

#### r/medicalAI

Title: `Open-source medical research workflow skills: references, reporting checks, meta-analysis, and submission hygiene`

Body outline:

- Lead with safety/hygiene: citation checks, reporting guideline checks, PII guard, public datasets only in demos.
- Show the clinical research workflow: literature search, full-text retrieval, study design, statistics, figures, manuscript, reporting, revision.
- Ask for feedback on reporting-guideline coverage and external validation expectations.

First comment:

```text
The demos use public/sample datasets only. I am especially looking for feedback on whether the validator and reporting-check surfaces are useful enough for independent reuse.
```

#### r/medicine

Title: `I open-sourced a physician-built toolkit for making research manuscripts less brittle`

Body outline:

- Avoid AI hype; frame as workflow documentation and QC automation.
- Mention that it is not clinical decision support and does not process patient data in demos.
- Ask for practical feedback from clinicians who write or review manuscripts.

First comment:

```text
This is aimed at research workflow hygiene, not patient care. The most useful criticism would be: what would make this trustworthy enough to try on a low-risk manuscript draft?
```

### Hacker News

Candidate title: `Show HN: MedSci Skills, Claude Code workflows for medical research manuscripts`

Timing: weekday morning Pacific Time. Post only after the README/Aperivue sync is live and the repo has no known PII hygiene blockers.

## Tier 3: JOSS Submission Prep

JOSS is a good medium-term target, but the current cycle should stop at prep. The refreshed 2026 criteria emphasize:

- 750-1750 word paper with required sections.
- Evidence of research impact or credible near-term significance.
- Six months of public development history before submission.
- Open-source practice signals: tests, CI, releases, changelog, documentation, contribution pathway.
- Transparent AI usage disclosure.

This cycle adds `paper.md`, `paper.bib`, and `CONTRIBUTING.md`. Do not submit to JOSS without a user confirmation pass and a fresh criteria check.

### Pre-submission Checklist

- [x] MIT `LICENSE`.
- [x] `CITATION.cff` refreshed for v3.1.0 date/version.
- [x] Zenodo concept DOI `10.5281/zenodo.20155321`.
- [x] README, skill documentation, and three public demos.
- [x] Validator and contract checks in repository scripts/CI.
- [x] `CONTRIBUTING.md` added in this cycle.
- [x] `paper.md` outline and `paper.bib` seed references added in this cycle.
- [ ] Fresh public-history check: JOSS currently expects more than six months of public development history before submission.
- [ ] Concrete external adoption/reuse evidence for the research impact statement.
- [ ] Fresh JOSS criteria review immediately before submission.

## Tier 2: Deferred

- Society newsletter outreach.
- X/Threads mention strategy beyond current organic traffic.
- Aperivue blog post.
- Main page redesign.

## External Maintainer Follow-up Drafts

### OpenClaw Issue #31

Status: opened 2026-05-13; 10 days elapsed as of 2026-05-23; no comments observed in the working plan. Re-ping threshold: 2026-06-12, or earlier only with explicit user approval.

Draft:

```text
Hi, quick follow-up on this. MedSci Skills has now added the v2.10 public hygiene updates: 40-skill roster sync, expanded PII validator coverage, and refreshed meta-analysis/reference-checking surfaces. If this still fits OpenClaw's scope, I would be happy to adjust the entry format or split the medical-research workflow pieces into a narrower listing.
```

### PR #18

Action remains separate from this PR. Close only after explicit user confirmation:

```text
Superseded by #23 -- v1.2.0 full-author cross-check + PubMed efetch authoritative path merged via PR #23 (2026-05-19). Closing this branch.
```

## PII Gate

Before any external post, PR body, issue comment, or commit message:

```bash
bash scripts/validate_skills.sh
```

Also run the publication guard in `~/.claude/rules/oss-publication-pii-guard.md` if available. External copy must have zero manuscript IDs, unpublished project IDs, real collaborator names, patient-level examples, or PMID lists. Keep raw blocklist patterns in validator code only, not in promotional copy.

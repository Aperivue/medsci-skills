# awesome-claude-code Resubmission — v3.0.1 + Zenodo DOI (2026-05-13)

**⚠️ CRITICAL — Manual Web UI submission only**

This repo's issue template explicitly **bans gh CLI submission** ("automatically closed", "violates Code of Conduct"). The user MUST submit via:

> https://github.com/hesreallyhim/awesome-claude-code/issues/new/choose
> → "🚀 Recommend New Resource"

Below are the form field values to copy-paste into the web UI. Do NOT use `gh issue create`.

---

## Form Field Values (copy-paste into web UI)

### Title (auto-prefixed `[Resource]:`)

```
MedSci Skills
```

### Display Name

```
MedSci Skills
```

### Category (dropdown)

```
Agent Skills
```

### Sub-Category (dropdown)

```
General
```

### Primary Link

```
https://github.com/Aperivue/medsci-skills
```

### Author Name

```
Yoojin Nam
```

### Author Link

```
https://github.com/Aperivue
```

### License (dropdown)

```
MIT
```

### Description (≤500 chars; 1-3 sentences; no emojis; descriptive not promotional; do not address reader)

⚠️ **Validation gate**: hesreallyhim/awesome-claude-code enforces 500-character cap. Submission #N (2026-05-13) was rejected at ~600 chars. Below is the 426-char compliant version.

```
A 39-skill Claude Code collection for the medical research lifecycle: PubMed search with anti-hallucination citation verification, IMRAD drafting, compliance audit against 33 EQUATOR reporting guidelines (STARD-AI, TRIPOD+AI, CLAIM, PRISMA-DTA, STROBE), peer review, and revision response. Three end-to-end demos run on public datasets to produce submission-ready manuscripts. Archived on Zenodo (DOI 10.5281/zenodo.20155321).
```

### Validate Claims

```
Run Demo 1 end-to-end in under 10 minutes. Clone the repo, install with `python3 installers/install.py --target claude`, then in the demo/01_wisconsin_bc/ directory ask Claude Code:

  /orchestrate --e2e

This produces a complete IMRAD manuscript with ROC curves, STARD 2015 compliance audit (28 items, ~82% compliance), self-review iteration, DOCX export, and 12-slide presentation with speaker notes. All input data is sklearn's load_breast_cancer() built-in (zero download), and all output artifacts are committed to the repo at demo/01_wisconsin_bc/ for direct inspection.

For a focused single-skill test that requires only Claude Code installed:

  /check-reporting any_manuscript.md --guideline STARD

This produces an item-by-item PRESENT / PARTIAL / MISSING audit against the STARD 2015 checklist with fix recommendations.

For new users who haven't installed Python or R:

  /setup-medsci

Reads-only. Runs `which python3 / Rscript / claude / node` and `claude mcp list`, prints a checklist with status (passing / missing / disconnected) and a link to the matching docs/setup/ guide for any failure. Does not install anything.

No network requests except public APIs (PubMed E-utilities, Semantic Scholar, CrossRef, OpenAlex/Unpaywall for OA-only PDF retrieval). No paywall bypass. No `--dangerously-skip-permissions` required.
```

### Specific Task(s)

```
1. Run Demo 1 (Wisconsin BC, sklearn built-in dataset): produces manuscript + ROC curves + STARD audit + slides at demo/01_wisconsin_bc/.

2. Run Demo 2 (BCG meta-analysis, R metafor::dat.bcg): produces pooled RR=0.489 (95% CI 0.344-0.696) across 13 RCTs with PRISMA 2020 audit (77.8% compliance, 21/27 PRESENT) at demo/02_metafor_bcg/.

3. Run Demo 3 (NHANES obesity, public CDC NHANES 2017-18): produces STROBE-compliant epidemiology manuscript with survey weights at demo/03_nhanes_obesity/.

4. /check-reporting against any existing manuscript markdown — supports 33 EQUATOR guidelines including STARD, STARD-AI, TRIPOD, TRIPOD+AI, CLAIM, PRISMA, PRISMA-DTA, STROBE, CONSORT, MI-CLEAR-LLM, PROBAST, PROBAST+AI.

5. /search-lit for any PubMed query — every returned reference is verified via PubMed/CrossRef API before inclusion (anti-hallucination).

6. /setup-medsci on a fresh machine — read-only diagnostic, prints checklist of Python / R / Claude Code / MCP server status with links to setup docs for any missing component.
```

### Specific Prompt(s)

```
1. /check-reporting manuscript.md --guideline STARD-AI

2. /search-lit "diagnostic accuracy of AI for lung nodule detection" --database pubmed --limit 10

3. /make-figures prisma --identified 500 --screened 350 --eligible 45 --included 23
```

### Additional Comments

```
Resubmission of #1389 (closed 2026-04-06, 7-day cooldown) and #1518 (closed 2026-04-13, 14-day extension applied). Both cooldowns expired (eligible after 2026-04-27).

Updates since the prior submission:
- 22 skills → 39 skills (now covers full lifecycle: topic discovery, IRB protocol, data cleaning, de-identification, IMRAD writing, AI-pattern humanization, journal selection, peer review, revision response, presentation generation)
- Three end-to-end demos with public datasets and reproducible output artifacts (Wisconsin Breast Cancer, BCG meta-analysis, NHANES obesity)
- 33 EQUATOR reporting guidelines (added STARD-AI, TRIPOD+AI, CLAIM 2024, MI-CLEAR-LLM, PROBAST+AI, RoB NMA, ROBINS-E, ROB-ME, etc.)
- New setup-medsci skill — read-only diagnostic for clinicians new to Python / R / Claude Code (no install logic, just verifies the environment and points to setup docs)
- New docs/setup/ — five-file clinician onboarding guide (Mac, Windows, MCP servers, common issues)
- v3.0.1 archived on Zenodo (concept DOI 10.5281/zenodo.20155321) for academic citation
- Anti-Reviewer-2 tone audit integrated into the peer-review skill (Aczel 2021 patterns)
- CITATION.cff for academic citation
- Repository renamed from medical-research-skills to medsci-skills (old URL auto-redirects)

All reporting guideline checklists retain original CC licenses. No paywall bypass. No `--dangerously-skip-permissions`. Network requests limited to public APIs (PubMed E-utilities, Semantic Scholar, CrossRef, Unpaywall, OpenAlex). Built and maintained by a practicing radiologist (Yoojin Nam, MD, ORCID 0000-0001-8565-1360, Aperivue), tested on real publications.
```

---

## Step-by-step submission

1. Open https://github.com/hesreallyhim/awesome-claude-code/issues/new/choose
2. Click **"🚀 Recommend New Resource"**
3. For each form field, copy-paste the value from the corresponding section above
4. Carefully review each field before submit (especially Description and Validate Claims — those are the most-scrutinized)
5. Submit
6. After submit: automated validation comment will appear within 1-5 minutes. If validation fails, the comment tells you which field is malformed — fix and edit the issue body
7. Manual review by the maintainer follows (no SLA, usually 1-7 days)

## 제출 메모 (한국어 작업 노트)

- 제출일 권장: 2026-05-13 (DOI 받은 직후, v3.0.1 release 직후, momentum)
- 자동 close 위험 회피: gh CLI 절대 사용 금지. Web UI만
- 이전 issues #1389, #1518 명시적으로 reference 했음 ("Resubmission of...")
- DOI는 concept DOI (10.5281/zenodo.20155321)로 통일 (always-latest, badge URL과 일치)
- 검토자 (maintainer)가 Claude Code로 내부 evaluate-repository 명령 실행하므로 README + CITATION.cff + setup 흐름이 깨끗해야 통과
- 제출 후 24-48h 모니터링 → validation 실패 시 즉시 수정

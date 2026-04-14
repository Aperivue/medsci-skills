# awesome-claude-code Resubmission — 04-27 이후 제출 (14일 연장 패널티)

## Issue Template Fields

**Title:** [Resource]: MedSci Skills

**Display Name:** MedSci Skills

**Category:** Agent Skills

**Sub-Category:** General

**Primary Link:** https://github.com/Aperivue/medsci-skills

**Author Name:** Aperivue

**Author Link:** https://github.com/Aperivue

**License:** MIT

**Description:**

22 Claude Code skills for the full medical research lifecycle — from PubMed literature search with anti-hallucination citation verification to submission-ready IMRAD manuscripts with reporting compliance audits against STARD, PRISMA, STROBE, and 12 other guidelines. Includes 3 end-to-end demos that each produce complete manuscripts, 300-dpi figures, and compliance reports from public datasets. Built by a radiologist and tested on real publications.

**Validate Claims:**

Run Demo 1 end-to-end in under 5 minutes:

```bash
git clone https://github.com/Aperivue/medsci-skills.git
cp -r medsci-skills/skills/* ~/.claude/skills/
cd medsci-skills/demo/01_wisconsin_bc
python 01_load_data.py
python 02_analyze.py
```

Then ask Claude Code: `/write-paper` — it generates a full IMRAD manuscript. Follow with `/check-reporting STARD` for a 30-item compliance audit with fix recommendations.

For a quick single-skill test: `/check-reporting any_manuscript.md --guideline STROBE` produces an item-by-item compliance report (PRESENT/PARTIAL/MISSING).

**Specific Task(s):**

1. Run Demo 1 (Wisconsin BC) — produces manuscript + ROC curves + STARD audit + slides from `sklearn.datasets.load_breast_cancer()`
2. Install `search-lit` and search PubMed — verify every citation has a real PMID (anti-hallucination)
3. Install `check-reporting` and audit any manuscript against STARD, STROBE, or PRISMA guidelines

**Specific Prompt(s):**

1. `/check-reporting manuscript.md --guideline STARD`
2. `/search-lit "diagnostic accuracy of AI for lung nodule detection" --database pubmed --limit 10`
3. `/make-figures prisma --identified 500 --screened 350 --eligible 45 --included 23`

**Additional Comments:**

Resubmission of #1389 (closed for 7-day cooldown) and #1518 (closed same day, 14-day extension applied, eligible after April 27, 2026). Updates since original submission: 9 skills expanded to 22, added 3 live end-to-end demos with public datasets, v2.1 pipeline with automatic skill chaining (analyze-stats → make-figures → write-paper → check-reporting). Repository renamed from medical-research-skills to medsci-skills (old URL auto-redirects). All reporting guideline checklists retain original CC licenses. No network requests except public APIs (PubMed, Semantic Scholar, CrossRef).

---

## 제출 메모

- 제출일: 04-27 (월) 이후 ← 14일 연장 패널티 (#1518 당일제출로 인해)
- Issue #1389 참조 (closed, 7-day cooldown)
- 레포 URL: medsci-skills (자동 리디렉트 확인 완료)
- 체크리스트 모두 충족 확인

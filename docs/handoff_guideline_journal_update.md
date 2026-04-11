# Handoff: Reporting Guideline & Journal Profile Update

> Date: 2026-04-11
> Trigger: LinkedIn feedback from Health Economist (NICE/Sheffield) pointing out TRIPOD versioning gap and journal profile statistical depth inconsistency
> Prior session: TRIPOD split + 13 journal stats sections completed

---

## Completed (this session)

| # | Task | Files | Status |
|---|------|-------|--------|
| 1 | TRIPOD.md (2015) checklist | `check-reporting/references/checklists/TRIPOD.md` (new) | Done |
| 2 | TRIPOD_AI.md item 12 fix | `check-reporting/references/checklists/TRIPOD_AI.md` | Done |
| 3 | self-review routing split | `self-review/SKILL.md` line 120 → 2 rows | Done |
| 4 | check-reporting stale docs + TRIPOD footnote | `check-reporting/SKILL.md` | Done |
| 5 | Statistical Reporting sections x13 | 13 journal profiles in `write-paper/references/journal_profiles/` | Done |
| 6 | RYAI duplicate line cleanup | `RYAI.md` | Done |

**Not yet committed.** Run `git add -A && git commit` with message like:
```
feat: add TRIPOD 2015 checklist, split routing, add statistical reporting to 13 journal profiles

- Create TRIPOD.md (22 items) for non-AI prediction models
- Fix missing item 12 in both TRIPOD.md and TRIPOD_AI.md
- Split self-review routing: non-AI → TRIPOD 2015, AI/ML → TRIPOD+AI 2024
- Add TRIPOD exception note to check-reporting (do NOT apply both simultaneously)
- Fix stale "not bundled" docs in check-reporting (CONSORT/CARE/SPIRIT/CLAIM are bundled)
- Add ## Statistical Reporting to 13 journal profiles (RYAI, BMJ, Lancet DH, AJR, IR, AR, JACR, Lancet, JMIR, JMIR ME, AIM, BMC ME, Medical Education)
```

---

## Remaining: Tier 1 — Routing Inconsistencies (do first)

These are referenced in routing tables but have no checklist file. The skill silently falls back to LLM knowledge, which is unreliable.

### 1. SQUIRE_2.md

- **What**: Quality improvement in education (SQUIRE 2.0, Ogrinc et al. 2015)
- **Where**: `check-reporting/references/checklists/SQUIRE_2.md`
- **Referenced by**: check-reporting routing table ("Educational study → SQUIRE 2.0"), self-review Category G ("Educational → SQUIRE 2.0")
- **Format**: Follow existing checklist format (see STROBE.md or TRIPOD.md as template)
- **Items**: 18 items across Introduction/Methods/Results/Discussion
- **Also update**: check-reporting SKILL.md bundled list, add `SQUIRE_2.md` entry

### 2. CLEAR.md

- **What**: Radiomics quality checklist (CLEAR, Kocak et al. 2023, Eur Radiol)
- **Where**: `check-reporting/references/checklists/CLEAR.md`
- **Referenced by**: self-review Category G ("AI / Radiomics → CLAIM 2024 / CLEAR")
- **Items**: 58 items across study design, imaging, feature extraction, modeling, performance, open science
- **Also update**: check-reporting routing table (add CLEAR alongside CLAIM), bundled list

### After creating both:
- Update check-reporting SKILL.md frontmatter: "16 guidelines" → "18 guidelines"
- Update README.md, skills.en.json, skills.ko.json accordingly

---

## Remaining: Tier 2 — New Checklists (high value)

### 3. MOOSE.md

- **What**: Meta-Analysis of Observational Studies in Epidemiology (Stroup et al. JAMA 2000)
- **Why**: PRISMA covers intervention reviews; observational MAs need MOOSE. Many journals require both.
- **Where**: `check-reporting/references/checklists/MOOSE.md`
- **Also**: Add to check-reporting routing table as a new row: "Meta-analysis of observational studies → MOOSE"
- **Items**: 35 items across reporting of background, search strategy, methods, results, discussion, conclusion

### 4. GRRAS.md

- **What**: Guidelines for Reporting Reliability and Agreement Studies (Kottner et al. 2011)
- **Why**: ICC, kappa, Bland-Altman reporting is extremely common in radiology. No current path to GRRAS.
- **Where**: `check-reporting/references/checklists/GRRAS.md`
- **Also**: Add to routing table: "Reliability/agreement study → GRRAS"
- **Items**: 15 items

### 5. RECORD.md (optional)

- **What**: Reporting of Studies Using Observational Routinely Collected Health Data (Benchimol et al. 2015)
- **Why**: Extension of STROBE for EHR/admin data studies. Increasingly common in medical AI.
- **Items**: 13 extension items beyond STROBE

### 6. COREQ.md (optional)

- **What**: Consolidated Criteria for Reporting Qualitative Research (Tong et al. 2007)
- **Why**: Medical education qualitative studies. Referenced in JMIR_Medical_Education profile.
- **Items**: 32 items across research team, study design, data analysis

---

## Completed: Tier 3 High Priority — Journal Profiles (session 2026-04-11b)

| Journal | write-paper | find-journal | Status |
|---------|:-----------:|:------------:|--------|
| **JAMA** | Created | Existed | Done |
| **Nature Medicine** | Created | Existed | Done |
| **Annals of Internal Medicine** | Created | Created | Done |
| **Medical Image Analysis** | Created | Existed | Done |
| **IEEE TMI** | Created | Created | Done |

Also updated: find-journal SKILL.md counts (21→23 local, 19→24 write-paper, 40→47 total), README.md (40→47 journal profiles).

## Completed: Tier 3 Medium Priority — Journal Profiles (session 2026-04-11c)

| Journal | write-paper | find-journal | Status |
|---------|:-----------:|:------------:|--------|
| **CVIR** | Created | Created | Done |
| **JVIR** | Created | Created | Done |
| **Neuroradiology** | Created | Existed | Done |
| **Abdominal Radiology** | Created | Existed | Done |
| **Diagnostics (MDPI)** | Created | Created | Done |

Also updated: find-journal SKILL.md counts (23→26 local, 24→29 write-paper, 47→55 total), README.md (47→55 journal profiles).

## Remaining: Tier 3 — Journal Profiles (Lower Priority)

### Lower priority

| Journal | Why |
|---------|-----|
| Skeletal Radiology | MSK subspecialty |
| Clinical Radiology | RCR (UK) journal |

### How to create a journal profile

1. Read existing profile (e.g., `Radiology.md`) for format reference
2. Sections needed: Journal Identity, Manuscript Types, Abstract Format, Keywords, Required Sections, Citation Style, Reporting Guidelines, **Statistical Reporting** (new standard), Special Notes
3. Source: journal's "Instructions for Authors" page
4. Add to both `write-paper/references/journal_profiles/` and `find-journal/references/journal_profiles/` (find-journal profiles are shorter, scope-focused)

---

## Remaining: Tier 4 — Documentation Updates

### README.md

| Location | Current | Fix |
|----------|---------|-----|
| Key Features section | "15 Reporting Guidelines" | → count after Tier 1-2 additions |
| Key Features section | "CONSORT, CARE, SPIRIT, CLAIM supported via knowledge-based assessment" | Delete — all 4 are bundled |
| Available Now table | check-reporting description | Update guideline count |

### skills.en.json + skills.ko.json

| Field | Current | Fix |
|-------|---------|-----|
| check-reporting description | "15 reporting guidelines" | → updated count |
| find-journal description | "Impact factor / CiteScore lookup" | Delete — skill does NOT provide this |

### Blog posts (low priority, cosmetic)

| File | Issue |
|------|-------|
| `doctor-built-research-skills-claude-code.mdx` | "16 skills" → "20 skills", skill table incomplete |
| `strobe-compliance-ai-checker.mdx` | "15 additional skills" → "19 additional skills" |

### Skills guide page

| File | Issue |
|------|-------|
| `content.en.tsx` / `content.ko.tsx` | check-reporting "Supports 15 guidelines" → update |

---

## Remaining: Tier 5 — Paper Type Templates (separate session)

These are structural additions to write-paper, not quick edits.

| Template | Gap |
|----------|-----|
| `rct.md` | write-paper references CONSORT but uses generic `original_article.md`. RCT needs randomization/blinding/ITT subsections. |
| `surgical_study.md` | self-review has full Surgical column + STROBE-Surgery, but write-paper has no matching template. |
| `educational_study.md` | Both skills reference SQUIRE for educational studies, no dedicated template. |

---

## Execution Order Recommendation

```
Tier 1 (SQUIRE + CLEAR)  ← fixes existing broken references
    ↓
Tier 4 (README/JSON)     ← update counts to match reality
    ↓
Tier 2 (MOOSE + GRRAS)   ← highest-value new checklists
    ↓
Tier 3 (JAMA, NatMed, CVIR...)  ← journal profiles, independent of each other
    ↓
Tier 5 (templates)        ← largest scope, separate planning session
```

Tier 1 + Tier 4 can be done in one session (~30 min).
Tier 2 can be done in the same or next session (~20 min).
Tier 3 journals are independent — do 3-5 per session as needed.
Tier 5 needs its own plan mode session.

---
name: render-pdf-doc
description: >
  Render Korean academic Markdown documents to publication-quality PDF via pandoc + xelatex.
  Targets non-bibliography artifacts: research proposals, IRB cover letters, briefing
  handouts, anchor docs (Q&A grids), and reference tables. Auto-infers pipe-table column
  widths from content (label column shrinks to fit, data columns share remaining width).
  CJK font fallback (Apple SD Gothic Neo on macOS, Noto Sans CJK KR on Linux).
  NOT for: manuscripts with bibliography (use /manage-refs render_pandoc.sh), Word form
  filling (/fill-protocol), figures (/make-figures).
triggers: render PDF, PDF 렌더, korean PDF, 한글 PDF, anchor doc PDF, briefing PDF, proposal PDF, 연구계획서 PDF, 표 정렬 PDF, 표 폭 자동, tbl-colwidths, 학술 PDF
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Render-PDF-Doc Skill

Markdown + frontmatter → publication-quality Korean academic PDF.

## Why This Skill Exists

In real circulation cycles for Korean academic PDFs, two recurring failure patterns appear:
1. v1 drafts: change-history, version numbers, and PI attribution leak into the attached PDF, confusing the first recipient.
2. v2 drafts: pandoc pipe-table dash ratios are misjudged, narrowing the first column and forcing label wrapping that hurts readability.

Manual fixes work but the same pattern recurs across proposals, briefings, IRB covers, exemption applications. This skill focuses on **layout** (CJK fonts + table column widths). Bibliography and CSL are handled by `/manage-refs`.

## Boundary (다른 스킬과 분리)

| 작업 | 스킬 |
|---|---|
| Manuscript + bibliography → DOCX/PDF | `/manage-refs scripts/render_pandoc.sh` (CSL + .bib) |
| 기관 .docx 양식 채움 | `/fill-protocol` |
| ICMJE COI 폼 | `/fill-icmje-coi` |
| Figure / PPTX | `/make-figures`, `/present-paper` |
| **이 스킬**: non-bib 학술 마크다운 → PDF (proposal, briefing, anchor doc, IRB cover) | `/render-pdf-doc` |

## Core Principles

1. **Pipe table column widths must be inferred from content.** 균등 분할 금지. 첫 열(라벨)은 최장 라벨에 맞추고, 데이터 열은 남은 폭을 content-proportional 분배.
2. **CJK font는 명시적으로 설정** — `mainfont` + `CJKmainfont`. Default fallback은 OS-detect.
3. **회람용 PDF에서는 변경이력·버전번호·PI attribution 제거** (또는 supplementary로 분리). frontmatter `redact_internal: true` 옵션.
4. **Quarto 의존성 없음** — raw pandoc + xelatex. Quarto의 `tbl-colwidths`는 PDF에서 regression 보고됨 (issue 6089/9200).

## Dependencies

```bash
# Required
brew install pandoc                                                   # macOS
brew install --cask mactex-no-gui          # xelatex + xeCJK (~5 GB)

# Linux
sudo apt-get install pandoc texlive-xetex texlive-lang-cjk fonts-noto-cjk
```

Detection:
```bash
bash scripts/check_deps.sh
```

## Workflow

### Step 1 — Author markdown with frontmatter

```yaml
---
title: "Paper 2 Calibration Anchor — Q&A Grid"
author: "<Author Group>"
date: "2026-05-01"
mainfont: "Apple SD Gothic Neo"        # macOS default
CJKmainfont: "Apple SD Gothic Neo"
geometry: "margin=0.85in"
fontsize: 11pt
linestretch: 1.25
colorlinks: true
---
```

For Linux/CI, use `Noto Sans CJK KR` instead. The render script auto-detects.

### Step 2 — Infer column widths

```bash
python scripts/infer_colwidths.py input.md > input.colwidths.md
```

The script:
1. Finds every pipe table block.
2. For each column, computes display width = `max(len(header), max(len(cell)))` (CJK = 2 cells, ASCII = 1).
3. Generates dash-row separator with proportional dash counts.
4. Writes a new file with separator rows replaced.

Override per-table via attribute: `{tbl-colwidths="[20,40,40]"}` after caption — passes through unchanged.

### Step 3 — Render

```bash
bash scripts/render_pdf.sh -i input.colwidths.md -o output.pdf
```

Or one-shot:
```bash
bash scripts/render_pdf.sh -i input.md -o output.pdf --infer-colwidths
```

### Step 4 — Visual verify

Open the PDF. Check:
- 첫 열 라벨이 wrap 안 되고 단일 행 유지
- 데이터 열 충분한 폭
- Korean glyph 깨짐 없음 (Times New Roman fallback 발생 시 CJKmainfont 미적용)
- 변경이력·내부 버전 노출 없음

## Templates

`templates/` 에 starter markdown:
- `anchor-doc.md` — Q&A grid (Paper 2 사례)
- `proposal-cover.md` — 연구계획서 cover page
- `briefing-handout.md` — 미팅 brief (1-page)
- `reference-table.md` — 비교표 형식

각 template은 `<!-- TODO: -->` 마커로 슬롯 표시.

## Anti-Patterns

| Anti-pattern | Consequence |
|---|---|
| 균등 dash 분할 (`\|---\|---\|---\|`) | 첫 열에 short label만 있어도 같은 폭 → 데이터 열 협소 |
| `CJKmainfont` 미설정 | Hangul이 Times New Roman fallback (Latin glyph 깨짐 또는 빈칸) |
| 회람 PDF에 v3.2.2 / 변경이력 / PI attribution 노출 | 첫 수신자 혼란, 내부 정보 유출 |
| Quarto `tbl-colwidths` for PDF | Quarto 1.4+에서 PDF regression — HTML만 신뢰 |

## Files

- `scripts/render_pdf.sh` — pandoc + xelatex wrapper, OS font detection
- `scripts/infer_colwidths.py` — pipe table separator dash-ratio 자동 생성
- `scripts/check_deps.sh` — pandoc / xelatex / CJK font 존재 확인
- `templates/` — 4개 starter
- `references/pandoc_korean_cheatsheet.md` — frontmatter 패턴 모음
- `references/known_pitfalls.md` — em-dash 줄바꿈, smart quote 등

## Anti-Hallucination

- Numerical content in tables: `~/.claude/rules/numerical-safety.md` 적용. CSV에서 read.
- Reference: 별도 `/manage-refs` 사용 — 이 스킬은 bib 처리 안 함.
- 회람 PDF 작성 시 `~/.claude/rules/senior-mentor-circulation.md` (1차 source 보존) + `~/.claude/rules/ai-drafted-document-policy.md` 적용.

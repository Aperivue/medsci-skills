# PLAN — `render-pdf-doc` skill (Korean 학술 PDF 렌더링)

**작성**: 2026-05-01 (MeducAI Paper 2 v3.2.2 calibration 작업 중 발생한 사용자 요청)
**상태**: 신규 스킬 개발 — 다음 세션에서 이 파일을 starting point로 작업 시작.
**작업 디렉토리**: `/Users/eugene/workspace/medsci-skills`

---

## Why

2026-05-01 Paper 2 calibration anchor PDF 회람 중 두 번 재작업 발생:
1. v1: 변경이력 · 버전번호 (v3.2.2) · PI 코멘트 attribution이 첨부 PDF에 그대로 노출 → 첫 수신자에게 혼란.
2. v2: pandoc pipe table 대시 비율 잘못 잡아 첫 열 너무 좁음 → 라벨 wrap, 가독성 저하.

Manual로 fix했으나 proposal / briefing / IRB cover / 면제 신청서 등 같은 패턴 반복 예상. 사용자 직접 요청 — "이런 서류 PDF 만드는 스킬 업데이트해보자, 폰트·크기·표 양식 잘해야 한다."

## 핵심 요구사항 (사용자 발화 그대로)

1. **표 양식이 핵심**: 첫 열은 라벨 길이에 맞춰 좁게, 데이터 열은 남는 폭 분배. **균등 분할 금지**.
2. 글자 폰트·크기: Korean CJK 깨짐 없음 + 헤더 hierarchy 일관.
3. proposal · IRB · briefing · anchor doc 등 학술 서류 통합.

상세 룰: `~/.claude/projects/-Users-eugene-workspace-5-Personal-Research-MeducAI/memory/feedback_pdf_table_columns.md`

## 즉시 실행 (다음 세션 시작 시)

### Step 1 — 기존 스킬 overlap 검토 (먼저)

다음 4개 SKILL.md 정독 후 새 스킬의 boundary 결정:

- `skills/fill-protocol/SKILL.md` — Word .docx **form filling** (기관 템플릿 채움). Korean CJK eastAsia font 처리 노하우 ★재사용 가능
- `skills/write-protocol/SKILL.md` — content drafting only, no rendering
- `skills/fill-icmje-coi/SKILL.md` — Word .docx 특수 폼 (체크박스, 13 항목)
- `skills/make-figures/SKILL.md` — PPTX/PNG figure 생성, python-pptx 기반

**가설** (검증 후 확정): 새 스킬 = **`render-pdf-doc`** (가칭). 입력 = 마크다운 + frontmatter, 출력 = pandoc xelatex PDF. fill-protocol(.docx) / make-figures(.pptx)과 출력 포맷이 다름 → overlap 명확하지 않음. 기존 스킬에 통합할지, 별도 스킬로 만들지가 결정 포인트.

### Step 2 — Web 리서치 (2-3개 패턴 비교)

Korean 학술 PDF 자동화 best practice 확보:

- "pandoc xelatex korean font tbl-colwidths"
- "Quarto Korean PDF template tbl-colwidths YAML" (Quarto 1.4+)
- "pandoc lua filter table column auto width content-based"
- python-docx vs pandoc vs Quarto vs typst — 표 폭 컨트롤 측면

특히 검토할 것:
- Quarto의 `tbl-colwidths: [25, 75]` YAML attribute — 가장 깔끔
- pandoc Lua filter로 열 라벨 길이 측정 후 동적 비율 계산 가능 여부
- typst (rust 기반) — Korean 지원 + table layout 강력하다는 평

### Step 3 — Skill design + scaffold

`skills/render-pdf-doc/` 디렉토리 생성. 제안 구조:

```
skills/render-pdf-doc/
├── SKILL.md                    # frontmatter + scope/triggers
├── templates/
│   ├── anchor-doc.md           # axis anchor table 형 (Paper2 사례)
│   ├── proposal-cover.md       # 연구계획서 cover
│   ├── briefing-handout.md     # 미팅 brief
│   └── reference-table.md      # 참고문헌 표
├── scripts/
│   ├── render_pdf.sh           # pandoc + xelatex wrapper
│   ├── infer_colwidths.py      # 표 라벨 길이 측정 → tbl-colwidths YAML 자동 주입
│   └── font_detect.sh          # macOS Apple SD Gothic Neo / Linux Noto Sans CJK KR fallback
└── references/
    ├── pandoc_korean_cheatsheet.md
    └── known_pitfalls.md       # CJK eastAsia, 표 폭, em-dash 줄바꿈 등
```

### Step 4 — 검증 (publishing 전)

- Paper 2 anchor 마크다운(`/Users/eugene/workspace/5_Personal_Research/MeducAI/7_Manuscript/Paper2/proposal/Paper2_QA_Anchor_KO.md`)을 input으로 → 자동 렌더 결과가 manual fix 결과와 동등 또는 우수해야 함
- IRB 연구계획서 본문 markdown → PDF 렌더 → 한글 폰트·표·인용 모두 정상

### Step 5 — Publish

`/publish-skill` 사용 (PII scrub + cross-platform 확인 + license).

## 기존 자산 (재사용)

- 검증된 frontmatter 패턴 + pandoc 명령:
  ```yaml
  ---
  mainfont: "Apple SD Gothic Neo"
  CJKmainfont: "Apple SD Gothic Neo"
  geometry: "margin=0.85in"
  fontsize: 11pt
  ---
  ```
  ```bash
  pandoc input.md --pdf-engine=xelatex -o output.pdf
  ```
- `skills/fill-protocol/scripts/` 한글 폰트 처리 로직 (Word지만 폰트 검출 패턴은 공유 가능)

## 보류 / 의사결정 포인트

- 스킬 이름: `render-pdf-doc` / `make-pdf` / `render-doc` / `pdf-doc` — Step 1 검토 후 결정
- Quarto vs raw pandoc — Quarto 1.4+ tbl-colwidths가 YAML로 깔끔, but Quarto 의존성 추가. raw pandoc + Lua filter도 옵션
- DOCX 동시 출력 — 일단 PDF only, 나중 add
- 기존 `pdf` 스킬(read/edit/combine/OCR)과는 명확히 분리 (그건 read-side, 이건 write-side)

## 관련

- 사용자 feedback memory: `~/.claude/projects/-Users-eugene-workspace-5-Personal-Research-MeducAI/memory/feedback_pdf_table_columns.md`
- 룰: `~/.claude/rules/agent-skill-routing.md`, `~/.claude/rules/institutional-form-fill.md`
- Publish: `/publish-skill`

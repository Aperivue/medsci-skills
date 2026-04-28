# medsci-skills Improvement Queue

다음 세션에서 처리할 스킬 개선 항목. 각 항목은 (a) 발생한 사건, (b) 재발 방지 메커니즘, (c) 영향받는 스킬 + 변경 사항을 포함.

---

## #1 — Manuscript ↔ rendered output cross-reference QC (DONE 2026-04-28)

✅ 처리 완료:
- 신규 스크립트: `skills/write-paper/scripts/check_xref.py` (3-way matrix: in-text citation ↔ body caption ↔ rendered DOCX caption, JSON audit + submission gate, panel-letter fallback)
- `/write-paper` Phase 7 Step 7.6a 신규 (Cross-Reference QC, post-DOCX-build pre-final-gate, `--strict` exit 1 차단)
- `/self-review` Phase 2.5d 신규 (DOCX 존재 시 동일 스크립트 재사용, P0 Major Comments로 변환, auto-fix 금지)
- Skill Interactions 표 갱신

남은 작업: CK-1 v6.3 빌드 시 Phase 7.6a 자동 실행 검증.

---

## #1-original (archived) — Manuscript ↔ rendered output cross-reference QC

**발생 사건** (2026-04-28, CK-1 CAC Warranty v6.2):
홍파 교수 회람 회신에서 supplementary table cross-reference 다수 어긋남 발견. 본문은 "Supp Table S4 (CAC>10 sensitivity)"라 인용하지만 실제 빌드된 PDF의 S4는 VIF Diagnostics. S1, S6, S7 모두 mismatch. S8, S9는 본문 인용은 있는데 PDF에 자체가 없음.

**근본 원인**:
- `manuscript.md`의 "Tables" 섹션(캡션 리스트)이 진짜 SSOT로 인식되지 않음
- `build_manuscript_docx.py` (또는 동등 빌드 스크립트)가 supplementary 캡션·순서를 하드코딩
- 본문 evolution 따라 빌드 스크립트가 자동 동기화되지 않음
- 본문 ↔ 빌드 산출물 cross-reference 자동 검증 부재

**영향받는 스킬**: `/write-paper`, `/check-reporting`, `/self-review`

**제안 변경**:

1. **`/write-paper` Phase 7.x 신규 (Pre-circulation cross-reference QC)**:
   - 본문에서 `Table \d+`, `Figure \d+`, `Supplementary Table S\d+`, `Supplementary Figure S\d+` 인용 토큰 추출
   - 빌드된 docx의 실제 캡션 추출 (python-docx)
   - 매핑: 인용된 모든 라벨에 대응 캡션이 존재하는가? 본문 캡션 정의(만약 있다면)와 일치하는가?
   - 미스매치 표 출력. submission gate.
   - 산출 스크립트: `scripts/check_xref.py` (medsci-skills shared)

2. **`/self-review` 신규 체크리스트 항목**: "All in-text Table/Figure references resolve to actual rendered captions, and caption text matches body description"

3. **`/check-reporting` STROBE/CONSORT/PRISMA item 검증 시 cross-ref도 함께 검사** (이미 부분적으로 STROBE Item 14, 16, 17 등에서 표·그림 인용 요구).

**구현 메모**:
- python-docx로 docx 캡션 추출: paragraphs 중 굵은 글씨 + "Table N." 또는 "Figure N." 패턴
- 본문 인용 토큰 정규식: `r"(Supplementary )?(Table|Figure)\s+(S?\d+[A-Z]?)"`
- 본문 캡션 리스트(예: manuscript.md의 ## Tables 섹션) 파싱: 동일 정규식 + 캡션 first-line text
- 출력: 3-way diff (인용 ↔ 본문 캡션 정의 ↔ 빌드 docx 캡션). PRESENT/MISSING/MISMATCH 각각.

---

## #2 — Build script SSOT 단일화 (MEDIUM PRIORITY)

**발생 사건** (동일 사고와 연결):
`manuscript/build_manuscript_docx.py`가 본문 SSOT가 아니라 자체 SSOT. 본문 line 216–227에 "Supplementary Table S1 = MetS TG-lab-only..." 정의가 있어도, 빌드 스크립트는 line 24–32 `TABLE_MAP`에 박힌 레거시 idx만 따름.

**제안 변경**:

1. **`/write-paper` 빌드 스크립트 템플릿 변경**: `build_manuscript_docx.py`가 manuscript.md의 ## Tables / ## Figure Legends 섹션을 파싱해서 supplementary 순서·캡션을 결정. CSV 데이터만 본문에 정의된 라벨/캡션과 매핑.

2. **레거시 Word 파일(`CK1_tables.docx` 등)은 archive로 이동**, 빌드는 CSV → python-docx만 사용. Idempotent하게.

**영향받는 스킬**: `/write-paper` 템플릿 + 가이드라인.

---

## #3 — JACC family CI 분기 (LOW, 단순)

**발생 사건** (2026-04-27):
`/make-figures` SKILL.md의 Central Illustration section이 PPTX-primary로 안내. 하지만 JACC: Asia 공식 submission은 **TIFF만** 받음 (PPTX 거절).

**제안 변경**:
SKILL.md "Central Illustration" 섹션에 JACC family 분기 추가:
```
JACC family / JACC: Asia: TIFF only (≥300 DPI, ≥13×18 cm). PPTX는 회람·발표 보조용으로만.
Other journals (Radiology, Circulation, Lancet 등): PPTX or TIFF; check author guidelines.
```

**영향받는 스킬**: `/make-figures`

---

## #4 — `/lit-sync` BBT auto-export 검증 명령 갱신 (DONE 2026-04-27)

✅ 이미 처리됨: `~/.claude/rules/zotero-workflow.md`에 outdated `read-only.json` 검증 표시 + GUI Status를 ground truth로 갱신.

---

## #5 — JACC family AI image policy + SMART Servier workflow (DONE 2026-04-27)

✅ 이미 처리됨:
- `~/.claude/rules/journal-ai-image-policies.md` 신규 (cross-project rule)
- `/make-figures` SKILL.md "Journal AI-Image Policies" 섹션 신규

---

## 처리 순서 (recommended)

1. **#1 Cross-reference QC 스크립트 prototype** — CK-1 v6.3에 즉시 적용 가능
2. **#2 build script SSOT 단일화** — #1 수정 과정에서 자연스럽게 따라옴
3. **#3 JACC CI 분기** — 1줄 패치, 마지막에

#1을 먼저 처리하면 CK-1 v6.3 빌드 시점에 자동 검증되어 같은 사건 재발 차단.

# MedSci Skills End-to-End Pipeline Update Plan

**목적**: AI Manuscript Quality Study Arm A (Pure AI) 지원을 위해
`/write-paper` 파이프라인이 human gate 없이 end-to-end로 동작하도록 스킬 업데이트.
공개 레포에 반영.

**배경**: 현재 `/write-paper`는 Phase 3-6(텍스트 생성)만 실제 동작하고,
Phase 2(T&F 생성), Phase 7(QC + 빌드)는 스펙만 있고 실행이 안 됨.
CK-1/CK-5 프로젝트에서 figure 생성, self-review, revision, DOCX 빌드를
모두 수동으로 별도 요청해야 했음.

---

## 현재 문제점 (CK-1/CK-5 경험 기반)

| 단계 | 스펙 | 실제 | 결과 |
|------|------|------|------|
| Phase 2 | `/make-figures` 자동 호출 | 미호출 | Figure 별도 요청 필요 |
| Phase 3-6 | Writer→Critic→Fixer loop | 동작함 | OK |
| Phase 7a | `/self-review` 호출 | 미호출 | 별도 요청 필요 |
| Phase 7b | Self-review 결과 반영 | 미구현 | 수동 수정 필요 |
| Phase 7c | `/check-reporting` 호출 | 미호출 | 미실행 |
| Phase 7d | `/search-lit` 참고문헌 검증 | 미호출 | 미실행 |
| Phase 7e | DOCX 빌드 (figure+table embed) | pandoc plain만 | 별도 빌드 스크립트 필요 |

---

## 수정 대상 스킬 (5개)

### 1. `/write-paper` — 핵심 파이프라인

#### 1a. `--autonomous` 플래그 추가
- Phase 0에서 `--autonomous` 감지
- 활성화 시: 모든 user gate(outline approval, discussion planning, section review) 스킵
- AI Manuscript Quality Study Arm A 전용
- 기본값: OFF (기존 동작 유지)

#### 1b. Phase 2 내부에서 `/make-figures` 자동 체이닝
현재 Phase 2는 "design each table/figure" 후 user gate에서 멈춤.

수정:
```
Phase 2 실행 순서:
1. 데이터 파일 스캔 → 가용 CSV/output 목록 확인
2. Study type에 따른 필수 figure set 결정:
   - Cohort study: flow diagram, KM, forest plot
   - DTA study: flow diagram, ROC, calibration
   - Meta-analysis: PRISMA, forest, funnel
3. `/make-figures` 호출 (study_type + data_dir 파라미터)
4. `_figure_manifest.md` 생성 확인
5. 테이블 CSV 존재 확인 → 없으면 `/analyze-stats` 호출 제안
6. [autonomous 아닌 경우] User gate
```

#### 1c. Phase 7 자동 QC 체인
현재 Phase 7은 "scan for AI patterns" 후 deliverables 나열로 끝남.

수정:
```
Phase 7 실행 순서:
1. AI 패턴 스캔 + 제거 (기존)
2. `/check-reporting` 호출 → compliance report 생성
3. `/search-lit --verify-only` 호출 → 참고문헌 검증
4. `/self-review` 호출 → review_comments.md 생성
5. Self-review 결과 파싱:
   - Major issues → 자동 수정 (텍스트 수정 가능한 것)
   - Data issues → 플래그만 (수동 확인 필요)
6. 수정 후 `/self-review` 재실행 (max 2회)
7. Unified DOCX 빌드:
   a. manuscript.md 파싱
   b. figure embed (from _figure_manifest.md)
   c. table embed (from tables/ CSV → formatted DOCX tables)
   d. pandoc 변환 (.pdf, .docx)
8. [autonomous 아닌 경우] 최종 확인 gate
```

#### 1d. Unified DOCX Build 로직 내장
현재 없음. `build_manuscript_docx.py` 템플릿을 스킬에 내장.

```python
# 빌드 스크립트 템플릿 (write-paper가 자동 생성)
# 입력: manuscript.md, figures/, tables/
# 출력: manuscript_final.docx, manuscript_final.pdf
# 기능:
#   - MD 파싱 (## 섹션 → Heading, **bold** → bold 등)
#   - Figure 삽입 (![Figure N](path) → inline image)
#   - Table 삽입 (CSV → python-docx formatted table)
#   - Times New Roman 11pt, double spacing, page numbers
```

---

### 2. `/make-figures` — 출력 표준화

#### 2a. `_figure_manifest.md` 자동 생성
현재: figure 파일만 생성, manifest 없음.
수정: 모든 figure 생성 후 manifest 파일 작성.

```markdown
# Figure Manifest
- Figure 1: figures/figure1_flow.png | Study flow diagram | CONSORT
- Figure 2: figures/figure2_km.png | Kaplan-Meier curves | survminer
- Figure 3: figures/figure3_forest.png | Forest plot | forestplot
```

#### 2b. Study-type 파라미터 수용
`/make-figures --study-type cohort --data-dir output/`
→ 해당 study type의 필수 figure set을 자동 생성

#### 2c. Flow diagram은 D2 우선
matplotlib FancyBboxPatch → D2로 변경 (CK-1/CK-5 경험)

---

### 3. `/self-review` — 구조화된 출력 + Fix 모드

#### 3a. 구조화된 JSON 출력
현재: 자유 텍스트 리뷰.
수정: 파싱 가능한 구조화 출력 추가.

```json
{
  "overall_score": 72,
  "issues": [
    {
      "id": "M1",
      "severity": "major",
      "category": "methods",
      "location": "line 65",
      "description": "E-value not reported for unmeasured confounding",
      "fixable_by_ai": true,
      "suggested_fix": "Add E-value calculation paragraph after sensitivity analyses"
    }
  ]
}
```

#### 3b. `--fix` 모드
`/self-review --fix` → 리뷰 후 fixable_by_ai=true인 이슈 자동 수정.
수정 후 diff 보고.

---

### 4. `/orchestrate` — Full Pipeline Mode 강화

#### 4a. 데이터 흐름 계약 강제
현재: spec만 있고 enforce 안 됨.
수정: 각 스킬 완료 후 expected output 파일 존재 확인.

```
analyze-stats 완료 → output/*.csv 존재 확인
make-figures 완료 → _figure_manifest.md 존재 확인
write-paper 완료 → manuscript.md + manuscript_final.docx 존재 확인
```

#### 4b. `--e2e` 플래그
`/orchestrate --e2e` → 전체 체인을 user confirmation 없이 실행.
내부적으로 `/write-paper --autonomous` 호출.

---

### 5. `/check-reporting` — 체크리스트 출력 표준화

현재: 자유 텍스트 compliance report.
수정: PRESENT/PARTIAL/MISSING 상태의 structured output 추가.
`/write-paper` Phase 7이 MISSING 항목을 자동 보완 시도.

---

## 구현 순서 (다음 세션)

### Step 1: `/make-figures` manifest 출력 추가 (30분)
- `_figure_manifest.md` 자동 생성 로직
- D2 flow diagram 기본값 설정
- Study-type 파라미터

### Step 2: `/self-review` 구조화 출력 + fix 모드 (30분)
- JSON 구조 출력
- `--fix` 모드 구현

### Step 3: `/write-paper` Phase 2, 7 체이닝 (1시간)
- Phase 2: `/make-figures` 자동 호출
- Phase 7: `/self-review` + `/check-reporting` + `/search-lit` 자동 호출
- Phase 7: self-review fix loop (max 2회)
- `--autonomous` 플래그
- DOCX build 템플릿 내장

### Step 4: `/orchestrate` e2e 모드 (20분)
- `--e2e` 플래그
- 데이터 흐름 계약 강제

### Step 5: 통합 테스트 (30분)
- CK-1 데이터로 `/orchestrate --e2e` 실행
- Arm A 시뮬레이션: 데이터만 주고 원고 생성까지 무개입 확인

### Step 6: 레포 정리 + 공개 (20분)
- CHANGELOG.md 업데이트
- README에 E2E pipeline 섹션 추가
- 버전 태그

---

## AI Manuscript Quality Study와의 연결

| Study 요구사항 | 스킬 대응 |
|---|---|
| Arm A: Pure AI, no human intervention | `/orchestrate --e2e` or `/write-paper --autonomous` |
| Arm B: AI + Human Edit 시간 측정 | 기존 `/write-paper` (gate 있는 버전) + 편집 시간 로깅 |
| 5 public datasets | `/analyze-stats` + `/make-figures` 자동 체이닝 |
| 8-domain Likert evaluation | `/self-review` 점수가 내부 QC용, 외부 평가는 Google Form |
| Reproducibility (OSF) | 전체 스킬 체인 로그 + 생성 파일 보존 |
| Contamination test (BLEU/cosine) | Phase 7에 similarity check 추가 가능 |

---

## 파일 변경 목록 (예상)

| 파일 | 변경 유형 |
|------|----------|
| `skills/write-paper/SKILL.md` | Major rewrite (Phase 2, 7) |
| `skills/write-paper/references/build_template.py` | 신규 (DOCX build 템플릿) |
| `skills/make-figures/SKILL.md` | Manifest 출력 + D2 + study-type |
| `skills/self-review/SKILL.md` | JSON 출력 + fix 모드 |
| `skills/orchestrate/SKILL.md` | e2e 모드 + 계약 강제 |
| `skills/check-reporting/SKILL.md` | Structured output |
| `CHANGELOG.md` | 업데이트 |
| `README.md` | E2E pipeline 섹션 |

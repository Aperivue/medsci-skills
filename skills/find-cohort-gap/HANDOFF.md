# HANDOFF: `/find-cohort-gap` 스킬 개발

> 범용 코호트 DB 연구주제 gap finder. 건진DB 전용이 아닌, 어떤 코호트 DB에든 적용 가능한 스킬.

---

## 배경

### 왜 만드는가

삼성창원 건진DB에서 CK-1~CK-13 주제를 발굴하면서, 교수님들이 높은 저널에 동의한 주제(CK-7→JACC, CK-13→J Hepatol)와 의문을 받은 주제(CK-3 "이미 많지 않냐?")의 차이를 분석했더니 **체계적 패턴**이 나옴. 이걸 스킬로 만들면 아산 이동 후 새 코호트에서도, NHIS 표본코호트에서도, 다른 연구자가 어떤 코호트 DB를 가져와도 동일한 수준으로 gap을 찾을 수 있음.

### 적용 가능 DB 예시

- 삼성창원 건진DB (49만명, 20년)
- 국민건강보험 표본코호트 (NHIS-NSC, 100만명)
- NHIS-HEALS (건강검진 코호트, 51만명)
- 서울아산 EMR 코호트
- UK Biobank, MESA, Framingham 등 해외 코호트
- 병원 특화 레지스트리 (암등록, 심혈관등록 등)

---

## 핵심 방법론 (메모리에서 추출, 범용화 필요)

### 6-Pattern Scoring (건진DB 실전에서 검증됨)

| # | Pattern | 건진DB 원본 | **범용화** |
|---|---------|-------------|-----------|
| P1 | Serial Data Advantage | 20년 반복측정 | → **Longitudinal Advantage**: DB의 반복측정/추적 구조 활용 여부 |
| P2 | Hard Endpoint Escalation | 사망DB 연결 | → **Endpoint Upgrade**: 기존 연구 대비 더 강한 endpoint (사망, 주요이벤트) |
| P3 | Population Novelty | 한국 최대/건강검진 | → **Cohort Uniqueness**: 규모, 인구, 세팅의 차별점 |
| P4 | Professor-Specialty Match | 학회직 정합 | → **PI-Topic Alignment**: PI/CA의 전문성과 주제 정합도 |
| P5 | Comparison Table 3+ gaps | 비교표 | → 동일 (범용) |
| P6 | Companion Paper | CK-4+CK-13 pair | → **Complementary Design**: 같은 DB에서 상보적 인구/변수 분석 |

### 7단계 파이프라인

1. **Cohort Profiling** — DB 메타데이터 입력 (N, 추적기간, 변수 카테고리, endpoints, 특수 강점)
2. **PI/CA Profiling** — PubMed에서 최근 5년 논문 키워드 추출, 학회직, 진료과
3. **Intersection Matrix** — DB 변수 클러스터 × PI 전문성 교차 → 후보 20-40개
4. **Literature Saturation Scan** — PubMed 검색 → Blue/Green/Yellow/Red 등급
5. **Comparison Table + 6-Pattern Scoring** — 차별점 3개 이상 + 점수 3점 이상 필터
6. **Feasibility Check** — 표본크기, 이벤트 수, 결측률, IRB
7. **One-Pager Output** — 표준 포맷으로 제안서 생성

---

## 개발 전 리서치 과제 (반드시 선행)

### 1. 웹 리서치

| 주제 | 검색 키워드 | 목적 |
|------|-----------|------|
| 코호트 연구 주제 선정 방법론 | "cohort study research question generation methodology" | 기존 프레임워크 존재 여부 확인 |
| NHIS 코호트 활용 가이드 | "NHIS cohort research guide Korea", "국민건강보험 코호트 연구 가이드" | 한국 대표 코호트 활용 패턴 파악 |
| Research gap identification tools | "research gap identification tool", "systematic gap analysis methodology" | 자동화 도구 선행사례 |
| Big data cohort study pitfalls | "big data cohort study common mistakes", "p-value inflation large cohort" | Feasibility check에 반영할 항목 |

### 2. YouTube 리서치

| 주제 | 검색어 | 목적 |
|------|--------|------|
| 코호트 연구 설계 | "how to design cohort study", "코호트 연구 설계" | 연구 설계 체계적 접근법 |
| Research question 도출 | "PICO framework cohort", "research gap identification tutorial" | 기존 교육 자료의 프레임워크 |
| 한국 빅데이터 연구 | "국민건강보험 빅데이터 연구", "건강검진 코호트 논문" | 한국 코호트 활용 실전 |

### 3. 논문 리서치 (`/search-lit`)

| 주제 | PubMed 쿼리 | 목적 |
|------|------------|------|
| Gap analysis methodology | `"research gap" AND "methodology" AND ("cohort" OR "database")` | 선행 방법론 논문 |
| Korean cohort studies guide | `"National Health Insurance" AND "Korea" AND "cohort" AND "methodology"` | NHIS 활용 방법론 논문 |
| Longitudinal advantage | `"longitudinal" AND "advantage" AND "cohort" AND "repeated measures"` | serial data 차별화 근거 |
| Research prioritization | `"research priority setting" AND "database" AND "observational"` | 주제 우선순위 결정 프레임워크 |

**리서치 완료 기준**: 각 카테고리에서 최소 3개 이상 유효한 소스 확보, 기존 프레임워크(PICO, FINER, PICOTS 등)와의 차별점 명확화

---

## 스킬 설계 초안

### 스킬명: `find-cohort-gap`

### SKILL.md 구조 (예상)

```
---
name: find-cohort-gap
description: Research gap finder for longitudinal cohort databases. Profiles cohort strengths, matches PI expertise, scans literature saturation, and outputs ranked topic proposals with gap evidence.
triggers: cohort gap, research topic, DB 주제, 코호트 갭, gap analysis, 연구주제 찾기, find research gap
tools: Read, Write, Edit, Bash, Grep, Glob
model: opus
---

# Phase 0: Cohort Intake
- DB 메타데이터 수집 (N, 추적기간, 변수 목록, endpoints, 특수 강점)
- 기존 연구 목록 확인 (이 DB로 이미 나온 논문)

# Phase 1: PI/CA Profiling
- PubMed에서 PI 최근 논문 키워드 추출 (/search-lit 연동)
- 학회직, 전문 분야, 선호 저널 파악

# Phase 2: Intersection Matrix
- DB 변수 클러스터 × PI 전문성 교차
- 0-3점 매칭 → 2점 이상 후보 추출

# Phase 3: Literature Saturation Scan
- 각 후보에 PubMed 검색 → 4등급 분류
- 핵심 필터: "이 주제로 longitudinal 쓴 논문 있나?"

# Phase 4: 6-Pattern Scoring + Comparison Table
- 기존 3-5편 vs THIS STUDY 비교표 생성
- 6패턴 점수 산출 → 3점 미만 kill or restructure

# Phase 5: Feasibility Gate
- 표본크기, 이벤트 수, 결측률, 추적기간
- Go/No-Go 기준 명시

# Phase 6: Output
- 주제 후보 3개 ranked
- 각 후보: 비교표, Zero Papers 주장, Go/No-Go, 타겟 저널, 타임라인
- One-pager 마크다운 생성
```

### references/ 폴더 (예상)

```
find-cohort-gap/
├── SKILL.md
└── references/
    ├── pattern_scoring_rubric.md    # 6-Pattern 채점 기준 + 예시
    ├── cohort_profile_template.md   # DB 메타데이터 입력 템플릿
    ├── onepager_template.md         # 제안서 출력 템플릿
    ├── known_cohorts/               # 주요 코호트 프로필 (선택)
    │   ├── nhis_nsc.md
    │   ├── nhis_heals.md
    │   └── uk_biobank.md
    └── saturation_query_templates.md # PubMed 검색 쿼리 템플릿
```

---

## 건진DB 특화 부분은 메모리에 유지

스킬에 넣지 않고 메모리(`checkup_db_gap_methodology.md`)에 남겨둘 것:
- CK 번호 체계 (CK-1~CK-13)
- 교수님-주제 매칭 (김덕경→CKM, 고광철→HBV 등)
- 삼성창원 변수 딕셔너리 (1,447 변수, 16 시트)
- S-Portal 데이터 신청 절차
- 건진DB 실전 교훈 (CK-3 사건 등)

이 메모리는 스킬 실행 시 자동으로 컨텍스트에 로드되므로, 건진DB에서 스킬을 호출하면 특화 정보가 자연스럽게 반영됨.

---

## 기존 스킬과의 관계

| 기존 스킬 | 관계 |
|----------|------|
| `/search-lit` | Phase 1, 3에서 **호출**. PI 논문 검색, saturation scan에 활용 |
| `/design-study` | Phase 5 feasibility와 일부 겹침. 하지만 design-study는 이미 정해진 주제의 설계 검증, find-cohort-gap은 **주제 자체를 찾는 것** |
| `/write-paper` | Phase 6 output이 write-paper Phase 0의 input이 됨 |
| `/intake-project` | 새 프로젝트 시작 시 intake → find-cohort-gap → design-study → write-paper 순서 |

---

## 다음 세션 실행 순서

1. **리서치** (웹 + YouTube + 논문) — 위 리서치 과제 3개 카테고리 병렬 실행
2. **프레임워크 정리** — 리서치 결과 + 건진DB 실전 경험 종합
3. **SKILL.md 작성** — `/Users/eugene/workspace/medsci-skills/skills/find-cohort-gap/SKILL.md`
4. **references/ 작성** — 채점 rubric, 템플릿 등
5. **테스트** — 건진DB로 CK-14 후보 발굴 시뮬레이션, NHIS로 가상 시나리오
6. **README/CHANGELOG 업데이트** — medsci-skills repo에 새 스킬 등록

---

## 성공 기준

- [ ] NHIS 표본코호트 프로필 입력 → 주제 3개 ranked output 생성 가능
- [ ] 건진DB 프로필 입력 → CK-7/CK-13 수준 주제 재현 가능
- [ ] 6-Pattern 점수가 3점 미만인 주제는 자동으로 restructure 권고
- [ ] 비교표 자동 생성 (기존 논문 vs THIS STUDY)
- [ ] `/search-lit`와 seamless 연동

---

*인계 작성: 2026-04-15 | 다음 세션에서 리서치부터 시작*

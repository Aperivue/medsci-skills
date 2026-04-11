# Handoff: Repository Improvement Plan (Reproducibility / Auditability / Fail-Fast)

> Date: 2026-04-11
> Scope: medsci-skills repository quality hardening
> Author intent: 연구 파이프라인의 재현성·감사가능성·실패즉시중단(Fail-Fast) 강화

---

## 0) Executive Summary

현재 레포는 도메인 커버리지와 데모 산출물은 강력하지만, 아래 3개 계약(invariant)이 깨질 가능성이 있습니다.

1. **문서-실체 동기화 계약 위반 위험**: README/스킬 문서 간 카운트·설명 불일치 가능
2. **Fail-Fast 계약 위반 위험**: 일부 문구/동작이 silent fallback으로 해석될 여지
3. **검증 자동화 계약 위반 위험**: 수동 점검 의존으로 릴리즈 시 회귀 탐지 지연

본 문서는 각 개선 항목을 **Reproduce → Isolate → Fix Root Cause → Prove** 순서로 인계합니다.

---

## 1) Improvement A — 문서 불일치 제거 (Single Source of Truth)

### Reproduce

아래 명령으로 주요 불일치를 재현합니다.

```bash
# README의 가이드라인 수치 확인
rg -n "22 reporting guidelines|22 Reporting Guidelines|22 guidelines" README.md

# orchestrate의 구형 수치 확인
rg -n "15 reporting guidelines|15 reporting" skills/orchestrate/SKILL.md
```

### Isolate

최소 범위는 2개 파일입니다.

- `README.md`
- `skills/orchestrate/SKILL.md`

핵심 계약:

- 공개 문서의 수치/설명은 동일한 기준값을 사용해야 함.

### Fix Root Cause

- 가이드라인/프로필/스킬 개수 같은 숫자는 **하드코딩 중복 금지**.
- 루트에 단일 메타데이터 파일(예: `metadata/catalog_counts.json`)을 두고, README 및 SKILL 문구는 생성 스크립트로 반영.
- 수동 편집 허용 시에도, pre-commit에서 값 일치 검사 실패 시 즉시 종료.

### Prove

```bash
python scripts/validate_catalog_consistency.py
# 기대: 0 exit code, 불일치 0건
```

성공 기준:

- README, 각 SKILL 문서, 소개 JSON의 카운트가 모두 동일.
- 불일치 시 CI가 즉시 실패.

---

## 2) Improvement B — Silent Fallback 제거 (Fail-Fast 명시화)

### Reproduce

문서/핸드오프에서 fallback 리스크를 재현합니다.

```bash
rg -n "silently|silent|fallback|knowledge fallback" README.md docs/ skills/
```

### Isolate

최소 범위는 `check-reporting` 계열 라우팅/체크리스트 로더입니다.

핵심 계약:

- 라우팅된 체크리스트 파일이 없으면 결과를 생성하지 말고 즉시 실패해야 함.

### Fix Root Cause

- 체크리스트 해석 경로에서 `required checklist file exists`를 hard invariant로 지정.
- 파일 미존재/파싱 실패/스키마 오류 시, 즉시 non-zero 종료 + 명확한 오류 메시지 출력.
- “LLM 지식으로 대체 평가” 경로를 제거하거나, 명시적 `--allow-nonfailfast` 플래그 없이는 금지.

### Prove

```bash
# 존재하지 않는 체크리스트를 의도적으로 요청
python scripts/check_reporting_contract_test.py --simulate-missing-checklist
# 기대: non-zero exit, "MISSING_CHECKLIST_CONTRACT_VIOLATION" 포함
```

성공 기준:

- 누락 체크리스트 상황에서 보고서 파일이 생성되지 않음.
- 오류가 조용히 묻히지 않고 표준화된 코드/메시지로 노출.

---

## 3) Improvement C — 라우팅 참조 무결성 검사 추가

### Reproduce

라우팅 테이블의 참조 파일이 실제 존재하는지 전수 검사합니다.

```bash
python scripts/validate_routing_assets.py --scan skills/*/SKILL.md
```

### Isolate

최소 범위:

- 각 `skills/*/SKILL.md`의 라우팅 규칙
- `skills/check-reporting/references/checklists/*.md`

핵심 계약:

- 라우팅 표에서 참조한 guideline/checklist는 파일 시스템에 반드시 존재해야 함.

### Fix Root Cause

- 정규식 기반 정적 검사기로 문서의 guideline 키워드 추출.
- 추출 키워드 ↔ 실제 체크리스트 파일 매핑을 강제.
- 누락 1건이라도 있으면 CI 실패.

### Prove

```bash
python scripts/validate_routing_assets.py --strict
# 기대: missing references 0
```

성공 기준:

- 신규 guideline 추가/삭제 시 검증 스크립트 동시 업데이트 없으면 머지 불가.

---

## 4) Improvement D — 릴리즈 게이트(자동 검증) 신설

### Reproduce

현재 검증 자동화 부재/부족 상태를 아래로 확인합니다.

```bash
find . -maxdepth 3 -type f | rg "^\./\.github/workflows/"
```

### Isolate

최소 범위:

- `.github/workflows/repo-integrity.yml` (신규)
- `scripts/validate_catalog_consistency.py` (신규)
- `scripts/validate_routing_assets.py` (신규)

### Fix Root Cause

릴리즈 전 필수 게이트를 CI에 추가합니다.

1. 카운트/문구 동기화 검사
2. 라우팅-자산 참조 무결성 검사
3. 데모 산출물 manifest 스키마 검사
4. FAIL-FAST 정책 위반 문자열 탐지(허용목록 기반 예외만 허용)

### Prove

```bash
# 로컬에서 CI와 동일 실행
bash scripts/run_repo_integrity_checks.sh
# 기대: 모든 체크 pass
```

성공 기준:

- 릴리즈 브랜치에서 검증 실패 시 병합 차단.

---

## 5) Improvement E — 데모 재현성 계약 강화 (Manifest + Hash)

### Reproduce

데모 산출물이 존재해도, 동일 입력 대비 동일 결과 보장을 자동 검증하지 못할 수 있습니다.

```bash
# 예시: 데모 산출물 목록 확인
find demo -maxdepth 3 -type f | rg "output/|figures/"
```

### Isolate

최소 범위:

- 각 데모 폴더의 `_analysis_outputs.md`
- 신규 `manifest.lock` (입력 데이터 해시 + 핵심 산출물 해시)

핵심 계약:

- 동일 입력/버전에서 산출물 무결성 해시가 일치해야 함.

### Fix Root Cause

- 각 데모에 `manifest.lock.json` 생성.
- 재실행 시 lock 갱신이 아니라 먼저 검증; 불일치면 즉시 실패.
- 허용 가능한 비결정적 산출물(PPTX timestamp 등)은 명시적 예외 키로만 허용.

### Prove

```bash
python scripts/verify_demo_manifest.py --demo demo/01_wisconsin_bc --strict
python scripts/verify_demo_manifest.py --demo demo/02_metafor_bcg --strict
python scripts/verify_demo_manifest.py --demo demo/03_nhanes_obesity --strict
```

성공 기준:

- 3개 데모 모두 strict 모드 통과.
- 해시 불일치 시 즉시 non-zero 종료.

---

## 6) 우선순위 (실행 순서)

1. **A 문서 동기화 계약 확립** (즉시)
2. **C 라우팅 참조 무결성 검사** (즉시)
3. **B Silent fallback 제거** (즉시)
4. **D CI 릴리즈 게이트 도입** (단기)
5. **E 데모 해시 기반 재현성 강화** (단기)

---

## 7) 인수 조건 (Definition of Done)

아래를 모두 만족하면 본 인계 이슈는 완료입니다.

- 문서 카운트 불일치 0건
- 라우팅 참조 누락 0건
- 체크리스트 누락 시 보고서 생성 금지 + 즉시 실패
- CI에서 무결성 검사 100% 수행
- 3개 데모 strict 재현성 검사 pass

---

## 8) 커뮤니케이션 규칙 (작업자용)

- 우회 금지: fallback·silent default·best-effort 금지
- 계약 위반 시 즉시 중단 후 원인 수정
- 결과 보고는 반드시 명령/출력 기반으로 작성
- 변경 설명은 "무엇/왜/어떤 계약을 강제했는지"를 분리해 기술

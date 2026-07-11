---
title: "MedSci Skills repository improvement audit"
date: 2026-07-11
language: ko
repository: Aperivue/medsci-skills
baseline_commit: 93ba4a2
baseline_release: v5.19.0
scope: architecture, duplication, routing, workflow, validation, documentation, distribution, adoption, promotion
status: analysis-only
---

# MedSci Skills 레포 개선 보고서

> **상태 업데이트 (v5.20.1, 2026-07-11):** 이 감사는 baseline `93ba4a2` / `v5.19.0` 기준이다. §4의 P0 두 건 — **F1** (`/orchestrate --e2e` 상태전이 오류)과 **F2** (라우팅 reachability: 20개 스킬 누락) — 그리고 §6.1의 public-claim drift(plugin 개수)는 그 재발방지 CI gate와 함께 **v5.20.1에서 수정·배포**되었다(이후 detector 수는 57). 나머지 P1 및 외부(공개 사이트·홍보) 항목은 진행 중이다. 공개용으로 대외 민감 지표(내부 traffic·경쟁 순위·조회수)는 일반화했다.

## 1. 결론

MedSci Skills는 기능이 부족한 레포가 아니다. 현재 강점은 오히려 분명하다.

- 의료 연구라는 좁고 가치가 높은 문제에 집중한다.
- 55개 스킬, 46개 reporting guideline/RoB 도구, 52개 deterministic detector를 갖고 있다.
- DOI, arXiv, 공개 데모, CI, 재현성 manifest, Windows 외부 검증 기록까지 신뢰 자산이 많다.
- 공개 관심도(stars/forks/traffic)는 꾸준히 증가하는 추세다.

그러나 이 강점이 사용자에게 전달되는 구조에는 세 가지 병목이 있다.

1. **단일 진입점인 `/orchestrate`가 현재 catalog를 따라가지 못한다.** 55개 중 20개를 전혀 언급하지 않으며, 특히 model-engineering lane 대부분이 라우팅에서 빠져 있다.
2. **검증기는 파일 구조에는 강하지만 실제 사용자 흐름에는 약하다.** E2E 단계 순서, routing reachability, trigger collision, 공개 사이트 drift는 현재 CI의 검사 대상이 아니다.
3. **좋은 증거가 너무 많이, 서로 다른 버전으로 노출된다.** README는 901줄이고, 공개 사이트·가이드·영상은 과거 시점의 skill/demo/guideline 개수를 보여준다.

따라서 다음 단계는 스킬 추가가 아니다. 가장 높은 수익을 내는 방향은 다음과 같다.

> **라우팅과 E2E 흐름을 먼저 고치고, 모든 공개 표면을 하나의 SSOT에 연결한 뒤, “55개 스킬”이 아니라 “세 가지 검증 가능한 연구 결과”를 홍보한다.**

즉시 권고는 다음과 같다.

- **P0:** `/orchestrate` E2E 상태전이 오류와 20개 스킬 누락 수정
- **P0:** Aperivue 사이트·가이드·YouTube의 오래된 숫자와 Claude-only 메시지 교정
- **P1:** `skill.yml`에서 routing/README/site/quality badge를 생성하는 reachability SSOT 구축
- **P1:** README를 약 200–300줄의 landing page로 축소하고 목적별 install bundle 제공
- **P2:** workflow gallery, `llms.txt`, behavioral trigger tests, 외부 사용자 사례 확보

## 2. 감사 범위와 방법

기준점은 `main` commit `93ba4a2`와 release `v5.19.0`이다. 다음을 확인했다.

- 55개 `SKILL.md`와 `skill.yml`
- `orchestrate`, `capabilities.yml`, artifact contract, schema 문서
- README, ROADMAP, IMPACT, generated skill docs, demo, installer, release workflow
- GitHub Actions와 현재 GitHub/npm 배포 상태
- 공개 Aperivue Skills landing/guide와 YouTube 소개 영상
- 공식 GitHub 소스를 통한 인기 agent-skill/developer-tool 레포 비교

실행한 검증은 모두 성공했다.

- `validate_skills.sh`
- `validate_skill_contracts.py`
- `validate_catalog_consistency.py`
- `validate_routing_assets.py --strict`
- `validate_capabilities.py --strict`
- `check_domain_probe_sync.py --strict`
- Python source compile check
- release ZIP / npm package audit

따라서 아래 문제는 “현재 CI가 빨간 레포”의 문제가 아니다. **현재 CI가 제품 수준의 중요한 계약을 검사하지 않는 문제**다.

## 3. 현재 상태 요약

| 영역 | 판정 | 요약 |
|---|---|---|
| 핵심 차별화 | 강함 | clinical submission reliability와 deterministic gate는 분명한 moat |
| 코드/구조 검증 | 강함 | main/release CI와 catalog/package 검증이 성숙함 |
| 실제 workflow 검증 | 주의 | 파일 존재 검사는 많지만 E2E state transition 검증은 부족 |
| 스킬 중복 관리 | 대체로 양호 | 의도적 vendoring은 좋으나 checklist/CSL 중복은 sync되지 않음 |
| 라우팅/탐색 | 취약 | `/orchestrate`가 catalog의 36%를 모르며 trigger 충돌이 존재 |
| 계약 일관성 | 취약 | layer/typed artifact 문서와 실제 `skill.yml`이 다름 |
| README 정보구조 | 과밀 | 901줄, 11,486단어, 19개 release 설명이 landing page에 공존 |
| 공개 사이트 | P0 drift | skill/demo/guideline/host/install 정보가 현재 release와 불일치 |
| 배포 UX | 보통 | 자체 installer는 좋지만 subset/standard ecosystem 경로가 약함 |
| 채택 증거 | 초기 | 관심은 증가하지만 citation/named downstream use는 거의 없음 |

## 4. 최우선 기술 발견사항

### F1. `/orchestrate --e2e`의 DOCX 완료 조건이 단계 순서와 충돌한다 — P0

표준 pipeline은 `/write-paper`가 Markdown manuscript를 만들고, 7단계 `/manage-refs`가 DOCX를 생성하도록 정의한다.

- pipeline 정의: [`skills/orchestrate/SKILL.md`](../../skills/orchestrate/SKILL.md) 271–280행
- post-skill validation: 같은 파일 282–300행

그런데 `/write-paper` 직후 검증에서 `--e2e`이면 `manuscript_final.docx`를 필수로 요구한다. 문구대로 실행하면 3단계 직후 멈추므로 DOCX를 생성하는 7단계에 도달할 수 없다.

추가로 `/write-paper` 내부 Phase 7이 `self-review`와 `check-reporting`을 호출하면서, orchestrator 단계 4와 6이 다시 해당 skill을 호출하는 것처럼 읽힌다. “호출”과 “기존 output 검증”의 소유권이 모호하다.

권고:

1. `/write-paper` post-check는 `manuscript.md`만 검증한다.
2. DOCX/xref 검증은 `/manage-refs` 완료 후에만 실행한다.
3. `check-reporting`/`self-review` 실행 주체를 write-paper 또는 orchestrate 중 한 곳으로 통일한다.
4. 임시 프로젝트를 만들어 단계 1→7을 실제로 통과시키는 state-transition test를 CI에 추가한다.

### F2. `/orchestrate`가 20/55개 스킬을 전혀 알지 못한다 — P0

README는 `/orchestrate`를 전체 bundle의 single entry point로 권장한다. 그러나 [`skills/orchestrate/SKILL.md`](../../skills/orchestrate/SKILL.md) 38–75행의 available-skills table은 35개에서 끝난다.

전혀 등장하지 않는 20개는 다음과 같다.

`architecture-zoo`, `author-strategy`, `batch-cohort`, `cross-national`, `design-ai-benchmarking`, `explainability`, `find-cohort-gap`, `ma-scout`, `mllm-eval`, `model-card`, `model-evaluation`, `model-scaffold`, `model-validation`, `polish-language`, `preprocess-imaging`, `radiomics-ml`, `replicate-study`, `review-paper`, `setup-medsci`, `uncertainty-imaging`.

특히 공개 메시지에서 크게 강조하는 model-engineering lane 대부분이 single entry point에서 도달 불가능하다. 이것은 단순 문서 누락이 아니라 기능 발견성 문제다.

권고:

- 하드코딩된 available-skills/routing table을 제거한다.
- `skill.yml`과 `metadata/skills_catalog.json`에서 routing index를 생성한다.
- 모든 `official` skill은 다음 중 하나를 가져야 한다.
  - 직접 trigger route
  - 명시적 umbrella route
  - `direct_only: true`와 사유
- 이 조건을 CI reachability gate로 만든다.

### F3. trigger 충돌을 구조적으로 검증하지 않는다 — P1

exact trigger phrase 기준으로 21개 스킬에 걸쳐 24개 충돌이 확인됐다. 대표적인 위험 구간은 다음과 같다.

| 충돌 | 필요한 구분 기준 |
|---|---|
| `reviewer comments`: `revise` vs `peer-review` | 받은 decision letter에 답변 vs 타인의 원고를 reviewer로 평가 |
| `citation`, `references`: `search-lit` vs `manage-refs` | 후보 발견 vs 기존 bibliography 렌더/수명주기 관리 |
| `ROC curve`: `analyze-stats` vs `make-figures` | 추정/통계 계산 vs 이미 계산된 결과 시각화 |
| `forest plot`: `meta-analysis` vs `make-figures` | synthesis pipeline vs plot artifact 생성 |
| `data leakage`: model lane 여러 스킬 | preprocessing, split, training, validation stage 구분 |
| `scoping review`: `review-paper` vs `check-reporting` | manuscript scaffold vs 완성 원고 compliance audit |

핵심은 키워드가 아니라 `intent + object + lifecycle stage`다. positive trigger뿐 아니라 negative trigger도 행동 테스트해야 한다.

권고 behavioral card:

- should-trigger 5개
- should-not-trigger 5개
- ambiguous/adversarial 2개
- expected artifact
- expected deterministic verifier

### F4. capability registry가 실제 contested domain을 놓친다 — P1

[`capabilities.yml`](../../capabilities.yml)은 겹치는 domain의 owner를 정하기 위한 파일이다. 그러나 실제 `skill.yml`을 집계하면 다음 6개 undeclared domain에서 여러 skill이 같은 `owner_domain`을 주장한다.

- `model_evaluation`
- `manuscript_optimization`
- `model_validation`
- `study_design`
- `form_filling`
- `data_preparation`

현재 validator는 domain이 `capabilities.yml`에 선언되지 않았으면 의도적으로 건너뛴다([`scripts/validate_capabilities.py`](../../scripts/validate_capabilities.py) 134–143행). 따라서 “registry consistent”가 전체 도달성이나 단일 ownership을 의미하지 않는다.

권고:

- ownership conflict registry와 routing reachability registry를 분리한다.
- undeclared domain에 claimant가 2개 이상이면 CI를 실패시킨다.
- model lane에는 stage-based umbrella를 둔다: `prepare → choose → scaffold → validate → evaluate → explain/uncertainty → document`.

### F5. `layer`와 typed artifact contract가 문서상 정책에 머문다 — P1

[`docs/skill_yml_schema_v2.md`](../skill_yml_schema_v2.md)는 Layer D를 `decisions/*.md` append-only로 정의한다. 실제로는 다음과 같다.

- Layer D `self-review`가 QC 파일을 쓰고 `--fix`에서 manuscript를 수정할 수 있다.
- Layer D `radiomics-ml`이 nested-CV training code와 JSON을 출력한다.
- Layer D `manage-project`/`intake-project`가 프로젝트 파일을 scaffold한다.
- Layer D `orchestrate`가 `qc/_pipeline_log.md`를 쓴다.

validator는 layer 값이 A/B/C/D 중 하나인지만 확인한다. side effect와 output이 layer 정책을 지키는지는 검사하지 않는다.

또한 55개 contract 중 input은 53개가 free-form string list이고, output은 52개가 string list다. 문서가 제시하는 typed `{path, schema, required}` 형태는 소수만 사용한다. `review-paper`는 유일하게 quality-card 5개 필드 전체가 없다.

권고:

1. layer를 실제 실행 권한으로 쓸 것인지, 설명용 taxonomy로만 쓸 것인지 결정한다.
2. 실행 권한이면 output/side-effect validator를 추가하고 잘못 분류된 skill을 B/C로 옮긴다.
3. 공식 skill에는 quality card를 필수화한다.
4. input/output string을 단계적으로 typed map으로 전환하고 legacy string에는 경고를 낸다.

### F6. obsolete artifact contract가 존재하지 않는 skill을 가리킨다 — P1

[`docs/artifact_contract.md`](../artifact_contract.md)와 [`docs/ssot_schema_v1.md`](../ssot_schema_v1.md)는 `/render`와 `/backport-to-ssot`를 현재 skill처럼 사용한다. 그러나 55개 bundle에는 이 skill들이 없다. 현재 DOCX writer는 `manage-refs`, submission package writer는 `sync-submission`이다.

같은 artifact contract는 “missing contracts are warnings”라고 쓰지만 현재 validator는 missing `skill.yml`을 실패시킨다.

권고:

- `/render`를 `manage-refs`/`sync-submission`의 실제 역할로 치환한다.
- `/backport-to-ssot`가 외부/local capability라면 명시적으로 표시하고 fallback을 제공한다.
- 문서 속 backtick slash-command를 catalog와 대조하는 validator를 추가한다.

### F7. `/orchestrate`의 reference pointer와 dialogue-node 설명이 드리프트했다 — P1

`orchestrate`는 `${SKILL_DIR}/references/...`를 사용하지만 repo의 검증 규약은 `${CLAUDE_SKILL_DIR}/...`만 검사한다. 현재 routing-asset validator가 이 pointer들을 보지 않는다. 또한 본문은 N1–N9의 9개 node라고 하지만 실제 reference와 workflow에는 N10/N11이 있다.

권고:

- pointer 변수를 repo 표준으로 통일하고 validator 대상에 포함한다.
- node 목록을 generated inventory로 만든다.
- 배포 skill이 참조하는 `~/.claude/rules/...`는 cross-host bundle에 vendoring하거나 optional enhancement로 낮춘다.

## 5. 스킬 중복 감사

### 5.1 파일 중복

200 bytes 이상 동일 파일 기준으로 29개 duplicate group, 58개 파일, 약 279KB의 extra copy가 있다.

| 종류 | 그룹 | extra bytes | 판정 |
|---|---:|---:|---|
| `peer-review` ↔ `self-review` domain probes | 22 | 약 241KB | 의도적 vendoring, sync gate 있음 — 유지 |
| `check-reporting` ↔ `meta-analysis` checklists | 6 | 약 20KB | 의도는 타당하나 sync gate 없음 — 보강 |
| `vancouver.csl` ↔ `nlm-citation-sequence.csl` | 1 | 약 18KB | alias 관계를 문서화하거나 build-time copy로 관리 |

현재 [`docs/dedup_audit.md`](../dedup_audit.md)의 결론처럼 runtime `_shared/` package를 만드는 것은 권하지 않는다. 개별 skill portability를 해칠 가능성이 높다.

대신 canonical source를 각 skill에 복사하는 **build-time vendoring manifest**를 일반화해야 한다. 현재 domain-probe sync 방식에 checklist 6개와 CSL alias를 등록하면 된다.

### 5.2 기능 중복

핵심 skill 대부분은 합칠 필요가 없다. 겹쳐 보이는 것은 lifecycle stage가 연속되기 때문이다.

| 군집 | 판정 | 조치 |
|---|---|---|
| `search-lit` → `lit-sync` → `manage-refs` → `verify-refs` | 유지 | 한 pipeline으로 표시 |
| `write-paper` / `self-review` / `peer-review` / `revise` | 유지 | author/external reviewer/revision intent를 trigger에 명시 |
| `humanize` → `polish-language` → `academic-aio` | 유지 | 순서와 output 차이를 한 카드로 표시 |
| `write-protocol` → `fill-protocol` | 유지 | content vs institutional template 경계 유지 |
| model-engineering 10개 | 유지 | stage-based umbrella와 routing 필요 |
| `ma-scout` / `find-cohort-gap` / `author-strategy` | 유지 | “Discover” umbrella 아래 진입 질문 통합 |
| `batch-cohort` / `cross-national` / `replicate-study` | 재평가 후보 | 사용 증거가 적으면 `analyze-stats` mode로 흡수 검토 |

삭제/병합은 이름 유사도만으로 결정하면 안 된다. 다음 네 조건을 함께 본다.

1. 같은 trigger인가?
2. 같은 input/output artifact인가?
3. 같은 lifecycle stage인가?
4. 독립적으로 설치할 가치가 있는가?

## 6. 검증과 오류 탐지의 빈틈

### 6.1 README detector 수가 이미 틀렸지만 CI는 녹색이다

SSOT와 최신 릴리스 설명은 52 detector다. 그러나 [`README.md`](../../README.md) 400행의 “Why This Repo?”는 여전히 36개라고 한다. `validate_catalog_consistency.py`의 detector claim 대상이 README를 포함하지 않기 때문이다.

같은 유형의 오류:

- plugin table은 9개인데 [`README.md`](../../README.md) 123행은 “All eight plugins”라고 한다.
- depth claim은 “150–600 lines”지만 실제 `SKILL.md` 범위는 103–1,384 lines다.
- `HANDOFF.md`는 과거 commit/detector/worktree 상태를 담고 있다.
- `docs/competitive_positioning.md`는 cross-host support를 planned라고 하지만 README/host docs는 현재 지원으로 표시한다.

권고: count만 검사하지 말고 public claims를 named marker/JSON-LD/metadata에서 생성한다.

### 6.2 Demo 4는 강하지만 manifest lock이 없다

README는 네 개의 full pipeline demo를 홍보한다. Demos 1–3은 CI에서 `manifest.lock.json`을 검증하지만 `demo/04_pneumoniamnist_cnn`에는 manifest가 없고 해당 output을 검증하는 CI도 없다.

3-seed training을 매번 CI에서 돌릴 필요는 없다. 다음이면 충분하다.

- committed output의 content manifest
- network-free code/build smoke test
- JSON schema와 figure/artifact 존재 확인
- training result는 특정 environment/version에 고정된 snapshot임을 표시

### 6.3 일부 runtime test는 skip이 성공으로 처리된다

예를 들어 survival template runtime smoke는 `lifelines`가 없으면 성공 코드로 skip한다. CI dependency에는 `lifelines`가 없다. “CI에 연결됨”과 “runtime이 실제 실행됨”을 구분해야 한다.

권고: 필수 runtime lane에는 dependency를 설치하고, 의도된 optional test에는 skip count를 summary로 노출한다.

### 6.4 evidence와 maturity를 분리해서 더 잘 보여줘야 한다

현재 evidence surface는 다음과 같다.

- `manual_workflow`: 21
- `bundled_script`: 15
- `ci_validator`: 11
- `demo`: 7
- missing: 1 (`review-paper`)

반면 maturity는 55개 모두 `official`이다. 이것은 모순은 아니지만 사용자는 `official`을 “동적으로 검증 완료”로 오해할 수 있다.

권고: catalog card에서 maturity보다 evidence badge와 limitation을 더 눈에 띄게 표시한다.

## 7. 정보구조와 설치 흐름

### 7.1 README는 문서이자 changelog이자 catalog라서 전환이 어렵다

현재 README는 901줄, 11,486단어, 약 99KB다. `What's New`에는 19개 release 설명이 들어 있다. Quick Start가 상단에 있는 점은 좋지만, 방문자는 value proposition, badge wall, 네 demo, release history, 55개 장문 설명, 설치 변형을 한 문서에서 처리해야 한다.

권장 first fold:

1. 한 문장 promise
2. `Install` / `Watch 2 min` / `Run first prompt` CTA
3. 세 개 proof card
4. 세 개 시작 경로

권장 영문 hero:

> **Clinical research workflows for AI agents—with integrity gates before peer review.**

권장 subheading:

> Search literature, analyze data, draft manuscripts, validate medical-AI models, and catch fabricated citations, numeric drift, and reporting gaps before submission.

상세 release history, 전체 catalog, 설치 변형, 평가 설명은 docs로 이동한다.

### 7.2 default install이 all-or-nothing이다

자체 installer는 clinician-friendly하고 update safety도 좋다. 하지만 CLI에는 target-host 옵션만 있고 skill/category subset 설치가 없다. 55개 description의 startup surface는 총 약 22.5KB이며, 사용자는 필요하지 않은 routing 후보까지 설치한다.

권고 bundle:

- `manuscript-qc`
- `data-to-paper`
- `meta-analysis`
- `medical-ai-model`
- `irb-protocol`
- `presentation`

자체 classroom installer는 유지하되 다음 portable 경로도 first-class로 검증한다.

- 표준 `npx skills add`
- `gh skill install`
- repo/SHA pinning
- selected skill/category install
- try-without-install

## 8. 공개 사이트와 홍보 — 가장 시급한 신뢰성 문제

### 8.1 공개 표면이 현재 release와 크게 다르다 — P0

공개 사이트(landing/guide), 소개 영상, 그리고 그 SEO/OpenGraph/JSON-LD 메타데이터가 현재 release보다 이전 시점의 skill/demo/guideline 개수와 단일 호스트(Claude 중심) 설치 흐름을 보여준다. repo README는 현재 release와 대체로 일치한다. 사이트에는 이미 search/category filter가 있으므로 새 explorer를 처음부터 만들 필요는 없다. **현재 explorer의 빌드를 repo catalog SSOT에 다시 연결하는 것이 먼저다.**

권고:

- site build가 `metadata/skills_catalog.json`과 `metadata/catalog_counts.json`을 직접 소비하게 한다.
- release workflow가 site consumer version/hash를 확인한다.
- site deploy가 늦으면 release check에 명시적인 `PUBLIC_SURFACE_PENDING`을 남긴다.
- 영상 title에서 변하는 skill count를 제거한다(evergreen).

### 8.2 관심은 늘지만 실제 채택 증거가 약하다

가시성(traffic·referral)은 늘고 있으나, 현재 병목은 awareness가 아니라 **confirmed use와 community conversion**이다 — 논문 citation, 검증된 downstream 사용, 외부 기여가 성장의 다음 지표다. 아래 지표로 이를 추적한다.

추천 지표:

- 설치 후 첫 workflow 성공률
- demo 실행/다운로드 수
- 외부 workflow recipe 수
- 실제 연구·교육 사용 사례
- DOI citation
- 외부 PR과 첫 issue 해결시간
- YouTube 30초 retention과 GitHub click-through

### 8.3 영상은 세 층으로 만든다

현재 2분 영상은 길이는 적절하나 제목에 변하는 skill count가 들어가 evergreen하지 않다. 인기 사례는 문제를 첫 30초에 제시하거나, 짧은 explainer와 긴 실습을 분리한다.

권장 구조:

1. **30–60초 problem hook**: fabricated citation, numeric drift, missing reporting item
2. **2–3분 evergreen explainer**: 세 workflow, gate, artifact, install CTA
3. **8–15분 use-case series**: manuscript audit / meta-analysis / medical-AI validation

제목 예:

- `Stop Fabricated Citations Before Peer Review | MedSci Skills`
- `Audit a Medical Manuscript with AI—Without Trusting AI Blindly`
- `From Clinical Data to a Checked Manuscript | MedSci Skills Demo`

## 9. 정보구조·배포 벤치마킹 (교훈 요약)

인기 agent-skill·개발도구·의료 도메인 레포에서 반복되는 IA·배포 패턴 (특정 레포명·순위·수치는 생략):

- skill **개수**가 아니라 하나의 일관된 workflow를 판다 → 하나의 clinical-reliability journey를 전면화.
- 정의 → 예시 → 사용 → 만들기의 단순 IA + 짧은 first fold + contributor onboarding.
- canonical catalog SSOT + granular package + eval harness → trigger/duplicate/token-burden을 행동 평가.
- search/filter + Learning Hub + `llms.txt` + contributor loop → catalog metadata를 검색/AI-discovery surface로.
- portable install(add/update/remove, project/global, target host) + topical subset.

추가 product/education 사례:

- [n8n workflow gallery](https://n8n.io/workflows/): 기능 목록보다 use-case workflow를 탐색하게 함
- [shadcn/ui blocks](https://ui.shadcn.com/blocks): 설명보다 실제 결과물을 먼저 보여줌
- [LangChain quickstart](https://docs.langchain.com/oss/python/langchain/quickstart): 첫 성공까지 걸리는 시간을 짧게 설계
- [MONAI](https://project-monai.github.io/): 의료 도메인 권위, tutorial, bootcamp, success story, citation을 연결

MedSci가 모방하지 말아야 할 것도 분명하다.

- “largest skill catalog” 경쟁
- 55개 모두를 별도 mirror repo로 분할
- 임상 사용자에게 기본 telemetry 도입
- 실제 수정 없이 security badge만 추가
- third-party workflow marketplace를 너무 일찍 구축

## 10. 권장 정보구조

### README

1. Hero: 문제/결과 중심 한 문장
2. 세 CTA: install, video, first prompt
3. 세 workflow: manuscript audit, data-to-paper, medical-AI model
4. artifact preview: reference audit, reporting checklist, figure/model-validation report
5. evidence: demos, detector count, DOI, CI
6. compact catalog link
7. install variants
8. contribution/citation

### Skill card

- 해결하는 문제
- should-trigger / should-not-trigger
- 필요한 input
- 생성 output
- 복사할 first prompt
- evidence surface
- known limitation
- guideline/standard
- dependency/network/host requirement
- upstream/downstream handoff

### Demo landing

- 연구 질문과 dataset
- workflow
- 핵심 artifact 3개 미리보기
- gate가 실제로 잡은 문제
- 재현 명령과 예상 시간
- 환경/version
- limitation

## 11. PR 단위 실행 로드맵

### 즉시: release 후 신뢰 복구

**PR-1 — orchestrate E2E state transition**

- write-paper DOCX post-condition 제거
- manage-refs 후 DOCX/xref 검증
- 중복 QC invocation 소유권 정리
- E2E state-transition fixture

**PR-2 — orchestrate reachability**

- 20개 누락 skill route 추가
- N1–N11/pointer 정리
- official-skill reachability validator

**PR-3 — public claim drift**

- README detector 36→SSOT
- 9/eight plugin 오류, line-range claim, host wording 수정
- public-claim validator 확대

**외부 사이트 작업 A — aperivue-web sync**

- 45/51/32/3/Claude-only/install 문구 교정
- repo catalog/hash consumer gate
- release→site deploy/check 연결

**홍보 작업 B — YouTube evergreen update**

- 기존 영상 title/description/thumbnail 교정
- count 없는 evergreen title
- 30–60초 problem hook 제작

### 2–4주: 구조 단순화

**PR-4 — contract semantics**

- multi-claim undeclared domains 실패
- layer/side-effect policy 결정
- official quality card 필수화
- typed I/O migration warning

**PR-5 — vendoring manifest**

- domain probes, checklist 6개, CSL alias를 한 manifest로 sync

**PR-6 — README progressive disclosure**

- 200–300줄 landing page
- release history/catalog 상세 docs 이동
- “zero manual steps”를 bounded autonomy + human verification으로 교정

**PR-7 — install bundles + standard distribution**

- 목적별 bundle
- selected install
- standard ecosystem install/pin/update 검증

**PR-8 — Demo 4 trust surface**

- output manifest
- network-free smoke/schema test
- environment/version limitation

### 1–3개월: 채택 전환

**PR-9 — generated discovery**

- `llms.txt`
- trigger/input/output/evidence 기반 catalog export
- task/study-type/evidence/host filter

**Community workstream**

- Discussions: Show and Tell / Workflow Request / Guideline Request
- `Research Workflow Recipe` 양식
- `Verified Community Workflow` 기준
- 매월 workflow/case study 1건
- 외부 연구자 또는 교육자 3명의 검증된 사용 사례 확보

## 12. 우선순위 결정 규칙

새 작업은 다음 순서로 평가하는 것이 좋다.

1. 현재 사용자가 잘못된 skill로 route되는가?
2. 현재 workflow가 중간에서 멈추거나 잘못된 artifact를 요구하는가?
3. public claim이 실제 release와 다른가?
4. deterministic gate가 없는 임상적으로 중요한 failure mode인가?
5. 확인된 사용자/reviewer/desk-reject 수요가 있는가?
6. 단지 catalog count를 늘리는가?

1–4는 즉시 고치고, 5는 backlog에 올리며, 6만 해당하면 만들지 않는다.

## 13. 최종 제안

다음 분기의 성공 기준을 “스킬 60개”로 두지 않는 편이 좋다. 더 좋은 기준은 다음이다.

- `/orchestrate` official-skill reachability 100%
- E2E state-transition fixture green
- public-site count/hash drift 0
- trigger behavioral cards가 hero workflow 전부를 커버
- README first-success path 5분 이내
- 외부 workflow recipe 3건
- named research/classroom use 3건
- DOI citation 또는 methods-use 보고 1건

MedSci Skills의 다음 경쟁력은 breadth가 아니라 **coherence, evidence, and adoption**이다. 현재 자산은 충분하다. 이제 해야 할 일은 더 만드는 것이 아니라, 이미 만든 시스템을 더 정확히 연결하고 더 쉽게 경험하게 만드는 것이다.

## Sources

### Internal

- [`skills/orchestrate/SKILL.md`](../../skills/orchestrate/SKILL.md)
- [`capabilities.yml`](../../capabilities.yml)
- [`scripts/validate_capabilities.py`](../../scripts/validate_capabilities.py)
- [`scripts/validate_skill_contracts.py`](../../scripts/validate_skill_contracts.py)
- [`docs/artifact_contract.md`](../artifact_contract.md)
- [`docs/skill_yml_schema_v2.md`](../skill_yml_schema_v2.md)
- [`docs/dedup_audit.md`](../dedup_audit.md)
- [`README.md`](../../README.md)
- [`IMPACT.md`](../../IMPACT.md)

### External primary sources

- [Aperivue Skills landing](https://aperivue.com/en/skills)
- [Aperivue Skills guide](https://aperivue.com/en/skills/guide)
- [MedSci Skills intro video](https://www.youtube.com/watch?v=MclQ_RIofpE)
- [Anthropic Skills](https://github.com/anthropics/skills)
- [Superpowers](https://github.com/obra/superpowers)
- [Awesome Copilot](https://github.com/github/awesome-copilot)
- [wshobson/agents](https://github.com/wshobson/agents)
- [K-Dense scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills)
- [Vercel skills CLI](https://github.com/vercel-labs/skills)
- [Agent Skills specification](https://agentskills.io/specification)
- [GitHub citation files](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files)
- [Zenodo GitHub release integration](https://help.zenodo.org/docs/github/describe-software/)

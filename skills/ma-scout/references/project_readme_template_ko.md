# MA-Scout Project README Template — Korean variant (PROSPERO-ready)

> Opt-in Korean variant. The default is the English `project_readme_template.md`. Use this when the
> README is supervisor / professor-facing for a Korean PI review. English section headings and
> PICO/PIRD structure are kept (so the README matches downstream `/meta-analysis` and `/search-lit`
> expectations); Korean prompts are used for the PI-facing fields.

Copy the block below into `{topic_folder}/README.md` and fill in the curly-brace fields.

````markdown
# {Topic Title} — {MA Type} Meta-analysis ({교수님 성함})

## Overview
- Supervisor: {교수님 성함} ({소속 이력})
- 교수님 영역: Pillar {N} — {영역명}
- Status: 기획 단계
- Priority: {순위}순위
- Created: {YYYY-MM-DD}

## Research Question
### PICO/PIRD
- **P**opulation: {구체적 환자군, 질환, 세팅}
- **I**ndex test / Intervention: {검사법 또는 중재}
- **C**omparator / Reference standard: {비교군 또는 참조표준}
- **O**utcome: {DTA: Se/Sp/AUC, Prognostic: HR/OR, 부작용 등}

### One-line RQ
{완성형 연구 질문 1문장}

## Key Gap
- 기존 MA: {N}편 ({상세, 가장 최근 연도, 범위 한계})
- Consensus/Scholar Gateway 추가 확인: {결과 요약}
- medRxiv/bioRxiv preprint MA: {있음/없음}
- PROSPERO 등록 프로토콜: {있음 (CRD#) / 없음}
- {구체적 gap 설명 — 왜 새 MA가 필요한지}

## Professor's Authority
- {분야 관련 논문 수, 대표 논문 1-2편, 독보적 기여}
- {왜 이 교수님이 이 주제에 적합한지}

## Preliminary Search ({날짜})
### Search Strategy (PubMed)
```
{실제 사용한 PubMed 검색식 — E-utilities esearch query 그대로}
```
- Total hits: {N}편 (raw)
- DTA/outcome extractable (estimated): {N}편 (×0.15-0.30 discount)
- 기존 MA: {N}편 (narrow) / {N}편 (broad SR 포함)
- Consensus 검색 결과: {N}편 추가 발견 여부
- bioRxiv/medRxiv: {N}편 preprint

### Embase Search Strategy (Draft)
```
{Embase용 검색식 초안 — Emtree 용어 포함}
```
(실행 전 초안 — Embase 접속 시 검증 필요)

## Target Journal
| 순위 | 저널명 | IF | MA 게재 비율 | Turnaround | 비고 |
|------|--------|-----|-------------|-----------|------|
| 1차 | {저널} | {IF} | {높음/중간} | {개월} | {근거} |
| 2차 | {저널} | {IF} | {높음/중간} | {개월} | {근거} |

## Timeline (역산)
| 단계 | 예상 시점 | 선행 조건 |
|------|----------|----------|
| 교수님 제안 | {YYYY-MM} | {조건} |
| PROSPERO 등록 | +1주 | 교수님 승인 |
| 검색 완료 | +2주 | PROSPERO 등록 |
| 스크리닝 완료 | +3주 | 2nd reviewer 확보 |
| 데이터 추출 | +4주 | 스크리닝 합의 |
| 분석 + 초안 | +6주 | 데이터 lock |
| 교수님 리뷰 | +8주 | 초안 완성 |
| 투고 | +10주 | 교수님 승인 |

## Data Sources Used
- PubMed E-utilities: ✅ (esearch count + efetch metadata)
- Consensus MCP: ✅/❌
- Scholar Gateway: ✅/❌
- bioRxiv/medRxiv: ✅/❌
- PROSPERO: ✅
````

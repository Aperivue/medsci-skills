# Phase 1C — Hooks Warning Mode (Scope Lock, 2026-04-24)

확정 출처: `_retros/medsci-skills_master-plan_2026-04-24_v1.1.1.md` §8 Phase 1C, §10.4 검증, §9 마이그레이션 정책.

**HANDOFF 추정 정정**: HANDOFF.md의 "SSOT migration validator 실 프로젝트 smoke test" 표현은 v1.1.1 §8과 일치하지 않는다. SSOT migration validator는 Phase 0.5.4 작업이며, Phase 1C의 본 범위는 **Hooks 인프라 warning-mode 도입**이다. Migration smoke test는 §9의 "기존 프로젝트 마이그레이션 정책" 일부로 별도 트랙으로 처리한다.

---

## 1. 목적

진행 중 프로젝트(multiple in-flight manuscripts)를 깨뜨리지 않으면서 Phase 1A에서 만든 reference safety gate(`/verify-refs --strict`)를 hook 인프라로 승격한다. **신규 프로젝트만 enforce**, 기존은 warn-only + bypass 허용.

## 2. 산정 (v1.1.1 §8 그대로)

| ID | 작업 | 예상 |
|---|---|---|
| 1C.1 | Feature flag 구조 (`~/.claude/settings.json` hooks 섹션 + 프로젝트별 `.claude/settings.local.json` override) | 0.5h |
| 1C.2 | PreSave hook for verify-refs: warn mode default, enforce when `SSOT.yaml`이 프로젝트 루트에 존재 | 1h |
| 1C.3 | `~/.claude/rules/citation-safety.md` rule → hook 승격 스크립트 (`~/.claude/hooks/verify-refs-guard.sh` 확장 또는 신규) | 0.5h |
| 1C.4 | `--force-bypass` 환경변수 + `~/.local/log/verify-refs-bypass.log` audit 라인 | 0.5h |

총 2.5h, 1 session.

## 3. 진입 조건

- ✅ Phase 1A 완료 (커밋 `c04b27f`)
- ✅ Phase 1B-a 회귀 테스트 통과 (`tests/test_phase1a_gates.sh`, 본 세션)
- ⏳ Phase 1B-b Zotero dry-run — **선행 권장**(snapshot polling 안정성 미확인 시 hook이 false-negative 양산 위험). 단, 1B-b는 프로젝트 freeze 정책상 사용자 승인 필요 → **1C는 1B-b와 독립 진행 가능**(hook은 `verify-refs` CLI를 invoke할 뿐 Zotero polling 의존 X).
- ⏳ Phase 1B.1~1B.3 (SSOT.yaml template / numbers.yaml / `/render --check`) — **부분 의존**: 1C.2 enforce 트리거가 "SSOT.yaml 존재"이므로 1B.1 template 합의 후 진입이 깔끔. 미완 상태에서 1C 진입 시 `enforce_when_ssot_yaml_exists` 플래그만 두고 후속 PR로 트리거 활성화 가능.

## 4. 비-목표 (Phase 1C에서 하지 않음)

- 기존 프로젝트(legacy `project.yaml` 기반)의 hook enforce 적용 — §9 freeze 원칙.
- Numbers/render drift hook (Phase 2.1~2.2 의제).
- Hook의 모든 PostToolUse 위치 정착 — 본 phase는 PreSave 1지점만 (verify-refs guard).
- citation-safety.md rule 본문 자체의 폐기 — rule은 유지(LLM 컨텍스트), hook은 결정론적 차선.

## 5. 검증 (v1.1.1 §10.4 그대로)

1. 신규 프로젝트(`SSOT.yaml` 존재) `manuscript/*.docx` PreSave에 fabricated citation 포함 → hook exit 2.
2. 기존 프로젝트(`project.yaml`만 존재) 동일 케이스 → warn 라인 출력, save 허용, audit log 1줄 append.
3. `MEDSCI_VERIFY_REFS_BYPASS=1` 환경변수 set 시 신규 프로젝트도 warn 처리 + audit log에 `bypass=user` 표기.
4. Hook 미설치 환경(staged rollout 미적용 사용자)에서 회귀 영향 0 — settings.json 미변경 사용자에게 부작용 없어야.

추가(본 phase 신설): `tests/test_phase1c_hooks.sh` 스켈레톤으로 1~3 자동화. 1C.4 종료 시 작성.

## 6. 리스크 & 완화

| 리스크 | 완화 |
|---|---|
| 신규 프로젝트 정의 모호 — `SSOT.yaml` 존재가 트리거인데 마이그레이션 중인 프로젝트가 우연히 SSOT.yaml을 두면 의도치 않게 enforce | 1C.2 트리거를 `SSOT.yaml` + `qc/migration_complete` 마커 둘 다 요구로 강화. 마커는 Phase 0.5.4 마이그레이션 스크립트가 set. |
| Hook이 PubMed/CrossRef 네트워크 호출로 PreSave를 느리게 만듦(>3s) | `verify_refs.py`에 `--cache qc/reference_audit.json` 모드 추가하여 직전 audit이 60s 이내면 재사용. (별도 P-항목으로 FOLLOWUPS에 추가) |
| `--force-bypass` 남용 → safety gate 무력화 | audit log에 user/timestamp/ref-count 기록, monthly grep 정기 점검 (수동). |

## 7. 산출물

- `~/.claude/hooks/verify-refs-guard.sh` (확장 또는 분기)
- `~/.claude/settings.json` hooks 섹션 patch (settings 변경은 `update-config` 스킬 경유)
- `tests/test_phase1c_hooks.sh`
- `FOLLOWUPS.md` 갱신 (cache 모드 P7 추가 가능성)
- `HANDOFF.md` 다음 세션 진입점 갱신

## 8. 다음 세션 진입점 (1C 시작 시)

1. 본 문서 §3 진입조건 재확인 (1B.1 template 합의 여부 / 1B-b dry-run 결과)
2. 1C.1 → 1C.2 → 1C.4 → 1C.3 순서 권장 (flag → hook → bypass → rule 마이그레이션)
3. 진입 직전 commit hash + `tests/test_phase1a_gates.sh` 재실행으로 baseline 확인

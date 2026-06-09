# `/orchestrate --e2e` REPORT Template (Korean variant)

> Opt-in Korean variant. The default English template is `report_template.md`. Use this when the
> user prefers a Korean-language project report.

```markdown
# {project_id} Phase {N} 완료 보고

## 한 줄 요약
{무엇을 했고 결과 어땠는지 1문장}

## Frozen / Version status
- Source artifact: {manuscript/<id>/v_N_package/draft.md, mtime, sha256}
- Frozen version: v_{N} (freeze date YYYY-MM-DD, 회람 발송 시점)
- This run wrote to: v_{N+1}_package/ (분기 OK) | OR v_{N} 직접 (**violation — halt**)
- `manuscript-versioning.md` 룰 준수: ✅ / ❌

## Source artifacts checked
- {path1} — read at {timestamp}, sha256 {hash}
- {path2} — ...
- 누락된 expected input: {list, or "(none)"}
- Pre-flight result: PASS | HALT (reason: STATUS_MISSING / FROZEN_VIOLATION / REQUIRED_INPUT_MISSING / DEPENDENCY_MISS)

## 변경 파일 (priority 순)
- {path} — {1줄 변경 요약}
- ...
- (없으면 "(none)")

## Changed claims
- {Methods §X에서 sample size N=68 → N=70 (CSV row count 재집계)}
- {Discussion에서 "primary outcome" → "co-primary outcome" 표현}
- (없으면 "no claim-level changes")

## 검토 포인트 (사용자 우선순위 순)
1. {가장 중요 — 보통 수치·인용·논리 검증 포인트}
2. {차순위}
3. {그 다음}

## 환각 게이트 결과
- citation_safety: PASS / FAIL ({n} refs verified, first-author cross-check applied)
- numerical_safety: PASS / FAIL ([VERIFY-CSV] 잔존 {n}건)
- dictionary_first: PASS / N/A (observational/cohort 컨텍스트만 적용)
- reporting_compliance: PASS / PARTIAL / FAIL ({guideline})

## QC artifact links
- `qc/reference_audit.json` — verify-refs 결과
- `qc/self_review.md` — self-review JSON 블록
- `qc/reporting_checklist.md` — check-reporting 결과
- `qc/xref_audit.json` — manage-refs cross-reference QC
- `qc/_pipeline_log.md` — Dialogue node defaults + halt reasons

## Human-only missing fields
이 항목은 사용자가 직접 채워야 함 (자율 작성 영구 금지):
- Funding grant IDs: ___
- Senior mentor 회람 답신 반영: ___
- Recommended reviewers (또는 "없음"): ___
- Cover letter 인사말 / corresponding 서명: ___
- (해당 없으면 "(none)")

## Tier-3 차단 항목
이 작업들은 `--e2e` 자동 진입 영구 금지. 시도 발생 시 halt + 아래 기록.

**Hook으로 차단 확인 (`~/.claude/hooks/tier3-confirm.sh`)**:
- `gws gmail +send/+reply`
- YouTube upload

**Prompt / skill guard만 (hook 미적용 — Worker prompt가 막음)**:
- `git push`, `gh pr create`
- MCP Gmail send, MCP Calendar send
- MCP GitHub create-pr
- `/sync-submission build` 외부 발행 path
- Phase 8 (submission docx 자동 빌드 / 투고)
- senior mentor 자동 회신

이번 run에서 시도 감지: `tier3_pending: <command or "(none)">`

## 다음 액션
- [ ] APPROVE → 다음 phase 진행
- [ ] REJECT (사유: ___)
- [ ] PARTIAL (수정사항: ___)

## Next safe command
다음 phase 위임 명령 (사용자가 그대로 복사):
`/orchestrate "<id> Phase {N+1} 끝까지" --e2e`

## Pipeline log
{qc/_pipeline_log.md 핵심 5줄 요약 — Dialogue node defaults, skill invocations, halt 사유}
```

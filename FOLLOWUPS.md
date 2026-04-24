# medsci-skills Follow-ups

장기 작업 큐. 기록 시점 + 우선순위 표시. 완료 시 줄 삭제 또는 `~~취소선~~`.

## 2026-04-24 — Reference hallucination prevention follow-ups

원본 인계 (SkullFx Paper 2 세션) 의 6항목 중 P0–P1은 본 세션에서 구현 완료
(`/verify-refs` 신규 + PostToolUse guard hook + `~/.claude/rules/citation-safety.md`
업데이트). 잔여 4건:

| ID | 우선순위 | 항목 | 변경 포인트 |
|---|---|---|---|
| P2 | 🟡 Med | `/search-lit` BibTeX 출력에 `verified: true/false` flag 추가 | `skills/search-lit/SKILL.md` Phase 4 + `references/parse_pubmed.py` bibtex mode. 환각 흔적 자동 표시. |
| P3 | 🟡 Med | `/self-review` 체크리스트에 "Reference hallucination scan" 추가 | `skills/self-review/SKILL.md`. 내부적으로 `/verify-refs` 호출. |
| P4 | 🟢 Low | `/manage-project init` Zotero collection 자동 생성 옵션 | `skills/manage-project/scripts/init.py` (또는 SKILL.md 워크플로우). |
| P5 | ✅ Done | 글로벌 룰 `~/.claude/rules/citation-safety.md` 보강 | 본 세션에서 `/verify-refs` 라인 + hook 라인 추가 완료. |
| P6 | ✅ Done | `verify_pubmed_pmid` PubMed esummary stub-error leak | `skills/verify-refs/scripts/verify_refs.py` 수정 — `item.get("error")` 검사 후 FABRICATED 반환. Phase 1B-a fixture(`refs_seed_phase1b.bib`)로 회귀 보장. |
| P7 | 🟡 Med | `/lit-sync` Phase 2.5 precondition assertion 부재 | `skills/lit-sync/SKILL.md` Step 2.5.1 보강 — `~/Zotero/better-bibtex/read-only.json`이 빈 list거나 target `refs.bib` 부재 시 polling 대신 setup 안내로 early-exit. Phase 1B-b dry-run에서 발견 (findings: `~/.local/cache/phase1b_b_dryrun/findings.md`). |
| P8 | 🟢 Low | `/lit-sync` Phase 2.5 polling 회귀 스크립트 추출 | `~/.local/cache/phase1b_b_dryrun/poll.sh` + 4-test 시나리오 → `skills/lit-sync/tests/test_poll_logic.sh`. 본 세션 isolation dry-run 4/4 PASS. |
| P9 | 🟡 Med | `verify_refs.py` cache 모드 (`--cache qc/reference_audit.json`, 60s TTL) | Phase 1C enforce 경로에서 PreSave hook latency >3s 대비. 직전 audit이 같은 bib hash + 60s 이내면 재검증 생략. scope doc §6 리스크 완화 근거. |

## 작성 규약

- 새 항목은 위 표에 행 추가, 우선순위 (🔴 High / 🟡 Med / 🟢 Low) + 1줄 변경 포인트.
- 완료 시 `✅ Done` 표시 또는 줄 삭제.
- 큰 항목은 별도 HANDOFF.md를 해당 프로젝트 루트에 두고 여기서 1줄 포인터만 유지.

# medsci-skills Follow-ups

장기 작업 큐. 기록 시점 + 우선순위 표시. 완료 시 줄 삭제 또는 `~~취소선~~`.

## 2026-04-24 — Reference hallucination prevention follow-ups

원본 인계 (SkullFx Paper 2 세션) 의 6항목 중 P0–P1은 본 세션에서 구현 완료
(`/verify-refs` 신규 + PostToolUse guard hook + `~/.claude/rules/citation-safety.md`
업데이트). 잔여 4건:

| ID | 우선순위 | 항목 | 변경 포인트 |
|---|---|---|---|
| P2 | ✅ Done | `/search-lit` BibTeX 출력에 `verified: true/false` flag 추가 | 2026-04-24: `skills/search-lit/SKILL.md` Phase 4 이미 스펙 문서화(`verified`/`verified_by`/`verified_on` 3필드, true/false/manual enum). `references/parse_pubmed.py` `generate_bibtex`에 구현 — `verified = bool(pmid)`, `verified_by = pubmed(+crossref)`, `verified_on = ISO date`. Phase 1A/1C regression 16/16 PASS. |
| P3 | ✅ Done | `/self-review` 체크리스트에 "Reference hallucination scan" 추가 | 2026-04-24: `skills/self-review/SKILL.md`에 Phase 2.5c 추가 — `/verify-refs` 호출 + `qc/reference_audit.json` 소비, `FABRICATED`→P0, `[@NEW:]` placeholder drift 검사 포함. Anti-Hallucination 섹션 링크. |
| P4 | 🟢 Low | `/manage-project init` Zotero collection 자동 생성 옵션 | `skills/manage-project/scripts/init.py` (또는 SKILL.md 워크플로우). |
| P5 | ✅ Done | 글로벌 룰 `~/.claude/rules/citation-safety.md` 보강 | 본 세션에서 `/verify-refs` 라인 + hook 라인 추가 완료. |
| P6 | ✅ Done | `verify_pubmed_pmid` PubMed esummary stub-error leak | `skills/verify-refs/scripts/verify_refs.py` 수정 — `item.get("error")` 검사 후 FABRICATED 반환. Phase 1B-a fixture(`refs_seed_phase1b.bib`)로 회귀 보장. |
| P7 | ✅ Done | `/lit-sync` Phase 2.5 precondition assertion 부재 | 2026-04-24: `skills/lit-sync/SKILL.md`에 Step 2.5.1b 추가 — `read-only.json` 빈 list or target refs.bib 부재 시 polling 스킵하고 setup 안내로 early-exit. Step 2.5.3 JSON에 `reason: "precondition:<which>"` 기록. |
| P8 | 🟢 Low | `/lit-sync` Phase 2.5 polling 회귀 스크립트 추출 | `~/.local/cache/phase1b_b_dryrun/poll.sh` + 4-test 시나리오 → `skills/lit-sync/tests/test_poll_logic.sh`. 본 세션 isolation dry-run 4/4 PASS. |
| P9 | 🟡 Med | `verify_refs.py` cache 모드 (`--cache qc/reference_audit.json`, 60s TTL) | Phase 1C enforce 경로에서 PreSave hook latency >3s 대비. 직전 audit이 같은 bib hash + 60s 이내면 재검증 생략. scope doc §6 리스크 완화 근거. |
| P10 | ✅ Done | `/meta-analysis` Failure Modes 자동화 스크립트 4종 | 2026-04-24: 4종 완료 — `scripts/prisma_5way_consistency.py` (DI-6 YAML SSOT + per-surface `require` 키), `scripts/extraction_consensus_log_init.py` (DI-1 10-컬럼 스캐폴드), `scripts/tag_cleanup_gate.sh` (DI-8 rg/grep 게이트), `scripts/verify_package_integrity.py` (SPD SHA-256 manifest, 저널 편집 허용 파일 제외). 스모크 테스트 PASS/FAIL + drift 케이스 전수 확인. |

## 작성 규약

- 새 항목은 위 표에 행 추가, 우선순위 (🔴 High / 🟡 Med / 🟢 Low) + 1줄 변경 포인트.
- 완료 시 `✅ Done` 표시 또는 줄 삭제.
- 큰 항목은 별도 HANDOFF.md를 해당 프로젝트 루트에 두고 여기서 1줄 포인터만 유지.

# RESUME — medsci-skills Phase 1A Reference Safety MVP (2026-04-24)

**⚠️ 이어서 작업 지시. "마무리할까요?" 금지. `## 즉시 실행` 첫 항목부터.**
**작업 디렉토리**: `/Users/eugene/workspace/medsci-skills`

---

## 즉시 실행

### Phase 0.5 산출물 커밋 (먼저)

변경 범위가 커서 선별 커밋 권장. 제안 분할:
1. `docs/{ssot_schema_v1,skill_yml_schema_v2,zotero_policy,artifact_contract}.md` + `capabilities.yml` — 계약 문서
2. `scripts/{validate_project_contract,validate_skill_contracts,migrate_project_to_ssot}.py` — validator 구현
3. `tests/fixtures/{legacy_project,ssot_project}/` — 회귀 fixture
4. `_retros/medsci-skills_phase0_decisions_2026-04-24.md` (별도 repo)

### Phase 1A Reference Safety MVP (2 세션, 5~6h)

v1.1.1 §8 Phase 1A 순서:
1. **1A.1** `/lit-sync` Zotero Better BibTeX auto-export path 확정 + `refs.bib` snapshot 갱신 플로우 문서화 — 1.5h
2. **1A.2** `/verify-refs` 방향 전환: write 로직 제거, `qc/reference_audit.json` 고정 output, PubMed/CrossRef audit — 2h
3. **1A.3** `/search-lit` BibTeX에 `verified: true/false` flag (FOLLOWUPS P2) — 1h
4. **1A.4** `/write-paper` citekey-only 진입 gate + `[@NEW:topic]` placeholder 규약 — 1h
5. **1A.5** Manual CLI 체크포인트 가이드 (`verify-refs --strict` 제출 전 수동 실행) — 0.5h

**Payoff**: SkullFx Ref 6 / CK-1 Ref 6 / MA-1 PRISMA citation hallucination manual gate 수준 차단.

**중단 조건**: `/verify-refs` write 제거가 기존 프로젝트 파이프라인 깨뜨림 (legacy flag 필요), Zotero Better BibTeX auto-export 경로 블로커.

---

## 블로커 / 대기

- 진행 프로젝트(SkullFx P2 RYAI 직전 / MA-1 academic_radiology 대기 / CK-1 Chest) — Phase 1A는 신규 프로젝트만 enforce, 기존 프로젝트는 manual opt-in
- FOLLOWUPS P2 (search-lit verified flag) → 1A.3에서 흡수

---

## 주의사항

- **D-결정 (2026-04-24)**: D-1 Pandoc markdown / D-2 Zotero owner-only / D-3 agent 3종 유지 / D-4 프로젝트 특화 스킬 deprecate / D-5 3-file 메모리 유지 / D-6 pragmatic submission / D-7 soft cap 150k / D-8 session-end 1줄
- **`/verify-refs` 방향 전환 (1A.2)**: `qc/reference_audit.json`만 write, 나머지 write 로직(references/verified_references.tsv 등) 제거. `artifact_contract.md` v1.1.1 roster 기준.
- **Sole writer 원칙**: `manuscript/_src/refs.bib` 는 `/lit-sync`만 write. `/search-lit`은 `references/library.bib` 후보군만.
- **Legacy skill.yml 보존**: 12개 v1 skill.yml은 2026-07-24까지 WARN만. 강제 마이그레이션 금지.
- **진행 프로젝트 보호**: SkullFx/MA-1/CK-1 freeze 유지. Phase 1A 도구는 신규 프로젝트 자동 enforce + 기존은 manual.

---

## 참조

- v1.1.1 계획서: `/Users/eugene/workspace/_retros/medsci-skills_master-plan_2026-04-24_v1.1.1.md`
- D-결정 기록: `/Users/eugene/workspace/_retros/medsci-skills_phase0_decisions_2026-04-24.md`
- Contract 문서: `docs/{ssot_schema_v1,skill_yml_schema_v2,zotero_policy,artifact_contract}.md`
- Validator: `scripts/{validate_project_contract,validate_skill_contracts,migrate_project_to_ssot}.py`
- Fixtures: `tests/fixtures/{legacy_project,ssot_project}/`

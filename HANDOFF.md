# RESUME — medsci-skills 공개 노출 작업 (2026-04-24)

**⚠️ 이어서 작업 지시. "마무리할까요?" 금지. `## 즉시 실행` 첫 항목부터.**
**작업 디렉토리**: `/Users/eugene/workspace/medsci-skills`

---

## 즉시 실행

직전 세션: FOLLOWUPS P2~P8/P10 + MA skill-level 통합 완료, origin 동기화 완료 (0 ahead). 코드 업데이트는 끝났으나 **공개 노출이 미반영** — 다음 3단계를 순서대로 진행.

1. **README 업데이트 — 최근 대규모 업데이트 반영**
   - 추가할 짧은 섹션 2개 (각 5~10줄):
     - **Reference Safety (Phase 1)**: SSOT.yaml + migration marker + hook mode (`auto`/`warn`/`enforce`). `MEDSCI_VERIFY_REFS_MODE` env, `qc/reference_audit.json` sole-writer 정책.
     - **Meta-Analysis Failure Modes**: MA01~03 empirical references (DI / RO / SPD / PSR) + 4종 자동화 스크립트 훅 (DI-1/6/8, SPD).
   - 기타: P4 Zotero auto-collection, P2 bibtex `verified=true` 플래그는 기존 스킬 표 엔트리에 한 줄 덧붙이기.
   - 절대경로 금지, 상대경로 + `${CLAUDE_SKILL_DIR}` 사용.

2. **GitHub Release cut — classroom ZIP**
   - `python3 scripts/build_classroom_release.py` 실행 → `medsci-skills-classroom-{macos,windows}.zip` 생성.
   - `gh release create vX.Y.Z --title ... --notes ...` (vX.Y.Z는 최근 태그 확인 후 semver bump).
   - README L248/254의 `releases/latest/download/...` 링크가 실제 다운로드 가능한지 검증.
   - Release notes에는 P10 스크립트, Phase 1A/1B/1C, classroom 번들 3개 축 요약.

3. **홈페이지 반영 — 별도 repo**
   - `aperivue-brain` (또는 `haejinlim.art` 웹 아님 — Aperivue 사업 페이지) 경로 확인 후 소식 섹션/블로그 포스트 초안.
   - 공개 repo 링크 + demo 3종 스크린샷 재활용.
   - 어느 채널 (aperivue.com/blog vs /research) 게시할지 사용자 확인.

**중단 조건**: 공저자 신규 초안 수신 → `/verify-refs` 우선. P9 트리거 발생 (새 SSOT 프로젝트 hook latency >3s) → P9 착수.

---

## 블로커 / 대기

- 진행 프로젝트(SkullFx P2 / MA-1 / CK-1) freeze 유지. auto 모드 = warn-only.
- P9 선착수 조건 미충족 (실측 latency 없음).

---

## 주의사항

- **커밋 게이트**: pre-commit hook이 `validate_skills.sh` 자동 실행. README 수정 시에도 한번 더 확인.
- **Precedent blocklist 엄수**: README/릴리스 노트에 MA01~03 / author-year / 내부 파일경로 / 에러코드 **노출 금지**. 추상화된 레퍼런스(`DI-1`, `SPD`) 수준까지만.
- **Zotero 테스트**: `scripts/init_project.py --zotero-collection` 테스트 시 실 API 호출됨. `env -u ZOTERO_API_KEY -u ZOTERO_LIBRARY_ID` 또는 fake 값.
- **Phase 1A/1C 계약 불변**:
  - `/verify-refs`는 `qc/reference_audit.json` sole-writer.
  - `auto` 모드 = `SSOT.yaml` + `qc/migration_complete` 둘 다 있어야 enforce.
  - 회귀: `tests/test_phase1a_gates.sh` (4), `tests/test_phase1c_hooks.sh` (12).
- **SKILL.md**: 절대경로(`/Users/eugene/...`) 금지 → 상대경로 + `${CLAUDE_SKILL_DIR}`. Legacy skill.yml WARN-only (2026-07-24 sunset).
- **Release tagging**: semver. 최근 변화량(classroom + P10 + Phase 1A~1C) 감안해 minor bump 이상 권장.

---

## 참조

- FOLLOWUPS: `FOLLOWUPS.md`
- Release builder: `scripts/build_classroom_release.py`
- Classroom docs: `docs/classroom_distribution_plan.md`, `docs/classroom_materials.md`, `README_FIRST.md`
- SSOT schema: `docs/ssot_schema_v1.md`
- 1C scope: `docs/phase1c_scope.md`
- MA failure refs: `skills/meta-analysis/references/{data_integrity_checklist,review_orchestration,submission_package_drift,post_submission_release_ops}.md`
- P10 scripts: `scripts/{prisma_5way_consistency,extraction_consensus_log_init,tag_cleanup_gate,verify_package_integrity}.*`

# RESUME — medsci-skills (2026-05-01 integration cleanup)

**⚠️ 이어서 작업 지시. "마무리할까요?" 금지. `## 즉시 실행` 첫 항목부터.**
**작업 디렉토리**: `/Users/eugene/workspace/medsci-skills`

---

## 즉시 실행

직전 세션 integration cleanup 완료. 단일 PR `feat/backbone-auto-proposal-clean → main` 머지 + origin 정리 + 외부 컨트리뷰터 답장 발송 단계 진행:

1. **PR 머지 확인 (HIGH)**
   - PR URL: GitHub web에서 확인. 머지 완료 여부 먼저 점검.
   - 미머지면 reviewer 응답 처리 후 머지.
   - 머지 후 즉시 다음 단계.

2. **Origin 브랜치 정리 (HIGH, 사용자 승인 필요)**
   - `git push origin --delete feat/write-paper-backbone-auto-proposal` (origin 891dd4a — clean 브랜치가 superset)
   - 로컬 `git branch -D feat/write-paper-backbone-auto-proposal` (3377041)
   - **사용자 명시 승인 후만 실행** — 파괴적 동작.

3. **Phase 10 — Ibad Mursalov 답장 발송**
   - 본문 `/Users/eugene/.local/cache/medsci-replies/reply_ibad_backbone.txt`의 `<ISSUE_OR_PR_URL>` 치환.
   - `python3 ~/.local/bin/gws-draft.py --to 'ibadmursalov@gmail.com' --subject 'Re: Skill finds a backbone article but does not use it automatically /write-paper' --body-file <path>` (서명 자동 첨부).
   - 사용자 검토 → 승인 시 발송.

4. **CHANGELOG `[Unreleased]` → release 승격 (LOW, post-merge)**
   - PR 머지 시 `[Unreleased]` → `[v0.x.y] - 2026-05-01`로 변경 (별도 PR 또는 머지 commit에 포함).

---

## 블로커 / 대기

- 없음. PR이 아직 안 만들어졌다면 `gh pr create` (사용자 권한). 머지/푸시는 사용자 명시 승인 후.

---

## 주의사항

- **HANDOFF 자체는 untracked**: 이번 통합에 포함됨 (commit 시 함께). 다음 세션 시작 시 SessionStart hook이 이 파일을 자동 로드.
- **render-pdf-doc Step 4 회귀 테스트 미수행**: MeducAI Paper 2 anchor `Paper2_QA_Anchor_KO.md`로의 회귀 테스트는 외부 manuscript 위치 의존이므로 별도 세션. 현재 skill은 smoke test만 통과.
- **post-submission-harvest 적용 누적**: RFA-Adjunct ER submission이 milestone에 도달하면 `~/.claude/rules/post-submission-harvest.md` 절차로 추가 룰 승격. 별도 trigger.
- **글로벌 룰 영역 (`~/.claude/rules/`)**: 이번 cleanup에서 repo 외부 룰은 변경 안 함. agent-skill-routing.md / manuscript-references.md는 직전 세션에서 갱신 완료. 새 매트릭스 `docs/rule-application-map.md`는 인덱스만.
- **40개 스킬 중 13개에만 skill.yml 존재**: render-pdf-doc + calc-sample-size 추가로 14개. 나머지 26개의 skill.yml v1 contract 작성은 follow-up. `feedback_reference_split_threshold.md` 패턴 따라 우선순위 정하기.

---

## 참조

- 직전 작업 plan: `~/.claude/plans/medsci-nested-cosmos.md` (Phase 1–10 전체)
- 통합 commit: 직전 push (clean 브랜치 70446c0 위에 누적 단일 commit)
- CHANGELOG `[Unreleased]` 첫 섹션 "Integration cleanup" — PR 본문에 그대로 사용 가능
- 외부 컨트리뷰터 thread: 사용자 inbox, "Skill finds a backbone article but does not use it automatically /write-paper" (ibadmursalov@gmail.com, 2026-05-01 14:27)
- 신규 dialogue nodes: `skills/orchestrate/references/dialogue_nodes.md` N10/N11
- IMPROVEMENT_QUEUE: `IMPROVEMENT_QUEUE.md` (#2 #3 미처리, 별도 cycle)
- FOLLOWUPS: `FOLLOWUPS.md`

# Global Rule × Skill Application Map

**Purpose**: medsci-skills repo는 자체 룰을 들고 있지 않음. Manuscript writing/QC에 적용되는 글로벌 룰들은 `~/.claude/rules/` (사용자 글로벌 영역, repo 외부)에 거주. 이 표는 어느 룰이 어느 스킬의 어느 phase에서 trigger되는지를 한 페이지로 매핑한다.

**Status**: 2026-05-01 신설. 룰 신규 추가 시 이 표도 갱신할 것.

**Authoritative source**: `~/.claude/rules/` (글로벌). 이 매트릭스는 인덱스. 룰 본문은 사용자의 `.claude/rules/` 폴더에서만 편집.

## Application Matrix

| Global rule (`~/.claude/rules/...`) | Trigger skill / phase | Severity |
|---|---|---|
| `manuscript-style-classical.md` | `/write-paper` Phase 7.1 (classical-style QC), `/self-review`, `/humanize` | ENFORCED |
| `manuscript-references.md` | `/write-paper` Phase 7.6 (delegates to `/manage-refs`), `/manage-refs` entry | ENFORCED |
| `senior-mentor-circulation.md` | `/write-paper` post-Phase 7.7 (circulation round entry), `/revise` entry | ADVISORY (until first co-author docx attached → ENFORCED) |
| `ai-drafted-document-policy.md` | `/meta-analysis` Phase 4.0 gate, `/write-paper` Phase 0 (when senior mentor attaches AI-draft), `/revise` (R1 attachments) | ENFORCED |
| `citation-safety.md` | `/verify-refs --strict` (first-author cross-check), `/manage-refs` Gate 1 | ENFORCED |
| `numerical-safety.md` | `/analyze-stats` Phase 2.5, `/write-paper` Phase 7.1, `/revise` Step 2.5 (`[VERIFY-CSV]` tagging), `/meta-analysis`, `/self-review` | ENFORCED |
| `data-integrity.md` | `/analyze-stats`, `/clean-data`, `/define-variables` Tier 0, `/meta-analysis` extraction phases | ENFORCED |
| `dictionary-first.md` | `/define-variables` Tier 0 (data-dictionary citation), `/replicate-study`, `/cross-national` | ENFORCED for DB-backed observational research |
| `pptx-mac-compatibility.md` | `/present-paper` Phase 3 Mode A (PPTX generation/edit) | ENFORCED |
| `journal-ai-image-policies.md` | `/make-figures` (figure generation entry); also `/write-paper` cover-letter-time AI disclosure | ENFORCED for JACC family / NEJM (default to non-AI assets) |
| `zotero-workflow.md` | `/lit-sync` setup + ongoing, `/manage-refs` Workflow B (CWYW) | ENFORCED for projects using Zotero |
| `manuscript-references.md` (Phase 1↔2↔3 transition) | `/manage-refs` decision tree (Workflow A vs B); orchestrate node N10 | ENFORCED at circulation entry |
| `agent-skill-routing.md` | `/orchestrate` routing classification | ENFORCED (drift between routing table + this rule = bug) |
| `domain-routing.md` | `/orchestrate` cross-domain ambiguity, `/research`, `/biz`, `/imagine` | ENFORCED |
| `model-routing.md` | session-level model selection (opus vs sonnet) | ADVISORY |
| `email-drafts.md` | when invoking `gws-draft.py` (e.g., `/manage-project` follow-ups, contributor replies) | ENFORCED |
| `terminal-ux.md` | all skills' user-facing output (absolute paths, alias usage, command length) | ADVISORY |
| `work-directory.md` | session start, `/intake-project`, `/manage-project init` | ENFORCED |
| `language.md` | all skills' Communication Rules section | ENFORCED |
| `user-profile.md` | `/write-paper` author block generation, `/find-journal` profile matching, all CV-touching skills | ENFORCED — never write outdated affiliation |
| `post-submission-harvest.md` | `/handoff`, `/manage-project` at submission/acceptance milestone | ENFORCED at milestone trigger |
| `session-end-checklist.md` + `handoff-protocol.md` | `/handoff` (session end orchestration) | ENFORCED |
| `institutional-form-fill.md` | `/fill-protocol` (skill selection + template detection) | ENFORCED |
| `icmje-coi-fill.md` | `/fill-icmje-coi` (entry, seed selection, batch generation) | ENFORCED |
| `medical-community-kakao.md` | `/biz` 또는 `/research` 커뮤니티 운영 요청 | ADVISORY |
| `codex-routing.md` | `/codex:rescue`, `/codex:review`, `/codex:adversarial-review` 진입 | ENFORCED |
| `writing-style.md` | `/write-paper`, `/humanize`, critic agent (general 18-pattern checklist) | ENFORCED |

## How to use

1. **새 룰 추가 시**: `~/.claude/rules/<rule>.md` 작성 후 이 표에 1줄 추가 (어느 스킬·phase에서 trigger되는지 + Severity). 룰 본문은 repo 외부, 인덱스만 repo 내부.
2. **스킬 신규/수정 시**: 해당 스킬이 어떤 글로벌 룰을 필요로 하는지 확인 → SKILL.md "관련 룰" 섹션과 이 표 양쪽 갱신.
3. **드리프트 점검**: `~/.claude/rules/agent-skill-routing.md`의 cross-cutting 룰 표와 이 매트릭스가 정합한지 분기마다 확인.

## 룰 본문 위치

이 repo는 룰 본문을 저장하지 않는다 (사용자 영역). 본문은 `~/.claude/rules/<rule_name>.md`. 아래 명령으로 한 번에 검토:

```bash
ls ~/.claude/rules/
```

## 관련

- `~/.claude/rules/agent-skill-routing.md` — 스킬 라우팅 표 (이 매트릭스의 상위 룰)
- `skills/orchestrate/SKILL.md` — 라우팅 실제 적용
- `skills/orchestrate/references/dialogue_nodes.md` — N1–N11 fork 노드

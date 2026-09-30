# Host Compatibility

How MedSci Skills installs and runs across agent hosts, what is verified, and what is not.

The guiding rule: **a cell is `VERIFIED` only with a source URL and retrieval date. Everything else is `UNVERIFIED`** — never "target support". MedSci Skills will not claim a host works until install and discovery are confirmed against that host's official documentation.

## Canonical source

The single source of truth for every skill is `skills/<name>/SKILL.md`. The repository follows the [Agent Skills open standard](https://agentskills.io/specification): a skill is a directory containing a `SKILL.md` (YAML frontmatter + Markdown body) plus optional `scripts/`, `references/`, and `assets/` subdirectories, loaded by progressive disclosure (name + description at startup; body on activation; bundled files on demand). The installer copies these directories verbatim into host skill folders — there is no per-host fork of any skill.

## Host matrix

Install paths below were read from each host's official documentation on **2026-09-30** (first read 2026-06-03). Skill counts and conventions drift; re-verify at the cited source.

| Host | Status | Discovered install path(s) | Source (retrieved 2026-09-30) |
|---|---|---|---|
| **Claude Code** | **VERIFIED** | Personal `~/.claude/skills/<name>/SKILL.md`; project `.claude/skills/<name>/SKILL.md` | https://code.claude.com/docs/en/skills |
| **OpenAI Codex** | **VERIFIED** | Personal `~/.agents/skills/`; repo `.agents/skills/` (scanned cwd→repo root); system `/etc/codex/skills`; config `~/.codex/config.toml` (`[[skills.config]]`). Codex also still reads `~/.codex/skills/`, which its source marks as a deprecated location kept for backward compatibility | https://developers.openai.com/codex/skills |
| **Cursor** | **VERIFIED** | Native `~/.cursor/skills/`, `.cursor/skills/`, `~/.agents/skills/`, `.agents/skills/`; also reads `~/.claude/skills/`, `.claude/skills/`, `~/.codex/skills/`, `.codex/skills/` for compatibility | https://cursor.com/docs/skills |
| **GitHub Copilot** | **VERIFIED** | Project `.github/skills/`, `.claude/skills/`, `.agents/skills/`; personal `~/.copilot/skills/`, `~/.agents/skills/`. Copilot in **VS Code** also reads personal `~/.claude/skills/` | https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills · https://code.visualstudio.com/docs/copilot/customization/agent-skills |
| **Generic Agent Skills standard** | **partial — see [Frontmatter](#claude-specific-assumptions-inventory)** | `<root>/<name>/SKILL.md`; the spec's `skills-ref validate ./<name>` rejects the 14 SKILL.md files that carry a Claude Code field | https://agentskills.io/specification · https://github.com/agentskills/agentskills |
| **OpenClaw** | **UNVERIFIED — roadmap** | Not confirmed against official docs; no install code | — |
| **Hermes** | **UNVERIFIED — roadmap** | Not confirmed against official docs; no install code | — |

### What this means in practice

The verified paths converge on two directories, which is why the existing installer needs no per-host rewrite:

- **`~/.claude/skills/`** (+ project `.claude/skills/`) is read by **Claude Code** (native), **Cursor** (compatibility), and **Copilot in VS Code**.
- **`~/.agents/skills/`** (+ project `.agents/skills/`) is read by **Codex** (native), **Cursor** (native), and **GitHub Copilot**.

`installers/install.py` already installs to both (`--target claude` → `~/.claude/skills`, `--target codex` → `~/.agents/skills`). The `codex → ~/.agents/skills` mapping is **verified correct** against the Codex docs above. The installer's optional `.cursor/rules/medsci-skills.mdc` project rule is now **legacy**: Cursor reads `~/.claude/skills` and `~/.agents/skills` directly, so a separate Cursor install is no longer required for skill discovery (the rule remains a convenience for steering, not a requirement).

OpenClaw and Hermes stay on the roadmap with no install code or support claim until their official conventions are confirmed.

## Claude-specific assumptions inventory

These are points where the repository or a workflow assumes a Claude Code environment. The skill **packages** are portable; some **workflows** are not.

**Frontmatter (spec-clean except 14 files).** Each `SKILL.md` uses `name`, `description` and `metadata.triggers`, all within the open standard: `triggers` sits under the standard's `metadata` map. Two Claude Code fields remain, and they are **not** in the standard:

- `model` — in the six skills that name a model (`opus` in five, `sonnet` in one). A skill with no `model` runs on the session's model.
- `disable-model-invocation: true` — in the eight v6 alias stubs, so that Claude Code never picks an old name on its own. Codex does not read this field and lists the aliases to its model; see [MIGRATION-v6.md](../MIGRATION-v6.md#renamed-skills).

What happens to a field outside the standard depends on who reads the file. Claude Code ignores a field it does not recognise, and Codex reads only `name`, `description` and `metadata.short-description`. Stricter consumers reject it: the spec's reference validator (`skills-ref validate`) and a claude.ai skill upload (as well as the Skills API and `package_skill.py`) accept only `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools`, and fail on anything else with `Unexpected key(s) in SKILL.md frontmatter`. Those 14 files have to lose the field before they can be uploaded to claude.ai. The former `tools` field was removed in v6 because hosts ignored it; it was not converted to the standard's `allowed-tools`, which pre-approves tools rather than listing them.

**Install / config paths.**
- `~/.claude/skills`, `~/.agents/skills` — install destinations (both verified above).
- `~/.claude/rules`, `~/.claude/hooks` — **host-local user configuration**, not part of any skill package and not installed by this repo. Behaviors that depend on user rules or hooks do not transfer to other hosts.

**Runtime references inside skills.**
- `${CLAUDE_SKILL_DIR}` — written about 460 times across the skills (about 400 of them in 46 `SKILL.md` files) to locate bundled `scripts/`/`references/`. It is a **text substitution, not an environment variable**: Claude Code replaces it with the folder that holds the `SKILL.md` before the model reads the file. Codex, Cursor and Copilot document no such substitution (Cursor: "reference scripts … using relative paths from the skill root"), so on those hosts the agent has to read `${CLAUDE_SKILL_DIR}` as "this skill's folder" itself; a command copied as written would expand the unset variable to an empty string. A skill that calls another skill's script uses `${CLAUDE_SKILL_DIR}/../<skill>/`, which resolves the same way in a repository clone and in an installed skills directory, provided that other skill is installed too.
- **MCP tool names** — some skills reference Claude MCP servers in their bodies (for example PubMed / CrossRef / Zotero / Google Drive, named like `mcp__claude_ai_*` or `mcp__zotero__*`). These are **not declared in the frontmatter** and are **host-specific**: off-Claude hosts without the same MCP servers fall back to the skills' deterministic scripts or to manual workflow.

## Skill portability vs full-workflow portability

- **Skill packaging is portable.** Every `SKILL.md` + bundled `scripts/`/`references/` installs into the verified hosts above without modification. The exceptions are the stricter consumers named under [Frontmatter](#claude-specific-assumptions-inventory): 14 files carry a Claude Code field that `skills-ref` and claude.ai upload reject.
- **Full-workflow portability varies.** A workflow degrades off-Claude when it depends on (a) a Claude MCP server for live data (citation verification, Zotero sync, Drive I/O), (b) host-local `~/.claude/rules` / `~/.claude/hooks`, or (c) the `${CLAUDE_SKILL_DIR}` substitution, which only Claude Code performs.

Skills whose value is mostly **bundled deterministic scripts + reference material** (for example reporting-checklist audits, figure generation, sample-size calculation, statistical code) port most cleanly. Skills whose value depends on **live MCP retrieval** (literature search, reference verification, Zotero/Drive sync) need those servers configured on the target host, or fall back to manual steps. Per-skill specifics are recorded in each skill's Quality Card (`evidence_surface` and `known_limitations`).

---

*Part of [MedSci Skills](../README.md). See also [`docs/competitive_positioning.md`](competitive_positioning.md) and the per-skill reference in [`docs/skills/`](skills/). Install instructions are in the [main README](../README.md#installation).*

# Host Compatibility

How MedSci Skills installs and runs across agent hosts, what is verified, and what is not.

The guiding rule: **a cell is `VERIFIED` only with a source URL and retrieval date. Everything else is `UNVERIFIED`** — never "target support". MedSci Skills will not claim a host works until install and discovery are confirmed against that host's official documentation.

## Canonical source

The single source of truth for every skill is `skills/<name>/SKILL.md`. The repository follows the [Agent Skills open standard](https://agentskills.io/specification): a skill is a directory containing a `SKILL.md` (YAML frontmatter + Markdown body) plus optional `scripts/`, `references/`, and `assets/` subdirectories, loaded by progressive disclosure (name + description at startup; body on activation; bundled files on demand). The installer copies these directories verbatim into host skill folders — there is no per-host fork of any skill.

## Host matrix

Install paths below were read from each host's official documentation on **2026-06-03**. Skill counts and conventions drift; re-verify at the cited source.

| Host | Status | Discovered install path(s) | Source (retrieved 2026-06-03) |
|---|---|---|---|
| **Claude Code** | **VERIFIED** | Personal `~/.claude/skills/<name>/SKILL.md`; project `.claude/skills/<name>/SKILL.md` | https://code.claude.com/docs/en/skills |
| **OpenAI Codex** | **VERIFIED** | Personal `~/.agents/skills/`; repo `.agents/skills/` (scanned cwd→repo root); system `/etc/codex/skills`; config `~/.codex/config.toml` (`[[skills.config]]`) | https://developers.openai.com/codex/skills |
| **Cursor** | **VERIFIED** | Native `~/.cursor/skills/`, `.cursor/skills/`, `~/.agents/skills/`, `.agents/skills/`; also reads `~/.claude/skills/`, `.claude/skills/`, `~/.codex/skills/`, `.codex/skills/` for compatibility | https://cursor.com/docs/skills |
| **GitHub Copilot** | **VERIFIED** | Project `.github/skills/`, `.claude/skills/`, `.agents/skills/`; personal `~/.copilot/skills/`, `~/.agents/skills/` | https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills |
| **Generic Agent Skills standard** | **standard-aligned** | `<root>/<name>/SKILL.md`; validate with `skills-ref validate ./<name>` | https://agentskills.io/specification · https://github.com/agentskills/agentskills |
| **OpenClaw** | **UNVERIFIED — roadmap** | Not confirmed against official docs; no install code | — |
| **Hermes** | **UNVERIFIED — roadmap** | Not confirmed against official docs; no install code | — |

### What this means in practice

The verified paths converge on two directories, which is why the existing installer needs no per-host rewrite:

- **`~/.claude/skills/`** (+ project `.claude/skills/`) is read by **Claude Code** (native), **GitHub Copilot**, and **Cursor** (compatibility).
- **`~/.agents/skills/`** (+ project `.agents/skills/`) is read by **Codex** (native), **Cursor** (native), and **GitHub Copilot**.

`installers/install.py` already installs to both (`--target claude` → `~/.claude/skills`, `--target codex` → `~/.agents/skills`). The `codex → ~/.agents/skills` mapping is **verified correct** against the Codex docs above. The installer's optional `.cursor/rules/medsci-skills.mdc` project rule is now **legacy**: Cursor reads `~/.claude/skills` and `~/.agents/skills` directly, so a separate Cursor install is no longer required for skill discovery (the rule remains a convenience for steering, not a requirement).

OpenClaw and Hermes stay on the roadmap with no install code or support claim until their official conventions are confirmed.

## Claude-specific assumptions inventory

These are points where the repository or a workflow assumes a Claude Code environment. The skill **packages** are portable; some **workflows** are not.

**Frontmatter (portable with a caveat).** Each `SKILL.md` uses `name`, `description`, `triggers`, `tools`, `model`. The open standard requires only `name` and `description`; `triggers`, `tools`, and `model` are **non-standard fields**. Compliant hosts ignore unknown fields, so they do not break discovery, but they are not interpreted off-Claude. (`tools` is also not the standard's `allowed-tools`.) A future alignment could move these under the standard's `metadata` map or add a `compatibility` field; out of scope here.

**Install / config paths.**
- `~/.claude/skills`, `~/.agents/skills` — install destinations (both verified above).
- `~/.claude/rules`, `~/.claude/hooks` — **host-local user configuration**, not part of any skill package and not installed by this repo. Behaviors that depend on user rules or hooks do not transfer to other hosts.

**Runtime references inside skills.**
- `${CLAUDE_SKILL_DIR}` — used by ~150 asset references across the skills to locate bundled `scripts/`/`references/`. Hosts that set this variable (or an equivalent skill-root variable) resolve them; a few skills also accept `${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}` as a fallback. On a host that sets neither, bundled-asset paths must be resolved relative to the skill root.
- **MCP tool names** — some skills reference Claude MCP servers in their bodies (for example PubMed / CrossRef / Zotero / Google Drive, named like `mcp__claude_ai_*` or `mcp__zotero__*`). These are **not declared in the `tools` frontmatter** and are **host-specific**: off-Claude hosts without the same MCP servers fall back to the skills' deterministic scripts or to manual workflow.

## Skill portability vs full-workflow portability

- **Skill packaging is portable.** Every `SKILL.md` + bundled `scripts/`/`references/` is standard-compliant and installs into the verified hosts above without modification.
- **Full-workflow portability varies.** A workflow degrades off-Claude when it depends on (a) a Claude MCP server for live data (citation verification, Zotero sync, Drive I/O), (b) host-local `~/.claude/rules` / `~/.claude/hooks`, or (c) a skill-root environment variable the host does not set.

Skills whose value is mostly **bundled deterministic scripts + reference material** (for example reporting-checklist audits, figure generation, sample-size calculation, statistical code) port most cleanly. Skills whose value depends on **live MCP retrieval** (literature search, reference verification, Zotero/Drive sync) need those servers configured on the target host, or fall back to manual steps. Per-skill specifics are recorded in each skill's Quality Card (`evidence_surface` and `known_limitations`).

---

*Part of [MedSci Skills](../README.md). See also [`docs/competitive_positioning.md`](competitive_positioning.md) and the per-skill reference in [`docs/skills/`](skills/). Install instructions are in the [main README](../README.md#installation).*

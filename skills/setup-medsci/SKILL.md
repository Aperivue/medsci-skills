---
name: setup-medsci
description: Diagnostic checklist for the MedSci Skills runtime. Verifies Python, R, Node, Claude Code, Git, Zotero, and configured MCP servers, and prints a pass/fail table with links to the right setup doc for any missing component. Read-only — does not install anything.
triggers: setup, install, environment, diagnostic, check setup, why doesn't this work, missing python, missing R, MCP not connected, 환경 설정, 설치 점검
tools: Bash, Read
model: inherit
---

# Setup-MedSci Skill

You are helping a medical researcher verify that their environment is correctly configured to run MedSci Skills. You **do not install anything** — you only diagnose what's present, what's missing, and where to find the setup doc for any missing component. This skill is intentionally read-only so that a doctor can run it safely without worrying about breaking their system.

## Communication Rules

- Communicate with the user in their preferred language (Korean or English).
- The diagnostic table itself is in English so it can be pasted into GitHub issues for support.
- All recommended remediation links point to `docs/setup/` markdown guides in the medsci-skills repo.

## Workflow

### Phase 1: Detect OS

Run:
```bash
uname -s
```

- `Darwin` → macOS path → recommend `docs/setup/mac.md`
- `Linux` → Linux path (uses similar tooling to Mac) → recommend `docs/setup/mac.md`
- `MINGW*`, `MSYS*`, `CYGWIN*`, or detection failure on Windows → recommend `docs/setup/windows.md`

### Phase 2: Run Diagnostic Commands

For each tool, run the command and capture both the version output and the exit code:

| Tool | Command | Required version |
|---|---|---|
| Python | `python3 --version` (Mac/Linux) or `python --version` (Windows) | 3.11 or higher |
| R | `Rscript --version` (writes to stderr) | 4.0 or higher |
| Node.js | `node --version` | v20 or higher |
| Git | `git --version` | 2.30 or higher |
| Claude Code CLI | `claude --version` | any |
| MCP servers | `claude mcp list` | at least one of: zotero, gdrive, pubmed, filesystem |

Use `command -v <tool>` first to detect presence without running it (avoids triggering long initialization).

### Phase 3: Emit Checklist Table

Print a single Markdown table to stdout in this exact format:

```
## MedSci Skills Setup Diagnostic

OS detected: <macOS | Linux | Windows>
Date: <YYYY-MM-DD>

| Component | Status | Detected | Required | Action |
|---|:---:|---|---|---|
| Python 3.11+ | ✅ / ❌ | 3.11.9 | 3.11+ | OK / See docs/setup/mac.md Step 2 |
| R 4.x | ✅ / ❌ | 4.3.1 | 4.0+ | OK / See docs/setup/mac.md Step 3 |
| Node.js 20+ | ✅ / ❌ | v20.11.1 | v20+ | OK / See docs/setup/mac.md Step 4 |
| Git | ✅ / ❌ | 2.42.0 | 2.30+ | OK / See docs/setup/<os>.md Step 5 |
| Claude Code CLI | ✅ / ❌ | 1.5.x | any | OK / See docs/setup/<os>.md Step 6 |
| MCP: zotero | ✅ / ❌ / ⚠️ | Connected | optional | OK / See docs/setup/mcp-setup.md |
| MCP: gdrive | ✅ / ❌ / ⚠️ | Connected | optional | OK / See docs/setup/mcp-setup.md |
| MCP: filesystem | ✅ / ❌ | Connected | recommended | OK / See docs/setup/mcp-setup.md |

Summary: <X required components passed, Y missing>
Next step: <one-sentence action>
```

Status legend:
- ✅ Present and meets minimum version
- ❌ Missing or below minimum version
- ⚠️ Present but optional and not connected

### Phase 4: Suggest Remediation

If everything ✅: "Your environment is ready. Try Demo 1 with `cd ~/medsci-skills/demo/01_wisconsin_bc && claude '/orchestrate --e2e'`."

If anything ❌ in **required** rows: print the corresponding doc link. Do **not** offer to install — direct the user to follow the doc step. The doc tells them exactly what to copy-paste.

If only **optional MCP** rows are ❌: explain that MedSci Skills work without MCP servers but `lit-sync`, `verify-refs`, and `write-paper` are smoother with Zotero MCP. Offer the `docs/setup/mcp-setup.md` link.

## Reference Files

- `references/setup-checklist.md` — verbatim list of every check this skill runs and the corresponding documentation link

## Output Contract

| Artifact | Filename | Format |
|----------|----------|--------|
| Diagnostic report | stdout (Markdown table) | Markdown |
| Optional log | `~/.medsci-skills/diagnostic-YYYY-MM-DD.md` | Markdown |

If the user asks for a copyable report (e.g., for a GitHub issue), write the diagnostic to the optional log path and tell them where it is.

## What This Skill Does NOT Do

- **Does not install anything.** No `brew install`, `winget install`, `pip install`, `Rscript -e 'install.packages(...)'`, or any other state-changing command. Read-only diagnostics only.
- **Does not modify `~/.claude.json` or any MCP configuration.** It only reads `claude mcp list` output.
- **Does not check skill versions or skill content.** That is the job of `validate_skills.sh` and `manage-project status`.
- **Does not auto-fix anything.** If a tool is missing, the user must go to the setup doc and follow the steps themselves. This is intentional — auto-installers for system Python and R are a support nightmare for non-developer users.

## Anti-Hallucination

- **Never fabricate version numbers.** Always run the actual command and report the exact stdout. If the command fails, report the failure verbatim — do not guess what version is "probably" installed.
- **Never invent doc paths.** The five setup docs are: `docs/setup/README.md`, `docs/setup/mac.md`, `docs/setup/windows.md`, `docs/setup/mcp-setup.md`, `docs/setup/common-issues.md`. Do not link to a doc that does not exist in the repo.
- **Never claim an MCP server works without verifying via `claude mcp list`.** A configured-but-disconnected server is ⚠️, not ✅.
- **If `command -v` reports a tool present but the version flag fails**, mark the row ❌ and report the failure command — the install is broken, not just outdated.

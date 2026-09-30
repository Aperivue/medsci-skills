---
name: setup-medsci
description: Use when a skill fails for a missing tool or the environment needs checking. Diagnoses Python, R, Node, Claude Code, Git, Zotero and configured MCP servers and prints a pass/fail table with links to the setup docs. Read-only; installs nothing.
metadata:
  triggers: "setup, install, environment, diagnostic, check setup, why doesn't this work, missing python, missing R, MCP not connected, 환경 설정, 설치 점검"
---

# Setup-MedSci Skill

Diagnose only. **Never install, upgrade or configure anything** — no `brew install`,
`winget install`, `pip install`, `Rscript -e 'install.packages(...)'`, and no edits to
`~/.claude.json` or any MCP configuration (read `claude mcp list` only) — because auto-installers
for system Python and R are a support nightmare for non-developer users. If a tool is missing,
the user follows the setup doc themselves. Skill versions and content are out of scope
(`validate_skills.sh`, `/manage-project status`).

The diagnostic table is in English so it can be pasted into a GitHub issue. Remediation links
point to the `docs/setup/` guides in the medsci-skills repository, and only these five exist:
`docs/setup/README.md`, `docs/setup/mac.md`, `docs/setup/windows.md`, `docs/setup/mcp-setup.md`,
`docs/setup/common-issues.md`.

## Workflow

### Phase 1: Detect OS

```bash
uname -s
```

- `Darwin` → macOS → `docs/setup/mac.md`
- `Linux` → Linux (similar tooling to Mac) → `docs/setup/mac.md`
- `MINGW*`, `MSYS*`, `CYGWIN*`, or detection failure on Windows → `docs/setup/windows.md`

### Phase 2: Run Diagnostic Commands

Read `references/setup-checklist.md` and run every check in it — R1-R5 required, O1-O5 optional —
with its detect command, version command, minimum version and status rule. Use `command -v <tool>`
first to detect presence without running it (avoids triggering long initialization). Capture the
version output and the exit code, and report the version exactly as printed: if a command fails,
report the failure verbatim rather than a version that is "probably" installed. If `command -v`
finds the tool but the version command or its parse fails, mark the row ❌ and report the failing
command — the install is broken, not just outdated. An MCP server is ✅ only when
`claude mcp list` shows it connected; configured-but-disconnected is ⚠️.

### Phase 3: Emit Checklist Table

Print a single Markdown table to stdout in this exact format, one row per check, with the doc
link from the reference for the detected OS:

```
## MedSci Skills Setup Diagnostic

OS detected: <macOS | Linux | Windows>
Date: <YYYY-MM-DD>

| Component | Status | Detected | Required | Action |
|---|:---:|---|---|---|
| Python 3.11+ | ✅ / ❌ | 3.11.9 | 3.11+ | OK / See docs/setup/mac.md Step 2 |
| MCP: zotero | ✅ / ❌ / ⚠️ | Connected | optional | OK / See docs/setup/mcp-setup.md |

Summary: <X required components passed, Y missing>
Next step: <one-sentence action>
```

Status legend:
- ✅ Present and meets minimum version
- ❌ Missing or below minimum version
- ⚠️ Present but optional and not connected

### Phase 4: Suggest Remediation

Use the reference's Summary Rules for the closing sentence.

- Everything required ✅ → point to Demo 1:
  `cd ~/medsci-skills/demo/01_wisconsin_bc && claude '/orchestrate --e2e'`.
- Any **required** row ❌ → print its doc link and tell them to follow that step. Do **not** offer
  to install; the doc tells them exactly what to copy-paste.
- Only **optional MCP** rows ❌ → explain that MedSci Skills work without MCP servers, but
  `lit-sync`, `verify-refs` and `write-paper` are smoother with Zotero MCP; link
  `docs/setup/mcp-setup.md`.

## Output

The diagnostic report goes to stdout. If the user asks for a copyable report (e.g. for a GitHub
issue), also write it to `~/.medsci-skills/diagnostic-YYYY-MM-DD.md` and tell them where it is.

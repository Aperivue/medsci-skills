# Setup Diagnostic Checklist

Verbatim list of every check `setup-medsci` runs, with the exact command, the parse rule, and the documentation link to print on failure.

## Required Components

| ID | Component | Detect command | Version command | Min version | Doc link on failure |
|---|---|---|---|---|---|
| R1 | Python 3 | `command -v python3` | `python3 --version` | 3.11.0 | `docs/setup/mac.md#step-2` (Mac) / `docs/setup/windows.md#step-3` (Windows) |
| R2 | R | `command -v Rscript` | `Rscript --version` (stderr) | 4.0.0 | `docs/setup/mac.md#step-3` / `docs/setup/windows.md#step-4` |
| R3 | Node.js | `command -v node` | `node --version` | 20.0.0 | `docs/setup/mac.md#step-4` / `docs/setup/windows.md#step-5` |
| R4 | Git | `command -v git` | `git --version` | 2.30.0 | `docs/setup/mac.md#step-5` / `docs/setup/windows.md#step-6` |
| R5 | Claude Code CLI | `command -v claude` | `claude --version` | any (latest recommended) | `docs/setup/mac.md#step-6` / `docs/setup/windows.md#step-7` |

## Optional Components

| ID | Component | Detect command | Status rule | Doc link on missing |
|---|---|---|---|---|
| O1 | MCP: zotero | `claude mcp list` | ✅ if "zotero ✓ Connected", ⚠️ if listed but not connected, ❌ if absent | `docs/setup/mcp-setup.md#zotero-mcp` |
| O2 | MCP: gdrive | `claude mcp list` | ✅ if "gdrive ✓ Connected", ⚠️ if listed but not connected, ❌ if absent | `docs/setup/mcp-setup.md#google-drive--workspace-mcp` |
| O3 | MCP: pubmed | `claude mcp list` | ✅ if "pubmed ✓ Connected", ⚠️ if listed but not connected, ❌ if absent | `docs/setup/mcp-setup.md#pubmed-mcp-alternative-to-built-in-search-lit` |
| O4 | MCP: filesystem | `claude mcp list` | ✅ if "filesystem ✓ Connected", ⚠️ if listed but not connected, ❌ if absent | `docs/setup/mcp-setup.md#filesystem-mcp-built-in-usually-pre-configured` |
| O5 | Zotero desktop | `pgrep -x Zotero` (Mac) / `tasklist /FI "IMAGENAME eq zotero.exe"` (Win) | ✅ if running, ⚠️ if installed but not running, ❌ if not installed | `docs/setup/mac.md#step-7` / `docs/setup/windows.md#step-8` |

## Version Comparison Rule

For required-version checks (R1-R4), parse the major.minor version from stdout, compare against minimum. If parse fails, mark ❌ and report the parse failure verbatim.

Examples of parsing:
- `Python 3.11.9` → `3.11`, compare to `3.11` → pass
- `Python 3.10.13` → `3.10`, compare to `3.11` → fail
- `R scripting front-end version 4.3.1 (2023-06-16)` → `4.3`, compare to `4.0` → pass
- `v20.11.1` → `20.11`, compare to `20.0` → pass
- `git version 2.42.0` → `2.42`, compare to `2.30` → pass

## Summary Rules

After running all checks:
- **All required ✅**: print "Your environment is ready. Try Demo 1 with `cd ~/medsci-skills/demo/01_wisconsin_bc && claude '/orchestrate --e2e'`."
- **One or more required ❌**: print "Setup incomplete. Address the ❌ rows above using the linked docs, then re-run `/setup-medsci`."
- **All required ✅, optional MCP all ❌**: print "Core environment ready. Optional MCP servers (Zotero / Google Drive / PubMed) are not configured — see `docs/setup/mcp-setup.md` for richer integration."

## What This Skill Does NOT Check

To keep the diagnostic fast and read-only, these are explicitly out of scope:
- Python package installs (matplotlib, pandas, scikit-learn, etc.) — checked by individual analysis skills when invoked
- R package installs (metafor, survey, etc.) — checked by `analyze-stats` and `meta-analysis` when invoked
- Disk space — irrelevant for skill execution
- Anthropic API quota / rate limits — visible only at runtime
- Claude Code skill installation — `validate_skills.sh` covers this
- Zotero library content / collection structure — `lit-sync` and `verify-refs` cover this

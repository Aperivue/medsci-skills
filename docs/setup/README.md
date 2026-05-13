# Setup Guide for MedSci Skills

**For physicians and clinical researchers who haven't used Python, R, or the command line before.**

You don't need to be a programmer to use these skills, but you do need to install three things first: Claude Code, Python, and R. This guide walks you through it. If anything fails, run the diagnostic skill (`/setup-medsci`) inside Claude Code and it will tell you exactly what's missing.

---

## Decision Tree

| Your Computer | Start Here |
|---|---|
| **Mac** (any model since 2017) | [`mac.md`](mac.md) |
| **Windows 10/11** | [`windows.md`](windows.md) |
| **Linux** | [`mac.md`](mac.md) (the Homebrew section maps to apt/dnf — most commands transfer) |

---

## What You Will Install

| Tool | What It Does | Required? |
|---|---|---|
| **Claude Code** | The CLI that runs the skills | **Yes** |
| **Python 3.11+** | Statistical analysis, figures, PDF processing | **Yes** |
| **R 4.x** | Meta-analysis (`metafor`), survival analysis, NHANES survey weighting | **Yes** if you do MA / survival / survey |
| **Node.js 20+** | MCP servers (Zotero, Google Drive integration) | Recommended |
| **Git** | Cloning the repo, version control of your manuscripts | **Yes** |
| **Zotero** + Better BibTeX | Reference management; auto-sync to your manuscripts | **Yes** for any paper |

**Time estimate**: 30-60 minutes if everything goes smoothly. 1-2 hours if you hit an issue (most are documented in [`common-issues.md`](common-issues.md)).

---

## After You Install Everything

1. **Verify with the diagnostic skill** (recommended):
   ```
   /setup-medsci
   ```
   This runs `which python3`, `which Rscript`, `which claude`, `which node`, and `claude mcp list` for you and prints a checklist showing what is ✅ and what is ❌.

2. **Install MedSci Skills** (after the diagnostic shows green for the core tools):

   **macOS** — double-click `installers/install-macos.command` from the cloned repo.

   **Windows** — double-click `installers/install-windows.cmd`.

   **Manually** (any OS):
   ```bash
   git clone https://github.com/Aperivue/medsci-skills.git
   cd medsci-skills
   python3 installers/install.py --target claude
   ```

3. **Add MCP servers** (optional but recommended for Zotero / Google Drive):

   See [`mcp-setup.md`](mcp-setup.md).

4. **Try Demo 1** to confirm everything works end-to-end:
   ```bash
   cd medsci-skills/demo/01_wisconsin_bc
   ```
   Then in Claude Code: `/orchestrate --e2e` (about 5-10 minutes; produces a manuscript, ROC curves, and a STARD compliance audit).

---

## If Something Breaks

- See [`common-issues.md`](common-issues.md) — covers the top 10 issues physicians run into (PATH, Python 2 vs 3, Apple Silicon, antivirus, JSON syntax errors).
- Run `/setup-medsci` again — the checklist will pinpoint the failure.
- Open an issue at <https://github.com/Aperivue/medsci-skills/issues> with the `/setup-medsci` output and the error message.

---

## Why a Setup Guide at All?

Most Claude Code skill collections assume you already have a working developer environment. We assume you don't — because most of our users are physicians and clinical researchers, and the install step is where they bounce. This guide aims to get you to a green diagnostic in under an hour, with no prior programming experience required.

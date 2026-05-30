# Setup on Windows

**Target**: Windows 10/11 users who have never installed Python or R before. WSL (Windows Subsystem for Linux) is **not required** — everything works natively on Windows.

If you already have some of these installed, the diagnostic skill (`/setup-medsci` from inside Claude Code) will tell you what to skip.

---

## Step 1 — Open PowerShell as Administrator

1. Press **Windows key**, type **"PowerShell"**.
2. Right-click **Windows PowerShell** → **Run as Administrator**.

Most installers below need admin rights.

---

## Step 2 — Install winget (the Windows package manager)

`winget` is built into Windows 11 and recent Windows 10. Verify:

```powershell
winget --version
```

If missing, install **App Installer** from the Microsoft Store (<https://www.microsoft.com/store/productId/9NBLGGH4NNS1>).

---

## Step 3 — Install Python 3.11

```powershell
winget install --id Python.Python.3.11 -e
```

**Important**: After install, **close PowerShell and reopen it** (so the PATH refreshes).

Verify:
```powershell
python --version
```
Expected: `Python 3.11.x`

If you see `Python 2.x.x` or "command not found", see [`common-issues.md`](common-issues.md) → "Windows Python PATH".

---

## Step 4 — Install R

```powershell
winget install --id RProject.R -e
```

Verify (after closing/reopening PowerShell):
```powershell
Rscript --version
```
Expected: `R scripting front-end version 4.x.x`

**Recommended GUI**: RStudio.
```powershell
winget install --id Posit.RStudio -e
```

---

## Step 5 — Install Node.js 20

```powershell
winget install --id OpenJS.NodeJS -e
```

Verify (close/reopen PowerShell):
```powershell
node --version
```
Expected: `v20.x.x`

---

## Step 6 — Install Git

```powershell
winget install --id Git.Git -e
```

Verify:
```powershell
git --version
```

---

## Step 7 — Install Claude Code

**Option A — Desktop app** (easiest): Download from <https://claude.ai/download> and install.

**Option B — Via winget** (if available):
```powershell
winget install --id Anthropic.Claude -e
```

Verify:
```powershell
claude --version
```

After install, run `claude` once → it opens your browser to log in to your Anthropic account.

---

## Step 8 — Install Zotero + Better BibTeX

1. Download Zotero from <https://www.zotero.org/download/> and install.
2. Open Zotero → **Edit** → **Preferences** → **Sync** → log in.
3. Install Better BibTeX: download `.xpi` from <https://github.com/retorquere/zotero-better-bibtex/releases/latest> → in Zotero, **Tools** → **Add-ons** → gear icon → **Install Add-on From File** → select the downloaded `.xpi`.
4. Restart Zotero.

---

## Step 9 — Verify Everything

In Claude Code, run:
```
/setup-medsci
```

You should see a checklist with all green ✅ marks. If anything is ❌, the checklist tells you which step to revisit.

---

## Step 10 — Install MedSci Skills

```powershell
cd $HOME
git clone https://github.com/Aperivue/medsci-skills.git
cd medsci-skills
.\installers\install-windows.cmd
```

Or double-click `install-windows.cmd` in File Explorer (Allow → Yes when SmartScreen warns; the script is open-source and viewable in the repo).

---

## Step 11 — Add MCP Servers (Optional)

See [`mcp-setup.md`](mcp-setup.md) for Zotero, Google Drive, and PubMed MCP integration.

---

## You're Done

Try Demo 1:
```powershell
cd $HOME\medsci-skills\demo\01_wisconsin_bc
```
Then in Claude Code: `/orchestrate --e2e`

Expected: a complete IMRAD manuscript + ROC curves + STARD compliance report in ~10 minutes.

Issues? See [`common-issues.md`](common-issues.md).

---

## Common Windows Quirks

- **PowerShell vs Command Prompt**: Use PowerShell. Most install commands assume PowerShell.
- **Antivirus warnings**: Windows Defender or third-party AV may flag `git`, `python`, or `claude` installers as "unrecognized." This is normal for newly-released versions — click **More info** → **Run anyway** if the source is the official one above.
- **PATH after install**: Always close and reopen PowerShell after installing a new tool, otherwise the new command isn't found yet.
- **OneDrive interference**: If you cloned the repo into a OneDrive-synced folder (Documents, Desktop), some scripts may stall. Move the repo to `C:\Users\YourName\medsci-skills` instead.

# Setup on macOS

**Target**: Mac users (Apple Silicon or Intel) who have never installed Python or R before.

If you already have some of these installed, the diagnostic skill (`/setup-medsci` from inside Claude Code) will tell you what to skip.

---

## Step 1 — Install Homebrew (the Mac package manager)

Open **Terminal** (Cmd+Space → type "Terminal" → Enter), then paste:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

You'll be asked for your Mac password (it won't show as you type — that's normal). After ~5 minutes, Homebrew prints "Installation successful!"

**Apple Silicon users (M1/M2/M3/M4)**: at the end of the install, Homebrew shows two `echo` commands to add Homebrew to your PATH. **Run them**, otherwise the `brew` command won't be found in new Terminal windows.

Verify:
```bash
brew --version
```
Expected: `Homebrew 4.x.x`

---

## Step 2 — Install Python (via pyenv, recommended)

Why `pyenv` instead of system Python: macOS ships with an old Python 2 that confuses many tools. `pyenv` lets you install a clean Python 3.11 alongside it without breaking the system.

```bash
brew install pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
exec zsh
pyenv install 3.11.9
pyenv global 3.11.9
```

Verify:
```bash
python3 --version
```
Expected: `Python 3.11.9`

**Faster alternative** (if you don't need to manage multiple Python versions): `brew install python@3.11` then symlink `python3` to it. Less robust long-term but works.

---

## Step 3 — Install R

```bash
brew install --cask r
```

The `--cask` flag installs the official R from CRAN (with the GUI). Takes about 5 minutes.

Verify:
```bash
Rscript --version
```
Expected: `R scripting front-end version 4.x.x`

**Recommended GUI**: Install RStudio for a nicer experience.
```bash
brew install --cask rstudio
```

---

## Step 4 — Install Node.js (for MCP servers)

```bash
brew install node@20
```

Verify:
```bash
node --version
```
Expected: `v20.x.x`

---

## Step 5 — Install Git

Usually already installed on Mac. Verify:
```bash
git --version
```

If missing:
```bash
brew install git
```

---

## Step 6 — Install Claude Code

Two options:

**Option A — Desktop app** (easiest): Download from <https://claude.ai/download> and install.

**Option B — CLI** (if you prefer Terminal):
```bash
brew install --cask claude
```

Verify:
```bash
claude --version
```

After install, run `claude` once and follow the login prompt (opens browser → log in to your Anthropic account).

---

## Step 7 — Install Zotero + Better BibTeX

1. Download Zotero from <https://www.zotero.org/download/> and install.
2. Open Zotero → **Preferences** → **Sync** → log in.
3. Install Better BibTeX: download `.xpi` from <https://github.com/retorquere/zotero-better-bibtex/releases/latest> → in Zotero, **Tools** → **Add-ons** → gear icon → **Install Add-on From File** → select the downloaded `.xpi`.
4. Restart Zotero.

---

## Step 8 — Verify Everything

In Claude Code, run:
```
/setup-medsci
```

You should see a checklist with all green ✅ marks. If anything is ❌, it tells you which step to revisit.

---

## Step 9 — Install MedSci Skills

```bash
git clone https://github.com/Aperivue/medsci-skills.git ~/medsci-skills
cd ~/medsci-skills
open installers/install-macos.command
```

The `.command` file is a double-clickable installer that copies the skills into `~/.claude/skills/` and prompts you for confirmations.

---

## Step 10 — Add MCP Servers (Optional)

See [`mcp-setup.md`](mcp-setup.md) for Zotero, Google Drive, and PubMed MCP integration.

---

## You're Done

Try Demo 1:
```bash
cd ~/medsci-skills/demo/01_wisconsin_bc
```
Then in Claude Code: `/orchestrate --e2e`

Expected: a complete IMRAD manuscript + ROC curves + STARD compliance report in ~10 minutes.

Issues? See [`common-issues.md`](common-issues.md).

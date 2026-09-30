# Installing MedSci Skills

Every install path below puts the same skill folders where your agent looks for them. Pick one.
The [README](../README.md#installation) gives the recommended path in one command; this page holds
the alternatives, where the files go, updating, and what individual skills need.

- [Requirements](#requirements)
- [npm / npx (recommended)](#npm--npx-recommended)
- [Classroom installer (no terminal)](#classroom-installer-no-terminal)
- [Claude Code plugin marketplace](#claude-code-plugin-marketplace)
- [GitHub CLI (`gh skill`)](#github-cli-gh-skill)
- [git clone](#git-clone)
- [Single-skill repositories](#single-skill-repositories)
- [Where the skills go](#where-the-skills-go)
- [Optional: let plain-language requests find the skills](#optional-let-plain-language-requests-find-the-skills)
- [Updating](#updating)
- [Setting up Python, R and the rest](#setting-up-python-r-and-the-rest)

## Requirements

**Python 3.9+ and an agent host. That is the whole hard requirement.** Every integrity detector is
stdlib-only, and so is drafting, reviewing, and auditing a manuscript. If you have no Python, the
double-click installer will offer to install it for you (`winget` on Windows, or the official
download page) rather than leaving you at a dead end.

- An [Agent Skills](https://agentskills.io)-compatible host — [Claude Code](https://claude.ai/code) (primary), or Codex / Cursor / GitHub Copilot (see [`host_compatibility.md`](host_compatibility.md); some live-data workflows rely on Claude MCP servers)
- Python 3.9+ — the floor is CI-enforced (`scripts/check_python_floor.py`). Newer is better; if you are installing Python today, take the latest.

Everything else is needed by *some* skills and not others. Rather than a shopping list of packages
you have never heard of, ask the toolkit what **this** computer can do:

```bash
python3 installers/doctor.py          # what works, what does not, and the exact fix for each
python3 installers/doctor.py --fix    # offers to install what is missing — asking before each one
```
(Or double-click `installers/check-setup-macos.command` / `installers/check-setup-windows.cmd`.)

It reports in terms of what you were trying to *do* — "turn your manuscript into a journal-formatted
Word file" needs **pandoc**; "read and QC submission PDFs" needs **poppler**; "open a .docx at all"
needs **python-docx** — and installs the small things on request. Large things (a TeX distribution,
R, PyTorch) are never installed for you: it prints the size and the command and leaves the choice
alone.

**R is not required.** `/analyze-stats` writes Python by default and only emits R if you ask it to;
the toolkit itself never executes R. Install R (with `meta`, `metafor`, `mada` for meta-analysis)
only if you want to run the R code it writes for you. The same is true of PyTorch and
`/model-scaffold`: writing the training code needs nothing; running it needs torch.

## npm / npx (recommended)

One command, nothing to clone. It copies the same skills via the dependency-free Python installer
(`installers/install.py`); the GitHub repository remains the source of truth.

```bash
npx medsci-skills install            # all hosts (Claude, Codex, Cursor)
npx medsci-skills install --target claude
npx medsci-skills list               # list bundled skills
npx medsci-skills doctor             # quick Node/Python/skill-folder check
```

Requires Node 18+ and (for `install`/`doctor`) `python3` on your PATH.

**Recommended (especially for clinicians):** add `--enable-update-notify` so Claude Code shows a
one-line *"update available"* notice when a new version ships — otherwise you stay on the version
you installed and are never told. (No terminal at all? The classroom installer below turns this on
for you.)

```bash
npx medsci-skills install --enable-update-notify        # install + in-app update reminders
```

Restart your agent, then start with **`/orchestrate`** — it classifies your request and routes you
to the right skill.

## Classroom installer (no terminal)

For non-programmers: download, unzip, double-click the installer, then restart your desktop agent app.

Windows:

```text
https://github.com/Aperivue/medsci-skills/releases/latest/download/medsci-skills-classroom-windows.zip
```

macOS:

```text
https://github.com/Aperivue/medsci-skills/releases/latest/download/medsci-skills-classroom-macos.zip
```

After unzipping:

- Windows: double-click `installers/install-windows.cmd`
- macOS: double-click `installers/install-macos.command`

This turnkey install also **turns on in-app update reminders** and adds an **"Update MedSci Skills"**
Desktop icon, so you are told when a new version ships and can update with one click — no terminal
needed (see [Updating](#updating)).

Then restart Claude Code Desktop, Codex Desktop, or Cursor and test with:

```text
MedSci Skills가 설치됐는지 확인하고, 오늘 실습에 쓸 대표 스킬 5개만 보여줘.
```

See [classroom_distribution_plan.md](classroom_distribution_plan.md) and
[classroom_materials.md](classroom_materials.md) for instructor distribution, email templates, and
first-class exercises.

## Claude Code plugin marketplace

One line adds the marketplace; `/plugin` then lets you browse the category plugins and enable the
ones you want:

```text
/plugin marketplace add Aperivue/medsci-skills
/plugin            # browse the category plugins; enable the ones you want
```

| Plugin | Covers |
|--------|--------|
| `medsci-literature` | Literature search, full-text retrieval, Zotero sync, reference-integrity audits |
| `medsci-data` | Study design, variable operationalization, sample size, data cleaning, de-identification, codebooks, dataset versioning |
| `medsci-modeling` | Architecture selection, reproducible model-scaffold repos, model-validation audits, Model Card/Datasheet, model & LLM/MLLM evaluation |
| `medsci-analysis` | Statistics, figures, batch/cross-national/replication analysis, meta-analysis |
| `medsci-writing` | IMRAD & protocol drafting, AI-pattern removal, AI-search optimization, reviewer responses |
| `medsci-review` | Self-review, peer review, reporting-guideline compliance |
| `medsci-submission` | Submission packaging, journal selection, ICMJE/IRB form filling, grant proposals |
| `medsci-project` | Orchestration, project intake/management, gap & topic discovery, author strategy |
| `medsci-presentation` | Presentations/PPTX, PDF/document rendering, environment setup, skill publishing |

The authoritative plugin list is [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json);
the README's skill map shows which skills each plugin enables.

Install a single category and invoke its skills under that namespace:

```text
/plugin install medsci-analysis@medsci-skills
/medsci-analysis:analyze-stats
```

The plugins share the same repository source, so this groups and enables skills by category — it is
not a partial download. The marketplace tracks `main`, so a plugin's version is its git commit.

**Note the name.** A skill installed as a plugin is invoked under its plugin's namespace
(`/medsci-analysis:analyze-stats`); the same skill installed into the skills folder by the `npx`,
`gh skill`, classroom, or manual paths is invoked bare (`/analyze-stats`). Both run the same skill —
press `/` and use Tab completion rather than typing the long form.

## GitHub CLI (`gh skill`)

MedSci Skills follows the [Agent Skills standard](https://agentskills.io), so
[GitHub CLI](https://cli.github.com/) ≥ 2.90 can search, preview, and install any skill straight from
this repo — no clone. It is a `gh` **preview** feature, so the exact flags may change.

```bash
gh skill search medsci                                   # list the whole collection
gh skill preview Aperivue/medsci-skills check-reporting  # read a skill before installing
gh skill install Aperivue/medsci-skills check-reporting  # install just that one
gh skill install --all Aperivue/medsci-skills            # or install every skill
```

`gh skill install` places skills in the host-specific folder for the agent you pick with `--agent`
(`claude-code` → `~/.claude/skills/`, `codex` → `~/.agents/skills/`, and many others), at user or
project `--scope` — the same folders the npx and git paths populate.

Search by a skill's own name (`check-reporting`, `verify-refs`, `meta-analysis`) or by `medsci` to
list them all — both return this repo directly. A broad topic word like `systematic review` is shared
by hundreds of skills across GitHub, so add `--owner Aperivue` to see only ours.

## git clone

Install all skills:

```bash
git clone https://github.com/Aperivue/medsci-skills.git
mkdir -p ~/.claude/skills
cp -r medsci-skills/skills/* ~/.claude/skills/
```

Install individual skills:

```bash
git clone https://github.com/Aperivue/medsci-skills.git
mkdir -p ~/.claude/skills
cp -r medsci-skills/skills/check-reporting ~/.claude/skills/
```

## Single-skill repositories

Two skills are also published as focused standalone repos (generated mirrors; this repo stays the
source of truth), each installable on its own with `/plugin marketplace add Aperivue/<repo>`:

- [`Aperivue/verify-refs`](https://github.com/Aperivue/verify-refs) — catch fabricated/mismatched citations (PubMed + CrossRef).
- [`Aperivue/check-reporting`](https://github.com/Aperivue/check-reporting) — audit a manuscript against the bundled EQUATOR reporting guidelines and risk-of-bias tools.

## Where the skills go

- Claude Code: skills are copied to `~/.claude/skills/` (also read by GitHub Copilot and Cursor).
- Codex: skills are copied to `~/.agents/skills/` (also read by Cursor and GitHub Copilot).
- Cursor: no separate step needed — Cursor reads `~/.claude/skills/` and `~/.agents/skills/` directly. The installer can still write an optional `.cursor/rules/` steering rule with `--cursor-project`; it carries no machine-specific path, so it is safe to commit.
- See [`host_compatibility.md`](host_compatibility.md) for the verified per-host install paths and their official sources.
- Windows users do not need WSL for the basic classroom workflow. Use WSL only for advanced reproducible Linux toolchains.

## Optional: let plain-language requests find the skills

Typing `/orchestrate` is the reliable way in. If you would rather just describe what you want, the
installer can write a short routing table into a project's `CLAUDE.md` so Claude Code reaches for
the right skill on its own whenever you work in that folder:

```bash
python3 installers/install.py --claude-project ~/research/my-study   # this project only
python3 installers/install.py --claude-user                          # every project (larger footprint)
python3 installers/install.py --claude-project ~/research/my-study --remove-routing
```

Both are **off by default**. The block is ~25 lines between `<!-- BEGIN/END medsci-skills routing -->`
markers and carries no machine-specific paths. It is spliced in, not written over: an existing
`CLAUDE.md` keeps its bytes outside the markers — line endings and file permissions included — the
write is atomic so an interrupted run cannot leave a truncated file, re-running updates the block in
place, and `--remove-routing` takes it back out. Prefer `--claude-project` — `--claude-user` loads in
every project you ever open, including work unrelated to research.

> **Tip:** Not sure which skill to use? Start with `/orchestrate` -- it will classify your request and route you to the right tool.

## Updating

MedSci Skills updates often. You do **not** need GitHub, git, or the command line to stay current.

- **One click (recommended for the classroom install).** The classroom installer sets this up for
  you automatically — it places an updater at `~/.medsci-skills/updater/`, drops an
  **"Update MedSci Skills"** icon on your Desktop (`--desktop-launcher`), and **turns on the in-app
  update reminder** (below). Double-click the icon: it downloads the latest release from GitHub,
  verifies it, and re-installs — transactionally, so an interrupted update never corrupts your install.
- **Already installed an old copy?** Re-download the latest classroom ZIP **once** and double-click
  the installer; from then on the one-click updater is in place for every future update.
- **Terminal users:** `npx medsci-skills@latest install` always installs the latest.
- **Just checking:** `python3 installers/install.py --check-update` reports whether a newer version
  is available and installs nothing.
- **Get reminded (Claude Code):** `python3 installers/install.py --enable-update-notify` (or
  `npx medsci-skills install --enable-update-notify`) shows a one-line *"update available"* notice
  when a Claude Code session starts. **The classroom installer enables this for you;** for the
  `npx`/manual paths it is **off by default** (the installer prints how to turn it on). It checks at
  most once a day, reads nothing about your session, and never installs anything. Turn it off with
  `--disable-update-notify`, or silence it with `MEDSCI_NO_UPDATE_CHECK=1`.
- **Claude Code plugin marketplace:** third-party marketplace **auto-update is off by default** —
  enable it in Claude Code or run a manual plugin update.

Updates connect only to GitHub, send no information about your machine or work, and create no
telemetry or tracking. Modified skills are backed up before an update and never auto-deleted. See
the [update privacy & data notice](update_privacy.md).

## Setting up Python, R and the rest

**New to Python, R, or the command line?** The full step-by-step guide for clinicians is in
[`setup/`](setup/README.md):

- [Mac setup](setup/mac.md) — Homebrew → Python 3.11 → R → Node → Claude Code (~30 min)
- [Windows setup](setup/windows.md) — winget-based, no WSL required
- [MCP server setup](setup/mcp-setup.md) — Zotero, Google Drive, PubMed integration
- [Common issues](setup/common-issues.md) — top 10 fixes (PATH, Apple Silicon, antivirus, JSON syntax)

**Verify your environment** with the diagnostic skill (read-only, installs nothing):

```
/setup-medsci
```

Prints a checklist showing which components are present, which are missing, and which doc to follow
for any gap.

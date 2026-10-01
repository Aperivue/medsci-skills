# Upgrading from v5 to v6

For people who already use MedSci Skills v5: what changed, and what to do.
Every change is listed in [CHANGELOG.md](CHANGELOG.md).

## Renamed skills

The twelve imaging and model-engineering skills are now seven. Three new skills replace eight old
ones; `model-scaffold`, `model-card`, `radiomics-ml` and `mllm-eval` keep their names. Each new
skill keeps the old skills' steps as phases, and every detector keeps its script name, flags and
JSON output.

| v5 name | v6 name | The old name now starts at |
|---|---|---|
| `architecture-zoo` | `model-selection` | Phases 1–3 |
| `model-sourcing` | `model-selection` | Phases 4–6 |
| `profile-imaging` | `imaging-data` | Phases 1–3 |
| `preprocess-imaging` | `imaging-data` | Phases 4–7 |
| `model-validation` | `model-assessment` | Part A, Phases 1–7 |
| `model-evaluation` | `model-assessment` | Part B, Phases 8–9 |
| `uncertainty-imaging` | `model-assessment` | Part C, Phases 10–11 |
| `explainability` | `model-assessment` | Part D, Phases 12–13 |

**The old names keep working until v7, as name-only aliases.** `/model-evaluation` still runs: it
hands the same arguments to `/model-assessment` and starts at the part in the table. In Claude Code
(and Cursor and Copilot in VS Code) the model never picks an alias on its own, so a plain-language
request goes to the new skill. Codex does not read the setting that hides them: it lists the eight
aliases to its model with their one-line "Renamed to …" descriptions, and an alias it picks
redirects to the new skill. With the plugin install this works the same way under the plugin's
namespace (`/medsci-modeling:model-evaluation` → `/medsci-modeling:model-assessment`).

**Script paths change now, not in v7.** An alias is a folder holding a single `SKILL.md` and no
scripts. If you run a detector by its path, keep the file name and change the folder, e.g.
`model-evaluation/scripts/check_metric_reporting.py` →
`model-assessment/scripts/check_metric_reporting.py`.

## Other changes

- **Shorter skill files.** Many `SKILL.md` files are shorter; material that only some runs need
  moved into files in the skill's `references/` folder.
- **SKILL.md frontmatter.** Each description is at most 300 characters and starts with "Use
  when"; `triggers` moved under `metadata`, and `tools` is gone. See [CHANGELOG.md](CHANGELOG.md).
- **A short README.** Install options, updating and requirements moved to
  [docs/install.md](docs/install.md), the demos to [docs/demos.md](docs/demos.md), and workflows
  and skill boundaries to [docs/workflows.md](docs/workflows.md). Links to sections of the old
  README still land on the section that now holds or links that content.

## What to do

1. Update through the channel you installed with (next section).
2. Replace the old names wherever you wrote them down: notes, saved prompts, scripts, and any
   `CLAUDE.md` or `AGENTS.md` that names a skill.
3. If you had edited one of the eight renamed skills, the installer keeps your version in a backup
   (next section); with `gh skill` or a hand copy, save it yourself before updating. Carry the
   change over to the new skill by hand, or offer it back with `/contribute`.

## Updating, by install channel

The MedSci Skills installer (`installers/install.py`) runs behind npx, the classroom ZIP and its
one-click updater, and can be run from a clone. It replaces each skill folder whole. Before it
replaces a folder you changed, or one it did not install itself, it copies that folder to
`~/.medsci-skills/backups/<time>/<target>/`; backups are never deleted automatically. From v5 to
v6 it removes nothing: each renamed skill's folder is replaced by its alias, so the v5 scripts in
it are gone (kept in the backup if you had changed that skill). Running it again changes nothing.

- **npx:** `npx medsci-skills@latest install`, with the `--target` you used before, if any.
- **Classroom ZIP:** double-click the **Update MedSci Skills** icon on your Desktop. No icon (an
  older classroom install)? Download the latest classroom ZIP once and double-click its installer;
  the icon is in place from then on. See [Updating](docs/install.md#updating).
- **Claude Code plugin marketplace:** the marketplace follows the repository's `main` branch.
  Auto-update for third-party marketplaces is off by default, so turn it on or run a manual plugin
  update from `/plugin`. Plugins are managed by Claude Code, not by the MedSci Skills installer,
  so no backup is made. To stay on v6.0.1 rather than follow `main`, add the marketplace with that
  tag; see [the plugin section](docs/install.md#claude-code-plugin-marketplace).
- **GitHub CLI (`gh skill`, a preview feature):** `gh skill update --all` updates the skills you
  already have. The three new skills are not among them, so install each by name with the same
  `--agent` and `--scope` as before, e.g. `gh skill install Aperivue/medsci-skills model-assessment`
  (then `imaging-data` and `model-selection`). `gh skill` does not run the MedSci Skills installer
  and makes no backup, so copy any skill you edited first. Afterwards each of the eight renamed
  folders should hold only `SKILL.md`; delete a v5 `scripts/` folder left inside one.
- **git clone:** `git pull`, then run `python3 installers/install.py` from the clone for the backup
  and clean replacement described above. If you copy by hand instead, `cp -r` adds files but never
  removes them: first move the eight renamed folders out of `~/.claude/skills/` (and
  `~/.agents/skills/` if you use Codex), then copy `skills/*` again. See
  [git clone](docs/install.md#git-clone).

## In v7

The eight aliases are removed and the old names stop working, so update anything that still uses
them before then. When a release no longer ships a skill, the installer removes that skill's
folder, backing it up first if you changed it. With `gh skill` or a hand copy, delete the eight
folders yourself.

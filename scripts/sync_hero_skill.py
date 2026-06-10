#!/usr/bin/env python3
"""Mirror a "hero" skill out to its focused standalone repo.

Why: a narrow single-purpose repo is a star funnel that backlinks to the full
suite. medsci-skills stays the SINGLE SOURCE OF TRUTH; each standalone repo is a
GENERATED mirror — the skill is copied verbatim and the repo wrappers
(README / LICENSE / CITATION.cff / .claude-plugin/marketplace.json / installer /
minimal CI) are generated from `metadata/hero_skills.json` + the canonical skill.
Contributions route back to canonical; the mirror is force-synced.

Author identity, version, release date, and DOI for the generated CITATION.cff are
read at RUNTIME from the canonical CITATION.cff (kept out of this script's source,
so no author PII is hard-coded here and there is one source for that metadata).

Stdlib-only. Two modes:
  python3 scripts/sync_hero_skill.py --skill verify-refs --staging-dir /tmp/vr   # build only (inspect/test)
  python3 scripts/sync_hero_skill.py --all --push                                 # build + push to each repo
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
HERO_JSON = ROOT / "metadata" / "hero_skills.json"
CITATION = ROOT / "CITATION.cff"
SCHEMA_URL = "https://json.schemastore.org/claude-code-marketplace.json"
OWNER_NAME = "Aperivue"
MAIN_REPO = "Aperivue/medsci-skills"
MAIN_URL = "https://github.com/Aperivue/medsci-skills"


class SyncError(Exception):
    pass


# ---------- small stdlib parsers (mirror gen_skills_catalog_json.py style) ----------

def _frontmatter_field(text: str, key: str) -> str | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    body: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        body.append(line)
    for line in body:
        m = re.match(rf"^{re.escape(key)}:(.*)$", line)
        if m and not line[:1].isspace():
            return m.group(1).strip().strip('"').strip("'")
    return None


def _first_sentence(desc: str, cap: int = 220) -> str:
    end = len(desc)
    p = desc.find(". ")
    if p != -1:
        end = p + 1
    end = min(end, cap)
    return desc[:end].rstrip()


def _citation_fields(text: str) -> dict:
    """Pull author + version + date-released + doi from the canonical CITATION.cff
    (narrow regex; avoids a pyyaml dependency and keeps author PII out of source)."""
    def scalar(key: str) -> str:
        m = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.M)
        return m.group(1).strip().strip('"').strip("'") if m else ""

    def author_field(key: str) -> str:
        m = re.search(rf"^\s+(?:-\s+)?{re.escape(key)}:\s*(.+)$", text, re.M)
        return m.group(1).strip().strip('"').strip("'") if m else ""

    fields = {
        "family_names": author_field("family-names"),
        "given_names": author_field("given-names"),
        "affiliation": author_field("affiliation"),
        "orcid": author_field("orcid"),
        "version": scalar("version"),
        "date_released": scalar("date-released"),
        "doi": scalar("doi"),
    }
    if not (fields["family_names"] and fields["given_names"]):
        raise SyncError("could not parse author from canonical CITATION.cff")
    return fields


# ---------- generated artifacts ----------

def _marketplace(entry: dict) -> str:
    obj = {
        "$schema": SCHEMA_URL,
        "name": entry["plugin_name"],
        "description": entry["tagline"],
        "owner": {"name": OWNER_NAME},
        "plugins": [{
            "name": entry["plugin_name"],
            "description": entry["tagline"],
            "source": "./",
            "strict": False,
            "skills": [f"./skills/{entry['skill']}"],
        }],
    }
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def _readme(entry: dict, description: str) -> str:
    skill = entry["skill"]
    repo = entry["repo"]
    plugin = entry["plugin_name"]
    return f"""# {skill}

**{entry['tagline']}**

`{skill}` is one skill from **[MedSci Skills]({MAIN_URL})**, a physician-built suite
for the medical research lifecycle. This repository is a focused, standalone mirror of
that one skill so you can install just this capability.

## What it does

{description}

## Install

**As a Claude Code plugin (one line):**

```text
/plugin marketplace add {repo}
/plugin install {plugin}@{plugin}
```

Then invoke it with `/{plugin}:{skill}`.

**Or copy the skill directly:**

```bash
git clone https://github.com/{repo}.git
mkdir -p ~/.claude/skills
cp -r {repo.split('/')[-1]}/skills/{skill} ~/.claude/skills/
```

Restart your agent, then use `/{skill}`. The installer also supports Codex/Cursor:
`python3 installers/install.py --target all`.

## Usage

See [`skills/{skill}/SKILL.md`](skills/{skill}/SKILL.md) for the full workflow and the
bundled deterministic script under `skills/{skill}/scripts/`.

## Part of MedSci Skills

This is one of 40+ skills covering literature search, study design, statistics,
figures, IMRAD writing, reporting-compliance audits, journal selection, peer review,
and revision. Get the whole suite:

```text
/plugin marketplace add {MAIN_REPO}
```

→ **[github.com/{MAIN_REPO}]({MAIN_URL})**

## Citation

If you use this in your research, cite via [`CITATION.cff`](CITATION.cff).

## Source of truth

This repository is a **generated mirror**. The canonical source and all
contributions live in **[{MAIN_REPO}]({MAIN_URL})** (`skills/{skill}/`) — please open
issues and pull requests there, not here. This mirror is overwritten on each sync.

## License

MIT — see [LICENSE](LICENSE).
"""


def _license(entry: dict, third_party: str | None) -> str:
    mit = (
        "MIT License\n\n"
        "Copyright (c) 2026 Aperivue (https://aperivue.com)\n\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
        'of this software and associated documentation files (the "Software"), to deal\n'
        "in the Software without restriction, including without limitation the rights\n"
        "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
        "copies of the Software, and to permit persons to whom the Software is\n"
        "furnished to do so, subject to the following conditions:\n\n"
        "The above copyright notice and this permission notice shall be included in all\n"
        "copies or substantial portions of the Software.\n\n"
        'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n'
        "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
        "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
        "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
        "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
        "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
        "SOFTWARE.\n"
    )
    if third_party:
        mit += (
            "\n---\n\n"
            "## Third-Party Content Licenses\n\n"
            "This skill bundles educational summaries of published assessment tools that "
            "retain their own licenses and are NOT covered by the MIT license above. "
            "Downstream use must comply with the original terms.\n\n"
            + third_party
        )
    return mit


def _citation(entry: dict, cf: dict) -> str:
    repo = entry["repo"]
    title = f"{entry['skill']}: a MedSci Skills hero skill"
    lines = [
        "cff-version: 1.2.0",
        'message: "If you use this skill in your research, please cite it as below."',
        "type: software",
        f'title: "{title}"',
        f'abstract: >-\n  {entry["tagline"]} A standalone mirror of the `{entry["skill"]}` skill '
        f"from MedSci Skills ({MAIN_URL}).",
        "authors:",
        f"  - family-names: {cf['family_names']}",
        f"    given-names: {cf['given_names']}",
    ]
    if cf["affiliation"]:
        lines.append(f'    affiliation: "{cf["affiliation"]}"')
    if cf["orcid"]:
        lines.append(f'    orcid: "{cf["orcid"]}"')
    lines += [
        f'repository-code: "https://github.com/{repo}"',
        f'url: "https://github.com/{repo}"',
        "license: MIT",
    ]
    if cf["version"]:
        lines.append(f'version: "{cf["version"]}"')
    if cf["date_released"]:
        lines.append(f'date-released: "{cf["date_released"]}"')
    if cf["doi"]:
        lines.append(f'doi: "{cf["doi"]}"')
    return "\n".join(lines) + "\n"


INSTALLER = '''#!/usr/bin/env python3
"""Install this single skill for local agent apps (Claude Code / Codex / Cursor).

Generated mirror installer — copies skills/{skill} to ~/.claude/skills and
~/.agents/skills. Stdlib-only.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = "{skill}"


def targets(which: str) -> list[Path]:
    home = Path.home()
    dests = {{"claude": home / ".claude" / "skills", "codex": home / ".agents" / "skills"}}
    return [dests[which]] if which in dests else list(dests.values())


def install(which: str) -> int:
    src = REPO_ROOT / "skills" / SKILL
    if not (src / "SKILL.md").is_file():
        print(f"ERROR: {{src}}/SKILL.md not found", file=sys.stderr)
        return 1
    for dest in targets(which):
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dest / SKILL, dirs_exist_ok=True)
        ok = (dest / SKILL / "SKILL.md").is_file()
        print(f"  {{'installed' if ok else 'FAILED'}} {{SKILL}} -> {{dest}}")
        if not ok:
            return 1
    print("Done. Restart your agent, then use /" + SKILL + ".")
    return 0


def self_test() -> int:
    src = REPO_ROOT / "skills" / SKILL
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "skills"
        dest.mkdir(parents=True)
        shutil.copytree(src, dest / SKILL, dirs_exist_ok=True)
        ok = (dest / SKILL / "SKILL.md").is_file()
    print(f"self-test: {{'OK' if ok else 'FAIL'}} ({{SKILL}} discoverable in temp target)")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Install the " + SKILL + " skill locally.")
    ap.add_argument("--target", choices=["all", "claude", "codex"], default="all")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    return self_test() if args.self_test else install(args.target)


if __name__ == "__main__":
    raise SystemExit(main())
'''


VALIDATE_YML = '''name: Validate skill

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Validate marketplace.json + SKILL.md frontmatter
        run: |
          python3 - <<'PY'
          import json, sys
          from pathlib import Path
          mk = json.load(open(".claude-plugin/marketplace.json"))
          assert mk["plugins"], "no plugins"
          for p in mk["plugins"]:
              for s in p["skills"]:
                  slug = s.removeprefix("./skills/")
                  assert (Path("skills") / slug / "SKILL.md").is_file(), f"missing {{slug}}/SKILL.md"
                  txt = (Path("skills") / slug / "SKILL.md").read_text(encoding="utf-8")
                  assert txt.startswith("---"), "SKILL.md missing frontmatter"
          print("OK: marketplace + SKILL.md valid")
          PY
      - name: Run bundled skill tests
        run: |
          shopt -s nullglob
          for t in skills/*/tests/*.sh; do echo "== $t =="; bash "$t"; done
'''


GITIGNORE = "__pycache__/\n*.pyc\n.DS_Store\n*-install-log.txt\n"


# ---------- build + push ----------

def build_standalone(entry: dict, staging: Path) -> None:
    skill = entry["skill"]
    src = SKILLS_DIR / skill
    if not (src / "SKILL.md").is_file():
        raise SyncError(f"canonical skill not found: {src}/SKILL.md")

    if staging.exists():
        shutil.rmtree(staging)
    (staging / "skills").mkdir(parents=True)
    shutil.copytree(src, staging / "skills" / skill)

    description = _first_sentence(_frontmatter_field((src / "SKILL.md").read_text(encoding="utf-8"), "description") or entry["tagline"])

    (staging / ".claude-plugin").mkdir(parents=True)
    (staging / ".claude-plugin" / "marketplace.json").write_text(_marketplace(entry), encoding="utf-8")
    (staging / "README.md").write_text(_readme(entry, description), encoding="utf-8")

    third_party = None
    tp_path = src / "references" / "LICENSES.md"
    if tp_path.is_file():
        third_party = tp_path.read_text(encoding="utf-8")
    (staging / "LICENSE").write_text(_license(entry, third_party), encoding="utf-8")

    (staging / "CITATION.cff").write_text(
        _citation(entry, _citation_fields(CITATION.read_text(encoding="utf-8"))), encoding="utf-8")

    (staging / "installers").mkdir(parents=True)
    (staging / "installers" / "install.py").write_text(INSTALLER.format(skill=skill), encoding="utf-8")

    (staging / ".github" / "workflows").mkdir(parents=True)
    (staging / ".github" / "workflows" / "validate.yml").write_text(VALIDATE_YML, encoding="utf-8")
    (staging / ".gitignore").write_text(GITIGNORE, encoding="utf-8")


def _git(args: list[str], cwd: Path, env: dict | None = None) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, env=env)


def push_standalone(entry: dict, staging: Path, token: str, source_sha: str) -> None:
    repo = entry["repo"]
    url = f"https://x-access-token:{token}@github.com/{repo}.git"
    env = {**os.environ,
           "GIT_AUTHOR_NAME": "medsci-skills-sync[bot]",
           "GIT_AUTHOR_EMAIL": "noreply@aperivue.com",
           "GIT_COMMITTER_NAME": "medsci-skills-sync[bot]",
           "GIT_COMMITTER_EMAIL": "noreply@aperivue.com"}
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "repo"
        try:
            _git(["clone", "--depth", "1", url, str(work)], cwd=Path(tmp), env=env)
        except subprocess.CalledProcessError:
            work.mkdir(parents=True, exist_ok=True)
            _git(["init"], cwd=work, env=env)
            _git(["remote", "add", "origin", url], cwd=work, env=env)
    # fresh checkout of main, replace all tracked content with staging
        _git(["checkout", "-B", "main"], cwd=work, env=env)
        for child in work.iterdir():
            if child.name == ".git":
                continue
            shutil.rmtree(child) if child.is_dir() else child.unlink()
        for child in staging.iterdir():
            dst = work / child.name
            shutil.copytree(child, dst) if child.is_dir() else shutil.copy2(child, dst)
        _git(["add", "-A"], cwd=work, env=env)
        # commit only if there is a change
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=work, env=env)
        if diff.returncode == 0:
            print(f"  {repo}: no changes, skipping push")
            return
        _git(["commit", "-m", f"sync {entry['skill']} from {MAIN_REPO}@{source_sha}"], cwd=work, env=env)
        _git(["push", "--force", "origin", "HEAD:main"], cwd=work, env=env)
        print(f"  {repo}: pushed sync of {entry['skill']} @ {source_sha}")


def load_entries(skill: str | None) -> list[dict]:
    data = json.loads(HERO_JSON.read_text(encoding="utf-8"))
    entries = data.get("hero_skills", [])
    if skill:
        entries = [e for e in entries if e["skill"] == skill]
        if not entries:
            raise SyncError(f"{skill} not found in {HERO_JSON}")
    return entries


def main() -> int:
    ap = argparse.ArgumentParser(description="Mirror a hero skill to its standalone repo.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--skill", help="single hero skill to sync")
    g.add_argument("--all", action="store_true", help="sync every hero skill in hero_skills.json")
    ap.add_argument("--staging-dir", type=Path, default=None,
                    help="build the standalone tree here (no push); default: a temp dir")
    ap.add_argument("--push", action="store_true", help="push to the target repo(s)")
    ap.add_argument("--token", default=os.environ.get("GH_TOKEN", ""),
                    help="GitHub token with Contents:write on the target repo (or env GH_TOKEN)")
    args = ap.parse_args()

    try:
        entries = load_entries(None if args.all else args.skill)
    except SyncError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1

    sha = ""
    if args.push:
        if not args.token:
            print("FAIL: --push needs --token or GH_TOKEN", file=sys.stderr)
            return 1
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True).stdout.strip()

    for entry in entries:
        if args.staging_dir and not args.all:
            staging = args.staging_dir
            build_standalone(entry, staging)
            print(f"OK: built {entry['skill']} standalone tree at {staging}")
            if args.push:
                push_standalone(entry, staging, args.token, sha)
        else:
            with tempfile.TemporaryDirectory() as tmp:
                staging = Path(tmp) / entry["skill"]
                build_standalone(entry, staging)
                print(f"OK: built {entry['skill']} standalone tree")
                if args.push:
                    push_standalone(entry, staging, args.token, sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())

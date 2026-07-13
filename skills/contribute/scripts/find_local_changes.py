#!/usr/bin/env python3
"""What have you changed? — find the local edits that could become a contribution.

The people who use this toolkit are clinicians. They install it once, adapt a skill to the
way their department actually works, add the journal they publish in, fix a checklist item
that was wrong for their specialty — and then stop. The edit sits on one laptop. They do not
open a pull request, because a pull request is not a thing they do; often they do not update
either, because they assume an update would destroy the changes.

(It would not: the installer already hashes every shipped file and takes a permanent backup
of any skill you modified before it overwrites. But nobody knows that, and nothing ever reads
the backup again.)

So the edit — which is frequently the most valuable thing in the repository, because it is a
real clinician's real domain knowledge — dies on the laptop. This script is the first half of
the fix: it compares what is installed against the hashes of what was shipped, and reports
exactly what you changed and what you added.

It reads only. Nothing is sent anywhere by this script, and nothing is sent by any script
without an explicit confirmation and a safety scan (`check_contribution_safety.py`).

Usage:
    find_local_changes.py [--target claude|codex|cursor|copilot] [--json] [--diff]

Exit 0 always (having no local changes is not an error). Stdlib only.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import sys
from pathlib import Path

TARGET_DIRS = {
    "claude": Path.home() / ".claude" / "skills",
    "codex": Path.home() / ".agents" / "skills",
    "cursor": Path.home() / ".agents" / "skills",
    "copilot": Path.home() / ".agents" / "skills",
}

# Files that are noise, not contributions.
IGNORE_PARTS = {"__pycache__", ".DS_Store", ".pytest_cache"}
IGNORE_SUFFIX = {".pyc", ".pyo"}


def state_home() -> Path:
    env = os.environ.get("MEDSCI_HOME")
    return Path(env).expanduser() if env else Path.home() / ".medsci-skills"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ignored(rel: str) -> bool:
    p = Path(rel)
    return bool(IGNORE_PARTS.intersection(p.parts)) or p.suffix in IGNORE_SUFFIX


def is_text(path: Path) -> bool:
    try:
        path.read_text(encoding="utf-8")
        return True
    except (UnicodeDecodeError, OSError):
        return False


def load_shipped(target: str) -> dict[str, dict[str, str]]:
    """{skill: {relpath: sha256}} as installed by the last install/update."""
    mf = state_home() / "targets" / target / "installed-manifest.json"
    if not mf.is_file():
        raise SystemExit(
            f"no install record for '{target}' at {mf}.\n"
            "MedSci Skills does not look installed for that host — run the installer first."
        )
    data = json.loads(mf.read_text(encoding="utf-8"))
    return {name: entry.get("inventory", {}) for name, entry in data.get("skills", {}).items()}


def scan(target: str, want_diff: bool) -> dict:
    root = TARGET_DIRS[target]
    shipped = load_shipped(target)

    changes: list[dict] = []
    for skill, inventory in sorted(shipped.items()):
        sdir = root / skill
        if not sdir.is_dir():
            continue

        on_disk: dict[str, str] = {}
        for f in sorted(sdir.rglob("*")):
            if not f.is_file() or f.is_symlink():
                continue
            rel = f.relative_to(sdir).as_posix()
            if ignored(rel):
                continue
            on_disk[rel] = sha256(f)

        for rel, h in on_disk.items():
            if rel not in inventory:
                kind = "added"
            elif inventory[rel] != h:
                kind = "modified"
            else:
                continue
            entry = {"skill": skill, "path": rel, "kind": kind,
                     "abs": str(sdir / rel), "text": is_text(sdir / rel)}
            changes.append(entry)

        for rel in inventory:
            if rel not in on_disk and not ignored(rel):
                changes.append({"skill": skill, "path": rel, "kind": "deleted",
                                "abs": str(sdir / rel), "text": True})

    if want_diff:
        for c in changes:
            c["diff"] = unified(c, root, shipped)

    return {
        "target": target,
        "skills_root": str(root),
        "n_changes": len(changes),
        "changes": changes,
        "summary": {
            k: sum(1 for c in changes if c["kind"] == k)
            for k in ("modified", "added", "deleted")
        },
    }


def unified(c: dict, root: Path, shipped: dict) -> str:
    """A diff of a MODIFIED file needs the shipped original, which we no longer have on disk —
    only its hash. So we can show the current content, and mark the shipped side as unavailable.
    An ADDED file is shown whole: that is the common and most valuable case (a new journal
    profile, a new CSL, a new exemplar)."""
    p = Path(c["abs"])
    if c["kind"] == "deleted" or not c["text"] or not p.is_file():
        return ""
    body = p.read_text(encoding="utf-8", errors="replace")
    if c["kind"] == "added":
        return "\n".join(f"+{line}" for line in body.splitlines())
    # modified: show the file as it now stands; the maintainer diffs it against the repo.
    return "\n".join(f" {line}" for line in body.splitlines())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", default="claude", choices=sorted(TARGET_DIRS))
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--diff", action="store_true", help="include file contents")
    ap.add_argument("--out", type=Path, help="write the JSON record here")
    a = ap.parse_args()

    rep = scan(a.target, a.diff or a.json)

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(rep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if a.json:
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0

    if not rep["n_changes"]:
        print(f"No local changes to the installed skills ({a.target}).")
        print("Nothing to contribute from this machine — which is fine; most installs never diverge.")
        return 0

    s = rep["summary"]
    print(f"You have changed the installed skills ({a.target}):")
    print(f"  {s['modified']} file(s) modified, {s['added']} added, {s['deleted']} removed\n")
    by_skill: dict[str, list[dict]] = {}
    for c in rep["changes"]:
        by_skill.setdefault(c["skill"], []).append(c)
    for skill, cs in by_skill.items():
        print(f"  /{skill}")
        for c in cs:
            mark = {"added": "new ", "modified": "edit", "deleted": "gone"}[c["kind"]]
            print(f"      [{mark}] {c['path']}")
    print(
        "\nA new file — a journal profile, a citation style, a reporting exemplar — is usually the\n"
        "most valuable thing here: it is domain knowledge nobody else in the project has.\n"
        "\nNothing has been sent anywhere. To offer any of this back to the project, run the\n"
        "safety scan and then the submission step; both stop and ask before anything leaves\n"
        "this machine. See the /contribute skill."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

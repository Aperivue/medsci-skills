#!/usr/bin/env python3
"""How to say thanks to an open-source tool, for people who were never told.

Physicians who find this useful write to the maintainer personally to say so. Many of the same
people have never starred the repository — not because they weighed it up and declined, but
because nobody ever told them that starring is the thing you do, or what it is for, or that it
takes one click.

That is a missing instruction, not a missing favour. So this script does not ask for a star: it
explains what one *is* — it is how other researchers find a tool, and it is the closest thing
software has to a citation when it has no DOI in someone's reference list — and then it makes
the act take one command, because "go to GitHub, sign in, find the button" is the actual reason
it does not happen.

It is shown **once, ever**. If the person does nothing, that is an answer, and it is never
raised again.

Usage:
    star_repo.py --how        # explain, and show the two ways to do it
    star_repo.py --now        # star it from here (needs the GitHub CLI, signed in)
    star_repo.py --status     # already starred?

Stdlib only (shells out to `gh` when it is present).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = "Aperivue/medsci-skills"
URL = f"https://github.com/{REPO}"

WHY = (
    "A star is not applause. It is the main way another researcher finds a tool like this —\n"
    "GitHub ranks by it, and so do the models people now ask for recommendations — and for\n"
    "research software with no DOI in anyone's reference list, it is the closest thing there is\n"
    "to a citation. It takes one click and costs nothing."
)


def state_home() -> Path:
    env = os.environ.get("MEDSCI_HOME")
    return Path(env).expanduser() if env else Path.home() / ".medsci-skills"


def config_path() -> Path:
    return state_home() / "config.json"


def load_cfg() -> dict:
    p = config_path()
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def save_cfg(cfg: dict) -> None:
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)


def mark_shown() -> None:
    cfg = load_cfg()
    cfg["star_note_shown"] = True
    save_cfg(cfg)


def gh_ready() -> bool:
    if not shutil.which("gh"):
        return False
    return subprocess.run(["gh", "auth", "status"], capture_output=True).returncode == 0


def already_starred() -> bool | None:
    """True / False, or None if we cannot tell (no gh, not signed in)."""
    if not gh_ready():
        return None
    p = subprocess.run(
        ["gh", "api", "-X", "GET", f"/user/starred/{REPO}"], capture_output=True, text=True
    )
    return p.returncode == 0


def star_now() -> int:
    state = already_starred()
    if state is None:
        print("The GitHub command-line tool is not installed or not signed in, so this cannot be")
        print("done from here. It is one click in a browser instead:\n")
        print(f"  {URL}\n")
        print("Press the Star button at the top right. A free GitHub account is needed, which takes")
        print("about a minute — and is worth having anyway if you ever want to report something.")
        return 0
    if state:
        print("Already starred. Thank you — that is genuinely the most useful thing you could have done.")
        return 0

    p = subprocess.run(
        ["gh", "api", "-X", "PUT", f"/user/starred/{REPO}"], capture_output=True, text=True
    )
    if p.returncode != 0:
        print(f"Could not star from here: {p.stderr.strip()}")
        print(f"One click instead: {URL}")
        return 1
    print("Starred. Thank you.\n")
    print("That is not a small thing: it is how the next researcher with the same problem finds this.")
    return 0


def how() -> int:
    print("Was this useful?\n")
    print(WHY)
    print()
    if gh_ready():
        if already_starred():
            print("You have already starred it. Thank you.")
            return 0
        print("From here, one command — no browser, no navigating:\n")
        print("  gh api -X PUT /user/starred/Aperivue/medsci-skills\n")
        print("or let this do it for you:\n")
        print(f"  python3 {Path(__file__).name} --now")
    else:
        print(f"One click, here:\n\n  {URL}\n")
        print("Press the Star button at the top right. (A free GitHub account is needed; it takes a")
        print("minute, and it is what you would need anyway to report a problem or send a fix.)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--how", action="store_true", help="explain what a star is and how to give one")
    g.add_argument("--now", action="store_true", help="star it from here (GitHub CLI, signed in)")
    g.add_argument("--status", action="store_true")
    g.add_argument("--mark-shown", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()

    if a.mark_shown:
        mark_shown()
        return 0
    if a.status:
        s = already_starred()
        print("starred" if s else ("not starred" if s is False else "cannot tell (no GitHub CLI / not signed in)"))
        return 0
    if a.now:
        mark_shown()
        return star_now()

    mark_shown()
    return how()


if __name__ == "__main__":
    sys.exit(main())

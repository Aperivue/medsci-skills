#!/usr/bin/env python3
"""Whether this machine wants to be reminded about contributing. Default: no.

A clinician installed a research tool. They did not sign up to be asked for things. If every
update greeted them with "you changed a file — would you like to share it?", the toolkit would
be nagging a physician about open-source etiquette while they are trying to finish a paper, and
they would be right to resent it.

So reminders are **opt-in, off by default**, and we ask exactly once — at the end of an install,
in one line — and then never again, whatever the answer. `asked_once` is recorded so a person who
ignored the question is not asked a second time. Silence is a valid answer.

What the preference does and does not govern:

  * It governs UNSOLICITED reminders only — the installer noticing you modified a skill.
  * It does NOT govern `/contribute` itself. Running it deliberately always works, whatever this
    is set to. Turning reminders off is not opting out of contributing; it is opting out of being
    asked.
  * It does NOT relax anything about safety. Opting in never means "send without asking". The
    patient-data scan and the line-by-line confirmation are unconditional, and this file cannot
    switch them off — there is deliberately no setting for that.

Usage:
    contribution_prefs.py --status
    contribution_prefs.py --on          # remind me if I've changed something worth sharing
    contribution_prefs.py --off         # never mention it again (the default)
    contribution_prefs.py --should-remind   # exit 0 to remind, 1 to stay quiet (for the installer)

Stdlib only. The file lives beside the install state, never in the user's project.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT = {
    "contribution_reminders": "off",   # "on" | "off"  — off is the default, deliberately
    "asked_once": False,               # we ask once, ever; ignoring the question is an answer
    "last_reminded": None,             # ISO date; used to keep even an opted-in reminder rare
}
REMIND_EVERY_DAYS = 30


def state_home() -> Path:
    env = os.environ.get("MEDSCI_HOME")
    return Path(env).expanduser() if env else Path.home() / ".medsci-skills"


def config_path() -> Path:
    return state_home() / "config.json"


def load() -> dict:
    p = config_path()
    if not p.is_file():
        return dict(DEFAULT)
    try:
        cfg = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return dict(DEFAULT)
    return {**DEFAULT, **cfg}


def save(cfg: dict) -> None:
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)


def reminders_on() -> bool:
    return load()["contribution_reminders"] == "on"


def should_remind(today: str | None = None) -> bool:
    """True only if the user asked to be reminded AND we have not reminded them recently.
    An opted-in reminder that fires on every update is still a nuisance."""
    cfg = load()
    if cfg["contribution_reminders"] != "on":
        return False
    last = cfg.get("last_reminded")
    if not last or not today:
        return True
    try:
        from datetime import date
        y1, m1, d1 = (int(x) for x in last.split("-"))
        y2, m2, d2 = (int(x) for x in today.split("-"))
        return (date(y2, m2, d2) - date(y1, m1, d1)).days >= REMIND_EVERY_DAYS
    except (ValueError, TypeError):
        return True


def mark_reminded(today: str) -> None:
    cfg = load()
    cfg["last_reminded"] = today
    save(cfg)


def mark_asked() -> None:
    cfg = load()
    cfg["asked_once"] = True
    save(cfg)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--status", action="store_true")
    g.add_argument("--on", action="store_true", help="remind me if I have changed something worth sharing")
    g.add_argument("--off", action="store_true", help="never mention it (the default)")
    g.add_argument("--should-remind", action="store_true", help="exit 0 to remind, 1 to stay quiet")
    g.add_argument("--mark-asked", action="store_true", help=argparse.SUPPRESS)
    g.add_argument("--mark-reminded", metavar="YYYY-MM-DD", help=argparse.SUPPRESS)
    ap.add_argument("--today", metavar="YYYY-MM-DD", help="for --should-remind (rate limit)")
    a = ap.parse_args()

    if a.should_remind:
        return 0 if should_remind(a.today) else 1
    if a.mark_asked:
        mark_asked()
        return 0
    if a.mark_reminded:
        mark_reminded(a.mark_reminded)
        return 0

    cfg = load()
    if a.on or a.off:
        cfg["contribution_reminders"] = "on" if a.on else "off"
        cfg["asked_once"] = True
        save(cfg)
        if a.on:
            print("Reminders on. If an update finds you have changed a skill, it will mention it —")
            print("at most once a month, and never more than a line.")
            print("\nThis does not change what gets sent, or when: nothing ever leaves this machine")
            print("without the patient-data scan and your explicit confirmation on every line.")
        else:
            print("Reminders off. Nothing will bring this up again.")
            print("\n/contribute still works whenever you choose to run it — this only turns off")
            print("being asked.")
        return 0

    print(f"Contribution reminders : {cfg['contribution_reminders']}")
    print(f"Config                 : {config_path()}")
    print(
        "\nOff by default. Reminders are the only thing this controls: /contribute works whenever\n"
        "you run it, and nothing is ever sent without the patient-data scan and your confirmation.\n"
        "\n  contribution_prefs.py --on    remind me if I have changed something worth sharing\n"
        "  contribution_prefs.py --off   never mention it"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

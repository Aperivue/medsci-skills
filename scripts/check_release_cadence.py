#!/usr/bin/env python3
"""A release is an event, not a commit. This stops us from pretending otherwise.

In the 37 days to 2026-07-13 this repository cut **42 releases** — a median gap of **zero
days**, three of them on one afternoon. Three things follow, and all three are worse than they
look:

  1. THE RELEASE STOPS MEANING ANYTHING. A user who sees forty-nine releases does not read a
     changelog; they wonder whether the thing is stable. A version number that changes daily is
     a commit log with extra ceremony.

  2. IT DESTROYS OUR OWN ADOPTION SIGNAL. Every release attracts a handful of automated asset
     downloads (mirrors, scanners, crawlers), so `release_downloads` grows with the *number of
     releases* rather than the number of users. Per-release downloads collapsed from 32 to 5
     across that window while the cumulative total doubled — and the cumulative total is the
     number we were about to cite as evidence of adoption. Cadence is a **measurement**
     decision, not only a shipping one.

  3. IT MAKES THE VERSION USELESS AS A COORDINATE. "Which version were you on?" stops being
     answerable when there were four that week.

So: **a release needs a reason to exist, and a gap since the last one.** Ship the work to `main`
continuously — that is what `main` is for — and let releases accumulate into something a person
would want to read about.

Exemption, and only this one: a **hotfix**. Something shipped is broken (it will not install, it
loses data, it is a security problem, or it produced a wrong result that a user might have
believed). Those go out immediately, and say so in the changelog:

    ## [5.20.1] - 2026-07-11

    **Hotfix:** `/orchestrate --e2e` halted at step 3 requiring a DOCX only rendered at step 7,
    so an end-to-end run could not complete.

Usage:
    check_release_cadence.py [--min-days 14] [--strict]

It is a no-op unless a release is actually being prepared: if `CITATION.cff` still declares the
version of the newest tag, there is nothing to check and it exits 0. Stdlib only (shells to git).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIN_DAYS = 14

# A release that fixes something already broken in the wild does not wait.
HOTFIX = re.compile(r"^\s*\*\*Hotfix:?\*\*\s*(.+)$", re.MULTILINE | re.IGNORECASE)

# A release must carry something a user would notice. These headings do not qualify on their own.
COSMETIC_ONLY = {"changed", "docs", "documentation", "internal", "chore", "ci"}


def git(*args: str) -> str:
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ""


def declared_version() -> str:
    m = re.search(r'^version:\s*"?([0-9]+\.[0-9]+\.[0-9]+)"?\s*$',
                  (ROOT / "CITATION.cff").read_text(encoding="utf-8"), re.MULTILINE)
    if not m:
        raise SystemExit("CITATION.cff: no semver version")
    return m.group(1)


def latest_tag() -> tuple[str, date] | None:
    line = git("for-each-ref", "--sort=-creatordate", "--count=1",
               "--format=%(refname:short)|%(creatordate:short)", "refs/tags")
    if not line or "|" not in line:
        return None
    tag, when = line.split("|", 1)
    try:
        return tag, datetime.strptime(when.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def changelog_section(version: str) -> str:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(rf"^## \[{re.escape(version)}\].*?$(.*?)(?=^## \[|\Z)", text,
                  re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def substantive(section: str) -> bool:
    """Does this release contain anything a user would notice?

    A docs-only or CI-only change is a fine thing to merge and a poor reason to make a hundred
    people update. It rides along with the next release that has a reason of its own.
    """
    headings = [h.strip().lower() for h in re.findall(r"^###\s+(.+)$", section, re.MULTILINE)]
    if not headings:
        return False
    return any(h not in COSMETIC_ONLY for h in headings)


def audit(min_days: int) -> tuple[list[str], dict]:
    problems: list[str] = []
    version = declared_version()
    tag = latest_tag()

    if tag and tag[0].lstrip("v") == version:
        return [], {"release_pending": False, "version": version, "last_tag": tag[0]}

    info = {
        "release_pending": True,
        "version": version,
        "last_tag": tag[0] if tag else None,
        "last_tag_date": tag[1].isoformat() if tag else None,
        "days_since": (date.today() - tag[1]).days if tag else None,
    }

    section = changelog_section(version)
    if not section.strip():
        problems.append(
            f"CHANGELOG.md has no `## [{version}]` section. A release that cannot be described "
            "is a release nobody asked for."
        )
        return problems, info

    hotfix = HOTFIX.search(section)
    info["hotfix"] = bool(hotfix)
    if hotfix:
        info["hotfix_reason"] = hotfix.group(1).strip()

    if tag and info["days_since"] is not None and info["days_since"] < min_days and not hotfix:
        problems.append(
            f"{info['days_since']} day(s) since {tag[0]} — a release needs {min_days}.\n"
            f"      A release is an event, not a commit. Merge the work to main and let it "
            f"accumulate into\n      something a person would want to read about; the version "
            f"number is a coordinate, and it stops\n      being one when there were four of them "
            f"that week.\n"
            f"      If something shipped is genuinely broken — it will not install, it loses "
            f"data, it is a\n      security problem, or it produced a wrong result someone may "
            f"have believed — say so in the\n      changelog section and this passes:\n\n"
            f"          ## [{version}] - <date>\n\n"
            f"          **Hotfix:** <what is broken for users right now>"
        )

    if not substantive(section) and not hotfix:
        problems.append(
            f"the `[{version}]` section carries nothing a user would notice "
            f"(only: {', '.join(re.findall(r'^###\\s+(.+)$', section, re.MULTILINE)) or 'no headings'}).\n"
            "      Docs, CI and internal changes are fine to merge and a poor reason to make a "
            "hundred people\n      update. Let them ride along with the next release that has a "
            "reason of its own."
        )

    return problems, info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-days", type=int, default=MIN_DAYS)
    ap.add_argument("--strict", action="store_true", help="exit 1 on any problem (CI gate)")
    a = ap.parse_args()

    problems, info = audit(a.min_days)

    if not info["release_pending"]:
        print(f"OK: no release pending (CITATION.cff and {info['last_tag']} both say {info['version']}).")
        return 0

    print(f"Release pending: {info['version']} (last: {info['last_tag']}, "
          f"{info['days_since']} day(s) ago)")
    if info.get("hotfix"):
        print(f"  HOTFIX declared: {info['hotfix_reason']}")

    if problems:
        print(f"\nRELEASE_CADENCE: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  - {p}\n")
        return 1 if a.strict else 0

    print("OK: enough has changed, and enough time has passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

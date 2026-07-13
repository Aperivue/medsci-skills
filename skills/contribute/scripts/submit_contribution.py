#!/usr/bin/env python3
"""Turn a local edit into a pull request, without the author ever typing a git command.

The audience for this script is a physician who changed a file because the toolkit was wrong
about their journal, their specialty, or their department — and who has never opened a pull
request and has no reason to learn how. Every step that a maintainer would do by hand is done
here; the author's only job is to read what is about to be sent and say yes.

It refuses to run unless the safety scan has passed, and it prints the exact payload before
it does anything irreversible. `--dry-run` is the default in the skill's workflow: it shows
the whole plan, sends nothing, and exits.

Ladder (it takes the highest rung available):
  1. `gh` present and authenticated  -> fork, branch, commit, push, open the PR. Nothing to type.
  2. `gh` present, not authenticated -> print the single command that fixes that, and stop.
  3. no `gh`                         -> write a patch file and open a pre-filled issue in the
                                        browser, so the contribution still reaches the project.

Usage:
    submit_contribution.py --changes qc/local_changes.json --safety qc/safety.json \\
        --title "Add the Korean Journal of Radiology profile" [--dry-run] [--issue-only]

Stdlib only (shells out to `git` and `gh`).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

REPO = "Aperivue/medsci-skills"
MAX_ISSUE_BODY = 6000  # a pre-filled issue URL cannot carry a whole file


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise SystemExit(f"{' '.join(cmd[:2])} failed:\n{p.stderr.strip() or p.stdout.strip()}")
    return p


def gh_state() -> str:
    if not shutil.which("gh"):
        return "absent"
    p = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    return "ready" if p.returncode == 0 else "unauthenticated"


def load(changes: Path, safety: Path) -> tuple[dict, dict]:
    ch = json.loads(changes.read_text(encoding="utf-8"))
    sf = json.loads(safety.read_text(encoding="utf-8"))
    if sf.get("blockers"):
        raise SystemExit(
            "The safety scan found patient-level data or a credential in what you are about to send.\n"
            "Nothing will be submitted. Remove those lines and re-run the scan."
        )
    if not sf.get("safe_to_send", False):
        raise SystemExit(
            "The safety scan is not clean. Fix the findings (or explicitly drop the files that carry\n"
            "them from the contribution) and re-run it. Nothing has been sent."
        )
    if not ch.get("changes"):
        raise SystemExit("There is nothing to contribute — no local changes were found.")
    return ch, sf


def describe(ch: dict, title: str) -> str:
    lines = [
        "This contribution comes from a MedSci Skills user who adapted the toolkit on their own",
        "machine and offered the change back. It was produced by `/contribute`, which compared the",
        "installed skills against the hashes of what was shipped, scanned the result for patient",
        "data and identifiers, and required the author to confirm every line before sending.",
        "",
        "**Files**",
        "",
    ]
    for c in ch["changes"]:
        mark = {"added": "new", "modified": "edited", "deleted": "removed"}[c["kind"]]
        lines.append(f"- `{c['skill']}/{c['path']}` ({mark})")
    lines += [
        "",
        "**For the maintainer**: the author is a clinician, not necessarily a git user. If something",
        "needs changing, say what and why in plain terms — they may not know what a rebase is, and",
        "they should not have to.",
    ]
    return "\n".join(lines)


def pr_flow(ch: dict, title: str, body: str, dry: bool) -> int:
    tmp = Path(tempfile.mkdtemp(prefix="medsci-contrib-"))
    clone = tmp / "medsci-skills"

    print(f"Plan:\n  1. fork {REPO} to your GitHub account (if you have not already)")
    print(f"  2. copy your {len(ch['changes'])} changed file(s) into it")
    print("  3. open a pull request\n")
    if dry:
        print("--dry-run: nothing was sent. Re-run without --dry-run to actually open the pull request.")
        return 0

    run(["gh", "repo", "fork", REPO, "--clone=false", "--remote=false"], check=False)
    user = run(["gh", "api", "user", "--jq", ".login"]).stdout.strip()
    run(["gh", "repo", "clone", f"{user}/medsci-skills", str(clone), "--", "--depth", "1"])

    branch = "contrib/" + "".join(c if c.isalnum() else "-" for c in title.lower())[:40].strip("-")
    run(["git", "checkout", "-b", branch], cwd=clone)

    for c in ch["changes"]:
        dest = clone / "skills" / c["skill"] / c["path"]
        if c["kind"] == "deleted":
            if dest.exists():
                dest.unlink()
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(c["abs"], dest)
        run(["git", "add", str(dest.relative_to(clone))], cwd=clone)

    run(["git", "commit", "-m", title, "-m", body], cwd=clone)
    run(["git", "push", "-u", "origin", branch], cwd=clone)
    p = run(["gh", "pr", "create", "--repo", REPO, "--head", f"{user}:{branch}",
             "--title", title, "--body", body], cwd=clone)
    print("\nYour pull request is open:\n  " + p.stdout.strip())
    print(
        "\nA maintainer will read it. You do not need to do anything else — if they ask for a change,\n"
        "you can reply in plain language on that page."
    )
    return 0


def issue_flow(ch: dict, title: str, body: str, dry: bool) -> int:
    """No gh, or the author prefers not to fork: reach the project as an issue instead."""
    patch_dir = Path.cwd() / "qc"
    patch_dir.mkdir(parents=True, exist_ok=True)
    patch = patch_dir / "contribution.patch"

    chunks = [body, "", "---", ""]
    for c in ch["changes"]:
        if c["kind"] == "deleted" or not c.get("text", True):
            continue
        text = Path(c["abs"]).read_text(encoding="utf-8", errors="replace")
        chunks += [f"### `{c['skill']}/{c['path']}`", "", "```", text, "```", ""]
    full = "\n".join(chunks)
    patch.write_text(full, encoding="utf-8")
    print(f"Wrote the contribution to {patch}")

    if dry:
        print("--dry-run: nothing was sent.")
        return 0

    short = full if len(full) <= MAX_ISSUE_BODY else (
        body + "\n\n---\n\nThe change is too large to inline. The author has it at "
        f"`{patch}` and can attach it to this issue."
    )
    if shutil.which("gh"):
        run(["gh", "issue", "create", "--repo", REPO, "--title", title, "--body", short, "--web"], check=False)
        print("Opened a pre-filled issue in your browser. Review it and press Submit.")
    else:
        url = (f"https://github.com/{REPO}/issues/new?title="
               f"{urllib.parse.quote(title)}&body={urllib.parse.quote(short[:MAX_ISSUE_BODY])}")
        print("\nOpen this in your browser, check it, and press Submit:\n\n  " + url)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--changes", required=True, type=Path)
    ap.add_argument("--safety", required=True, type=Path)
    ap.add_argument("--title", required=True, help="one plain sentence: what does this change do?")
    ap.add_argument("--dry-run", action="store_true", help="show the whole plan, send nothing")
    ap.add_argument("--issue-only", action="store_true", help="do not fork; reach the project as an issue")
    a = ap.parse_args()

    ch, _ = load(a.changes, a.safety)
    body = describe(ch, a.title)

    print("This is what would be sent:\n")
    for c in ch["changes"]:
        print(f"  {c['kind']:9} {c['skill']}/{c['path']}")
    print()

    state = gh_state()
    if a.issue_only or state == "absent":
        if state == "absent" and not a.issue_only:
            print("The GitHub command-line tool is not installed, so a pull request cannot be opened")
            print("from here. Falling back to an issue, which reaches the project just as well.\n")
        return issue_flow(ch, a.title, body, a.dry_run)

    if state == "unauthenticated":
        print("You have the GitHub tool but are not signed in. Run this once, then run me again:\n")
        print("  gh auth login\n")
        print("(Choose GitHub.com, HTTPS, and log in through the browser. It takes about a minute.)")
        return 1

    return pr_flow(ch, a.title, body, a.dry_run)


if __name__ == "__main__":
    sys.exit(main())

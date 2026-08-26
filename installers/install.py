#!/usr/bin/env python3
"""Install MedSci Skills for local agent apps.

Dependency-free. Installs the repository's skills into common local skill folders via a
**transactional, crash-recoverable** install (see installers/medsci_txn.py) so an
interrupted install is recovered on the next run, and optionally writes a small Cursor
project rule. No network access here.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path

# The floor the README promises. Checked here as well as in the double-click installers, because
# the failure it prevents is a clinician staring at a Python traceback: on 3.8 this file *parses*
# (so there is no clean syntax error to explain itself) and then dies somewhere in the middle,
# leaving a half-explained wall of text and no idea what to do next.
MIN_PYTHON = (3, 9)
if sys.version_info < MIN_PYTHON:
    have = ".".join(str(n) for n in sys.version_info[:3])
    sys.exit(
        f"\nMedSci Skills needs Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer. This computer has {have}.\n\n"
        "  Install the latest Python from  https://www.python.org/downloads/\n"
        "  then run this installer again.\n\n"
        "Nothing has been changed on your computer.\n"
    )

sys.path.insert(0, str(Path(__file__).resolve().parent))  # allow `import medsci_txn` when run as a script
import medsci_txn  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
LOG_NAME = "medsci-skills-install-log.txt"


def log(message: str, log_lines: list[str]) -> None:
    print(message)
    log_lines.append(message)


def default_target_dir(target: str) -> Path:
    # Verified against official host docs on 2026-06-03 (see docs/host_compatibility.md):
    #   claude -> ~/.claude/skills   (Claude Code; also read by GitHub Copilot and Cursor)
    #   codex  -> ~/.agents/skills   (Codex personal scope per developers.openai.com/codex/skills;
    #                                 also read by Cursor and GitHub Copilot)
    # These two destinations together cover Claude Code, Codex, Cursor, and Copilot, so no
    # per-host fork is needed. OpenClaw/Hermes remain unverified and are intentionally absent.
    home = Path.home()
    if target == "claude":
        return home / ".claude" / "skills"
    if target == "codex":
        return home / ".agents" / "skills"
    raise ValueError(f"Unknown target: {target}")


def verify_discoverable(dest: Path, skill_names: list[str], log_lines: list[str]) -> None:
    """Assert each installed skill landed at <dest>/<name>/SKILL.md so a host can discover it."""
    missing = [s for s in skill_names if not (dest / s / "SKILL.md").is_file()]
    log(f"  verified {len(skill_names) - len(missing)}/{len(skill_names)} skills discoverable at {dest}", log_lines)
    if missing:
        raise RuntimeError(f"discoverability check failed at {dest}: missing SKILL.md for {', '.join(missing)}")


def copy_skills(target: str, dest: Path, log_lines: list[str], dry_run: bool) -> int:
    if not SKILLS_DIR.exists():
        raise FileNotFoundError(f"skills directory not found: {SKILLS_DIR}")

    owned = sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").exists())
    log(f"\n[{target}] installing {len(owned)} skills to {dest}", log_lines)

    if dry_run:
        for name in owned:
            log(f"  DRY RUN install {name}", log_lines)
        return len(owned)

    result = medsci_txn.install_target(
        SKILLS_DIR, dest, target, owned, medsci_txn.state_home(),
        lambda m: log(m, log_lines),
    )
    verify_discoverable(dest, owned, log_lines)
    return result["installed"]


def install_cursor_rule(project: Path, log_lines: list[str], dry_run: bool) -> None:
    rules_dir = project / ".cursor" / "rules"
    rule_path = rules_dir / "medsci-skills.mdc"
    body = f"""---
description: Use MedSci Skills for medical research writing, literature search, statistics, figures, and submission workflows.
alwaysApply: false
---

# MedSci Skills

When the user asks for medical research workflows, inspect the relevant
`skills/<skill-name>/SKILL.md` file in this repository before acting.

Start with these entry points:

- `skills/search-lit/SKILL.md` for literature search and verified citations
- `skills/analyze-stats/SKILL.md` for statistical tables and analysis code
- `skills/make-figures/SKILL.md` for publication figures
- `skills/write-paper/SKILL.md` for manuscript sections
- `skills/check-reporting/SKILL.md` for reporting guideline audits

Use small single-skill tasks first. Avoid running the full end-to-end pipeline
unless the user explicitly asks and provides the required project files.

Repository path:
`{REPO_ROOT}`
"""
    log(f"\n[cursor] writing project rule to {rule_path}", log_lines)
    if dry_run:
        log("  DRY RUN write Cursor rule", log_lines)
        return
    rules_dir.mkdir(parents=True, exist_ok=True)
    rule_path.write_text(body, encoding="utf-8")
    log("  installed Cursor project rule", log_lines)


ROUTING_BEGIN = "<!-- BEGIN medsci-skills routing -->"
ROUTING_END = "<!-- END medsci-skills routing -->"

# Deliberately carries no local path. The Cursor rule above embeds REPO_ROOT, which is fine for a
# file nobody shares — but a CLAUDE.md sits in a project folder and gets committed, and the absolute
# path of a home directory is the installer's name. Nothing here is machine-specific.
ROUTING_BLOCK = f"""{ROUTING_BEGIN}
## MedSci Skills

MedSci Skills is installed. When a request matches a row below, invoke that skill rather than
answering from scratch. When the right one is not obvious, invoke `orchestrate` — it classifies the
request and routes to the rest.

| Request | Skill |
|---|---|
| Find papers; check that a citation is real; build a reference list | `search-lit`, `verify-refs`, `manage-refs` |
| Plan a study; sample size; define variables; de-identify data | `design-study`, `calc-sample-size`, `define-variables`, `deidentify` |
| Run statistics; draw a publication figure | `analyze-stats`, `make-figures` |
| Draft or revise a manuscript; write an IRB protocol | `write-paper`, `revise`, `write-protocol` |
| Audit against a reporting guideline (STROBE, PRISMA, CONSORT, STARD, TRIPOD) or a risk-of-bias tool | `check-reporting` |
| Self-review before submitting; answer reviewers; review someone else's paper | `self-review`, `revise`, `peer-review` |
| Choose a journal; assemble a submission package | `find-journal`, `sync-submission` |
| Medical-research work that is not obviously one of the above | `orchestrate` |

How a skill is invoked depends on how it was installed: bare (`/write-paper`) for a skills-folder
install, namespaced (`/medsci-writing:write-paper`) for a plugin install. Skip any skill that is not
installed, and never invent one.

These skills draft and audit. They do not replace authors, statisticians, reviewers, or an IRB, and
every output needs human-expert verification.

Everything between the two markers above and below is managed by the MedSci Skills installer and is
replaced or removed wholesale when it runs. Put your own notes outside them.
{ROUTING_END}
"""


LF = "\n"
CRLF = "\r\n"


def _dominant_newline(text: str) -> str:
    """Which line ending this file already uses, so the block matches it instead of mixing."""
    crlf = text.count(CRLF)
    return CRLF if crlf > text.count(LF) - crlf else LF


def _write_preserving_mode(path: Path, text: str, newline: str) -> None:
    """Atomically replace `path`, keeping the permissions it already had.

    The mode step mirrors update._write_settings: a user who ran `chmod 600` on their CLAUDE.md
    should not have it widened to the umask default as a side effect of an install.
    """
    prev_mode = os.stat(path).st_mode & 0o777 if path.is_file() else None
    medsci_txn.atomic_write_bytes(path, text.encode("utf-8"))
    if prev_mode is not None:
        try:
            os.chmod(path, prev_mode)
        except OSError:
            pass


def apply_routing(md_path: Path, remove: bool, dry_run: bool, log_lines: list[str]) -> str:
    """Splice the routing block into a CLAUDE.md. Returns: added | updated | unchanged | removed | absent.

    What is actually guaranteed, because the first version of this docstring claimed more than the
    code delivered and an external review said so:

    * **The write is atomic.** Content goes to a temp file beside the target and is `os.replace`d
      into position (medsci_txn.atomic_write_bytes), so an interrupted run leaves the previous file
      intact. The previous version called `Path.write_text`, which opens in "w" mode and therefore
      truncates before writing -- an interrupt there left a zero-byte CLAUDE.md.
    * **Bytes outside the two markers are preserved, line endings included.** The file is read with
      `read_bytes` and decoded here, so nothing on the path performs universal-newline translation;
      a CRLF file stays CRLF, and the block is emitted with the file's own line ending rather than
      mixing one in.
    * **Permissions are preserved.**

    The one thing it does NOT preserve, stated rather than hidden: a file with no trailing newline
    gains one, and removal does not take it back. The newline is needed to put the block on its own
    line, and nothing in the file records that it was ours.

    A CLAUDE.md is where a user keeps their own standing instructions. Anything less than the above
    is a data-loss bug, not an install step.
    """
    # A symlinked CLAUDE.md must be edited through to its target: `os.replace` onto the link would
    # replace the link itself with a regular file, and unlinking it would delete the user's link
    # while leaving the block sitting in the file it pointed at.
    linked = md_path.is_symlink()
    target = md_path.resolve() if linked else md_path

    raw = target.read_bytes() if target.is_file() else None
    head = raw.decode("utf-8") if raw is not None else ""
    nl = _dominant_newline(head)
    block = ROUTING_BLOCK if nl == LF else ROUTING_BLOCK.replace(LF, nl)
    region = block[: -len(nl)]  # the block without its own trailing newline

    # Count every marker rather than finding the first of each. Reasoning from `find()` alone
    # gets three cases wrong, and all three were reachable: markers in reverse order spliced a
    # duplicate of the user's text and left a dangling fence; two blocks in one file never
    # converged; and `--remove-routing` on two blocks reported "removed" while one survived --
    # a success message that was not true. Anything other than one clean fence is refused, which
    # is what the half-marker case already did.
    n_begin, n_end = head.count(ROUTING_BEGIN), head.count(ROUTING_END)
    if n_begin != n_end:
        raise RuntimeError(
            f"{md_path} has {n_begin} '{ROUTING_BEGIN}' and {n_end} '{ROUTING_END}'; refusing to "
            f"guess where the block ends. Fix the markers by hand, then re-run."
        )
    if n_begin > 1:
        raise RuntimeError(
            f"{md_path} contains {n_begin} routing blocks. Refusing to touch it: removing one "
            f"would leave the rest while reporting success. Delete the extra blocks by hand, "
            f"then re-run."
        )
    begin, end = head.find(ROUTING_BEGIN), head.find(ROUTING_END)
    if begin != -1 and begin > end:
        raise RuntimeError(
            f"{md_path} has the routing markers in reverse order (END before BEGIN). Splicing "
            f"that would duplicate the text between them. Fix the markers by hand, then re-run."
        )

    if remove:
        if begin == -1:
            return "absent"
        # Exact slice. The previous version ran rstrip("\n") + "\n" over the head, which silently
        # collapsed the user's own blank lines: "KEEP\n\n" came back as "KEEP\n".
        tail = head[end + len(ROUTING_END):]
        if tail.startswith(nl):
            tail = tail[len(nl):]
        rest = head[:begin] + tail
        if dry_run:
            return "removed"
        if rest.strip() or linked or not target.is_file():
            _write_preserving_mode(target, rest, nl)
        else:
            target.unlink()
        return "removed"

    if begin != -1:
        if head[begin:end + len(ROUTING_END)] == region:
            return "unchanged"
        merged = head[:begin] + region + head[end + len(ROUTING_END):]
        outcome = "updated"
    else:
        merged = (head if not head or head.endswith(nl) else head + nl) + block
        outcome = "added"

    if not dry_run:
        _write_preserving_mode(target, merged, nl)
    return outcome


def install_claude_routing(md_path: Path, remove: bool, log_lines: list[str], dry_run: bool) -> None:
    """Add or remove the routing block in one CLAUDE.md, reporting exactly what happened."""
    verb = "removing" if remove else "writing"
    log(f"\n[routing] {verb} the routing block in {md_path}", log_lines)
    if dry_run:
        outcome = apply_routing(md_path, remove, True, log_lines)
        log(f"  DRY RUN would report: {outcome}", log_lines)
        return
    outcome = apply_routing(md_path, remove, False, log_lines)
    log({
        "added": "  added the routing block (the rest of the file was left as it was)",
        "updated": "  updated the existing routing block (nothing outside the markers changed)",
        "unchanged": "  already present and identical; no write",
        "removed": "  removed the routing block",
        "absent": "  no routing block was there; nothing to remove",
    }[outcome], log_lines)


def run_self_test() -> int:
    """Simulate installs into throwaway temp dirs, assert every skill is discoverable, and
    prove no real host directory is touched. Returns 0 on pass, 1 on failure. Writes nothing
    outside a TemporaryDirectory."""
    import tempfile

    source = sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").exists())
    n = len(source)
    problems: list[str] = []
    sink: list[str] = []

    # Snapshot real host + state dirs to prove the self-test never creates them.
    host_dirs = [default_target_dir("claude"), default_target_dir("codex")]
    real_state = medsci_txn.state_home()
    watched = host_dirs + [real_state]
    existed_before = {d: d.exists() for d in watched}

    prev_home = os.environ.get("MEDSCI_HOME")
    with tempfile.TemporaryDirectory(prefix="medsci-selftest-") as tmp:
        tmp_path = Path(tmp)
        os.environ["MEDSCI_HOME"] = str(tmp_path / "state")  # isolate transactional state to temp
        try:
            dest = tmp_path / "skills"
            try:
                copied = copy_skills("self-test", dest, sink, dry_run=False)  # transactional + verify
            except Exception as exc:  # noqa: BLE001
                problems.append(f"install/verify raised: {exc}")
                copied = -1
            if copied != n:
                problems.append(f"installed {copied} != source skill count {n}")
            # a second install must be idempotent (recovery + re-commit, no error)
            try:
                copy_skills("self-test", dest, sink, dry_run=False)
            except Exception as exc:  # noqa: BLE001
                problems.append(f"second (idempotent) install raised: {exc}")

            proj = tmp_path / "project"
            install_cursor_rule(proj, sink, dry_run=False)
            if not (proj / ".cursor" / "rules" / "medsci-skills.mdc").is_file():
                problems.append("cursor project rule was not written")
        finally:
            if prev_home is None:
                os.environ.pop("MEDSCI_HOME", None)
            else:
                os.environ["MEDSCI_HOME"] = prev_home

    for d in watched:
        if not existed_before[d] and d.exists():
            problems.append(f"self-test created a real dir: {d}")

    print("MedSci Skills installer self-test")
    print(f"  source skills: {n}")
    if problems:
        for p in problems:
            print(f"  FAIL: {p}")
        return 1
    print(f"  OK: {n}/{n} skills discoverable in temp target; idempotent; cursor rule written; no host/state dir touched")
    return 0


LOG_DIR = REPO_ROOT / "installers" / ".logs"
LOG_KEEP = 10  # retain the most recent N install logs; prune older


def write_log(log_lines: list[str]) -> Path:
    """Write the timestamped install log to installers/.logs/ (gitignored) and keep only
    the most recent LOG_KEEP — logs used to accumulate in the repo root."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = LOG_DIR / f"{stamp}-{LOG_NAME}"
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    old = sorted(LOG_DIR.glob(f"*-{LOG_NAME}"))
    for stale in old[:-LOG_KEEP]:
        try:
            stale.unlink()
        except OSError:
            pass
    return log_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install MedSci Skills locally.")
    parser.add_argument(
        "--target",
        choices=["all", "claude", "codex", "cursor"],
        default="all",
        help="Install target. 'all' installs Claude and Codex, and Cursor if --cursor-project is provided.",
    )
    parser.add_argument(
        "--cursor-project",
        type=Path,
        default=None,
        help="Project folder where a .cursor/rules/medsci-skills.mdc rule should be written.",
    )
    parser.add_argument(
        "--claude-project",
        type=Path,
        default=None,
        help="Opt in: add a short skill-routing block to <folder>/CLAUDE.md so plain-language "
             "requests in that project reach the right skill. Scoped to that folder; nothing else "
             "in the file is touched.",
    )
    parser.add_argument(
        "--claude-user",
        action="store_true",
        help="Opt in: add the same routing block to ~/.claude/CLAUDE.md, which Claude Code loads in "
             "EVERY project. Larger footprint than --claude-project; prefer that one unless you "
             "want it everywhere.",
    )
    parser.add_argument(
        "--remove-routing",
        action="store_true",
        help="Remove the routing block from whichever target you name with --claude-project / "
             "--claude-user. Leaves the rest of the file alone.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions without changing files.")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Simulate installs into temp dirs, assert all skills are discoverable, and touch no host directory. Exits 0 on pass.",
    )
    parser.add_argument(
        "--check-update",
        action="store_true",
        help="Report whether a newer release is available (connects to GitHub; installs nothing).",
    )
    parser.add_argument(
        "--desktop-launcher",
        action="store_true",
        help="With your consent, also place an 'Update MedSci Skills' launcher on your Desktop.",
    )
    parser.add_argument(
        "--enable-update-notify",
        action="store_true",
        help="Opt in: show a one-line 'update available' notice at Claude Code session start "
             "(merges a hook into ~/.claude/settings.json; 24h-cached; no telemetry).",
    )
    parser.add_argument(
        "--disable-update-notify",
        action="store_true",
        help="Opt out: remove the session-start update-notice hook from ~/.claude/settings.json.",
    )
    return parser.parse_args()



def _offer_contribution_reminders_once(log_lines) -> None:
    """Mention — once, ever — that the option exists. Then never again, whatever they do.

    A person who ignores the question has answered it. Asking a second time would be the exact
    nagging this setting exists to prevent, so `asked_once` is recorded whether or not they act.
    """
    import json as _json
    home = medsci_txn.state_home()
    cfg_path = home / "config.json"
    try:
        cfg = _json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.is_file() else {}
    except (ValueError, OSError):
        cfg = {}
    if cfg.get("asked_once"):
        return

    log(
        "\nTwo things, once — then we will not bring either up again:\n"
        "\n"
        "  1. If you ever adapt a skill (add your journal, fix something wrong for your specialty),\n"
        "     that change can be offered back with /contribute. Reminders are OFF by default, and\n"
        "     nothing is ever sent without a patient-data scan and your confirmation on every line.\n"
        "         python3 ~/.claude/skills/contribute/scripts/contribution_prefs.py --on\n"
        "\n"
        "  2. If this ends up saving you time, the way to say so is a star on the repository.\n"
        "     Not applause — it is how the next researcher with your problem finds it, and for\n"
        "     software with no DOI in anyone's reference list it is the closest thing to a citation.\n"
        "     Most people who write to say thanks have never done it, because nobody told them.\n"
        "     One command, no browser:\n"
        "         python3 ~/.claude/skills/contribute/scripts/star_repo.py --now\n"
        "     (or one click: https://github.com/Aperivue/medsci-skills)",
        log_lines,
    )
    cfg["asked_once"] = True
    try:
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        medsci_txn.atomic_write_json(cfg_path, cfg)
    except OSError:
        pass  # never fail an install over a preference file

def main() -> int:
    args = parse_args()
    if args.self_test:
        return run_self_test()
    if args.check_update:
        try:
            import update  # noqa: PLC0415 - optional, only when explicitly requested
            return update.check_update(medsci_txn.state_home())
        except Exception as exc:  # noqa: BLE001
            print(f"MedSci Skills: update check unavailable ({exc}).", file=sys.stderr)
            return 1
    if args.enable_update_notify or args.disable_update_notify:
        try:
            import update  # noqa: PLC0415
            home = medsci_txn.state_home()
            if args.disable_update_notify:
                r = update.unregister_session_hook(home, update.default_settings_path())
                print("Session-start update notice disabled." if r == "disabled"
                      else "Session-start update notice was not enabled; nothing to do.")
                return 0
            # Opt-in: ensure the updater home (with the hook script) exists, then register the hook.
            update.install_updater_home(REPO_ROOT, home, lambda _m: None)
            r = update.register_session_hook(home, update.default_settings_path())
            print("Opted in: Claude Code will show a one-line update notice at session start "
                  "(24h-cached, no telemetry). Disable with: install.py --disable-update-notify"
                  if r == "enabled" else "Already opted in to the session-start update notice; no change.")
            return 0
        except Exception as exc:  # noqa: BLE001
            print(f"MedSci Skills: could not change the update-notify setting ({exc}).", file=sys.stderr)
            return 1
    log_lines: list[str] = []
    log("MedSci Skills Installer", log_lines)
    log(f"Repository: {REPO_ROOT}", log_lines)
    log(f"Python: {sys.version.split()[0]}", log_lines)
    log(f"OS: {os.name}", log_lines)

    # Each target is an independent transaction: a failure on one (e.g. a fail-closed corrupt
    # journal) is logged and the others still proceed; successful targets are fully committed.
    targets = [t for t in ("claude", "codex") if args.target in {"all", t}]
    failures: list[str] = []
    for t in targets:
        try:
            copy_skills(t, default_target_dir(t), log_lines, args.dry_run)
        except Exception as exc:  # noqa: BLE001 - classroom installer shows friendly per-target errors.
            failures.append(t)
            log(f"\n[{t}] FAILED: {exc}", log_lines)
            log(f"  [{t}] left unchanged (transactional); other targets continue.", log_lines)

    try:
        if args.target == "cursor" and not args.cursor_project:
            log("\n[cursor] skipped: pass --cursor-project <folder> to install a Cursor rule.", log_lines)
        if args.cursor_project:
            install_cursor_rule(args.cursor_project.expanduser().resolve(), log_lines, args.dry_run)
    except Exception as exc:  # noqa: BLE001
        failures.append("cursor")
        log(f"\n[cursor] FAILED: {exc}", log_lines)

    try:
        if args.claude_project:
            install_claude_routing(
                args.claude_project.expanduser().resolve() / "CLAUDE.md",
                args.remove_routing, log_lines, args.dry_run,
            )
        if args.claude_user:
            install_claude_routing(
                Path.home() / ".claude" / "CLAUDE.md",
                args.remove_routing, log_lines, args.dry_run,
            )
        if args.remove_routing and not (args.claude_project or args.claude_user):
            log("\n[routing] --remove-routing needs a target: pass --claude-project <folder> "
                "and/or --claude-user.", log_lines)
    except Exception as exc:  # noqa: BLE001
        failures.append("routing")
        log(f"\n[routing] FAILED: {exc}", log_lines)
        log("  the CLAUDE.md was left exactly as it was.", log_lines)

    # Place the one-click updater under ~/.medsci-skills/updater/ so a future update needs no
    # GitHub/terminal even if this download folder is deleted (best-effort; never fatal).
    if not args.dry_run:
        try:
            import update  # noqa: PLC0415
            update.install_updater_home(REPO_ROOT, medsci_txn.state_home(),
                                        lambda m: log(m, log_lines),
                                        desktop=args.desktop_launcher)
        except Exception as exc:  # noqa: BLE001
            log(f"\n[updater] could not install the one-click updater ({exc}); updates still work via re-running the installer.", log_lines)

    # One-time nudge: if the in-app update reminder is not enabled, surface how to turn it on.
    # (The classroom installers enable it automatically; this covers npx / manual installs so a
    # clinician who installed via "install this repo" is told how to get update notices.) Read-only.
    if not args.dry_run:
        try:
            import update  # noqa: PLC0415
            if not update.session_hook_enabled(medsci_txn.state_home(), update.default_settings_path()):
                log("\n[update reminders] OFF — Claude Code will not tell you when a new version is out.", log_lines)
                log("  Turn on with:  npx medsci-skills install --enable-update-notify", log_lines)
                log("  (or:           python3 installers/install.py --enable-update-notify)", log_lines)
        except Exception:  # noqa: BLE001 - nudge is best-effort, never block the install
            pass

    if failures:
        log(f"\nCompleted with errors on: {', '.join(failures)}. Other targets are fully installed.", log_lines)
        log("If this happened during class, send the install log to the instructor.", log_lines)
        log_path = write_log(log_lines)
        print(f"\nInstall log: {log_path}")
        return 1

    # Say what ELSE this computer needs, while they are still looking at the screen.
    #
    # Every integrity detector is stdlib-only, so the install above is enough to use most of the
    # toolkit. But a few skills need a program we do not ship — pandoc to render a manuscript into
    # a journal-formatted Word file, poppler to read a submission PDF. Those skills already fail
    # politely; the problem is that they fail *later*, in the middle of the work, to someone who
    # will not go and install a package manager at that moment. Tell them now, when the answer is
    # one command. Read-only, asks nothing, installs nothing, and can never fail the install.
    if not args.dry_run:
        try:
            import doctor  # noqa: PLC0415

            doctor.brief_summary(lambda m: log(m, log_lines))
        except Exception:  # noqa: BLE001 - a setup *check* must never break an install that worked
            pass

    _offer_contribution_reminders_once(log_lines)
    log("\nDone. Restart Claude Code, Codex, or Cursor before testing the skills.", log_lines)
    log("First test prompt:", log_lines)
    log("MedSci Skills가 설치됐는지 확인하고, 오늘 실습에 쓸 대표 스킬 5개만 보여줘.", log_lines)
    log_path = write_log(log_lines)
    print(f"\nInstall log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

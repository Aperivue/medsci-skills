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


def write_log(log_lines: list[str]) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = REPO_ROOT / f"{stamp}-{LOG_NAME}"
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
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

    if failures:
        log(f"\nCompleted with errors on: {', '.join(failures)}. Other targets are fully installed.", log_lines)
        log("If this happened during class, send the install log to the instructor.", log_lines)
        log_path = write_log(log_lines)
        print(f"\nInstall log: {log_path}")
        return 1

    log("\nDone. Restart Claude Code, Codex, or Cursor before testing the skills.", log_lines)
    log("First test prompt:", log_lines)
    log("MedSci Skills가 설치됐는지 확인하고, 오늘 실습에 쓸 대표 스킬 5개만 보여줘.", log_lines)
    log_path = write_log(log_lines)
    print(f"\nInstall log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

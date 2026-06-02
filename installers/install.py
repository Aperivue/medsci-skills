#!/usr/bin/env python3
"""Install MedSci Skills for local agent apps.

This installer is intentionally conservative and dependency-free. It copies the
repository's skills into common local skill folders and optionally writes a
small Cursor project rule that tells Cursor where to find the skills.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import sys
from pathlib import Path


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

    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").exists())
    log(f"\n[{target}] installing {len(skill_dirs)} skills to {dest}", log_lines)

    if dry_run:
        for skill in skill_dirs:
            log(f"  DRY RUN copy {skill.name}", log_lines)
        return len(skill_dirs)

    dest.mkdir(parents=True, exist_ok=True)
    for skill in skill_dirs:
        shutil.copytree(skill, dest / skill.name, dirs_exist_ok=True)
        log(f"  installed {skill.name}", log_lines)
    verify_discoverable(dest, [s.name for s in skill_dirs], log_lines)
    return len(skill_dirs)


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

    # Snapshot real host dirs to prove the self-test never creates them.
    host_dirs = [default_target_dir("claude"), default_target_dir("codex")]
    existed_before = {d: d.exists() for d in host_dirs}

    with tempfile.TemporaryDirectory(prefix="medsci-selftest-") as tmp:
        tmp_path = Path(tmp)
        dest = tmp_path / "skills"
        try:
            copied = copy_skills("self-test", dest, sink, dry_run=False)  # includes verify_discoverable
        except Exception as exc:  # noqa: BLE001
            problems.append(f"copy/verify raised: {exc}")
            copied = -1
        if copied != n:
            problems.append(f"copied {copied} != source skill count {n}")

        proj = tmp_path / "project"
        install_cursor_rule(proj, sink, dry_run=False)
        if not (proj / ".cursor" / "rules" / "medsci-skills.mdc").is_file():
            problems.append("cursor project rule was not written")

    for d in host_dirs:
        if not existed_before[d] and d.exists():
            problems.append(f"self-test created a real host dir: {d}")

    print("MedSci Skills installer self-test")
    print(f"  source skills: {n}")
    if problems:
        for p in problems:
            print(f"  FAIL: {p}")
        return 1
    print(f"  OK: {n}/{n} skills discoverable in temp target; cursor rule written; no host dir touched")
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return run_self_test()
    log_lines: list[str] = []
    log("MedSci Skills Installer", log_lines)
    log(f"Repository: {REPO_ROOT}", log_lines)
    log(f"Python: {sys.version.split()[0]}", log_lines)
    log(f"OS: {os.name}", log_lines)

    try:
        if args.target in {"all", "claude"}:
            copy_skills("claude", default_target_dir("claude"), log_lines, args.dry_run)
        if args.target in {"all", "codex"}:
            copy_skills("codex", default_target_dir("codex"), log_lines, args.dry_run)
        if args.target == "cursor" and not args.cursor_project:
            log("\n[cursor] skipped: pass --cursor-project <folder> to install a Cursor rule.", log_lines)
        if args.cursor_project:
            install_cursor_rule(args.cursor_project.expanduser().resolve(), log_lines, args.dry_run)

        log("\nDone. Restart Claude Code, Codex, or Cursor before testing the skills.", log_lines)
        log("First test prompt:", log_lines)
        log("MedSci Skills가 설치됐는지 확인하고, 오늘 실습에 쓸 대표 스킬 5개만 보여줘.", log_lines)
    except Exception as exc:  # noqa: BLE001 - classroom installer should show friendly errors.
        log(f"\nERROR: {exc}", log_lines)
        log("If this happened during class, send the install log to the instructor.", log_lines)
        write_log(log_lines)
        return 1

    log_path = write_log(log_lines)
    print(f"\nInstall log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""`.cursor/rules/medsci-skills.mdc` is written into a project folder, and that folder is usually a
git repository. So the two properties worth testing are the ones that survive a `git add`: the file
must carry nothing machine-specific, and writing it must not be able to leave a half-written file
behind.

The version this replaces embedded `REPO_ROOT` -- the absolute path of the installing user's home
directory -- and wrote with `Path.write_text`, which opens in "w" mode and truncates first.

Every case runs in a TemporaryDirectory. Nothing outside it is read or written.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import install  # noqa: E402
import medsci_txn  # noqa: E402

FAIL: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    print(f"{'PASS' if cond else 'FAIL'}  {label}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAIL.append(label)


def run() -> int:
    with tempfile.TemporaryDirectory() as td:
        proj = Path(td) / "project"
        proj.mkdir()
        rule = proj / ".cursor" / "rules" / "medsci-skills.mdc"

        install.install_cursor_rule(proj, [], dry_run=False)
        check("rule written", rule.is_file())
        body = rule.read_text(encoding="utf-8")

        # The reason this test exists. `.cursor/rules/` gets committed; a home path in it is the
        # installer's name travelling into a shared repository.
        check("no home path in the rule",
              "/Users/" not in body and "/home/" not in body and "C:\\" not in body,
              body[:200])
        check("no repository path in the rule", str(install.REPO_ROOT) not in body)
        # It must still be a usable Cursor rule, not just an empty file that passes the scan.
        check("frontmatter intact", body.startswith("---") and "alwaysApply:" in body)
        check("points at where Cursor actually reads skills",
              "~/.claude/skills/" in body and "~/.agents/skills/" in body)
        check("names orchestrate as the entry point", "orchestrate" in body)

        # Idempotent: a second run produces the same bytes.
        first = rule.read_bytes()
        install.install_cursor_rule(proj, [], dry_run=False)
        check("re-run produces identical bytes", rule.read_bytes() == first)

        # Mode is preserved (POSIX only -- on Windows os.chmod moves the read-only bit and nothing
        # else, so the assertion could not tell preserved from widened; skipped out loud).
        if os.name != "posix":
            print("SKIP  rule mode preserved (POSIX modes are not meaningful on this platform)")
        else:
            os.chmod(rule, 0o600)
            install.install_cursor_rule(proj, [], dry_run=False)
            check("rule mode preserved", (os.stat(rule).st_mode & 0o777) == 0o600,
                  oct(os.stat(rule).st_mode & 0o777))

        # An interrupted write must leave the previous file intact, not a truncated one.
        before = rule.read_bytes()
        real_replace = medsci_txn.os.replace

        def boom(*_a, **_k):
            raise OSError("simulated interruption")

        medsci_txn.os.replace = boom
        try:
            install.install_cursor_rule(proj, [], dry_run=False)
            check("interrupted write raises", False, "it returned normally")
        except OSError:
            check("interrupted write raises", True)
        finally:
            medsci_txn.os.replace = real_replace
        check("interrupted write left the rule byte-identical", rule.read_bytes() == before)
        leftovers = sorted(q.name for q in rule.parent.iterdir())
        check("interrupted write left no temp file behind",
              leftovers == ["medsci-skills.mdc"], str(leftovers))

        # --dry-run writes nothing at all.
        proj2 = Path(td) / "dry"
        proj2.mkdir()
        install.install_cursor_rule(proj2, [], dry_run=True)
        check("dry run created nothing", not (proj2 / ".cursor").exists())

    print()
    if FAIL:
        print(f"FAILED: {len(FAIL)} — " + "; ".join(FAIL))
        return 1
    print("All Cursor-rule checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

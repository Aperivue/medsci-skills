#!/usr/bin/env python3
"""The routing block goes into a CLAUDE.md — a file the user keeps their OWN standing
instructions in. So the thing under test is not "does the block appear". It is "does
everything else survive", which is the property `install_cursor_rule`'s
`rule_path.write_text(body)` does not have.

Every case runs in a TemporaryDirectory. Nothing outside it is read or written.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import install  # noqa: E402

FAIL: list[str] = []
USER_TEXT = (
    "# My instructions\n\nAlways answer in Korean.\nNever touch ~/secrets.\n\n"
    "## House style\n\n- em-dashes are fine\n"
)


def check(label: str, cond: bool, detail: str = "") -> None:
    print(f"{'PASS' if cond else 'FAIL'}  {label}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAIL.append(label)


def run() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # 1. A missing file is created and carries the block.
        p = tmp / "fresh" / "CLAUDE.md"
        out = install.apply_routing(p, remove=False, dry_run=False, log_lines=[])
        check("missing file -> added", out == "added", out)
        check("block present", install.ROUTING_BEGIN in p.read_text() and install.ROUTING_END in p.read_text())

        # 2. THE REGRESSION. An existing file keeps every byte the user wrote.
        #    A wholesale write_text(body) fails exactly here.
        p2 = tmp / "existing" / "CLAUDE.md"
        p2.parent.mkdir(parents=True)
        p2.write_text(USER_TEXT, encoding="utf-8")
        install.apply_routing(p2, remove=False, dry_run=False, log_lines=[])
        after = p2.read_text(encoding="utf-8")
        check("user content survives an add", USER_TEXT.rstrip("\n") in after,
              "the user's own CLAUDE.md was clobbered")
        check("block appended after user content", after.index("My instructions") < after.index(install.ROUTING_BEGIN))

        # 3. Idempotent: a second run neither duplicates nor rewrites.
        out = install.apply_routing(p2, remove=False, dry_run=False, log_lines=[])
        check("re-run -> unchanged", out == "unchanged", out)
        check("no duplicate block", p2.read_text().count(install.ROUTING_BEGIN) == 1)

        # 4. A stale block is replaced in place; text on both sides is untouched.
        p3 = tmp / "stale" / "CLAUDE.md"
        p3.parent.mkdir(parents=True)
        p3.write_text(
            f"BEFORE\n\n{install.ROUTING_BEGIN}\nold and wrong\n{install.ROUTING_END}\n\nAFTER\n",
            encoding="utf-8",
        )
        out = install.apply_routing(p3, remove=False, dry_run=False, log_lines=[])
        body = p3.read_text(encoding="utf-8")
        check("stale block -> updated", out == "updated", out)
        check("stale content gone", "old and wrong" not in body)
        check("text before and after preserved", body.startswith("BEFORE") and body.rstrip().endswith("AFTER"))

        # 5. Removal takes the block and nothing else.
        out = install.apply_routing(p2, remove=True, dry_run=False, log_lines=[])
        body = p2.read_text(encoding="utf-8")
        check("remove -> removed", out == "removed", out)
        check("block gone", install.ROUTING_BEGIN not in body)
        check("user content survives a remove", USER_TEXT.rstrip("\n") in body)
        check("removing twice is not an error", install.apply_routing(p2, True, False, []) == "absent")

        # 6. A file that held only our block is cleaned up rather than left as a husk.
        install.apply_routing(p, remove=True, dry_run=False, log_lines=[])
        check("block-only file is deleted on remove", not p.exists())

        # 7. Half a fence is refused — guessing the end could eat the user's text.
        p4 = tmp / "half" / "CLAUDE.md"
        p4.parent.mkdir(parents=True)
        half = f"keep me\n{install.ROUTING_BEGIN}\ndangling\n"
        p4.write_text(half, encoding="utf-8")
        try:
            install.apply_routing(p4, remove=False, dry_run=False, log_lines=[])
            check("half marker refused", False, "it proceeded instead of raising")
        except RuntimeError:
            check("half marker refused", True)
        check("half-marker file untouched", p4.read_text(encoding="utf-8") == half)

        # 8. --dry-run writes nothing.
        p5 = tmp / "dry" / "CLAUDE.md"
        out = install.apply_routing(p5, remove=False, dry_run=True, log_lines=[])
        check("dry run reports added", out == "added", out)
        check("dry run created no file", not p5.exists())

        # 9. The block carries nothing machine-specific. A CLAUDE.md gets committed, and the
        #    absolute path of a home directory is the installer's name.
        blk = install.ROUTING_BLOCK
        check("no home path in block", "/Users/" not in blk and "/home/" not in blk and "C:\\\\" not in blk)
        check("no repo path in block", str(install.REPO_ROOT) not in blk)
        check("block stays small", len(blk.split()) < 350, f"{len(blk.split())} words on every request")

    print()
    if FAIL:
        print(f"FAILED: {len(FAIL)} — " + "; ".join(FAIL))
        return 1
    print("All routing checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

#!/usr/bin/env python3
"""The routing block goes into a CLAUDE.md -- a file the user keeps their OWN standing
instructions in. So the thing under test is not "does the block appear". It is "does
everything else survive, byte for byte".

The first version of this file asserted preservation with `USER_TEXT.rstrip("\\n") in after`.
A substring test cannot see a collapsed blank line, a CRLF rewritten to LF, or a changed file
mode -- and an external review found exactly those defects sitting under a green suite. The
assertions here compare bytes.

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
USER_TEXT = (
    "# My instructions\n\nAlways answer in Korean.\nNever touch ~/secrets.\n\n"
    "## House style\n\n- em-dashes are fine\n\n"
)
BARE_LF = b"\n"
CRLF_B = b"\r\n"


def check(label: str, cond: bool, detail: str = "") -> None:
    print(f"{'PASS' if cond else 'FAIL'}  {label}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAIL.append(label)


def outside(raw: bytes, nl: bytes = BARE_LF) -> bytes:
    """The file's bytes with the managed region removed, so the rest can be compared exactly."""
    b = raw.find(install.ROUTING_BEGIN.encode())
    e = raw.find(install.ROUTING_END.encode())
    if b == -1:
        return raw
    tail = raw[e + len(install.ROUTING_END.encode()):]
    if tail.startswith(nl):
        tail = tail[len(nl):]
    return raw[:b] + tail


def run() -> int:  # noqa: PLR0915 - a flat list of cases reads better than nested helpers
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        original = USER_TEXT.encode()

        # 1. A missing file is created and carries the block.
        p = tmp / "fresh" / "CLAUDE.md"
        out = install.apply_routing(p, remove=False, dry_run=False, log_lines=[])
        check("missing file -> added", out == "added", out)
        check("block present", install.ROUTING_BEGIN in p.read_text() and install.ROUTING_END in p.read_text())

        # 2. THE REGRESSION. An existing file keeps every byte the user wrote -- not "contains
        #    the text somewhere", but byte-identical outside the managed region.
        p2 = tmp / "existing" / "CLAUDE.md"
        p2.parent.mkdir(parents=True)
        p2.write_bytes(original)
        install.apply_routing(p2, remove=False, dry_run=False, log_lines=[])
        after = p2.read_bytes()
        check("user bytes survive an add (exact)", outside(after) == original,
              f"{outside(after)!r} != {original!r}")
        check("block appended after user content",
              after.index(b"My instructions") < after.index(install.ROUTING_BEGIN.encode()))

        # 3. Idempotent: a second run neither duplicates nor rewrites.
        out = install.apply_routing(p2, remove=False, dry_run=False, log_lines=[])
        check("re-run -> unchanged", out == "unchanged", out)
        check("no duplicate block", p2.read_text().count(install.ROUTING_BEGIN) == 1)

        # 4. A stale block is replaced in place; bytes on both sides are untouched.
        p3 = tmp / "stale" / "CLAUDE.md"
        p3.parent.mkdir(parents=True)
        stale_outside = b"BEFORE\n\nAFTER\n"
        p3.write_bytes(
            b"BEFORE\n\n" + install.ROUTING_BEGIN.encode() + b"\nold and wrong\n"
            + install.ROUTING_END.encode() + b"\nAFTER\n"
        )
        out = install.apply_routing(p3, remove=False, dry_run=False, log_lines=[])
        check("stale block -> updated", out == "updated", out)
        check("stale content gone", b"old and wrong" not in p3.read_bytes())
        check("bytes around a replaced block are exact", outside(p3.read_bytes()) == stale_outside,
              f"{outside(p3.read_bytes())!r}")

        # 5. ROUND TRIP. add -> remove must return the original bytes. The old removal ran
        #    rstrip + "\n" over the head, so b"KEEP\n\n" came back as b"KEEP\n".
        for shape in (b"KEEP\n\n", b"KEEP\n", b"A\n\n\nB\n\n", b"# T\n\n- a\n- b\n"):
            p4 = tmp / "rt" / "CLAUDE.md"
            p4.parent.mkdir(parents=True, exist_ok=True)
            p4.write_bytes(shape)
            install.apply_routing(p4, remove=False, dry_run=False, log_lines=[])
            install.apply_routing(p4, remove=True, dry_run=False, log_lines=[])
            check(f"round trip is byte-exact for {shape!r}", p4.read_bytes() == shape,
                  f"got {p4.read_bytes()!r}")

        # 6. The one documented exception: a file with no trailing newline gains one, and removal
        #    does not take it back. Asserted so it stays a decision rather than a surprise.
        p5 = tmp / "nonl" / "CLAUDE.md"
        p5.parent.mkdir(parents=True)
        p5.write_bytes(b"KEEP")
        install.apply_routing(p5, remove=False, dry_run=False, log_lines=[])
        install.apply_routing(p5, remove=True, dry_run=False, log_lines=[])
        check("documented: a missing trailing newline is added and kept",
              p5.read_bytes() == b"KEEP\n", f"got {p5.read_bytes()!r}")

        # 7. CRLF. read_text() translated these to LF and wrote them back that way, silently
        #    rewriting every line of a Windows user's file.
        p6 = tmp / "crlf" / "CLAUDE.md"
        p6.parent.mkdir(parents=True)
        crlf = b"# Mine\r\n\r\nUse R.\r\n"
        p6.write_bytes(crlf)
        install.apply_routing(p6, remove=False, dry_run=False, log_lines=[])
        body = p6.read_bytes()
        check("CRLF bytes outside the block are preserved", outside(body, CRLF_B) == crlf,
              f"{outside(body, CRLF_B)!r}")
        bare = body.count(BARE_LF) - body.count(CRLF_B)
        check("the block itself introduces no bare LF", bare == 0, f"{bare} bare LF")
        install.apply_routing(p6, remove=True, dry_run=False, log_lines=[])
        check("CRLF round trip is byte-exact", p6.read_bytes() == crlf, f"got {p6.read_bytes()!r}")

        # 8. An interrupted write must leave the previous file intact. Path.write_text opened in
        #    "w" mode and truncated first, so an interrupt there produced a zero-byte CLAUDE.md.
        p7 = tmp / "atomic" / "CLAUDE.md"
        p7.parent.mkdir(parents=True)
        p7.write_bytes(original)
        real_replace = medsci_txn.os.replace

        def boom(*_a, **_k):
            raise OSError("simulated interruption")

        medsci_txn.os.replace = boom
        try:
            install.apply_routing(p7, remove=False, dry_run=False, log_lines=[])
            check("interrupted write raises", False, "it returned normally")
        except OSError:
            check("interrupted write raises", True)
        finally:
            medsci_txn.os.replace = real_replace
        check("interrupted write left the file byte-identical", p7.read_bytes() == original,
              f"got {p7.read_bytes()!r}")
        leftovers = sorted(q.name for q in p7.parent.iterdir())
        check("interrupted write left no temp file behind", leftovers == ["CLAUDE.md"], str(leftovers))

        # 9. Permissions survive. A user who ran chmod 600 should not have it widened by an install.
        p8 = tmp / "mode" / "CLAUDE.md"
        p8.parent.mkdir(parents=True)
        p8.write_bytes(original)
        os.chmod(p8, 0o600)
        install.apply_routing(p8, remove=False, dry_run=False, log_lines=[])
        check("file mode preserved", (os.stat(p8).st_mode & 0o777) == 0o600,
              oct(os.stat(p8).st_mode & 0o777))

        # 10. A symlinked CLAUDE.md is edited through to its target. Deleting the link would remove
        #     the user's link and leave the block in the file it pointed at -- wrong twice.
        shared = tmp / "shared.md"
        shared.write_bytes(install.ROUTING_BLOCK.encode())
        linkdir = tmp / "linked"
        linkdir.mkdir()
        link = linkdir / "CLAUDE.md"
        try:
            link.symlink_to(shared)
        except (OSError, NotImplementedError):
            print("SKIP  symlink cases (symlinks unavailable on this platform)")
        else:
            out = install.apply_routing(link, remove=True, dry_run=False, log_lines=[])
            check("symlink remove -> removed", out == "removed", out)
            check("the symlink itself still exists", link.is_symlink())
            check("the block is gone from the symlink target",
                  install.ROUTING_BEGIN not in shared.read_text())

        # 11. Removal takes the block and nothing else.
        out = install.apply_routing(p2, remove=True, dry_run=False, log_lines=[])
        check("remove -> removed", out == "removed", out)
        check("user bytes survive a remove (exact)", p2.read_bytes() == original,
              f"got {p2.read_bytes()!r}")
        check("removing twice is not an error", install.apply_routing(p2, True, False, []) == "absent")

        # 12. A regular file that held only our block is cleaned up rather than left as a husk.
        install.apply_routing(p, remove=True, dry_run=False, log_lines=[])
        check("block-only file is deleted on remove", not p.exists())

        # 13. Half a fence is refused -- guessing the end could eat the user's text.
        p9 = tmp / "half" / "CLAUDE.md"
        p9.parent.mkdir(parents=True)
        half = f"keep me\n{install.ROUTING_BEGIN}\ndangling\n".encode()
        p9.write_bytes(half)
        try:
            install.apply_routing(p9, remove=False, dry_run=False, log_lines=[])
            check("half marker refused", False, "it proceeded instead of raising")
        except RuntimeError:
            check("half marker refused", True)
        check("half-marker file untouched", p9.read_bytes() == half)

        # 14. Markers in REVERSE order. Both are present, so the half-marker guard passes them
        #     through; splicing on find() duplicated the text between them.
        p10 = tmp / "reversed" / "CLAUDE.md"
        p10.parent.mkdir(parents=True)
        rev = f"HEAD\n{install.ROUTING_END}\nIMPORTANT USER NOTES\n{install.ROUTING_BEGIN}\nTAIL\n".encode()
        p10.write_bytes(rev)
        try:
            install.apply_routing(p10, remove=False, dry_run=False, log_lines=[])
            check("reversed markers refused", False, "it spliced instead of raising")
        except RuntimeError:
            check("reversed markers refused", True)
        check("reversed-marker file untouched", p10.read_bytes() == rev)

        # 15. Two blocks in one file. The old code replaced the first and left the second, so
        #     --remove-routing reported "removed" with a block still in the file.
        p11 = tmp / "double" / "CLAUDE.md"
        p11.parent.mkdir(parents=True)
        dbl = f"A\n{install.ROUTING_BLOCK}\nB\n{install.ROUTING_BLOCK}\nC\n".encode()
        p11.write_bytes(dbl)
        for mode in (False, True):
            try:
                install.apply_routing(p11, remove=mode, dry_run=False, log_lines=[])
                check(f"two blocks refused (remove={mode})", False, "it reported success")
            except RuntimeError:
                check(f"two blocks refused (remove={mode})", True)
        check("two-block file untouched", p11.read_bytes() == dbl)

        # 16. --dry-run writes nothing.
        p12 = tmp / "dry" / "CLAUDE.md"
        out = install.apply_routing(p12, remove=False, dry_run=True, log_lines=[])
        check("dry run reports added", out == "added", out)
        check("dry run created no file", not p12.exists())

        # 17. The block carries nothing machine-specific. A CLAUDE.md gets committed, and the
        #     absolute path of a home directory is the installer's name.
        blk = install.ROUTING_BLOCK
        check("no home path in block",
              "/Users/" not in blk and "/home/" not in blk and "C:\\" not in blk)
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

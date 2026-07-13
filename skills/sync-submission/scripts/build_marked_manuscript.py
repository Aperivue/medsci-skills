#!/usr/bin/env python3
"""Build a marked (tracked-changes) manuscript by driving Microsoft Word's own
Compare, then prove the result with `check_marked_manuscript.py`.

    build_marked_manuscript.py --original R0.docx --revised v8_clean.docx \\
        --out marked.docx --author "Submitting Author" [--line-numbers]

WHY WORD. `pandiff` and LibreOffice `--compare` corrupt OOXML on real
manuscripts — tables collapse and affiliation superscripts are lost. Word's
Compare is the only producer safe enough for a submission. It does *not* follow
that a human must click through it: Word for Mac's AppleScript dictionary
exposes `compare` with `author name`, `detect format changes` and `ignore all
comparison warnings`, so the whole build is scriptable and every revision is
attributed correctly at source — no post-hoc rewriting of `w:author`.

Two traps that defeat naive automation, both handled here:

  1. SANDBOX. `save as` to a *new* path makes Word raise a modal "Grant File
     Access" sheet, and AppleScript then blocks until a human dismisses it — the
     script appears to hang. Avoided by seeding the destination with a copy of
     the original, letting Word OPEN that file (Word may always write a file it
     opened itself), comparing in place, and calling a plain `save`.

  2. OTHER DOCUMENTS. The user may have unrelated documents open in Word. Only
     the document this script opened is closed, by name.

This is a macOS + Microsoft Word tool and is therefore NOT a portable detector:
it is deliberately excluded from the detector catalog. The verification half —
`check_marked_manuscript.py` — is stdlib-only, runs anywhere, and can audit a
marked file produced by any means (including a Word GUI pass).
"""

from __future__ import annotations

import argparse
import platform
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_marked_manuscript import check  # noqa: E402

APPLESCRIPT = """
with timeout of {timeout} seconds
  tell application "Microsoft Word"
    open POSIX file "{out}"
    set d to active document
    compare d path "{revised}" author name "{author}" ¬
      target compare target current ¬
      detect format changes false ¬
      ignore all comparison warnings true
    delay 3
    save d
    delay 2
    close d saving no
    return "ok"
  end tell
end timeout
"""


def _as_literal(s: str) -> str:
    """Escape a value for interpolation into an AppleScript string literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def run_compare(original: Path, revised: Path, out: Path, author: str, timeout: int) -> None:
    if platform.system() != "Darwin":
        raise SystemExit(
            "build_marked_manuscript.py drives Microsoft Word via AppleScript and runs on "
            "macOS only. Produce the marked file with Word's Compare on a Mac (or by hand), "
            "then verify it anywhere with check_marked_manuscript.py."
        )

    # Seed the destination with the original so Word opens — and may therefore write — it.
    shutil.copyfile(original, out)
    script = APPLESCRIPT.format(
        timeout=timeout,
        out=_as_literal(str(out)),
        revised=_as_literal(str(revised)),
        author=_as_literal(author),
    )
    try:
        p = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=timeout + 30
        )
    except subprocess.TimeoutExpired:
        raise SystemExit(
            "Word did not respond. It is most likely showing a modal sheet — check for a "
            '"Grant File Access" dialog and dismiss it, then re-run.'
        )
    if p.returncode != 0:
        raise SystemExit(f"Word Compare failed: {p.stderr.strip()}")


def inject_line_numbers(path: Path) -> None:
    """Continuous line numbers — most journals require them on a revision."""
    ln = '<w:lnNumType w:countBy="1" w:restart="continuous"/>'
    tmp = path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.namelist():
            data = zin.read(item)
            if item == "word/document.xml":
                xml = data.decode("utf-8")
                if "w:lnNumType" not in xml:
                    xml, n = re.subn(r"<w:pgMar\b[^>]*/>", lambda m: m.group(0) + ln, xml)
                    if n == 0:
                        xml = xml.replace("</w:sectPr>", ln + "</w:sectPr>")
                data = xml.encode("utf-8")
            zout.writestr(item, data)
    shutil.move(str(tmp), str(path))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--original",
        required=True,
        type=Path,
        help="baseline = the version the reviewers saw (R0), NOT the previous round's clean copy",
    )
    ap.add_argument("--revised", required=True, type=Path, help="the new clean manuscript")
    ap.add_argument("--out", required=True, type=Path, help="marked (tracked-changes) file to write")
    ap.add_argument(
        "--author", required=True, help="name to attribute every revision to (the submitting author)"
    )
    ap.add_argument("--line-numbers", action="store_true", help="inject continuous line numbering")
    ap.add_argument("--timeout", type=int, default=180)
    a = ap.parse_args()

    for f in (a.original, a.revised):
        if not f.is_file():
            raise SystemExit(f"not found: {f}")
    a.out.parent.mkdir(parents=True, exist_ok=True)

    run_compare(a.original.resolve(), a.revised.resolve(), a.out.resolve(), a.author, a.timeout)
    if a.line_numbers:
        inject_line_numbers(a.out)

    findings, summary = check(a.out, a.original, a.revised, a.author)
    m = summary["revision_marks"]
    print(
        f"{a.out.name}: ins {m['ins']}, del {m['del']}, "
        f"moveTo {m['moveTo']}, moveFrom {m['moveFrom']}"
    )
    for f in findings:
        print(f"  [{f['severity'].upper()}] {f['verdict']}: {f['detail']}")
    if findings:
        raise SystemExit("\nverification FAILED — do not upload this file")

    print("  OK — accept-all == revised, reject-all == original; marked manuscript verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())

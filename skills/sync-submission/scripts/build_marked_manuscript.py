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

  1. SANDBOX. Word for Mac is sandboxed. Touching a file it was never granted
     makes it raise a modal "Grant File Access" sheet, and AppleScript then
     blocks until a human dismisses it — the script appears to hang, then fails
     with an AppleEvent timeout. Writing a new path triggers it, and so does
     READING one: `compare ... path` hands Word the revised manuscript as a bare
     path it never opened. Seeding the destination with a copy of the original
     (an earlier version of this script) cured only the write. Both files are
     therefore copied into a private folder inside Word's own container, which
     Word may always read and write, compared there, and the result moved to
     --out. The folder holds manuscript copies, so it is removed whether the run
     succeeds or fails.

  2. OTHER DOCUMENTS. The user may have unrelated documents open in Word. Only
     the document this script opened is closed, by name.

This is a macOS + Microsoft Word tool and is therefore NOT a portable detector:
it is deliberately excluded from the detector catalog. The verification half —
`check_marked_manuscript.py` — is stdlib-only, runs anywhere, and can audit a
marked file produced by any means (including a Word GUI pass).
"""

from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_marked_manuscript import check  # noqa: E402

# Word's sandbox container. Anything under it is Word's own and never prompts. It exists once Word
# has been launched; when it does not, staging falls back to --out's folder (and may prompt).
WORD_DOCUMENTS = Path.home() / "Library/Containers/com.microsoft.Word/Data/Documents"

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

    # --out is deleted before Word starts (below), so it must not BE an input: pointed at
    # --original that deletion destroys the manuscript, and pointed at --revised an earlier version
    # of this script overwrote it with the original. A symlink or hard link counts as the same file.
    for src in (original, revised):
        if out.resolve() == src.resolve() or (out.exists() and out.samefile(src)):
            raise SystemExit(f"--out must be a new file, not one of the inputs: {out}")

    # Nothing may sit at --out unless this run produced it. A Compare that dies must not leave a
    # plausible .docx at exactly the path the user asked the marked manuscript to be written to:
    # observed on an AJNR major revision, where an earlier version of this script seeded --out
    # with the original, the AppleEvent failed -1712, and the copy it left carried zero tracked
    # changes yet was indistinguishable by inspection from a marked manuscript with nothing to
    # mark. A file left by an earlier run is no better, so it goes before Word starts.
    out.unlink(missing_ok=True)

    if WORD_DOCUMENTS.is_dir():
        staging = Path(tempfile.mkdtemp(prefix="medsci-marked-", dir=WORD_DOCUMENTS))
        sandboxed = True
    else:
        print(
            f"WARN: Word's sandbox container was not found ({WORD_DOCUMENTS}); comparing next to "
            f"--out instead. Word may ask for file access — if it does, the run will wait.",
            file=sys.stderr,
        )
        staging = Path(tempfile.mkdtemp(prefix=".medsci-marked-", dir=out.parent))
        sandboxed = False

    # Unique names: Word may still hold a same-named document from an earlier, failed run.
    token = staging.name.rsplit("-", 1)[-1]
    seed = staging / f"marked_{token}.docx"
    staged_revised = staging / f"revised_{token}.docx"

    def _abandon(message: str) -> "SystemExit":
        out.unlink(missing_ok=True)
        return SystemExit(
            f"{message}\nWord may still have {seed.name} open, possibly behind a dialog: cancel "
            f"the dialog and close the document without saving. Nothing was written to {out.name}."
        )

    try:
        # Word opens the seed and saves the comparison into it — it may always write a file it
        # opened itself — and reads the revised copy beside it.
        shutil.copyfile(original, seed)
        shutil.copyfile(revised, staged_revised)
        script = APPLESCRIPT.format(
            timeout=timeout,
            out=_as_literal(str(seed)),
            revised=_as_literal(str(staged_revised)),
            author=_as_literal(author),
        )
        try:
            p = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=timeout + 30
            )
        except subprocess.TimeoutExpired:
            raise _abandon("Word did not respond, and osascript itself had to be stopped.")
        if p.returncode != 0:
            err = p.stderr.strip()
            hint = ""
            if "-1712" in err or "timed out" in err.lower():
                # From here a waiting dialog and a slow comparison are the same failure, so name
                # both. Before staging, a 300-second run that was only ever waiting on a "Grant
                # File Access" sheet was told to raise --timeout.
                dialog = (
                    'a "Grant File Access" sheet, since the files could not be staged inside '
                    "Word's container"
                    if not sandboxed
                    else "a document-recovery, file-conversion or other prompt"
                )
                hint = (
                    f"\nThat is the AppleEvent timeout: Word did not finish within --timeout "
                    f"({timeout}s). Look at Word before re-running. If it is showing a dialog — "
                    f"{dialog} — that is what it was waiting on, and a longer --timeout will not "
                    f"help. If it is not, Compare needed longer: a whole-manuscript revision "
                    f"routinely does, so re-run with a larger --timeout."
                )
            raise _abandon(f"Word Compare failed: {err}{hint}")
        # The container and --out may be on different volumes, where a move is a copy that can
        # die half-written. Copy beside --out, then rename: --out appears whole or not at all.
        part = out.with_name(f".{out.name}.{token}.part")
        try:
            shutil.copyfile(seed, part)
            os.replace(part, out)
        finally:
            part.unlink(missing_ok=True)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


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
    # 180 was the old default and it is not enough. A major revision is measured in whole
    # sections moved, not sentences edited, and Word's Compare on one (149 paragraphs and no
    # tables against 193 paragraphs and two) ran past 180s and failed; the same pair completed
    # in well under 600. Waiting is cheap here — the cost of the low default was a failed run
    # and a file that looked like a result.
    ap.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="seconds Word may spend comparing (default 600; a whole-manuscript revision needs "
             "minutes, and the old 180 failed on one)",
    )
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

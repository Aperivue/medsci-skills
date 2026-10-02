#!/usr/bin/env python3
"""Regression test for obsidian-paper-vault/scripts/extract_pdfs.py (OPV-01).

An image-only PDF, or max_pages <= 0, used to write a 0-byte .txt that was
counted as "Extracted" and then handed to a note-writing subagent -- the exact
condition SKILL.md says produces a note invented from training data.

CI does not install PyMuPDF, so the script is run as a subprocess with a stub
`fitz` module first on PYTHONPATH. A stub "PDF" is a JSON file holding the text
of each page; that is all extract_pdfs.py asks of fitz (open, len, load_page,
get_text). Stdlib-only, network-free.

Set EXTRACT_PDFS_SCRIPT to run the same cases against another copy of the
script (used for the old-vs-new differential run).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = Path(os.environ.get("EXTRACT_PDFS_SCRIPT", HERE.parent / "scripts" / "extract_pdfs.py"))

STUB_FITZ = '''
import builtins
import json


class _Page:
    def __init__(self, text):
        self._text = text

    def get_text(self, kind="text"):
        return self._text


class _Doc:
    def __init__(self, pages):
        self._pages = pages

    def __len__(self):
        return len(self._pages)

    def load_page(self, i):
        return _Page(self._pages[i])

    def close(self):
        pass


def open(path):
    with builtins.open(path, encoding="utf-8") as f:
        data = json.load(f)
    return _Doc(data["pages"])
'''


def write_pdf(folder: Path, name: str, pages: list) -> Path:
    p = folder / name
    p.write_text(json.dumps({"pages": pages}), encoding="utf-8")
    return p


def run(stub_dir: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(stub_dir) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run([sys.executable, str(SCRIPT), *args], env=env,
                          capture_output=True, text=True)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def main() -> int:
    assert SCRIPT.exists(), f"ENV-ERR: {SCRIPT} missing"
    fails = []

    def check(label: str, cond: bool, detail: str = "") -> None:
        print(f"  {'PASS' if cond else 'FAIL'}  {label}")
        if not cond:
            fails.append(label)
            if detail:
                print("        " + detail.strip().replace("\n", "\n        "))

    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        stub = t / "stub"
        stub.mkdir()
        (stub / "fitz.py").write_text(STUB_FITZ, encoding="utf-8")

        pdfs = t / "pdfs"
        pdfs.mkdir()
        write_pdf(pdfs, "paper.pdf", ["Abstract. 42 patients were enrolled.", "Results page."])
        write_pdf(pdfs, "scanned.pdf", ["", "   \n", ""])

        # ---- POSITIVE: image-only PDF in a folder run --------------------
        out = t / "out1"
        r = run(stub, str(pdfs), str(out))
        log = r.stdout + r.stderr
        check("folder run: image-only PDF writes no .txt", not (out / "scanned.txt").exists(), log)
        check("folder run: image-only PDF reported FAILED / needs OCR",
              "FAILED scanned.pdf" in log and "needs OCR" in log, log)
        check("folder run: only the text PDF counts as extracted",
              "Extracted 1 PDFs" in log and "Failed: 1" in log, log)
        # NEGATIVE control: the PDF with text is still extracted unchanged.
        txt = read(out / "paper.txt")
        check("folder run: text PDF still extracted with page break",
              "42 patients" in txt and "===PAGE BREAK===" in txt, log)

        # ---- POSITIVE: single-file image-only PDF ------------------------
        out = t / "out2"
        r = run(stub, str(pdfs / "scanned.pdf"), str(out))
        log = r.stdout + r.stderr
        check("single file: image-only PDF writes no .txt", not (out / "scanned.txt").exists(), log)
        check("single file: image-only PDF reported needs OCR", "needs OCR" in log, log)

        # ---- POSITIVE: max_pages <= 0 or non-integer -> exit 2, no file ---
        for bad in ("0", "-1", "abc"):
            out = t / f"out_bad_{bad}"
            r = run(stub, str(pdfs / "paper.pdf"), str(out), bad)
            log = r.stdout + r.stderr
            check(f"max_pages={bad!r}: exit 2", r.returncode == 2, f"exit={r.returncode}\n{log}")
            check(f"max_pages={bad!r}: message names the value",
                  "max_pages" in log and repr(bad) in log, log)
            check(f"max_pages={bad!r}: no .txt written", not (out / "paper.txt").exists(), log)

        # ---- NEGATIVE controls -------------------------------------------
        out = t / "out3"
        r = run(stub, str(pdfs / "paper.pdf"), str(out), "1")
        txt = read(out / "paper.txt")
        check("max_pages=1: exit 0 and first page only",
              r.returncode == 0 and "42 patients" in txt and "PAGE BREAK" not in txt,
              r.stdout + r.stderr)

        # A blank cover page followed by a text page is not image-only.
        write_pdf(pdfs, "cover.pdf", ["", "Methods: retrospective cohort."])
        out = t / "out4"
        r = run(stub, str(pdfs / "cover.pdf"), str(out))
        txt = read(out / "cover.txt")
        check("blank cover page + text page: still extracted",
              r.returncode == 0 and "retrospective cohort" in txt, r.stdout + r.stderr)

    if fails:
        print(f"FAIL: {len(fails)} check(s) failed")
        return 1
    print("PASS: extract_pdfs.py empty-extraction and max_pages checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())

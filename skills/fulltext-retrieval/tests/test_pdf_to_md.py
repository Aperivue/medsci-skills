#!/usr/bin/env python3
"""Regression test for fulltext-retrieval/pdf_to_md.py pure helpers.

pdf_to_md.py exits at import time if pymupdf4llm is unavailable, so we stub that
module before importing and exercise only the dependency-free, deterministic
helpers: parse_page_range (page-spec parsing) and clean_markdown (post-process).
This keeps CI free of the heavy PyMuPDF/pymupdf4llm dependency while still
gating the logic most prone to silent breakage. Stdlib-only, network-free.
"""
import importlib.util
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE.parent / "pdf_to_md.py"


def load_module():
    # Stub pymupdf4llm so the module-level import does not sys.exit(1).
    sys.modules.setdefault("pymupdf4llm", types.ModuleType("pymupdf4llm"))
    spec = importlib.util.spec_from_file_location("pdf_to_md", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    assert MODULE_PATH.exists(), f"ENV-ERR: {MODULE_PATH} missing"
    mod = load_module()
    fails = []

    def check(label, cond):
        print(f"  {'PASS' if cond else 'FAIL'}  {label}")
        if not cond:
            fails.append(label)

    # --- parse_page_range ---
    check("range '0-9' -> 0..9", mod.parse_page_range("0-9") == list(range(0, 10)))
    check("list '0,2,5-7' -> [0,2,5,6,7]", mod.parse_page_range("0,2,5-7") == [0, 2, 5, 6, 7])
    check("single '3' -> [3]", mod.parse_page_range("3") == [3])
    check("whitespace ' 1 , 4 ' tolerated", mod.parse_page_range(" 1 , 4 ") == [1, 4])

    # --- clean_markdown ---
    out = mod.clean_markdown("a\n\n\n\n\nb   \n\n\n")
    check("collapses 4+ newlines to 3", "\n\n\n\n" not in out)
    check("rstrips line trailing spaces", "b   " not in out and "b" in out)
    check("ends with exactly one newline", out.endswith("\n") and not out.endswith("\n\n"))
    check("strips leading/trailing blank lines", out == "a\n\n\nb\n")
    # idempotent
    check("clean_markdown is idempotent", mod.clean_markdown(out) == out)

    if fails:
        print(f"FAILURES: {len(fails)}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

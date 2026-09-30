#!/usr/bin/env python3
"""
Convert research paper PDFs to LLM-friendly Markdown.

Uses pymupdf4llm for high-quality extraction optimized for academic papers:
two-column layout handling, table preservation, header/footer removal.

Requires: pip install pymupdf4llm

Usage:
    python pdf_to_md.py pdfs/                   # convert all PDFs in directory
    python pdf_to_md.py paper.pdf               # convert single file
    python pdf_to_md.py pdfs/ -o markdown/       # custom output directory
    python pdf_to_md.py pdfs/ --pages 0-9        # first 10 pages only
    python pdf_to_md.py pdfs/ --force            # overwrite existing .md files
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import pymupdf4llm
except ImportError:
    print("Error: pymupdf4llm is not installed.", file=sys.stderr)
    print("Install with: pip install pymupdf4llm", file=sys.stderr)
    sys.exit(1)


def parse_page_range(spec: str) -> list[int]:
    """Parse page range string like '0-9' or '0,2,5-7' into list of ints."""
    pages = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            pages.extend(range(int(start), int(end) + 1))
        else:
            pages.append(int(part))
    return pages


def clean_markdown(text: str) -> str:
    """Post-process pymupdf4llm output for cleaner LLM consumption."""
    # Collapse excessive blank lines (3+ → 2)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    # Strip trailing whitespace per line
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip() + "\n"


def convert_pdf(pdf_path: Path, out_dir: Path, *,
                pages: list[int] | None = None,
                force: bool = False,
                verbose: bool = False) -> bool:
    """Convert a single PDF to Markdown. Returns True on success."""
    md_path = out_dir / pdf_path.with_suffix(".md").name

    if md_path.exists() and md_path.stat().st_size > 0 and not force:
        if verbose:
            print(f"  SKIP: {md_path.name} (exists, use --force to overwrite)")
        return True

    try:
        kwargs = {
            "show_progress": False,
            # Academic paper defaults: skip images (saves tokens),
            # strict table detection for grid-line tables
            "write_images": False,
            "ignore_images": True,
            "table_strategy": "lines_strict",
        }
        if pages is not None:
            kwargs["pages"] = pages

        # Suppress pymupdf's C-level OCR/parser messages (stdout + stderr)
        if not verbose:
            import os as _os
            _devnull = _os.open(_os.devnull, _os.O_WRONLY)
            _old_stdout = _os.dup(1)
            _old_stderr = _os.dup(2)
            _os.dup2(_devnull, 1)
            _os.dup2(_devnull, 2)
        try:
            md_text = pymupdf4llm.to_markdown(str(pdf_path), **kwargs)
        finally:
            if not verbose:
                _os.dup2(_old_stdout, 1)
                _os.dup2(_old_stderr, 2)
                _os.close(_devnull)
                _os.close(_old_stdout)
                _os.close(_old_stderr)
        md_text = clean_markdown(md_text)

        md_path.write_text(md_text, encoding="utf-8")
        if verbose:
            kb = len(md_text.encode("utf-8")) / 1024
            print(f"  OK: {md_path.name} ({kb:.1f} KB)")
        return True
    except Exception as e:
        print(f"  FAIL: {pdf_path.name}: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Convert research PDFs to LLM-friendly Markdown "
                    "(via pymupdf4llm).")
    parser.add_argument("input", type=Path,
                        help="PDF file or directory containing PDFs")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="Output directory (default: same as input)")
    parser.add_argument("--pages", type=str, default=None,
                        help="Page range, e.g. '0-9' for first 10 pages")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing .md files")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show per-file progress")
    args = parser.parse_args()

    # Resolve input
    if args.input.is_file():
        pdfs = [args.input]
        default_out = args.input.parent
    elif args.input.is_dir():
        pdfs = sorted(args.input.glob("*.pdf"))
        default_out = args.input
    else:
        print(f"Error: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    out_dir = args.output or default_out
    out_dir.mkdir(parents=True, exist_ok=True)

    if not pdfs:
        print("No PDF files found.")
        return

    # Parse pages
    pages = parse_page_range(args.pages) if args.pages else None

    print(f"Converting {len(pdfs)} PDF(s) → Markdown", flush=True)
    ok = 0
    fail = 0
    for pdf in pdfs:
        if convert_pdf(pdf, out_dir, pages=pages, force=args.force,
                       verbose=args.verbose):
            ok += 1
        else:
            fail += 1

    print(f"\n--- Summary ---")
    print(f"  Converted: {ok}")
    print(f"  Failed:    {fail}")
    print(f"  Total:     {len(pdfs)}")


if __name__ == "__main__":
    main()

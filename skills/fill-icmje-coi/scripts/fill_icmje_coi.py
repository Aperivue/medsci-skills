#!/usr/bin/env python3
"""
fill_icmje_coi.py — Batch-fill ICMJE Conflict of Interest Disclosure Forms.

Approach: ICMJE's official `coi_disclosure.docx` uses Content Controls (SDTs).
python-docx's `cell.text` ignores SDT-wrapped content, so we operate on
`word/document.xml` directly via zipfile + targeted string replacement.

Template strategy (works because it avoids authoring SDT XML from scratch):
- Use a previously-filled ICMJE form ("seed template") as the source, where
  all 13 disclosure items are already marked ☒ + "None" and the final
  certification is ☒.
- Clone the seed per-author and replace only three fields:
    1. Date  (e.g. "April 12, 2026" → "April 20, 2026")
    2. Name  (seed author full name → target author full name)
    3. Title (seed manuscript title → target manuscript title)

Usage (Python API):
    from fill_icmje_coi import fill_icmje_forms
    fill_icmje_forms(
        seed_docx=Path("/path/to/ICMJE_COI_02_Taein_An.docx"),
        seed_name="Taein An",
        seed_title="So Far, Human-in-the-Loop Remains ...",
        seed_date="April 12, 2026",
        new_title="Incidental Emphysema on ...",
        new_date="April 20, 2026",
        authors=[(1, "Yoojin Nam"), (2, "Hye Ree Cho"), ...],
        out_dir=Path("submission/chest/icmje_forms"),
    )

CLI:
    fill_icmje_coi.py --seed <docx> --seed-name "X" --seed-title "Y" \
        --seed-date "April 12, 2026" --new-title "Z" \
        --new-date "April 20, 2026" --out-dir <dir> \
        --authors '[[1,"A"],[2,"B"]]'

Safety:
- Only a literal-string replacement in word/document.xml; no SDT surgery.
- Seed-value collisions inside other document text are unlikely but verify
  by dumping the seed XML first (see test section in source).
- All other .docx parts (styles.xml, rels, etc.) copied byte-identically.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Iterable


DOCUMENT_XML = "word/document.xml"


def _replace_in_zip(src: Path, dst: Path, replacements: dict[str, str]) -> None:
    """Copy src → dst, replacing text in word/document.xml per replacements."""
    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == DOCUMENT_XML:
                text = data.decode("utf-8")
                for old, new in replacements.items():
                    if old and old not in text:
                        raise ValueError(
                            f"[{dst.name}] seed string not found in document.xml: {old!r}\n"
                            f"Dump with: unzip -p <seed.docx> word/document.xml | grep -o '<w:t[^>]*>[^<]*</w:t>'"
                        )
                    if old:
                        # XML-escape new value (& < > " ')
                        escaped = (new.replace("&", "&amp;")
                                      .replace("<", "&lt;")
                                      .replace(">", "&gt;"))
                        text = text.replace(old, escaped)
                data = text.encode("utf-8")
            zout.writestr(item, data)


def fill_icmje_forms(
    seed_docx: Path,
    seed_name: str,
    seed_title: str,
    seed_date: str,
    new_title: str,
    new_date: str,
    authors: Iterable[tuple[int, str]],
    out_dir: Path,
    filename_template: str = "ICMJE_COI_{idx:02d}_{slug}.docx",
) -> list[Path]:
    """Generate one filled docx per author. Returns list of written paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for idx, author_name in authors:
        slug = re.sub(r"\s+", "_", author_name.strip())
        out_path = out_dir / filename_template.format(idx=idx, slug=slug)
        replacements = {
            seed_title: new_title,
            seed_date: new_date,
            seed_name: author_name,
        }
        _replace_in_zip(seed_docx, out_path, replacements)
        written.append(out_path)
        print(f"  ✓ {out_path.name}  ({author_name})")
    return written


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--seed", type=Path, required=True, help="Filled ICMJE docx to clone")
    p.add_argument("--seed-name", required=True)
    p.add_argument("--seed-title", required=True)
    p.add_argument("--seed-date", required=True)
    p.add_argument("--new-title", required=True)
    p.add_argument("--new-date", required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--authors", required=True, help='JSON list: [[1,"Full Name"],...]')
    args = p.parse_args()

    authors = [tuple(x) for x in json.loads(args.authors)]
    print(f"Seed: {args.seed}")
    print(f"Output dir: {args.out_dir}")
    print(f"Authors: {len(authors)}")
    fill_icmje_forms(
        seed_docx=args.seed,
        seed_name=args.seed_name,
        seed_title=args.seed_title,
        seed_date=args.seed_date,
        new_title=args.new_title,
        new_date=args.new_date,
        authors=authors,
        out_dir=args.out_dir,
    )
    print(f"Done. {len(authors)} forms written to {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

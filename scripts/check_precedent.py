#!/usr/bin/env python3
"""Precedent / personal-identifier scan (self-doxxing-safe).

`validate_skills.sh` blocks project-specific identifiers from reaching the public
surface. Historically the blocklist was a single plaintext regex inside the
validator — which meant the maintainer's name, mentor names, and internal project
codes were themselves enumerated in cleartext in the public repo (the self-doxxing
trade-off noted in oss-publication-pii-guard §5). This helper resolves that by
splitting the blocklist into two layers:

  1. STRUCTURAL — generic project/artifact *shapes* that are not themselves
     personally identifying (CK-<n>, MA-<n>, <X><n>_Consensus_Sheet, ...). These
     stay as plaintext regex below; revealing them dox nobody.

  2. HASHED LITERALS — real names, mentor initials, institutions, product names,
     and specific project codes. Stored only as SHA-256 digests in
     precedent_hashes.txt, never in cleartext. Detection tokenises the scanned
     text into word n-grams (1..MAX_NGRAM), lowercases, and hashes each, matching
     against the digest set. The scanned text may itself contain a term (that is
     what we are catching); the runtime match is shown to the local author, but
     the committed blocklist stays hash-only.

Exit codes: 0 = clean, 3 = precedent hit found (first hit printed as
"<lineno>:<match>"), other = usage/IO error. Stdlib-only.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

# Layer 1 — structural shapes (safe to keep in cleartext; identify no person).
STRUCTURAL = [
    re.compile(r"\bCK-[0-9]+\b"),
    re.compile(r"\bMA-[0-9]+\b"),
    re.compile(r"\bMA0[0-9]\b"),
    re.compile(r"CAC>[0-9]+"),
    re.compile(r"[가-힣]{2,4}\s*(?:교수님|선생님)"),  # <Korean name> 교수님/선생님
    re.compile(r"[A-Z]+[0-9]+_Consensus_Sheet"),
    re.compile(r"v[0-9]+_edit_plan\.md"),
    re.compile(r"screening_consensus_final\.md"),
    re.compile(r"fulltext_screening_final\.tsv"),
    re.compile(r"VIF\s+Diag"),
]

_HERE = Path(__file__).resolve().parent
# Paths are overridable via env for testing (so regression tests can exercise
# the hash path with a synthetic digest set instead of committing real terms).
HASH_FILE = Path(os.environ.get("PRECEDENT_HASH_FILE", _HERE / "precedent_hashes.txt"))
AUTHOR_HASH_FILE = Path(os.environ.get("PRECEDENT_AUTHOR_HASH_FILE", _HERE / "precedent_author_hashes.txt"))
MAX_NGRAM = 4
_STRIP = ".,;:!?()[]{}\"'`<>·…"

EXIT_CLEAN = 0
EXIT_HIT = 3


def _read_digests(path: Path) -> set[str]:
    hs: set[str] = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                hs.add(line.lower())
    return hs


def load_hashes(allow_author: bool = False) -> set[str]:
    hs = _read_digests(HASH_FILE)
    if allow_author:
        # Attribution files (README/CITATION/...) legitimately carry the
        # maintainer's own name; subtract those digests so only that name is
        # exempt while every other identifier on the line is still caught.
        hs -= _read_digests(AUTHOR_HASH_FILE)
    return hs


def line_ngrams(line: str) -> set[str]:
    toks = [t.strip(_STRIP) for t in line.split()]
    toks = [t for t in toks if t]
    grams: set[str] = set()
    for n in range(1, MAX_NGRAM + 1):
        for i in range(len(toks) - n + 1):
            grams.add(" ".join(toks[i:i + n]).lower())
    return grams


def scan_text(text: str, hashes: set[str]) -> tuple[int, str] | None:
    for lineno, line in enumerate(text.splitlines(), 1):
        for rx in STRUCTURAL:
            m = rx.search(line)
            if m:
                return lineno, m.group(0)
        if hashes:
            for gram in line_ngrams(line):
                if hashlib.sha256(gram.encode("utf-8")).hexdigest() in hashes:
                    return lineno, gram
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan text for precedent/personal identifiers.")
    ap.add_argument("path", nargs="?", default="-",
                    help="File to scan, or '-' for stdin (default).")
    ap.add_argument("--allow-author", action="store_true",
                    help="Exempt the maintainer's own name digests (for citation/"
                         "attribution files such as README.md, CITATION.cff).")
    args = ap.parse_args()

    if args.path == "-":
        text = sys.stdin.read()
    else:
        text = Path(args.path).read_text(encoding="utf-8", errors="replace")

    hit = scan_text(text, load_hashes(allow_author=args.allow_author))
    if hit:
        print(f"{hit[0]}:{hit[1]}")
        return EXIT_HIT
    return EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main())

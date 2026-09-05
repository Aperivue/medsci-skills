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
    # <Korean name> + academic honorific. On 교수 the 님 is OPTIONAL, and that is the point: the
    # pattern was written against `교수님`, the polite form used when ADDRESSING someone, while
    # prose MENTIONING a colleague in the third person drops it — `김OO 교수 회신에서…`. Every
    # real occurrence in this repository's own commit messages and planning notes was bare, so
    # the pattern was calibrated to the one shape the leaks do not take and read clean on all of
    # them. `check_contribution_safety.py` had `교수님?` from the start; three copies of one
    # check disagreed and the strictest was not the one guarding the repository.
    #
    # The stoplist is why this is safe to broaden. Without 님 the name slot will swallow whatever
    # Korean word precedes the role — `지도 교수`, `담당 교수` are job descriptions, not people,
    # and a gate that fires on those is one people route around. The lookahead blocks the match
    # at that position, and the leftover single syllable cannot satisfy {2,4}, so the whole
    # phrase is skipped. 선생 stays 님-only: no leak here has ever used the bare form, and
    # broadening it on speculation buys false positives for nothing.
    re.compile(r"(?!지도|담당|책임|주임|객원|초빙|겸임|특임|임상|명예|정년|외래)"
               r"[가-힣]{2,4}\s*(?:교수님?|선생님)"),
    re.compile(r"[A-Z]+[0-9]+_Consensus_Sheet"),
    re.compile(r"v[0-9]+_edit_plan\.md"),
    re.compile(r"screening_consensus_final\.md"),
    re.compile(r"fulltext_screening_final\.tsv"),
    re.compile(r"VIF\s+Diag"),
    # A journal submission ID (LETTERS-D-YY-NNNNN, with or without an RN revision suffix).
    # `/contribute` has blocked this shape from CONTRIBUTIONS since it shipped, rated major, on the
    # grounds that a manuscript under review is confidential and its ID identifies it. Nothing
    # applied the same rule to the repository's OWN files, and one had been sitting in a shipped
    # reviewer profile: the toolkit held contributors to a standard it did not hold itself to.
    # See also reviewer_profiles/README.md, which now requires round + date and forbids the ID.
    re.compile(r"\b[A-Z]{2,6}(?:-[A-Z])?-\d{2}-\d{3,6}(?:R\d{1,2})?\b"),
]

# A published DOI can end in the same shape (Annals of Internal Medicine mints
# `10.7326/ANNALS-25-02104`), and a vendored checklist citing its own source is not a disclosure.
# A DOI is public by definition; a submission ID is the opposite.
DOI_SUFFIX = re.compile(r"\b10\.\d{4,9}/\S*$")

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
    grams: set[str] = set()
    # Identifiers also occur inside paths and compound project slugs. Keep the
    # original n-grams (some literals contain punctuation) and check components
    # separated by path/slug delimiters without matching arbitrary substrings.
    for source in (line, re.sub(r"[/\\\\_-]+", " ", line)):
        toks = [t.strip(_STRIP) for t in source.split()]
        toks = [t for t in toks if t]
        for n in range(1, MAX_NGRAM + 1):
            for i in range(len(toks) - n + 1):
                grams.add(" ".join(toks[i:i + n]).lower())
    return grams


def scan_text(text: str, hashes: set[str]) -> tuple[int, str] | None:
    for lineno, line in enumerate(text.splitlines(), 1):
        for rx in STRUCTURAL:
            for m in rx.finditer(line):
                if DOI_SUFFIX.search(line[:m.start()]):
                    continue
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

#!/usr/bin/env python3
"""Does this row's DOI point at this row's paper?

A screening table's `doi` column is not always something a database handed over with the record. It
is often something a pipeline *worked out* — matched by title similarity against Crossref, at a
score somebody chose. When that match is wrong, the DOI is a valid, resolvable identifier for a
different paper, and nothing downstream can tell. Every check that follows treats it as ground
truth: deduplication, full-text retrieval, the reference list, the eligibility decision.

Two failures inside two days, from one such column:

  * a conference-abstract record carried the DOI of a **different study already in the cohort**,
    which produced a false limitation — a "missed eligible paper" that did not exist. It reached
    the supporting material of a submitted abstract.
  * another record's DOI resolved to an **entire supplement of abstracts** rather than to an
    article, sending a reader to look for a paper that was never there.

Neither is detectable by looking at the DOI. Both are obvious the moment you resolve it and read
the title back.

    DOI_NOT_THIS_RECORD  the DOI resolves, and to a different paper than the row describes
    DOI_IS_CONTAINER     the DOI resolves to an issue, a supplement, a book or proceedings — a
                         container, not an article
    DOI_UNRESOLVED       the DOI does not resolve at all (reported, never silently dropped)

WHAT THIS IS NOT
    It is not `/verify-refs`, which audits a manuscript's finished reference list against PubMed
    and Crossref. This runs earlier, on the screening table, where a wrong DOI is still cheap — and
    where the reference list does not exist yet.

    It also cannot tell you a DOI is *right*. A title that matches is consistent with the row; it
    is not proof the record was correctly extracted. It rules out one specific, recurring, and
    otherwise invisible way of being wrong.

DETERMINISM
    `--cache DIR` reads recorded Crossref responses (`<url-safe-doi>.json`) instead of the network,
    which is how the challenge card runs offline. With `--cache` and no recorded response, a row is
    UNRESOLVED — the cache is never quietly topped up from the network mid-run, because a check
    that is half-recorded and half-live is reproducible in neither direction.

Stdlib only.

Usage:
    check_doi_record_match.py --table screening.tsv [--title-col title] [--doi-col doi]
                             [--id-col record_id] [--email you@example.org]
                             [--threshold 0.90] [--cache DIR] [--json out.json] [--strict]

Exit: 0 clean (or findings without --strict), 1 findings with --strict, 2 unusable input.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional

DETECTOR = "check_doi_record_match"

CROSSREF = "https://api.crossref.org/works/"

# Crossref `type` values that are an article-shaped thing a screening row can legitimately BE.
# Anything else is a container: resolving to it means the row points at the box, not the paper.
ARTICLE_TYPES = {
    "journal-article", "proceedings-article", "posted-content", "book-chapter",
    "report", "dissertation", "peer-review", "reference-entry", "other",
}

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")


@dataclass
class Finding:
    detector: str
    verdict: str
    record: Optional[str]
    summary: str
    evidence: List[str] = field(default_factory=list)


def normalise(s: str) -> str:
    """Compare what a title says, not how a database punctuated it."""
    s = unicodedata.normalize("NFKD", s or "").lower()
    s = re.sub(r"<[^>]+>", " ", s)          # Crossref titles carry JATS markup
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return " ".join(s.split())


def similarity(a: str, b: str) -> float:
    na, nb = normalise(a), normalise(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def clean_doi(raw: str) -> str:
    """Accept a DOI however a spreadsheet wrote it: bare, prefixed, or as a URL."""
    m = DOI_RE.search((raw or "").strip())
    return m.group(0).rstrip(".,;)") if m else ""


def cache_path(cache: Path, doi: str) -> Path:
    return cache / (urllib.parse.quote(doi, safe="") + ".json")


def resolve(doi: str, email: Optional[str], cache: Optional[Path],
            pause: float) -> Optional[dict]:
    """-> the Crossref `message` object, or None if it did not resolve."""
    if cache is not None:
        p = cache_path(cache, doi)
        if not p.is_file():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8")).get("message")
        except (json.JSONDecodeError, OSError):
            return None

    url = CROSSREF + urllib.parse.quote(doi, safe="/")
    ua = "check_doi_record_match/1.0"
    if email:
        ua += f" (mailto:{email})"
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 - fixed https host
            payload = json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError):
        return None
    finally:
        time.sleep(pause)
    return payload.get("message")


def resolved_title(msg: dict) -> str:
    t = msg.get("title") or []
    return t[0] if t else ""


def audit(rows: List[Dict[str, str]], id_col: str, title_col: str, doi_col: str,
          threshold: float, email: Optional[str], cache: Optional[Path],
          pause: float) -> List[Finding]:
    out: List[Finding] = []
    for i, row in enumerate(rows, start=2):  # 1 is the header; report the line a person can open
        rid = (row.get(id_col) or f"row {i}").strip() or f"row {i}"
        own_title = (row.get(title_col) or "").strip()
        doi = clean_doi(row.get(doi_col) or "")
        if not doi:
            continue
        if not own_title:
            out.append(Finding(
                DETECTOR, "DOI_UNRESOLVED", rid,
                f"{rid}: carries a DOI but no title, so the DOI cannot be checked against "
                "anything.",
                [f"doi: {doi}", "A DOI with nothing to compare it to is an assertion, not a fact."],
            ))
            continue

        msg = resolve(doi, email, cache, pause)
        if msg is None:
            out.append(Finding(
                DETECTOR, "DOI_UNRESOLVED", rid,
                f"{rid}: the DOI did not resolve.",
                [f"doi: {doi}", f"row title: {own_title[:80]!r}",
                 "Reported rather than dropped: an unresolvable DOI in a screening table is a "
                 "record nobody can retrieve, which is a finding of its own."],
            ))
            continue

        got = resolved_title(msg)
        ratio = similarity(own_title, got)
        kind = (msg.get("type") or "").lower()

        if kind and kind not in ARTICLE_TYPES:
            out.append(Finding(
                DETECTOR, "DOI_IS_CONTAINER", rid,
                f"{rid}: the DOI resolves to a {kind}, not to an article.",
                [f"doi: {doi}", f"resolved to: {got[:80]!r}", f"row title: {own_title[:80]!r}",
                 "Following this DOI leads to the volume the paper is in, or to a whole "
                 "supplement of abstracts. Anyone sent there looks for a paper that is not "
                 "separately registered."],
            ))
            continue

        if ratio < threshold:
            out.append(Finding(
                DETECTOR, "DOI_NOT_THIS_RECORD", rid,
                f"{rid}: the DOI resolves to a different paper (title similarity "
                f"{ratio:.2f} < {threshold:.2f}).",
                [f"doi: {doi}",
                 f"row title:      {own_title[:100]!r}",
                 f"resolved title: {got[:100]!r}",
                 "If this column was filled by matching titles against Crossref, this is what that "
                 "match got wrong — and downstream it is indistinguishable from a real record."],
            ))
    return out


def read_table(path: Path) -> List[Dict[str, str]]:
    text = path.read_text(encoding="utf-8-sig")
    delim = "\t" if path.suffix.lower() in {".tsv", ".tab"} or "\t" in text.split("\n")[0] else ","
    return list(csv.DictReader(text.splitlines(), delimiter=delim))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--table", type=Path, required=True, help="screening table (.tsv or .csv)")
    ap.add_argument("--id-col", default="record_id")
    ap.add_argument("--title-col", default="title")
    ap.add_argument("--doi-col", default="doi")
    ap.add_argument("--threshold", type=float, default=0.90,
                    help="title similarity below which the DOI is another paper (default 0.90). "
                         "Pipelines that FILL a doi column commonly accept ~0.79, which is how "
                         "the wrong DOIs got in; do not set this to the value that produced them.")
    ap.add_argument("--email", help="contact address for the Crossref polite pool")
    ap.add_argument("--cache", type=Path,
                    help="directory of recorded Crossref responses; disables all network access")
    ap.add_argument("--pause", type=float, default=0.2, help="seconds between live requests")
    ap.add_argument("--json", type=Path)
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()

    if not a.table.is_file():
        print(f"cannot read {a.table}", file=sys.stderr)
        return 2
    if a.cache is not None and not a.cache.is_dir():
        print(f"cache directory {a.cache} does not exist", file=sys.stderr)
        return 2

    rows = read_table(a.table)
    if not rows:
        print(f"{a.table} has no data rows", file=sys.stderr)
        return 2
    missing = [c for c in (a.title_col, a.doi_col) if c not in rows[0]]
    if missing:
        print(f"{a.table} has no column(s) named {', '.join(missing)} "
              f"(found: {', '.join(rows[0])})", file=sys.stderr)
        return 2

    findings = audit(rows, a.id_col, a.title_col, a.doi_col, a.threshold,
                     a.email, a.cache, a.pause)

    checked = sum(1 for r in rows if clean_doi(r.get(a.doi_col) or ""))
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(
            {"detector": DETECTOR, "table": str(a.table), "rows": len(rows),
             "rows_with_doi": checked, "threshold": a.threshold,
             "source": "cache" if a.cache else "crossref",
             "findings": [f.__dict__ for f in findings]},
            indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not findings:
        print(f"OK: {checked} DOI(s) each resolve to the record that carries them.")
        return 0

    print(f"{len(findings)} finding(s) across {checked} DOI(s)\n")
    for f in findings:
        print(f"  [{f.verdict}] ({f.record})")
        print(f"      {f.summary}")
        for e in f.evidence:
            print(f"      - {e}")
        print()
    return 1 if a.strict else 0


if __name__ == "__main__":
    sys.exit(main())

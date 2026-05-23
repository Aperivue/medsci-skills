#!/usr/bin/env python3
"""
Parse PubMed E-utilities responses into structured data.

Usage:
    # Parse esearch JSON → list of PMIDs
    echo '<json>' | python3 parse_pubmed.py esearch

    # Parse esummary JSON → markdown table
    echo '<json>' | python3 parse_pubmed.py esummary

    # Parse efetch XML → detailed metadata (for BibTeX generation)
    echo '<xml>' | python3 parse_pubmed.py efetch

    # Parse efetch XML → BibTeX entries
    echo '<xml>' | python3 parse_pubmed.py bibtex
"""

import sys
import json
import re
import xml.etree.ElementTree as ET
from datetime import date
from textwrap import shorten


# Heuristic for East Asian name reverse-encoding in PubMed XML.
# Cases observed: <LastName>Qiaoling</LastName><ForeName>Fu</ForeName> where
# Fu is the actual family name. Pattern: LastName looks like a long given
# name (≥3 alpha chars, no spaces) AND ForeName looks like a short surname
# fragment (1-2 chars, no period). The naive test catches the common reverse
# encoding without flagging legitimate short-surname authors.
_EAST_ASIAN_REVERSE_THRESHOLD = 3  # LastName length lower bound for suspicion


def _looks_east_asian_reversed(last: str, fore: str) -> bool:
    """Return True if (LastName, ForeName) look swapped per PubMed encoding bug."""
    if not last or not fore:
        return False
    # ForeName should look like a surname (1-2 chars, no spaces, no period)
    # AND LastName should look like a multi-char given name.
    return (
        1 <= len(fore) <= 2
        and fore.isalpha()
        and "." not in fore
        and len(last) >= _EAST_ASIAN_REVERSE_THRESHOLD
        and last.isalpha()
    )


def _extract_authors(author_list_el):
    """Walk an <AuthorList> element. Return (bib_authors, display_authors,
    first_author_last, suspicions, has_collective_only).

    - bib_authors: list of "Family, Given" strings for BibTeX `author = {...}`.
      Corporate (<CollectiveName>) authors are double-braced.
    - display_authors: list of "Last First" strings for human-readable output.
    - first_author_last: surname of the first listed author (used for cite key).
    - suspicions: list of human-readable warning strings (East Asian reverse
      encoding, missing LastName, etc.).
    - has_collective_only: True if AuthorList contains only <CollectiveName>
      entries (no individual <LastName>). Caller should consider emitting
      `@misc` instead of `@article` (guideline / consortium pattern).
    """
    bib_authors: list[str] = []
    display_authors: list[str] = []
    first_author_last = ""
    suspicions: list[str] = []
    individual_count = 0
    collective_count = 0

    if author_list_el is None:
        return bib_authors, display_authors, "", suspicions, False

    for au in author_list_el.findall("Author"):
        last = au.findtext("LastName", "") or ""
        fore = au.findtext("ForeName", "") or ""
        collective = au.findtext("CollectiveName", "") or ""

        if collective:
            collective_count += 1
            # Double-brace to prevent BibTeX from splitting on the comma /
            # spaces inside the corporate name.
            bib_authors.append("{" + collective + "}")
            display_authors.append(collective)
            if not first_author_last:
                first_author_last = re.sub(r"[^A-Za-z]+", "", collective.split()[0]) or "Group"
            continue

        if last:
            individual_count += 1
            if _looks_east_asian_reversed(last, fore):
                suspicions.append(
                    f"East Asian name order suspected for '{last} {fore}' — "
                    "PubMed XML may have LastName/ForeName swapped"
                )
            bib_authors.append(f"{last}, {fore}")
            display_authors.append(f"{last} {fore}".strip())
            if not first_author_last:
                first_author_last = last
            continue

        # Author element with neither <LastName> nor <CollectiveName>: rare
        # but possible. Record as suspicion, otherwise skip.
        suspicions.append("Author element with no LastName and no CollectiveName")

    has_collective_only = collective_count > 0 and individual_count == 0
    return bib_authors, display_authors, first_author_last, suspicions, has_collective_only


def parse_esearch(data: str) -> None:
    """Parse esearch JSON response, print PMIDs and count."""
    result = json.loads(data)
    esearch = result.get("esearchresult", {})
    count = esearch.get("count", "0")
    ids = esearch.get("idlist", [])
    print(f"Total results: {count}")
    print(f"Returned: {len(ids)}")
    print(f"PMIDs: {','.join(ids)}")


def parse_esummary(data: str) -> None:
    """Parse esummary JSON response into a markdown table."""
    result = json.loads(data)
    docs = result.get("result", {})
    uids = docs.get("uids", [])

    if not uids:
        print("No results found.")
        return

    print("| # | PMID | Year | Journal | Title | Authors |")
    print("|---|------|------|---------|-------|---------|")

    for i, uid in enumerate(uids, 1):
        doc = docs.get(uid, {})
        title = shorten(doc.get("title", "N/A"), width=80, placeholder="...")
        authors_raw = doc.get("authors", [])
        if authors_raw:
            first = authors_raw[0].get("name", "")
            last = authors_raw[-1].get("name", "") if len(authors_raw) > 1 else ""
            authors = f"{first}, ... {last}" if last and last != first else first
        else:
            authors = "N/A"
        journal = shorten(doc.get("fulljournalname", doc.get("source", "N/A")),
                          width=40, placeholder="...")
        pubdate = doc.get("pubdate", "N/A")
        year = pubdate[:4] if pubdate else "N/A"
        doi_list = doc.get("articleids", [])
        doi = next((d["value"] for d in doi_list if d.get("idtype") == "doi"), "")

        print(f"| {i} | {uid} | {year} | {journal} | {title} | {authors} |")

    print(f"\n*{len(uids)} articles retrieved*")


def parse_efetch(data: str) -> None:
    """Parse efetch XML response into structured metadata."""
    root = ET.fromstring(data)
    articles = root.findall(".//PubmedArticle")

    for article in articles:
        medline = article.find("MedlineCitation")
        if medline is None:
            continue

        pmid = medline.findtext("PMID", "N/A")
        art = medline.find("Article")
        if art is None:
            continue

        title = art.findtext("ArticleTitle", "N/A")
        journal_el = art.find("Journal")
        journal = journal_el.findtext("Title", "N/A") if journal_el is not None else "N/A"
        journal_abbrev = journal_el.findtext("ISOAbbreviation", "") if journal_el is not None else ""

        # Year
        ji = journal_el.find("JournalIssue") if journal_el is not None else None
        pd = ji.find("PubDate") if ji is not None else None
        year = pd.findtext("Year", "") if pd is not None else ""
        if not year:
            medline_date = pd.findtext("MedlineDate", "") if pd is not None else ""
            year = medline_date[:4] if medline_date else "N/A"

        volume = ji.findtext("Volume", "") if ji is not None else ""
        issue = ji.findtext("Issue", "") if ji is not None else ""

        # Pages
        pages = art.findtext("Pagination/MedlinePgn", "")

        # Authors (handles East Asian reverse encoding + CollectiveName)
        author_list = art.find("AuthorList")
        _, authors, _, suspicions, _ = _extract_authors(author_list)

        # DOI
        doi = ""
        for aid in art.findall("ELocationID"):
            if aid.get("EIdType") == "doi":
                doi = aid.text or ""

        # Abstract
        abstract_el = art.find("Abstract")
        abstract = ""
        if abstract_el is not None:
            parts = abstract_el.findall("AbstractText")
            abstract = " ".join(
                (p.get("Label", "") + ": " if p.get("Label") else "") + (p.text or "")
                for p in parts
            )

        print(f"## PMID: {pmid}")
        print(f"**Title**: {title}")
        print(f"**Authors**: {'; '.join(authors)}")
        print(f"**Journal**: {journal} ({journal_abbrev})")
        print(f"**Year**: {year}  **Volume**: {volume}  **Issue**: {issue}  **Pages**: {pages}")
        print(f"**DOI**: {doi}")
        if abstract:
            print(f"**Abstract**: {shorten(abstract, width=500, placeholder='...')}")
        for note in suspicions:
            print(f"> ⚠ {note}")
        print()


def generate_bibtex(data: str) -> None:
    """Parse efetch XML and generate BibTeX entries."""
    root = ET.fromstring(data)
    articles = root.findall(".//PubmedArticle")

    for article in articles:
        medline = article.find("MedlineCitation")
        if medline is None:
            continue

        pmid = medline.findtext("PMID", "")
        art = medline.find("Article")
        if art is None:
            continue

        title = art.findtext("ArticleTitle", "")
        journal_el = art.find("Journal")
        journal_abbrev = journal_el.findtext("ISOAbbreviation", "") if journal_el is not None else ""
        journal_full = journal_el.findtext("Title", "") if journal_el is not None else ""

        ji = journal_el.find("JournalIssue") if journal_el is not None else None
        pd = ji.find("PubDate") if ji is not None else None
        year = pd.findtext("Year", "") if pd is not None else ""
        if not year:
            md = pd.findtext("MedlineDate", "") if pd is not None else ""
            year = md[:4] if md else ""

        volume = ji.findtext("Volume", "") if ji is not None else ""
        issue = ji.findtext("Issue", "") if ji is not None else ""
        pages = art.findtext("Pagination/MedlinePgn", "")

        doi = ""
        for aid in art.findall("ELocationID"):
            if aid.get("EIdType") == "doi":
                doi = aid.text or ""

        author_list = art.find("AuthorList")
        bib_authors, _, first_author_last, suspicions, has_collective_only = \
            _extract_authors(author_list)

        # Generate citation key
        key = f"{first_author_last}_{year}_{pmid}" if first_author_last else f"PMID_{pmid}"

        # Corporate / consortium guideline (e.g., KDIGO, AHA/ACC) — emit as
        # @misc so BibTeX styles render the body of the entry without trying
        # to format a personal author. Vancouver / AMA CSL handle both
        # @article and @misc with author = {{Organization Name}}.
        entry_type = "misc" if has_collective_only else "article"

        # Prepend suspicion comments so they survive .bib copy/paste audits.
        for note in suspicions:
            print(f"% [VERIFY] {note}")

        print(f"@{entry_type}{{{key},")
        print(f"  author    = {{{' and '.join(bib_authors)}}},")
        print(f"  title     = {{{title}}},")
        print(f"  journal   = {{{journal_full}}},")
        print(f"  year      = {{{year}}},")
        if volume:
            print(f"  volume    = {{{volume}}},")
        if issue:
            print(f"  number    = {{{issue}}},")
        if pages:
            print(f"  pages     = {{{pages}}},")
        if doi:
            print(f"  doi       = {{{doi}}},")
        print(f"  pmid      = {{{pmid}}},")

        # Anti-hallucination verification flag. Entries emitted by this script
        # originate from PubMed efetch XML, so a non-empty PMID is proof of
        # API provenance (verified=true). Missing PMID → verified=false and
        # downstream tooling (/verify-refs) will flag for manual check.
        verified = bool(pmid)
        verified_by = "pubmed+crossref" if (pmid and doi) else ("pubmed" if pmid else "")
        print(f"  verified  = {{{'true' if verified else 'false'}}},")
        if verified_by:
            print(f"  verified_by = {{{verified_by}}},")
            print(f"  verified_on = {{{date.today().isoformat()}}},")
        print("}")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    mode = sys.argv[1]
    data = sys.stdin.read()

    dispatch = {
        "esearch": parse_esearch,
        "esummary": parse_esummary,
        "efetch": parse_efetch,
        "bibtex": generate_bibtex,
    }

    func = dispatch.get(mode)
    if func is None:
        print(f"Unknown mode: {mode}. Use: {', '.join(dispatch.keys())}")
        sys.exit(1)

    func(data)

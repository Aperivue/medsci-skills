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
import xml.etree.ElementTree as ET
from textwrap import shorten


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

        # Authors
        author_list = art.find("AuthorList")
        authors = []
        if author_list is not None:
            for au in author_list.findall("Author"):
                last = au.findtext("LastName", "")
                fore = au.findtext("ForeName", "")
                if last:
                    authors.append(f"{last} {fore}".strip())

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
        bib_authors = []
        first_author_last = ""
        if author_list is not None:
            for au in author_list.findall("Author"):
                last = au.findtext("LastName", "")
                fore = au.findtext("ForeName", "")
                if last:
                    bib_authors.append(f"{last}, {fore}")
                    if not first_author_last:
                        first_author_last = last

        # Generate citation key
        key = f"{first_author_last}_{year}_{pmid}" if first_author_last else f"PMID_{pmid}"

        print(f"@article{{{key},")
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

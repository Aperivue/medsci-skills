#!/usr/bin/env python3
"""
Open-access full-text PDF batch retrieval.

Pipeline: Unpaywall → PMC (Europe PMC REST / OA FTP / web) →
          OpenAlex → Crossref → landing-page scrape.

Usage:
    python fetch_oa.py dois.txt --output pdfs/ --email user@example.com
    python fetch_oa.py dois.txt -o pdfs/ -e user@example.com --verbose
"""

import argparse
import json
import logging
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

MIN_PDF_BYTES = 10 * 1024
USER_AGENT = "medsci-skills/1.0"

log = logging.getLogger("fetch_oa")


# ============================================================
# Helpers
# ============================================================

def _ua(email: str) -> str:
    """Build a polite User-Agent string with contact email."""
    return f"{USER_AGENT} (mailto:{email})"


def is_valid_pdf(data: bytes) -> bool:
    return data.startswith(b"%PDF-") and len(data) >= MIN_PDF_BYTES


def fetch_bytes(url: str, email: str, accept: str = "*/*",
                timeout: int = 30) -> tuple[bytes, str, str]:
    req = urllib.request.Request(url, headers={
        "User-Agent": _ua(email),
        "Accept": accept,
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.geturl(), resp.headers.get("Content-Type", "")


def save_pdf(data: bytes, path: Path) -> bool:
    if not is_valid_pdf(data):
        return False
    path.write_bytes(data)
    return True


def existing_pdf_ok(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        return is_valid_pdf(path.read_bytes())
    except OSError:
        return False


# ============================================================
# 1. Unpaywall
# ============================================================

def unpaywall_lookup(doi: str, email: str) -> str | None:
    url = f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi, safe='/')}" \
          f"?email={urllib.parse.quote(email)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _ua(email)})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        best = data.get("best_oa_location")
        if best and best.get("url_for_pdf"):
            return best["url_for_pdf"]
        for loc in data.get("oa_locations", []):
            if loc.get("url_for_pdf"):
                return loc["url_for_pdf"]
        if best and best.get("url"):
            return best["url"]
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
        log.debug("Unpaywall error for %s: %s", doi, e)
    return None


# ============================================================
# 2. PMC (3-method fallback, JS-challenge resistant)
# ============================================================

def id_to_pmcid(identifier: str, email: str) -> str | None:
    """Convert PMID or DOI to PMCID via NCBI ID converter."""
    if not identifier:
        return None
    url = (f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
           f"?ids={urllib.parse.quote(identifier, safe='/')}&format=json")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _ua(email)})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        records = data.get("records", [])
        if records and records[0].get("pmcid"):
            return records[0]["pmcid"]
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
        log.debug("NCBI ID converter error for %s: %s", identifier, e)
    return None


def download_pmc_pdf(pmcid: str, outpath: Path, email: str) -> bool:
    """Download PDF from PMC via Europe PMC → OA FTP → web fallback."""

    # Method A: Europe PMC REST API (most reliable, no JS)
    try:
        url = (f"https://europepmc.org/backend/ptpmcrender.fcgi"
               f"?accid={pmcid}&blobtype=pdf")
        data, _, _ = fetch_bytes(url, email, accept="application/pdf,*/*", timeout=30)
        if save_pdf(data, outpath):
            log.debug("PMC Method A (Europe PMC) succeeded for %s", pmcid)
            return True
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        log.debug("PMC Method A failed for %s: %s", pmcid, e)

    # Method B: PMC OA FTP service (XML with direct PDF link)
    try:
        url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={pmcid}"
        xml_data, _, _ = fetch_bytes(url, email, timeout=15)
        root = ET.fromstring(xml_data)
        # Check for error response (non-OA articles)
        if root.find(".//error") is not None:
            log.debug("PMC Method B: %s is not in OA subset", pmcid)
        else:
            for link in root.iter("link"):
                href = link.get("href", "")
                if href.endswith(".pdf"):
                    if href.startswith("ftp://"):
                        href = href.replace(
                            "ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/",
                            "https://ftp.ncbi.nlm.nih.gov/pub/pmc/", 1)
                    data, _, _ = fetch_bytes(
                        href, email, accept="application/pdf,*/*", timeout=30)
                    if save_pdf(data, outpath):
                        log.debug("PMC Method B (OA FTP) succeeded for %s", pmcid)
                        return True
    except (urllib.error.URLError, urllib.error.HTTPError,
            ET.ParseError, OSError) as e:
        log.debug("PMC Method B failed for %s: %s", pmcid, e)

    # Method C: Direct PMC web URL (may hit JS PoW challenge)
    try:
        url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
        data, final_url, ct = fetch_bytes(
            url, email, accept="application/pdf,*/*")
        if "pdf" in ct.lower() or final_url.endswith(".pdf"):
            if save_pdf(data, outpath):
                log.debug("PMC Method C (web) succeeded for %s", pmcid)
                return True
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        log.debug("PMC Method C failed for %s: %s", pmcid, e)

    return False


# ============================================================
# 3. OpenAlex + Crossref
# ============================================================

def openalex_lookup(doi: str, email: str) -> list[str]:
    url = (f"https://api.openalex.org/works/"
           f"https://doi.org/{urllib.parse.quote(doi, safe='/')}")
    candidates = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _ua(email)})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        oa = data.get("open_access", {}) or {}
        primary = data.get("primary_location", {}) or {}
        for v in [primary.get("pdf_url"), oa.get("oa_url"),
                  primary.get("landing_page_url")]:
            if v and v not in candidates:
                candidates.append(v)
    except (urllib.error.URLError, urllib.error.HTTPError,
            json.JSONDecodeError) as e:
        log.debug("OpenAlex error for %s: %s", doi, e)
    return candidates


def crossref_lookup(doi: str, email: str) -> list[str]:
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='/')}"
    candidates = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _ua(email)})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        msg = data.get("message", {}) or {}
        for link in msg.get("link", []) or []:
            v = link.get("URL")
            if v and v not in candidates:
                candidates.append(v)
        primary = ((msg.get("resource") or {}).get("primary") or {}).get("URL")
        if primary and primary not in candidates:
            candidates.append(primary)
    except (urllib.error.URLError, urllib.error.HTTPError,
            json.JSONDecodeError) as e:
        log.debug("Crossref error for %s: %s", doi, e)
    return candidates


# ============================================================
# 4. Landing page scraper
# ============================================================

def scrape_pdf_candidates(html: str) -> list[str]:
    patterns = [
        r'citation_pdf_url"\s+content="([^"]+)"',
        r"name=\"citation_pdf_url\"\s+content=\"([^\"]+)\"",
        r'href="([^"]+\.pdf[^"]*)"',
    ]
    found = []
    for pat in patterns:
        for m in re.findall(pat, html, flags=re.IGNORECASE):
            if m not in found:
                found.append(m)
    return found


def download_from_landing(url: str, outpath: Path, email: str) -> bool:
    try:
        raw, final_url, ct = fetch_bytes(url, email, accept="text/html,*/*")
        if "pdf" in ct.lower():
            return save_pdf(raw, outpath)
        html = raw.decode("utf-8", errors="ignore")
        for candidate in scrape_pdf_candidates(html):
            absolute = urllib.parse.urljoin(final_url, candidate)
            try:
                data, _, _ = fetch_bytes(
                    absolute, email, accept="application/pdf,*/*")
                if save_pdf(data, outpath):
                    return True
            except (urllib.error.URLError, urllib.error.HTTPError, OSError):
                continue
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        log.debug("Landing page error for %s: %s", url, e)
    return False


def download_pdf(url: str, outpath: Path, email: str) -> bool:
    try:
        data, _, _ = fetch_bytes(url, email, accept="application/pdf,*/*")
        return save_pdf(data, outpath)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        log.debug("Direct download error for %s: %s", url, e)
    return False


# ============================================================
# 5. Main pipeline
# ============================================================

def gather_candidates(doi: str, email: str) -> list[str]:
    """Collect OA PDF candidate URLs from multiple sources."""
    urls: list[str] = []

    def add(v: str | None):
        if v and v not in urls:
            urls.append(v)

    add(unpaywall_lookup(doi, email))
    for v in openalex_lookup(doi, email):
        add(v)
    for v in crossref_lookup(doi, email):
        add(v)
    add(f"https://doi.org/{doi}")
    return urls


def process_doi(doi: str, outdir: Path, email: str,
                pmid: str = "") -> str:
    """Try to download a PDF for one DOI. Returns status string."""
    safe_name = re.sub(r"[^\w\-.]", "_", doi)
    outpath = outdir / f"{safe_name}.pdf"

    if existing_pdf_ok(outpath):
        return "skip"

    # Remove stale stub
    if outpath.exists():
        outpath.unlink(missing_ok=True)

    # Step 1: DOI-based OA candidates
    for url in gather_candidates(doi, email):
        if ".pdf" in url.lower():
            ok = download_pdf(url, outpath, email)
        else:
            ok = download_from_landing(url, outpath, email)
        if ok:
            return "oa"
        time.sleep(0.3)

    # Step 2: PMC (PMID → PMCID, then DOI → PMCID)
    pmcid = id_to_pmcid(pmid, email) if pmid else None
    if not pmcid:
        pmcid = id_to_pmcid(doi, email)
    if pmcid and download_pmc_pdf(pmcid, outpath, email):
        return "pmc"

    return "fail"


def read_doi_file(path: Path) -> list[dict]:
    """Read DOI list. Supports plain DOIs or TSV with DOI/PMID columns."""
    records = []
    with open(path, encoding="utf-8") as f:
        first_line = f.readline().strip()
        f.seek(0)

        # TSV with header containing DOI column
        if "\t" in first_line and "doi" in first_line.lower():
            import csv
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                doi = ""
                pmid = ""
                for k, v in row.items():
                    if k.lower().strip() == "doi":
                        doi = (v or "").strip()
                    elif k.lower().strip() == "pmid":
                        pmid = (v or "").strip()
                if doi:
                    records.append({"doi": doi, "pmid": pmid})
        else:
            # Plain text: one DOI per line
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    records.append({"doi": line, "pmid": ""})
    return records


def main():
    parser = argparse.ArgumentParser(
        description="Batch download open-access PDFs by DOI.")
    parser.add_argument("input", type=Path,
                        help="File with DOIs (one per line, or TSV with DOI column)")
    parser.add_argument("-o", "--output", type=Path, default=Path("pdfs"),
                        help="Output directory (default: pdfs/)")
    parser.add_argument("-e", "--email", required=True,
                        help="Contact email (required by Unpaywall TOS)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show debug messages")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    args.output.mkdir(parents=True, exist_ok=True)
    records = read_doi_file(args.input)
    print(f"Loaded {len(records)} DOIs from {args.input}")

    stats = {"oa": 0, "pmc": 0, "fail": 0, "skip": 0}

    for i, rec in enumerate(records, 1):
        doi = rec["doi"]
        pmid = rec.get("pmid", "")
        print(f"  [{i}/{len(records)}] {doi}", end=" … ", flush=True)

        status = process_doi(doi, args.output, args.email, pmid)
        stats[status] += 1

        labels = {"oa": "OK (OA)", "pmc": "OK (PMC)",
                  "fail": "FAIL", "skip": "SKIP"}
        print(labels[status])
        time.sleep(0.5)

    print(f"\n--- Summary ---")
    print(f"  OA:      {stats['oa']}")
    print(f"  PMC:     {stats['pmc']}")
    print(f"  Failed:  {stats['fail']}")
    print(f"  Skipped: {stats['skip']}")
    total = stats["oa"] + stats["pmc"] + stats["fail"]
    if total > 0:
        pct = (stats["oa"] + stats["pmc"]) / total * 100
        print(f"  Success: {pct:.0f}%")

    # Write failed DOIs for manual retrieval
    if stats["fail"] > 0:
        fail_path = args.output / "manual_needed.txt"
        with open(fail_path, "w") as f:
            f.write("# DOIs needing manual retrieval\n")
            f.write("# Options: institutional access, ILL\n\n")
            for rec in records:
                safe = re.sub(r"[^\w\-.]", "_", rec["doi"])
                pdf = args.output / f"{safe}.pdf"
                if not existing_pdf_ok(pdf):
                    f.write(f"{rec['doi']}\n")
        print(f"  Manual list: {fail_path}")


if __name__ == "__main__":
    main()

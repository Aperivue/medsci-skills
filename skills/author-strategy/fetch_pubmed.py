#!/usr/bin/env python3
"""
Fetch PubMed publications for an author, with an explicit disambiguation gate.

Network fetch uses NCBI E-utilities via Biopython. All XML parsing and target-author
attribution lives in the stdlib-only pubmed_parse module (so that logic is CI-tested
without Biopython).

Disambiguation gate (see SKILL.md Step 6):
  - A surname alone does NOT resolve an author. Pass disambiguators
    (--initials / --orcid / --affiliation / --year-from / --year-to) and review the
    candidate clusters this script surfaces.
  - The finalized CSV is always written WITH a corpus_manifest.json that records the
    query, disambiguators, included/excluded PMIDs, a CSV sha256, a sorted-PMID-set
    hash, and review_status.
  - review_status is "approved" ONLY when --approve is passed, which is a HUMAN gate:
    the user passes it after reviewing the clusters. classify_archetypes.py refuses to
    run on a manifest that is not approved (or whose hashes do not match the CSV).

Usage:
    python fetch_pubmed.py "Author Name" --initials AB [--orcid 0000-...] \
        [--affiliation "Some Institution"] [--year-from 2015] [--year-to 2026] \
        [--disambiguate] [--include-pmids inc.txt] [--exclude-pmids exc.txt] [--approve] \
        [--output out.csv] [--email user@example.com]
"""

import argparse
import csv
import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from Bio import Entrez

import pubmed_parse

BATCH_SIZE = 100


def build_query(author: str, affiliation: str = "", year_from: str = "", year_to: str = "") -> str:
    q = f'"{author}"[Author]'
    if affiliation:
        q += f' AND "{affiliation}"[Affiliation]'
    if year_from or year_to:
        lo = year_from or "1900"
        hi = year_to or "3000"
        q += f' AND ("{lo}"[dp] : "{hi}"[dp])'
    return q


def search_pubmed(query: str) -> list[str]:
    handle = Entrez.esearch(db="pubmed", term=query, retmax=0)
    record = Entrez.read(handle)
    handle.close()
    total = int(record["Count"])
    print(f"Total results: {total}")

    pmids: list[str] = []
    for start in range(0, total, BATCH_SIZE):
        handle = Entrez.esearch(db="pubmed", term=query, retstart=start, retmax=BATCH_SIZE)
        record = Entrez.read(handle)
        handle.close()
        pmids.extend(record["IdList"])
        time.sleep(0.4)
    return pmids


def fetch_details(pmids: list[str], target_last: str, target_initials: str, target_orcid: str) -> list[dict]:
    all_records: list[dict] = []
    for start in range(0, len(pmids), BATCH_SIZE):
        batch = pmids[start:start + BATCH_SIZE]
        print(f"Fetching details {start+1}-{start+len(batch)} of {len(pmids)}...")
        handle = Entrez.efetch(db="pubmed", id=batch, rettype="xml", retmode="xml")
        xml_data = handle.read()
        handle.close()
        all_records.extend(
            pubmed_parse.records_from_xml(xml_data, target_last, target_initials, target_orcid)
        )
        time.sleep(0.5)
    return all_records


def read_pmid_file(path: str) -> set[str]:
    text = Path(path).read_text(encoding="utf-8")
    return {tok for tok in re.split(r"[\s,]+", text) if tok.strip().isdigit()}


def _affiliation_key(aff: str) -> str:
    if not aff:
        return "(affiliation unknown)"
    # First comma-delimited segment, lowercased, trimmed — a coarse institution token.
    seg = aff.split(",")[0].strip().lower()
    return seg[:60] or "(affiliation unknown)"


def cluster_candidates(records: list[dict]) -> list[dict]:
    """Group records into candidate clusters by target affiliation token + year span."""
    buckets: dict[str, list[dict]] = {}
    for r in records:
        buckets.setdefault(_affiliation_key(r.get("target_affiliation", "")), []).append(r)
    clusters = []
    for key, rows in buckets.items():
        years = [int(r["year"]) for r in rows if str(r.get("year", "")).isdigit()]
        clusters.append({
            "affiliation_token": key,
            "n_papers": len(rows),
            "year_min": min(years) if years else None,
            "year_max": max(years) if years else None,
            "sample_titles": [r["title"][:90] for r in rows[:3]],
            "pmids": [r["pmid"] for r in rows],
        })
    clusters.sort(key=lambda c: c["n_papers"], reverse=True)
    return clusters


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pmid_set_hash(pmids) -> str:
    joined = "\n".join(sorted(set(str(p) for p in pmids)))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def write_manifest(manifest_path: Path, *, query, disambiguators, included, excluded,
                   approved, output_csv: Path, record_count: int, pmids) -> None:
    manifest = {
        "schema": "author-strategy/corpus_manifest@1",
        "query": query,
        "disambiguators": disambiguators,
        "included_pmids": sorted(set(str(p) for p in included)) if included else [],
        "excluded_pmids": sorted(set(str(p) for p in excluded)) if excluded else [],
        "review_status": "approved" if approved else "pending",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "record_count": record_count,
        "csv_path": output_csv.name,
        "csv_sha256": sha256_file(output_csv),
        "pmid_set_hash": pmid_set_hash(pmids),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Fetch PubMed publications for an author (with disambiguation gate)")
    parser.add_argument("author", help="Author name for PubMed search (e.g., 'Kim DK')")
    parser.add_argument("--last-name", help="Last name for attribution (auto-detected if omitted)")
    parser.add_argument("--initials", default="", help="Target author initials for attribution (e.g., 'DK')")
    parser.add_argument("--orcid", default="", help="Target author ORCID (authoritative attribution)")
    parser.add_argument("--affiliation", default="", help="Affiliation filter to refine the PubMed search")
    parser.add_argument("--year-from", default="", help="Earliest publication year (refines search)")
    parser.add_argument("--year-to", default="", help="Latest publication year (refines search)")
    parser.add_argument("--output", "-o", help="Output CSV path", default=None)
    parser.add_argument("--manifest", help="Corpus manifest path (default: alongside CSV)", default=None)
    parser.add_argument("--include-pmids", help="File of PMIDs to keep (whitespace/comma separated)", default=None)
    parser.add_argument("--exclude-pmids", help="File of PMIDs to drop", default=None)
    parser.add_argument("--disambiguate", action="store_true",
                        help="Surface candidate clusters for manual review (does not auto-approve)")
    parser.add_argument("--approve", action="store_true",
                        help="HUMAN GATE: mark the corpus manifest review_status=approved after reviewing clusters")
    parser.add_argument("--email", help="Email for NCBI E-utilities", default="research@example.com")
    args = parser.parse_args()

    Entrez.email = args.email

    target_last = args.last_name or args.author.split()[-1]
    query = build_query(args.author, args.affiliation, args.year_from, args.year_to)

    if args.output:
        output_csv = Path(args.output)
    else:
        safe_name = args.author.replace(" ", "_").replace('"', "")
        output_csv = Path(f"{safe_name}_publications.csv")
    manifest_path = Path(args.manifest) if args.manifest else output_csv.with_name("corpus_manifest.json")

    has_disambiguator = bool(args.initials or args.orcid or args.affiliation or args.year_from or args.year_to)

    print(f"Searching PubMed for: {query}")
    print(f"Target last name for attribution: {target_last}")
    pmids = search_pubmed(query)
    print(f"Found {len(pmids)} PMIDs")
    if not pmids:
        print("No results found. Check the author name format (e.g., 'Yon DK' vs 'Yon D').")
        return

    records = fetch_details(pmids, target_last, args.initials, args.orcid)

    include = read_pmid_file(args.include_pmids) if args.include_pmids else None
    exclude = read_pmid_file(args.exclude_pmids) if args.exclude_pmids else set()
    if include is not None:
        records = [r for r in records if r["pmid"] in include]
    if exclude:
        records = [r for r in records if r["pmid"] not in exclude]
    print(f"Finalized corpus: {len(records)} records")

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=pubmed_parse.CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)
    print(f"Saved CSV: {output_csv}")

    # Candidate clusters for disambiguation review.
    clusters = cluster_candidates(records)
    candidates_path = output_csv.with_name("candidates.json")
    candidates_path.write_text(json.dumps(clusters, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n=== Candidate clusters (review before classifying) ===")
    for c in clusters:
        span = f"{c['year_min']}-{c['year_max']}" if c["year_min"] else "n/a"
        print(f"  [{c['n_papers']:>3} papers | {span}] {c['affiliation_token']}")
        for t in c["sample_titles"]:
            print(f"        - {t}")

    disambiguators = {
        "initials": args.initials, "orcid": args.orcid, "affiliation": args.affiliation,
        "year_from": args.year_from, "year_to": args.year_to,
    }
    write_manifest(
        manifest_path, query=query, disambiguators=disambiguators,
        included=include, excluded=exclude, approved=args.approve,
        output_csv=output_csv, record_count=len(records), pmids=[r["pmid"] for r in records],
    )
    print(f"\nSaved manifest: {manifest_path} (review_status={'approved' if args.approve else 'pending'})")

    if not args.approve:
        print("\n[GATE] Classification is BLOCKED until you approve the corpus.")
        if not has_disambiguator:
            print("       A surname alone does not resolve an author — pass --initials/--orcid/"
                  "--affiliation/--year-from/--year-to.")
        print("       Review candidates.json, then re-run with --include-pmids/--exclude-pmids "
              "and --approve to finalize.")

    # Quick summary.
    types = Counter(r["study_type"] for r in records)
    positions = Counter(r["author_position"] for r in records)
    print("\n=== Study Type Distribution ===")
    for k, v in types.most_common():
        print(f"  {k}: {v} ({v/len(records)*100:.1f}%)")
    print("\n=== Author Position (positional heuristic) ===")
    for k, v in positions.most_common():
        print(f"  {k}: {v} ({v/len(records)*100:.1f}%)")


if __name__ == "__main__":
    main()

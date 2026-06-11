#!/usr/bin/env python3
"""Step A helper — prepare the next batch from the queue.

Reads the next N uncommented lines of doi_lists/queue.txt, scaffolds the gitignored
_corpus/ directories, and appends a manifest stub per record (with safe defaults:
verbatim_allowed=false, public_reuse_policy=synthetic_only) for the agent to complete.

This does NOT download anything — fetching full text is done per PLAYBOOK Step A using
the fulltext-retrieval skill (OA articles) or open-review APIs. This only stages the
batch and the provenance ledger.

Usage:
    python3 reverse_engineer/scripts/acquire.py --batch 5
    python3 reverse_engineer/scripts/acquire.py --batch 5 --date 2026-06-12
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = RE_DIR.parent
QUEUE = RE_DIR / "doi_lists" / "queue.txt"
CORPUS = REPO_ROOT / "_corpus"
MANIFEST = CORPUS / "manifest.json"
RECORD_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_]{2,79}$")
DOMAINS = {"radiology_ai", "medical_ai", "medical_education", "clinical", "biostatistics", "ml_medicine"}


def read_queue(n: int) -> list[dict]:
    if not QUEUE.exists():
        sys.exit(f"queue not found: {QUEUE}")
    out = []
    for ln, raw in enumerate(QUEUE.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in re.split(r"\t+", line)]
        if len(parts) < 3:
            sys.exit(f"queue.txt line {ln}: expected 'record_id<TAB>doi_or_url<TAB>domain'")
        rid, src, domain = parts[0], parts[1], parts[2]
        if not RECORD_ID_RE.match(rid):
            sys.exit(f"queue.txt line {ln}: bad record_id '{rid}'")
        if domain not in DOMAINS:
            sys.exit(f"queue.txt line {ln}: unknown domain '{domain}' (one of {sorted(DOMAINS)})")
        out.append({"record_id": rid, "source": src, "domain": domain})
        if len(out) >= n:
            break
    return out


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"schema_version": 1, "records": []}


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage the next corpus batch + manifest stubs.")
    ap.add_argument("--batch", type=int, default=5, help="How many queue records to stage.")
    ap.add_argument("--date", default="", help="retrieved_at date (YYYY-MM-DD). Pass explicitly; not auto-stamped.")
    args = ap.parse_args()

    batch = read_queue(args.batch)
    if not batch:
        print("Queue is empty — nothing to stage.")
        return 0

    (CORPUS / "papers").mkdir(parents=True, exist_ok=True)
    (CORPUS / "analysis").mkdir(parents=True, exist_ok=True)

    manifest = load_manifest()
    existing = {r.get("record_id") for r in manifest.get("records", [])}
    added = 0
    for item in batch:
        rid = item["record_id"]
        if rid in existing:
            continue
        manifest["records"].append({
            "record_id": rid,
            "source_url": item["source"],
            "doi": item["source"] if item["source"].startswith("http") and "doi.org" in item["source"] else None,
            "source_type": "open_review" if "review" in rid else "oa_article",
            "license": "unknown",
            "license_url": "",
            "retrieved_at": args.date or "TODO-YYYY-MM-DD",
            "verbatim_allowed": False,
            "public_reuse_policy": "synthetic_only",
            "notes": "STUB — set real license/license_url and retrieved_at before distilling."
        })
        added += 1

    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Staged {len(batch)} record(s); {added} new manifest stub(s) in {MANIFEST}.")
    print("Next: fetch full text into _corpus/papers/<record_id>.md, then complete each")
    print("manifest record's license/license_url/retrieved_at (defaults stay until verified).")
    for item in batch:
        print(f"  - {item['record_id']}  [{item['domain']}]  {item['source']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

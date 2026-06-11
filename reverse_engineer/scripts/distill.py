#!/usr/bin/env python3
"""Step C gate — the license firewall in code.

Before any public artifact is emitted from a corpus source, the source must have a
complete, valid manifest record whose policy permits the intended reuse. This script:

  --check                 validate _corpus/manifest.json against the schema (stdlib only,
                          no jsonschema dependency) and reject leftover stubs.
  --authorize ID MODE     exit 0 iff record ID is valid AND permits MODE; MODE in
                          {synthetic, paraphrase, verbatim}. The record is re-validated
                          here too, so an invalid record can never authorize reuse.

Reuse rules (fail-closed):
  synthetic   — non-derivative output. Allowed only if the license is known (honest
                provenance); permitted for any known license.
  paraphrase  — allowed only if public_reuse_policy in {paraphrase_ok, cc_by_attribution}
                AND the license is permissive (CC-BY / CC0 family). NC/ND are blocked.
  verbatim    — allowed only if verbatim_allowed is strictly True AND public_reuse_policy
                == cc_by_attribution AND the license is permissive AND attribution is set.

A record with an unknown/empty license is learn-only: it authorizes nothing.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = RE_DIR.parent
SCHEMA = RE_DIR / "source_manifest.schema.json"
MANIFEST = REPO_ROOT / "_corpus" / "manifest.json"
RECORD_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_]{2,79}$")
MODES = ("synthetic", "paraphrase", "verbatim")

# Licenses that permit derivative reuse (paraphrase / verbatim). Compared lower-cased.
# NonCommercial (NC) and NoDerivatives (ND) variants are intentionally excluded.
PERMISSIVE_LICENSES = {
    "cc-by-4.0", "cc-by-3.0", "cc-by-2.0", "cc-by", "cc-by-sa-4.0",
    "cc0-1.0", "cc0", "publicdomain", "public-domain",
}
UNKNOWN_LICENSE = {"", "unknown", "none", "n/a", "na"}


def norm_license(lic) -> str:
    return str(lic or "").strip().lower()


def license_known(lic) -> bool:
    return norm_license(lic) not in UNKNOWN_LICENSE


def is_permissive(lic) -> bool:
    return norm_license(lic) in PERMISSIVE_LICENSES


def load_schema_enums() -> dict:
    """Read enum lists + required fields from the schema so it stays the SSOT."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    rec = schema["$defs"]["record"]
    return {
        "required": rec["required"],
        "source_type": rec["properties"]["source_type"]["enum"],
        "public_reuse_policy": rec["properties"]["public_reuse_policy"]["enum"],
    }


def load_manifest() -> dict:
    if not MANIFEST.exists():
        sys.exit(f"manifest not found: {MANIFEST} (run acquire.py first)")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def validate_record(r: dict, enums: dict) -> list[str]:
    """Per-record validation. Used by both --check and the --authorize gate."""
    errs: list[str] = []
    tag = r.get("record_id", "<no record_id>")
    for k in enums["required"]:
        if k not in r:
            errs.append(f"{tag}: missing required field '{k}'")
    rid = r.get("record_id", "")
    if rid and not RECORD_ID_RE.match(rid):
        errs.append(f"{tag}: bad record_id pattern")
    if r.get("source_type") not in enums["source_type"]:
        errs.append(f"{tag}: source_type must be one of {enums['source_type']}")
    policy = r.get("public_reuse_policy")
    if policy not in enums["public_reuse_policy"]:
        errs.append(f"{tag}: public_reuse_policy must be one of {enums['public_reuse_policy']}")
    # Strict types on the leakage-relevant fields.
    if not isinstance(r.get("verbatim_allowed"), bool):
        errs.append(f"{tag}: verbatim_allowed must be a JSON boolean (true/false)")
    if not isinstance(r.get("license", ""), str):
        errs.append(f"{tag}: license must be a string")
    # Stub / consistency checks.
    if str(r.get("retrieved_at", "")).startswith("TODO"):
        errs.append(f"{tag}: retrieved_at is still a stub")
    if "STUB" in str(r.get("notes", "")):
        errs.append(f"{tag}: notes still marked STUB — complete the record")
    # Policy ⇄ license/attribution coherence.
    if policy and policy != "synthetic_only" and not license_known(r.get("license")):
        errs.append(f"{tag}: unknown license cannot carry policy '{policy}'")
    if policy in ("paraphrase_ok", "cc_by_attribution"):
        if not r.get("license_url"):
            errs.append(f"{tag}: policy '{policy}' requires a license_url")
        if not is_permissive(r.get("license")):
            errs.append(f"{tag}: policy '{policy}' requires a permissive license (CC-BY/CC0); got '{r.get('license')}'")
    if policy == "cc_by_attribution" and not str(r.get("attribution", "")).strip():
        errs.append(f"{tag}: policy 'cc_by_attribution' requires a non-empty attribution")
    if r.get("verbatim_allowed") is True and policy != "cc_by_attribution":
        errs.append(f"{tag}: verbatim_allowed requires public_reuse_policy 'cc_by_attribution'")
    return errs


def validate(manifest: dict, enums: dict) -> list[str]:
    errs: list[str] = []
    if manifest.get("schema_version") != 1:
        errs.append("schema_version must be 1")
    records = manifest.get("records")
    if not isinstance(records, list):
        return ["'records' must be a list"]
    seen = set()
    for r in records:
        rid = r.get("record_id", "")
        if rid in seen:
            errs.append(f"{rid}: duplicate record_id")
        seen.add(rid)
        errs.extend(validate_record(r, enums))
    return errs


def find_record(manifest: dict, rid: str) -> dict | None:
    for r in manifest.get("records", []):
        if r.get("record_id") == rid:
            return r
    return None


def authorize(rec: dict, mode: str) -> tuple[bool, str]:
    lic = rec.get("license")
    if not license_known(lic):
        return False, "license is unknown/empty — acquire a real license before any reuse"
    policy = rec.get("public_reuse_policy", "synthetic_only")
    if mode == "synthetic":
        return True, "synthetic (non-derivative) output is permitted"
    if mode == "paraphrase":
        if policy in ("paraphrase_ok", "cc_by_attribution") and is_permissive(lic):
            return True, f"paraphrase permitted under '{policy}' ({lic})"
        return False, f"paraphrase needs policy paraphrase_ok/cc_by_attribution + a permissive license (got '{policy}', '{lic}')"
    if mode == "verbatim":
        if (rec.get("verbatim_allowed") is True
                and policy == "cc_by_attribution"
                and is_permissive(lic)
                and str(rec.get("attribution", "")).strip()):
            return True, "verbatim permitted (verbatim_allowed + cc_by_attribution + permissive + attribution)"
        return False, "verbatim needs verbatim_allowed=true + cc_by_attribution + permissive license + attribution"
    return False, f"unknown mode '{mode}'"


def main() -> int:
    ap = argparse.ArgumentParser(description="Manifest reuse gate (license firewall).")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="Validate the whole manifest.")
    g.add_argument("--authorize", nargs=2, metavar=("RECORD_ID", "MODE"),
                   help="Exit 0 iff RECORD_ID is valid and permits MODE (synthetic|paraphrase|verbatim).")
    args = ap.parse_args()

    enums = load_schema_enums()
    manifest = load_manifest()

    if args.check:
        errs = validate(manifest, enums)
        if errs:
            print("MANIFEST INVALID:")
            for e in errs:
                print(f"  - {e}")
            return 1
        print(f"OK: manifest valid ({len(manifest.get('records', []))} record(s))")
        return 0

    rid, mode = args.authorize
    if mode not in MODES:
        sys.exit(f"MODE must be one of {MODES}")
    rec = find_record(manifest, rid)
    if rec is None:
        print(f"DENY: no manifest record for '{rid}'")
        return 1
    # An invalid record can never authorize reuse (fail-closed).
    rec_errs = validate_record(rec, enums)
    if rec_errs:
        print(f"DENY: record '{rid}' fails validation:")
        for e in rec_errs:
            print(f"  - {e}")
        return 1
    ok, reason = authorize(rec, mode)
    print(f"{'ALLOW' if ok else 'DENY'}: {rid} / {mode} — {reason}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

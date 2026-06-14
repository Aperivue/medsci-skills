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
# Content licenses permissive enough for paraphrase/verbatim reuse. ShareAlike (CC-BY-SA) is
# intentionally EXCLUDED: it is copyleft, so reusing it into this MIT-licensed repo would
# impose share-alike obligations — learn from it, author fresh instead.
PERMISSIVE_LICENSES = {
    "cc-by-4.0", "cc-by-3.0", "cc-by-2.0", "cc-by",
    "cc0-1.0", "cc0", "publicdomain", "public-domain",
}
# Permissive SOFTWARE licenses — relevant only to linked code_repo artifacts, which carry a
# software license, not a content license. Verbatim code reuse is permitted under these (with
# attribution per the license). NonCommercial/NoDerivatives and copyleft-with-conditions stay
# out of the "verbatim without thought" set; the program publishes synthesis by default anyway.
SOFTWARE_PERMISSIVE_LICENSES = {
    "mit", "apache-2.0", "apache2.0", "apache-2", "bsd-2-clause", "bsd-3-clause",
    "bsd", "isc", "0bsd", "unlicense", "cc0-1.0", "cc0",
}
UNKNOWN_LICENSE = {"", "unknown", "none", "n/a", "na"}


def norm_license(lic) -> str:
    return str(lic or "").strip().lower()


def license_known(lic) -> bool:
    return norm_license(lic) not in UNKNOWN_LICENSE


def is_permissive(lic) -> bool:
    return norm_license(lic) in PERMISSIVE_LICENSES


def is_permissive_artifact(lic, artifact_type=None) -> bool:
    """Whether a linked artifact's license permits paraphrase/verbatim reuse.

    Artifact-type-aware: a SOFTWARE license (MIT/Apache/BSD/...) only authorizes reuse of a
    code repository's *code*. Data, supplementary, figures, model cards, and text are content,
    so they need a CONTENT-permissive license (CC-BY/CC0) — a dataset stamped 'MIT' does not
    authorize copying its figures/text."""
    n = norm_license(lic)
    if artifact_type == "code_repo":
        return n in (PERMISSIVE_LICENSES | SOFTWARE_PERMISSIVE_LICENSES)
    return n in PERMISSIVE_LICENSES


def load_schema_enums() -> dict:
    """Read enum lists + required fields from the schema so it stays the SSOT."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    rec = schema["$defs"]["record"]
    art = schema["$defs"]["linked_artifact"]
    return {
        "required": rec["required"],
        "source_type": rec["properties"]["source_type"]["enum"],
        "public_reuse_policy": rec["properties"]["public_reuse_policy"]["enum"],
        "artifact_required": art["required"],
        "artifact_type": art["properties"]["artifact_type"]["enum"],
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
    # Linked artifacts (supplementary / code repo / dataset / model card) — each carries its
    # OWN license, verified independently of the article.
    arts = r.get("linked_artifacts")
    if arts is not None:
        if not isinstance(arts, list):
            errs.append(f"{tag}: linked_artifacts must be a list")
        else:
            for i, a in enumerate(arts):
                errs.extend(validate_artifact(a, enums, f"{tag}#{i}"))
    return errs


def validate_artifact(a: dict, enums: dict, tag: str) -> list[str]:
    """Validate one linked artifact's shape + license/policy coherence (fail-closed)."""
    errs: list[str] = []
    if not isinstance(a, dict):
        return [f"{tag}: linked_artifact must be an object"]
    for k in enums["artifact_required"]:
        if k not in a:
            errs.append(f"{tag}: missing required field '{k}'")
    if a.get("artifact_type") not in enums["artifact_type"]:
        errs.append(f"{tag}: artifact_type must be one of {enums['artifact_type']}")
    policy = a.get("public_reuse_policy", "synthetic_only")
    if policy not in enums["public_reuse_policy"]:
        errs.append(f"{tag}: public_reuse_policy must be one of {enums['public_reuse_policy']}")
    if "verbatim_allowed" in a and not isinstance(a.get("verbatim_allowed"), bool):
        errs.append(f"{tag}: verbatim_allowed must be a JSON boolean (true/false)")
    if not isinstance(a.get("license", ""), str):
        errs.append(f"{tag}: license must be a string")
    if "STUB" in str(a.get("notes", "")):
        errs.append(f"{tag}: notes still marked STUB — complete the artifact")
    if policy and policy != "synthetic_only" and not license_known(a.get("license")):
        errs.append(f"{tag}: unknown license cannot carry policy '{policy}'")
    if policy in ("paraphrase_ok", "cc_by_attribution"):
        if not a.get("license_url"):
            errs.append(f"{tag}: policy '{policy}' requires a license_url")
        if not is_permissive_artifact(a.get("license"), a.get("artifact_type")):
            kind = "CC-BY/CC0, or a permissive software license for a code_repo" \
                if a.get("artifact_type") == "code_repo" else "CC-BY/CC0 (content)"
            errs.append(f"{tag}: policy '{policy}' requires a permissive license ({kind}); got '{a.get('license')}'")
    if policy == "cc_by_attribution" and not str(a.get("attribution", "")).strip():
        errs.append(f"{tag}: policy 'cc_by_attribution' requires a non-empty attribution")
    if a.get("verbatim_allowed") is True and policy != "cc_by_attribution":
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
    for i, r in enumerate(records):
        if not isinstance(r, dict):
            errs.append(f"records[{i}]: each record must be an object")
            continue
        rid = r.get("record_id", "")
        if rid in seen:
            errs.append(f"{rid}: duplicate record_id")
        seen.add(rid)
        errs.extend(validate_record(r, enums))
    return errs


def find_record(manifest: dict, rid: str) -> dict | None:
    for r in manifest.get("records", []):
        if isinstance(r, dict) and r.get("record_id") == rid:
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


def authorize_artifact(art: dict, mode: str) -> tuple[bool, str]:
    """Like authorize(), but for a linked artifact: software-permissive licenses also count
    (a code repo's MIT/Apache license permits code reuse; a CC0/CC-BY dataset permits data/
    figure reuse)."""
    lic = art.get("license")
    atype = art.get("artifact_type")
    if not license_known(lic):
        return False, "artifact license is unknown/empty — verify it before any reuse"
    policy = art.get("public_reuse_policy", "synthetic_only")
    if mode == "synthetic":
        return True, "synthetic (non-derivative) output is permitted"
    if mode == "paraphrase":
        if policy in ("paraphrase_ok", "cc_by_attribution") and is_permissive_artifact(lic, atype):
            return True, f"paraphrase/adaptation permitted under '{policy}' ({lic})"
        return False, f"paraphrase needs policy paraphrase_ok/cc_by_attribution + a license permissive for this artifact type (got '{policy}', '{lic}', type '{atype}')"
    if mode == "verbatim":
        if (art.get("verbatim_allowed") is True
                and policy == "cc_by_attribution"
                and is_permissive_artifact(lic, atype)
                and str(art.get("attribution", "")).strip()):
            return True, "verbatim permitted (verbatim_allowed + cc_by_attribution + permissive + attribution)"
        return False, "verbatim needs verbatim_allowed=true + cc_by_attribution + permissive license + attribution"
    return False, f"unknown mode '{mode}'"


def main() -> int:
    ap = argparse.ArgumentParser(description="Manifest reuse gate (license firewall).")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="Validate the whole manifest.")
    g.add_argument("--authorize", nargs=2, metavar=("RECORD_ID", "MODE"),
                   help="Exit 0 iff the source is valid and permits MODE (synthetic|paraphrase|verbatim). "
                        "RECORD_ID may be 'id' (the article) or 'id#N' (its Nth linked artifact, 0-based).")
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

    target, mode = args.authorize
    if mode not in MODES:
        sys.exit(f"MODE must be one of {MODES}")

    has_hash = "#" in target
    rid, _, art_idx = target.partition("#")
    rec = find_record(manifest, rid)
    if rec is None:
        print(f"DENY: no manifest record for '{rid}'")
        return 1
    # An invalid record can never authorize reuse (fail-closed) — validates its artifacts too.
    rec_errs = validate_record(rec, enums)
    if rec_errs:
        print(f"DENY: record '{rid}' fails validation:")
        for e in rec_errs:
            print(f"  - {e}")
        return 1

    if not has_hash:
        ok, reason = authorize(rec, mode)
        print(f"{'ALLOW' if ok else 'DENY'}: {rid} / {mode} — {reason}")
        return 0 if ok else 1

    # Authorize a specific linked artifact. A '#' with a malformed/empty index fails closed
    # (ASCII-digits only — some Unicode digits pass str.isdigit() but break int()).
    arts = rec.get("linked_artifacts") or []
    if not re.fullmatch(r"[0-9]+", art_idx) or int(art_idx) >= len(arts):
        print(f"DENY: '{rid}' has no linked artifact #{art_idx} (has {len(arts)})")
        return 1
    art = arts[int(art_idx)]
    ok, reason = authorize_artifact(art, mode)
    label = f"{rid}#{art_idx} ({art.get('artifact_type', '?')})"
    print(f"{'ALLOW' if ok else 'DENY'}: {label} / {mode} — {reason}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

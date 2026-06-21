#!/usr/bin/env python3
"""Version-drift gate (self-update foundation).

CITATION.cff is the canonical version SSOT. This asserts that the three places a
release version is declared agree, so a release can never ship mismatched versions:

  CITATION.cff `version:`  ==  package.json `version`  ==  metadata/distribution_manifest.json `version`

Stdlib-only. Exit 0 if all agree, 1 on any mismatch, 2 on a read error. CI gate.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def citation_version() -> str:
    text = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    m = re.search(r'^version:\s*"?([0-9]+\.[0-9]+\.[0-9]+)"?\s*$', text, re.MULTILINE)
    if not m:
        raise ValueError("CITATION.cff: no semver version: field")
    return m.group(1)


def package_version() -> str:
    v = json.loads((ROOT / "package.json").read_text(encoding="utf-8")).get("version", "")
    if not SEMVER.match(v):
        raise ValueError(f"package.json: version {v!r} is not semver")
    return v


def manifest_version() -> str:
    p = ROOT / "metadata" / "distribution_manifest.json"
    if not p.exists():
        raise ValueError("metadata/distribution_manifest.json missing — run gen_distribution_manifest.py")
    v = json.loads(p.read_text(encoding="utf-8")).get("version", "")
    if not SEMVER.match(v):
        raise ValueError(f"distribution_manifest.json: version {v!r} is not semver")
    return v


def main() -> int:
    try:
        cit, pkg, man = citation_version(), package_version(), manifest_version()
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print("=" * 41)
    print(" Version Consistency")
    print("=" * 41)
    print(f"  CITATION.cff                : {cit}")
    print(f"  package.json                : {pkg}")
    print(f"  distribution_manifest.json  : {man}")
    if cit == pkg == man:
        print(f"\nOK: all three declare {cit}.")
        return 0
    print("\nVERSION_DRIFT: CITATION.cff is canonical; bring package.json and "
          "distribution_manifest.json (re-run gen_distribution_manifest.py) into agreement.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

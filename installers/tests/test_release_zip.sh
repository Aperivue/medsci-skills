#!/usr/bin/env bash
# Release-ZIP provenance + updater-consumability round-trip (PR-2, release-workflow hardening).
#
# Builds the real classroom ZIPs the way the release workflow does (with an injected provenance.json)
# and verifies them with scripts/check_release_zip.py, which runs the UPDATER'S OWN safe_extract +
# validate_provenance. This guarantees a tagged release cannot ship a ZIP the self-updater would
# reject (inventory hash drift, missing provenance, tag mismatch). Hash-sensitive -> Ubuntu CI only
# (the `validate` job), like gen_distribution_manifest --check.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

fail() { echo "FAIL: $*" >&2; exit 1; }

VER="$(python3 -c 'import json;print(json.load(open("metadata/distribution_manifest.json"))["version"])')"
TAG="v${VER}"
echo "release-zip test: building tag ${TAG}"

cleanup() { rm -rf dist; }
trap cleanup EXIT

# 1. Build with provenance (deterministic git-sha/built-at), exactly as release.yml will.
python3 scripts/build_classroom_release.py --tag "$TAG" --git-sha "0000000000000000000000000000000000000000" --built-at "2020-01-01T00:00:00Z" >/dev/null

# 2. Both ZIPs must be updater-consumable with matching provenance tag + present provenance.
for plat in macos windows; do
  zip="dist/medsci-skills-classroom-${plat}.zip"
  [ -f "$zip" ] || fail "build did not produce $zip"
  python3 scripts/check_release_zip.py --zip "$zip" --expect-tag "$TAG" --require-provenance \
    || fail "$zip is not updater-consumable"
done
echo "PASS  both ZIPs round-trip through update.safe_extract with provenance tag ${TAG}"

# 3. Version gate: building with a tag that disagrees with the manifest must fail the build.
if python3 scripts/build_classroom_release.py --tag "v0.0.0" >/dev/null 2>&1; then
  fail "build accepted a tag that disagrees with distribution_manifest version"
fi
echo "PASS  build rejects a tag/version mismatch (release cannot ship a stale manifest)"

# 4. Verifier rejects an expect-tag mismatch (provenance tag must equal the release tag).
python3 scripts/build_classroom_release.py --tag "$TAG" --git-sha x --built-at 2020-01-01T00:00:00Z >/dev/null
if python3 scripts/check_release_zip.py --zip "dist/medsci-skills-classroom-macos.zip" --expect-tag "v0.0.0" >/dev/null 2>&1; then
  fail "verifier accepted a provenance/expect-tag mismatch"
fi
echo "PASS  verifier rejects a provenance/expect-tag mismatch"

# 5. --expect-tag must not pass vacuously on a provenance-less (local) build.
python3 scripts/build_classroom_release.py >/dev/null   # no --tag -> no provenance.json
if python3 scripts/check_release_zip.py --zip "dist/medsci-skills-classroom-macos.zip" --expect-tag "$TAG" >/dev/null 2>&1; then
  fail "verifier accepted --expect-tag on a ZIP with no provenance.json"
fi
echo "PASS  verifier rejects --expect-tag when provenance.json is absent"

echo "test_release_zip: all checks passed"

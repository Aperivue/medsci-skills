#!/usr/bin/env bash
# Reproducible, network-free regression test for the distill.py license firewall, focused on
# linked_artifacts (supplementary / code repo / data deposit). Builds a temporary, gitignored
# _corpus/manifest.json fixture, asserts the --check and --authorize behaviors, and restores
# any pre-existing manifest. Run: bash reverse_engineer/scripts/test_distill_artifacts.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
RE_DIR="$(dirname "$HERE")"
REPO_ROOT="$(dirname "$RE_DIR")"
DISTILL="$RE_DIR/scripts/distill.py"
CORPUS="$REPO_ROOT/_corpus"
MANIFEST="$CORPUS/manifest.json"
BACKUP=""

cleanup() {
  rm -f "$MANIFEST"
  if [ -n "$BACKUP" ] && [ -f "$BACKUP" ]; then mv "$BACKUP" "$MANIFEST"; fi
  rmdir "$CORPUS" 2>/dev/null || true
}
trap cleanup EXIT

if [ -f "$MANIFEST" ]; then BACKUP="$MANIFEST.testbak"; mv "$MANIFEST" "$BACKUP"; fi
mkdir -p "$CORPUS"

cat > "$MANIFEST" <<'JSON'
{
  "schema_version": 1,
  "records": [
    {
      "record_id": "fixture_paper_2026",
      "source_url": "https://doi.org/10.1234/fixture",
      "doi": "10.1234/fixture",
      "source_type": "oa_article",
      "license": "CC-BY-4.0",
      "license_url": "https://creativecommons.org/licenses/by/4.0/",
      "retrieved_at": "2026-06-14",
      "verbatim_allowed": false,
      "public_reuse_policy": "synthetic_only",
      "notes": "fixture",
      "linked_artifacts": [
        {"url": "https://github.com/x/y", "artifact_type": "code_repo", "license": "MIT",
         "license_url": "https://github.com/x/y/blob/main/LICENSE", "public_reuse_policy": "synthetic_only", "notes": "code"},
        {"url": "https://zenodo.org/records/1", "artifact_type": "dataset", "doi": "10.5281/zenodo.1", "license": "CC0-1.0",
         "license_url": "https://creativecommons.org/publicdomain/zero/1.0/", "public_reuse_policy": "synthetic_only", "notes": "data"},
        {"url": "https://ex.com/s.pdf", "artifact_type": "supplementary", "license": "unknown",
         "license_url": "", "public_reuse_policy": "synthetic_only", "notes": "suppl"}
      ]
    }
  ]
}
JSON

fail=0
expect() { # <desc> <expected_exit> <cmd...>
  local desc="$1" want="$2"; shift 2
  "$@" >/dev/null 2>&1; local got=$?
  if [ "$got" = "$want" ]; then echo "ok   ($want) $desc"; else echo "FAIL (want $want got $got) $desc"; fail=1; fi
}

expect "manifest with linked_artifacts validates"        0 python3 "$DISTILL" --check
expect "article synthetic allowed"                       0 python3 "$DISTILL" --authorize fixture_paper_2026 synthetic
expect "code_repo#0 (MIT) synthetic allowed"             0 python3 "$DISTILL" --authorize fixture_paper_2026#0 synthetic
expect "code_repo#0 verbatim denied (synthetic_only)"    1 python3 "$DISTILL" --authorize fixture_paper_2026#0 verbatim
expect "dataset#1 (CC0) synthetic allowed"               0 python3 "$DISTILL" --authorize fixture_paper_2026#1 synthetic
expect "supplementary#2 (unknown) synthetic denied"      1 python3 "$DISTILL" --authorize fixture_paper_2026#2 synthetic
expect "out-of-range artifact denied"                    1 python3 "$DISTILL" --authorize fixture_paper_2026#9 synthetic

expect "trailing '#' with empty index denied (not the article)" 1 python3 "$DISTILL" --authorize "fixture_paper_2026#" synthetic
expect "negative index denied"                                  1 python3 "$DISTILL" --authorize "fixture_paper_2026#-1" synthetic

# A code_repo declaring paraphrase_ok under a permissive software license must authorize paraphrase.
setpol() { python3 - "$MANIFEST" "$@" <<'PY'
import json,sys
p=sys.argv[1]; idx=int(sys.argv[2]); d=json.load(open(p))
a=d["records"][0]["linked_artifacts"][idx]
for kv in sys.argv[3:]:
    k,v=kv.split("=",1); a[k]=v
open(p,"w").write(json.dumps(d))
PY
}
setpol 0 public_reuse_policy=paraphrase_ok
expect "code_repo#0 paraphrase allowed under MIT+paraphrase_ok"  0 python3 "$DISTILL" --authorize fixture_paper_2026#0 paraphrase
setpol 0 license=GPL-3.0
expect "code_repo#0 GPL paraphrase DENIED (copyleft, not permissive)" 1 python3 "$DISTILL" --authorize fixture_paper_2026#0 paraphrase

# Reset code_repo#0 to a valid state so the record validates while we exercise artifact #1
# (any invalid artifact makes the whole record fail-closed — fine in practice, noisy in tests).
setpol 0 license=MIT license_url=https://github.com/x/y/blob/main/LICENSE public_reuse_policy=synthetic_only

# Artifact-type-aware: a dataset stamped with a SOFTWARE license must NOT authorize content reuse.
setpol 1 public_reuse_policy=paraphrase_ok license=MIT license_url=https://opensource.org/license/mit
expect "dataset#1 MIT paraphrase DENIED (software license != content)" 1 python3 "$DISTILL" --authorize fixture_paper_2026#1 paraphrase
setpol 1 license=CC-BY-4.0 license_url=https://creativecommons.org/licenses/by/4.0/
expect "dataset#1 CC-BY paraphrase allowed (content-permissive)"       0 python3 "$DISTILL" --authorize fixture_paper_2026#1 paraphrase
setpol 1 license=CC-BY-NC-4.0 license_url=https://creativecommons.org/licenses/by-nc/4.0/
expect "dataset#1 CC-BY-NC paraphrase DENIED (NonCommercial)"          1 python3 "$DISTILL" --authorize fixture_paper_2026#1 paraphrase

if [ "$fail" = 0 ]; then echo "ALL DISTILL ARTIFACT TESTS PASSED"; else echo "DISTILL ARTIFACT TESTS FAILED"; fi
exit "$fail"

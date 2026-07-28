#!/usr/bin/env bash
# Self-test for the held-out acquisition pipeline. Network-free: the frame and fetch phases are
# the only ones that touch E-utilities, and everything downstream reads artifacts, so every rule
# that decides WHAT ENDS UP IN THE CORPUS is testable offline.
#
# The case that matters is `seal`. Its whole job is to refuse, and a gate never shown refusing is
# a gate nobody has tested — so each target is violated in turn and the refusal is required.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
A="$HERE/acquire_heldout.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }

W="$TMP/work"; mkdir -p "$W"

echo "== 1. exclusion rules drop what the protocol says to drop, and COUNT each reason =="
cat > "$W/candidates.json" <<'EOF'
{"query": "test", "retrieved_at": "2026-08-01", "n": 6, "candidates": [
 {"pmcid":"PMC1","doi":"10.1000/aaa","title":"A randomized trial of something","journal":"J","pubdate":"2025","pubtype":["Journal Article"]},
 {"pmcid":"PMC2","doi":"10.1000/bbb","title":"CONSORT 2025 explanation and elaboration","journal":"J","pubdate":"2025","pubtype":["Journal Article"]},
 {"pmcid":"PMC3","doi":"10.1000/ccc","title":"Erratum: an earlier paper","journal":"J","pubdate":"2025","pubtype":["Published Erratum"]},
 {"pmcid":"PMC4","doi":"","title":"A paper with no DOI","journal":"J","pubdate":"2025","pubtype":["Journal Article"]},
 {"pmcid":"PMC5","doi":"10.1000/ddd","title":"A cohort study of outcomes","journal":"J","pubdate":"2025","pubtype":["Journal Article"]},
 {"pmcid":"PMC6","doi":"10.1000/eee","title":"PRISMA extension statement for scoping reviews","journal":"J","pubdate":"2025","pubtype":["Journal Article"]}
]}
EOF
python3 "$A" --phase exclude --work "$W" > "$TMP/ex.txt" 2>&1 || fail "exclude phase failed"
python3 - "$W/eligible.json" <<'PY' || exit 1
import json, sys
d = json.load(open(sys.argv[1]))
kept = {c["pmcid"] for c in d["eligible"]}
assert kept == {"PMC1", "PMC5"}, "wrong survivors: %r" % kept
c = d["exclusion_counts"]
# Each reason counted on its own. "excluded: 4" is not an audit trail.
for reason in ("reporting_guideline_document", "non_research_article_type", "no_doi"):
    assert c.get(reason), "reason not counted: %s (%r)" % (reason, c)
assert c["reporting_guideline_document"] == 2, c   # CONSORT E&E and the PRISMA extension
PY

echo "== 2. a DOI already in the development corpus is refused =="
# The measurement claims no detector was written knowing this paper. A DOI the project has already
# read breaks that claim silently, which is the worst way for it to break.
DL="$HERE/../doi_lists"; mkdir -p "$DL"
echo "10.1000/ddd  already-read" > "$DL/_test_seen.txt"
python3 "$A" --phase exclude --work "$W" >/dev/null 2>&1 || fail "exclude phase failed"
rm -f "$DL/_test_seen.txt"
python3 - "$W/eligible.json" <<'PY' || exit 1
import json, sys
d = json.load(open(sys.argv[1]))
assert {c["pmcid"] for c in d["eligible"]} == {"PMC1"}, d["eligible"]
assert d["exclusion_counts"].get("already_in_development_corpus") == 1, d["exclusion_counts"]
PY
python3 "$A" --phase exclude --work "$W" >/dev/null 2>&1   # restore the 2-survivor state

echo "== 3. the draw is seeded, reproducible, and refuses an allocation chosen after the fact =="
python3 - "$W/eligible.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
d["eligible"] = [{"pmcid": f"PMC{i}", "doi": f"10.1000/x{i}", "title": f"t{i}",
                  "journal": "J", "pubdate": "2025", "pubtype": ["Journal Article"]}
                 for i in range(1, 21)]
json.dump(d, open(sys.argv[1], "w"))
PY
python3 - "$TMP/alloc.json" <<'PY'
import json, sys
assign = {f"PMC{i}": ("rct" if i <= 10 else "cohort") for i in range(1, 21)}
json.dump({"targets": {"rct": 3, "cohort": 3}, "assign": assign}, open(sys.argv[1], "w"))
PY
# Compare the DRAWN SET, never the artifact. selection.json records the seed it was given, so a
# whole-file comparison differs whenever the seed differs — including when the seed is ignored
# entirely. A first version did exactly that and passed happily against a build with the seed
# hardcoded to 0: an assertion that looked like reproducibility and tested bookkeeping.
drawn_ids() { python3 -c "import json,sys;print(' '.join(sorted(c['pmcid'] for c in json.load(open(sys.argv[1]))['drawn'])))" "$1"; }
python3 "$A" --phase sample --work "$W" --alloc "$TMP/alloc.json" --seed 42 >/dev/null 2>&1
A42="$(drawn_ids "$W/selection.json")"; cp "$W/selection.json" "$TMP/sel_a.json"
python3 "$A" --phase sample --work "$W" --alloc "$TMP/alloc.json" --seed 42 >/dev/null 2>&1
[ "$(drawn_ids "$W/selection.json")" = "$A42" ] || fail "same seed drew a different sample"
python3 "$A" --phase sample --work "$W" --alloc "$TMP/alloc.json" --seed 7 >/dev/null 2>&1
[ "$(drawn_ids "$W/selection.json")" != "$A42" ] \
  || fail "a different seed drew the same sample — the recorded seed does not govern the draw"
cp "$TMP/sel_a.json" "$W/selection.json"

python3 - "$TMP/noalloc.json" <<'PY'
import json, sys
json.dump({"assign": {}}, open(sys.argv[1], "w"))
PY
python3 "$A" --phase sample --work "$W" --alloc "$TMP/noalloc.json" >/dev/null 2>&1 \
  && fail "sampling proceeded with no pre-registered target allocation"

echo "== 4. SEAL REFUSES each way the corpus can fail to be what was promised =="
OUT="$TMP/corpus"; mkdir -p "$OUT"
# Build a selection + rendered corpus that PASSES, then break it one target at a time.
python3 - "$W/selection.json" "$OUT" <<'PY'
import json, pathlib, sys
sel = json.load(open(sys.argv[1]))
out = pathlib.Path(sys.argv[2])
drawn = []
for i in range(1, 15):
    rid = f"ho_p{i:02d}"
    drawn.append({"pmcid": f"PMC{i}", "doi": f"10.1000/x{i}", "record_id": rid,
                  "license": "CC-BY-4.0", "coverage_design": f"design{i}",
                  "coverage_modality": f"mod{i}", "coverage_task": f"task{i}"})
    (out / f"{rid}.md").write_text("# paper\n")
sel["drawn"] = drawn
json.dump(sel, open(sys.argv[1], "w"))
PY
python3 "$A" --phase seal --work "$W" --out "$OUT" --manifest "$TMP/m.json" \
    --frozen-at 2026-08-01 --min-n 14 --min-profiles 12 >/dev/null 2>&1 \
  || fail "seal refused a corpus that meets every target"

python3 "$A" --phase seal --work "$W" --out "$OUT" --manifest "$TMP/m.json" \
    --frozen-at 2026-08-01 --min-n 40 --min-profiles 12 >"$TMP/s1.txt" 2>&1 \
  && fail "seal accepted 14 papers when 40 were required"
grep -q "only 14 rendered" "$TMP/s1.txt" || fail "the n shortfall was not named: $(cat "$TMP/s1.txt")"

# concentration: one design value taking most of the corpus
python3 - "$W/selection.json" <<'PY'
import json, sys
sel = json.load(open(sys.argv[1]))
for c in sel["drawn"][:10]:
    c["coverage_design"] = "retrospective_ct"
json.dump(sel, open(sys.argv[1], "w"))
PY
python3 "$A" --phase seal --work "$W" --out "$OUT" --manifest "$TMP/m.json" \
    --frozen-at 2026-08-01 --min-n 14 --min-profiles 12 >"$TMP/s2.txt" 2>&1 \
  && fail "seal accepted a corpus where one design holds 10 of 14"
grep -q "coverage_design=retrospective_ct holds 10/14" "$TMP/s2.txt" \
  || fail "concentration was not named: $(cat "$TMP/s2.txt")"

# duplicate full profiles: one pattern measured twice is not two observations
python3 - "$W/selection.json" <<'PY'
import json, sys
sel = json.load(open(sys.argv[1]))
for i, c in enumerate(sel["drawn"]):
    c["coverage_design"] = f"design{i}"
sel["drawn"][1].update(sel["drawn"][0]); sel["drawn"][1]["record_id"] = "ho_p02"
json.dump(sel, open(sys.argv[1], "w"))
PY
python3 "$A" --phase seal --work "$W" --out "$OUT" --manifest "$TMP/m.json" \
    --frozen-at 2026-08-01 --min-n 14 --min-profiles 12 >"$TMP/s3.txt" 2>&1 \
  && fail "seal accepted a corpus with a duplicated coverage profile"
grep -q "appear more than once" "$TMP/s3.txt" || fail "the duplicate profile was not named"

echo "== 5. an unlicensed record cannot seal silently =="
python3 - "$W/selection.json" <<'PY'
import json, sys
sel = json.load(open(sys.argv[1]))
for i, c in enumerate(sel["drawn"]):
    c.update({"coverage_design": f"design{i}", "coverage_modality": f"mod{i}",
              "coverage_task": f"task{i}", "record_id": f"ho_p{i+1:02d}"})
sel["drawn"][3].pop("license", None)
json.dump(sel, open(sys.argv[1], "w"))
PY
python3 "$A" --phase seal --work "$W" --out "$OUT" --manifest "$TMP/m.json" \
    --frozen-at 2026-08-01 --min-n 14 --min-profiles 12 >"$TMP/s4.txt" 2>&1 \
  && fail "seal returned success with an unlicensed record"
grep -q "no license" "$TMP/s4.txt" || fail "the unlicensed record was not named"

echo "PASS: exclusions counted per reason, development-corpus DOIs refused, draw seeded and"
echo "      reproducible, and seal refuses on n, concentration, duplicate profile and license."

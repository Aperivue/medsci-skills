#!/usr/bin/env bash
# Self-test for scripts/check_domain_probe_sync.py (the vendoring drift gate).
#
# The defect this gate was extended to catch: six risk-of-bias checklists are vendored
# byte-identical from /check-reporting into /meta-analysis and NOTHING asserted they stay in sync.
# Case 3 restores that defect (drift a vendored checklist) and asserts the gate FAILS. Before the
# extension, that case exited 0 — a gate that watched the probes and looked straight past the
# checklists.
#
#  1) live repo passes                                    (no drift today)
#  2) copied tree passes                                  NEGATIVE FIXTURE — silent on good work
#  3) drifted vendored CHECKLIST fails                    <-- THE DEFECT (previously ungated)
#  4) --sync repairs the drift
#  5) drifted vendored PROBE fails                        (original behaviour preserved)
#  6) drifted vendored CODE helper fails                  (the sets are not all Markdown)
#  7) an UNDECLARED vendored pair fails                   (a further set cannot be forgotten)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GATE="$ROOT/scripts/check_domain_probe_sync.py"

CHECKLIST="skills/meta-analysis/references/checklists/RoB2.md"
PROBE="skills/self-review/references/domain-probes/sr_ma.md"
CODE="skills/verify-refs/scripts/_quote_match.py"

# 1) live repo passes
python3 "$GATE" --strict >/dev/null || { echo "FAIL: live repo should be in sync" >&2; exit 1; }

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/skills"
# Which skills the fixture needs is DERIVED from the gate's own table, not listed here. A
# hardcoded list silently becomes wrong the moment a set is added: the copied tree then lacks a
# declared canonical dir, the gate aborts with "canonical dir missing", and the failure reads as
# a broken gate rather than a stale fixture. It did exactly that once.
VSKILLS="$(python3 - "$ROOT" <<'VS_EOF'
import importlib.util, pathlib, sys
root = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("gate", root / "scripts/check_domain_probe_sync.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
skills = {d.split("/")[1] for vs in mod.VENDOR_SETS for d in (vs.canonical, vs.vendored)
          if d.split("/")[0] == "skills"}
print(" ".join(sorted(skills)))
VS_EOF
)"
for s in $VSKILLS; do
  cp -R "$ROOT/skills/$s" "$tmp/skills/$s"
done

# 2) NEGATIVE FIXTURE: an untouched copy must stay silent — including meta-analysis's local-only
#    JBI_Case_Series.md, which has no canonical counterpart and must NOT be reported as a stray.
python3 "$GATE" --root "$tmp" --strict >/dev/null \
  || { echo "FAIL: an untouched tree must pass (gate fires on good work)" >&2; exit 1; }

# 3) THE DEFECT: drift a vendored checklist by one byte -> must FAIL
printf '\n<!-- drift -->\n' >> "$tmp/$CHECKLIST"
if python3 "$GATE" --root "$tmp" --strict >/dev/null 2>&1; then
  echo "FAIL: a drifted vendored CHECKLIST must exit 1 (this is the defect the gate exists for)" >&2
  exit 1
fi
# the gate exits 1 here, so capture before grepping (pipefail would swallow the report)
report="$(python3 "$GATE" --root "$tmp" --strict 2>&1 || true)"
grep -q "rob-checklists.*drift: RoB2.md" <<<"$report" \
  || { echo "FAIL: the report must name the drifted checklist" >&2; echo "$report" >&2; exit 1; }

# 4) --sync repairs it
python3 "$GATE" --root "$tmp" --sync >/dev/null
python3 "$GATE" --root "$tmp" --strict >/dev/null \
  || { echo "FAIL: --sync should restore byte-identity" >&2; exit 1; }
cmp -s "$tmp/$CHECKLIST" "$ROOT/skills/check-reporting/references/checklists/RoB2.md" \
  || { echo "FAIL: --sync must reproduce the canonical bytes" >&2; exit 1; }

# 5) original behaviour preserved: a drifted vendored probe still fails
printf '\n<!-- drift -->\n' >> "$tmp/$PROBE"
if python3 "$GATE" --root "$tmp" --strict >/dev/null 2>&1; then
  echo "FAIL: a drifted vendored PROBE must exit 1" >&2; exit 1
fi
python3 "$GATE" --root "$tmp" --sync >/dev/null
python3 "$GATE" --root "$tmp" --strict >/dev/null || { echo "FAIL: --sync should repair probe" >&2; exit 1; }

# 6) the sets are not all Markdown: a vendored CODE helper must be guarded too. Before the
#    pattern extension the membership checks globbed *.md only, so a .py set could be declared
#    while neither side's files were ever listed.
printf '\n# drift\n' >> "$tmp/$CODE"
if python3 "$GATE" --root "$tmp" --strict >/dev/null 2>&1; then
  echo "FAIL: a drifted vendored CODE helper must exit 1" >&2; exit 1
fi
report="$(python3 "$GATE" --root "$tmp" --strict 2>&1 || true)"
grep -q "quote-match-helper.*drift: _quote_match.py" <<<"$report" \
  || { echo "FAIL: the report must name the drifted helper" >&2; echo "$report" >&2; exit 1; }
python3 "$GATE" --root "$tmp" --sync >/dev/null
python3 "$GATE" --root "$tmp" --strict >/dev/null || { echo "FAIL: --sync should repair the helper" >&2; exit 1; }

# 7) a further vendored set nobody declared: identical bytes in two skills -> must FAIL.
#    This is what makes forgetting structurally impossible: the table does not have to be
#    remembered, because undeclared duplicate content is discovered.
echo "shared vendored content" > "$tmp/skills/peer-review/references/_new_shared.md"
cp "$tmp/skills/peer-review/references/_new_shared.md" "$tmp/skills/self-review/references/_new_shared.md"
if python3 "$GATE" --root "$tmp" --strict >/dev/null 2>&1; then
  echo "FAIL: an undeclared cross-skill duplicate must exit 1" >&2; exit 1
fi
report="$(python3 "$GATE" --root "$tmp" --strict 2>&1 || true)"
grep -q "undeclared" <<<"$report" \
  || { echo "FAIL: the report must flag it as undeclared vendoring" >&2; echo "$report" >&2; exit 1; }

echo "PASS: vendoring gate — clean tree silent; drifted checklist, drifted probe, drifted code"
echo "      helper and an undeclared vendored pair all fail; --sync repairs."

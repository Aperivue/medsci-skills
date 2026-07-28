#!/usr/bin/env bash
# Deterministic verifier for the figure portal-readiness challenge card.
# Network-free, stdlib-only, NO committed binaries — fixtures are byte files with figure
# extensions (the check reads size + extension, never image content). Also exercises the
# preflight-gate wiring (skip when no figures dir; warn P1 vs halt under --strict).
# Exit 0 = every stage matches expectations.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../figure_portal_readiness_check.py"
GATE="$HERE/../preflight_gate.py"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

[ -f "$DET" ] || { echo "ENV-ERR: figure_portal_readiness_check.py missing" >&2; exit 2; }

figs="$tmp/figures"; mkdir -p "$figs"
python3 - "$figs" <<'PY'
import sys, pathlib
d = pathlib.Path(sys.argv[1])
(d / "fig1.png").write_bytes(b"x" * 3000)   # ~3 KB PNG
(d / "fig2.tiff").write_bytes(b"y" * 1500)  # ~1.5 KB TIFF
(d / "notes.txt").write_text("not a figure")  # must be ignored
PY

# (1) FORMAT: SNAPP accepts tiff/jpeg/eps -> the .png is rejected, the .tiff is not,
#     the .txt is ignored (2 figures scanned).
python3 "$DET" --figures-dir "$figs" --accept tiff --accept jpeg --accept eps \
  --quiet --out "$tmp/fmt.json" && { echo "FAIL: a .png under SNAPP formats did not flag" >&2; exit 1; }
python3 - "$tmp/fmt.json" <<'PY'
import json, os, sys
d = json.load(open(sys.argv[1]))
assert d["scanned"]["figures"] == 2, d["scanned"]           # .txt ignored
kinds = {(os.path.basename(f["path"]), f["kind"]) for f in d["findings"]}
assert ("fig1.png", "FIGURE_FORMAT_REJECTED") in kinds, d["findings"]
assert not any(f["path"].endswith("fig2.tiff") for f in d["findings"]), "an accepted .tiff was flagged"
assert d["detector"] == "figure_portal_readiness_check", "envelope does not self-identify"
print("OK-FORMAT: .png rejected, .tiff accepted, .txt ignored")
PY

# (2) SIZE: a cap below the .png size flags it OVERSIZE.
python3 "$DET" --figures-dir "$figs" --max-mb 0.002 \
  --quiet --out "$tmp/size.json" && { echo "FAIL: a figure over the cap did not flag" >&2; exit 1; }
grep -q '"kind": "FIGURE_OVERSIZE"' "$tmp/size.json" || { echo "FAIL: no FIGURE_OVERSIZE" >&2; cat "$tmp/size.json" >&2; exit 1; }
echo "OK-SIZE: a figure over --max-mb flags FIGURE_OVERSIZE"

# (3) CLEAN: accepting png+tiff under the 25 MB default is silent (no false positive).
python3 "$DET" --figures-dir "$figs" --accept png --accept tiff --quiet --out "$tmp/clean.json"
grep -qE '"kind":' "$tmp/clean.json" && { echo "FAIL: clean fixture flagged (false positive)" >&2; cat "$tmp/clean.json" >&2; exit 1; }
echo "OK-CLEAN: png+tiff under the default cap is silent"

# (4) PREFLIGHT WIRING: warn (P1) by default vs halt under --strict; skip with no figures dir.
if [ -f "$GATE" ]; then
  echo "y" > "$tmp/manuscript.md"
  # figures present, tiny cap + accept tiff -> warn, gate does NOT halt (exit 0)
  python3 "$GATE" --project-root "$tmp" --figure-max-mb 0.002 --figure-accept tiff \
    --quiet --out "$tmp/pf.json" || { echo "FAIL: preflight halted on a P1 warn (should not)" >&2; exit 1; }
  python3 - "$tmp/pf.json" <<'PY'
import json, sys
c = [x for x in json.load(open(sys.argv[1]))["checks"] if x["id"] == "figure_readiness"][0]
assert c["status"] == "warn", c
print("OK-PREFLIGHT-WARN: figure_readiness warns (P1) without halting")
PY
  # under --strict the same becomes a blocker -> gate halts (exit 1)
  if python3 "$GATE" --project-root "$tmp" --figure-max-mb 0.002 --figure-accept tiff \
       --strict --quiet --out "$tmp/pfs.json" >/dev/null 2>&1; then
    echo "FAIL: --strict did not halt on an over-cap figure" >&2; exit 1
  fi
  # no figures dir -> skipped (never an error)
  empty="$tmp/empty"; mkdir -p "$empty"; echo "y" > "$empty/manuscript.md"
  python3 "$GATE" --project-root "$empty" --quiet --out "$empty/pf.json" >/dev/null 2>&1 || true
  python3 - "$empty/pf.json" <<'PY'
import json, sys
c = [x for x in json.load(open(sys.argv[1]))["checks"] if x["id"] == "figure_readiness"][0]
assert c["status"] == "skipped", c
print("OK-PREFLIGHT-SKIP: no figures dir -> skipped, not error")
PY
fi

echo "PASS: figure readiness flags wrong-format + over-cap figures, stays clean on good ones, and wires into the preflight gate (warn P1 / halt --strict / skip when absent)."

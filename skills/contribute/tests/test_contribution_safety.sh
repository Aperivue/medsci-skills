#!/usr/bin/env bash
# Regression test for the /contribute safety gate and the local-change detector.
#
# The gate is the only thing standing between a clinician's laptop and a public commit. The
# positives are the things that must never be published: a patient identifier, a national ID, an
# IRB number, a manuscript under review, a colleague's name, a home directory, a credential.
#
# The negatives matter just as much. A contribution is a journal profile or a checklist fix, and
# it is full of ordinary clinical prose — "STROBE", "the corresponding author", "a tertiary-care
# hospital", "2,500 words". A gate that fires on those is a gate people route around, and the
# first thing they route around it with is the diff they never read.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
S="$REPO_ROOT/skills/contribute/scripts/check_contribution_safety.py"
D="$REPO_ROOT/skills/contribute/scripts/find_local_changes.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-56s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-56s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

# --- what must NEVER leave a clinician's machine ---------------------------------------------
cat > "$TMP/leaky.md" <<'MD'
# Notes while adapting this skill

The pipeline failed on patient MRN 4471903 during the review.
Subject 880101-1234567 was excluded after chart review.
Approved under IRB 2024-0451 at Severance Hospital.
I was reviewing EURE-D-26-00203 when this happened.
Prof. Kim Namkuk suggested the change; reach me at yj.nam@hospital.or.kr.
Output was written to /Users/yoojinnam/manuscripts/draft.docx.
MD

# --- an ordinary, entirely publishable contribution -------------------------------------------
cat > "$TMP/clean.md" <<'MD'
# Korean Journal of Radiology — profile

- Body word limit: 3,000 words (excluding references)
- Abstract: structured, 300 words (Objective / Materials and Methods / Results / Conclusion)
- References: Vancouver, first three authors then et al.
- AI policy: generative AI may not be listed as an author; use must be disclosed in the Methods.
- Reporting: STROBE for observational work; STARD for diagnostic accuracy.

Approved by the institutional review board of a tertiary-care hospital; the corresponding
author confirmed the word limit against the journal's public author guidelines in 2026.
Figures were exported at 600 dpi and the study enrolled 1,284 participants.
MD

# 1) every category of identifier is caught
python3 "$S" --text "$TMP/leaky.md" --out "$TMP/leaky.json" --quiet > /dev/null 2>&1
ck "a leaky file is blocked" 1 "$?"

python3 - "$TMP/leaky.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
v = {f["verdict"] for f in r["findings"]}
for must in ("PHI_SUSPECTED", "IDENTITY", "INSTITUTION", "APPROVAL_ID", "MANUSCRIPT_ID", "LOCAL_PATH"):
    assert must in v, f"{must} not caught: {sorted(v)}"
assert r["blockers"] >= 1, "patient identifiers must be blockers"
assert r["safe_to_send"] is False
# every finding tells the author what to DO — a verdict with no remedy is noise
assert all(f["advice"] for f in r["findings"])
PY
ck "MRN, national ID, IRB, manuscript ID, name, path all caught" 0 "$?"

# 2) THE FALSE-POSITIVE GUARD: an ordinary journal profile must sail through
python3 "$S" --text "$TMP/clean.md" --quiet > /dev/null 2>&1
ck "an ordinary journal profile is not flagged" 0 "$?"

# 2b) FAIL-CLOSED. Every other detector in this repo is advisory unless --strict. This one is
# the reverse, deliberately: a tool that returns success while printing a hospital name will
# eventually be trusted to have said nothing.
python3 "$S" --text "$TMP/leaky.md" --quiet > /dev/null 2>&1
ck "a finding fails by DEFAULT (no --strict needed)" 1 "$?"

# ...and --warn-only cannot wave through patient data.
python3 "$S" --text "$TMP/phi_only.md" --warn-only --quiet > /dev/null 2>&1
ck "--warn-only still cannot pass patient data" 1 "$?"

# an ordinary institution-free profile is still clean under --warn-only (no blanket failure)
python3 "$S" --text "$TMP/clean.md" --warn-only --quiet > /dev/null 2>&1
ck "--warn-only does not invent findings" 0 "$?"

# 3) patient-level data is a BLOCKER, not a warning — it cannot be waved through
cat > "$TMP/phi_only.md" <<'MD'
The case was patient ID 30298471, imaged on the scanner.
MD
python3 "$S" --text "$TMP/phi_only.md" --out "$TMP/phi.json" --quiet > /dev/null 2>&1
ck "patient data alone blocks (no --strict needed)" 1 "$?"
python3 - "$TMP/phi.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
assert r["blockers"] >= 1
assert any(f["verdict"] == "PHI_SUSPECTED" and f["severity"] == "blocker" for f in r["findings"])
PY
ck "patient data is severity=blocker" 0 "$?"

# 4) a credential is a blocker too, and is never echoed in full
cat > "$TMP/secret.md" <<'MD'
export GH_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz0123456789
MD
python3 "$S" --text "$TMP/secret.md" --out "$TMP/sec.json" --quiet > /dev/null 2>&1
ck "a credential blocks" 1 "$?"
python3 - "$TMP/sec.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
f = next(x for x in r["findings"] if x["verdict"] == "SECRET")
assert f["severity"] == "blocker"
assert "abcdefghijklmnopqrstuvwxyz" not in f["match"], "the scanner must not reprint the whole token"
PY
ck "the credential is truncated in the report" 0 "$?"

# 5) the local-change detector: an added file is found, and named as ADDED
FAKE_HOME="$TMP/home"
mkdir -p "$FAKE_HOME/.claude/skills/find-journal/references" \
         "$FAKE_HOME/.medsci-skills/targets/claude"
printf 'original content\n' > "$FAKE_HOME/.claude/skills/find-journal/SKILL.md"
printf '# my journal\nWord limit: 3000\n' > "$FAKE_HOME/.claude/skills/find-journal/references/my_journal.md"
python3 - "$FAKE_HOME" <<'PY'
import hashlib, json, sys
from pathlib import Path
home = Path(sys.argv[1])
skill = home / ".claude/skills/find-journal"
inv = {}
# record ONLY SKILL.md as shipped -> the reference file is a local addition
b = (skill / "SKILL.md").read_bytes()
inv["SKILL.md"] = hashlib.sha256(b).hexdigest()
mf = home / ".medsci-skills/targets/claude/installed-manifest.json"
mf.write_text(json.dumps({"schema_version": 1, "target": "claude",
                          "skills": {"find-journal": {"inventory": inv}}}, indent=2))
PY
HOME="$FAKE_HOME" MEDSCI_HOME="$FAKE_HOME/.medsci-skills" python3 "$D" --target claude --json > "$TMP/c1.json" 2>/dev/null
python3 - "$TMP/c1.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
adds = [c for c in r["changes"] if c["kind"] == "added"]
assert len(adds) == 1, r["changes"]
assert adds[0]["path"] == "references/my_journal.md", adds[0]
assert r["summary"]["modified"] == 0
PY
ck "a locally added file is detected as 'added'" 0 "$?"

# 6) ...and an edit to a shipped file is detected as MODIFIED
printf 'original content\nplus my fix\n' > "$FAKE_HOME/.claude/skills/find-journal/SKILL.md"
HOME="$FAKE_HOME" MEDSCI_HOME="$FAKE_HOME/.medsci-skills" python3 "$D" --target claude --json > "$TMP/c2.json" 2>/dev/null
python3 - "$TMP/c2.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
mods = [c for c in r["changes"] if c["kind"] == "modified"]
assert len(mods) == 1 and mods[0]["path"] == "SKILL.md", r["changes"]
PY
ck "an edit to a shipped file is detected as 'modified'" 0 "$?"

# 7) an untouched install reports nothing (no false "you changed something")
printf 'original content\n' > "$FAKE_HOME/.claude/skills/find-journal/SKILL.md"
rm "$FAKE_HOME/.claude/skills/find-journal/references/my_journal.md"
HOME="$FAKE_HOME" MEDSCI_HOME="$FAKE_HOME/.medsci-skills" python3 "$D" --target claude --json > "$TMP/c3.json" 2>/dev/null
python3 - "$TMP/c3.json" <<'PY'
import json, sys
assert json.load(open(sys.argv[1]))["n_changes"] == 0
PY
ck "an untouched install reports no changes" 0 "$?"

# 8) the JSON envelope names the detector (repo-wide artifact contract)
python3 - "$TMP/leaky.json" <<'PY'
import json, sys
assert json.load(open(sys.argv[1]))["detector"] == "check_contribution_safety"
PY
ck "JSON envelope self-identifies" 0 "$?"

echo "----"
echo "test_contribution_safety: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Regression test for skills/manage-refs/scripts/check_bib_title_markup.py.
#
# The positives are the two titles that actually shipped into a rendered reference list as
# garbage. The negatives are the reason the fusion rule is narrow: `mRNA`, `hTERT`, `nnU-Net`
# and `1,2-dichloroethane` are ordinary scientific typography, and a gate that cries wolf on
# them is worse than no gate.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
V="$REPO_ROOT/skills/manage-refs/scripts/check_bib_title_markup.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-52s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-52s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

# --- corrupted: raw CrossRef markup, BBT-escaped markup, and tag-strip fusion ---
cat > "$TMP/dirty.bib" <<'BIB'
@article{louis2021who,
  title = {The 2021 <scp>WHO</scp> Classification of Tumors of the Central Nervous System},
  author = {Louis, David N.},
  year = {2021},
}
@article{brat2021escaped,
  title = {The 2021 {$<$}scp{$>$}WHO{$<$}/scp{$>$} Classification: A Summary},
  author = {Brat, Daniel J.},
  year = {2021},
}
@article{eckel2015glioma,
  title = {Glioma Groups Based on 1p/19q,IDH, andTERTPromoter Mutations in Tumors},
  author = {{Eckel-Passow}, Jeanette E.},
  year = {2015},
}
BIB

# --- clean: ordinary scientific typography that must NOT fire ---
cat > "$TMP/clean.bib" <<'BIB'
@article{isensee2021nnunet,
  title = {nnU-Net: a self-configuring method for deep learning-based biomedical image segmentation},
  author = {Isensee, Fabian},
  year = {2021},
}
@article{sahin2021mrna,
  title = {mRNA-based COVID-19 vaccines and hTERT expression in 1,2-dichloroethane exposure},
  author = {Sahin, Ugur},
  year = {2021},
}
@article{plain2020title,
  title = {Radiomics and machine learning for glioma grading, staging, and outcome prediction},
  author = {Smith, John},
  year = {2020},
}
BIB

# 1) corrupted titles fail under --strict
python3 "$V" --bib "$TMP/dirty.bib" --strict --quiet > /dev/null 2>&1
ck "markup + fusion titles fail (--strict)" 1 "$?"

# 2) clean titles pass
python3 "$V" --bib "$TMP/clean.bib" --strict --quiet > /dev/null 2>&1
ck "clean scientific typography passes (--strict)" 0 "$?"

# 3) each corruption shape is reported, on the right key
python3 "$V" --bib "$TMP/dirty.bib" --out "$TMP/d.json" --quiet > /dev/null 2>&1
python3 - "$TMP/d.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
by_key = {}
for f in r["findings"]:
    by_key.setdefault(f["key"], set()).add(f["verdict"])
assert "TITLE_MARKUP" in by_key.get("louis2021who", set()), "raw <scp> not caught"
assert "TITLE_MARKUP" in by_key.get("brat2021escaped", set()), "BBT-escaped {$<$} not caught"
assert "TITLE_FUSION" in by_key.get("eckel2015glioma", set()), "andTERT / ,IDH fusion not caught"
assert r["titles_checked"] == 3, r["titles_checked"]
assert r["submission_safe"] is False
PY
ck "every corruption shape reported on its own key" 0 "$?"

# 4) the false-positive guards, asserted individually — this is what makes the gate usable
python3 -B - "$V" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("m", sys.argv[1])
m = importlib.util.module_from_spec(spec); sys.modules["m"] = m; spec.loader.exec_module(m)
clean = [
    "nnU-Net: a self-configuring method",
    "mRNA-based vaccines",
    "hTERT promoter mutations",
    "Exposure to 1,2-dichloroethane and 10,000 participants",
    "pH-sensitive nanoparticles for siRNA delivery",
    "Comparison of CT and MRI in glioma",
]
for t in clean:
    f = m.findings_for("k", t)
    assert not f, f"false positive on {t!r}: {[x['verdict'] for x in f]}"
dirty = ["Based on 1p/19q,IDH, andTERT Promoter", "The 2021 <scp>WHO</scp> Classification"]
for t in dirty:
    assert m.findings_for("k", t), f"missed corruption in {t!r}"
PY
ck "no false positives on mRNA / hTERT / nnU-Net / 1,2-" 0 "$?"

# 5) corruption is reported but tolerated without --strict
python3 "$V" --bib "$TMP/dirty.bib" --quiet > /dev/null 2>&1
ck "corruption tolerated without --strict" 0 "$?"

# 6) the JSON envelope names the detector (repo-wide artifact contract)
python3 - "$TMP/d.json" <<'PY'
import json, sys
assert json.load(open(sys.argv[1]))["detector"] == "check_bib_title_markup"
PY
ck "JSON envelope self-identifies" 0 "$?"

echo "----"
echo "test_bib_title_markup: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Regression test for two precision defects in verify_refs.py's author cross-check.
#
# Both were found on the same clean bibliography, and they fail in opposite directions:
#
#   1. FALSE ALARM. A publisher-supplied Unicode hyphen (U+2010) in a hyphenated surname was
#      DELETED by the normalizer's final `[^a-z\s-]` filter rather than folded, so CrossRef's
#      `Foltyn‐Dumitru` normalized to `foltyndumitru` while the identical ASCII bib entry gave
#      `foltyn-dumitru` — and the audit fired MISMATCH, its loudest verdict, on a correct entry.
#
#   2. FALSE PASS, which is worse. Better BibTeX brace-protects a hyphenated or particle surname
#      (`{Eckel-Passow}, Jeanette E.`) so BibTeX will not re-split it. The corporate-author
#      heuristic treated any brace as an organization and SKIPPED the author cross-check — the
#      one thing this tool exists to do — without the user noticing.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
V="$REPO_ROOT/skills/verify-refs/scripts/verify_refs.py"

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

# 1) Unicode dash variants fold to ASCII — no false MISMATCH on a hyphenated surname
python3 -B - "$V" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("vr", sys.argv[1])
m = importlib.util.module_from_spec(spec); sys.modules["vr"] = m; spec.loader.exec_module(m)
n = m._normalize_surname
# every Unicode dash the publishers actually emit
for dash in ("‐", "‑", "‒", "–", "—", "−"):
    assert n(f"Foltyn{dash}Dumitru") == n("Foltyn-Dumitru"), f"U+{ord(dash):04X} not folded"
# the accent coverage that was already there must not regress
assert n("Çolakoğlu") == n("Colakoglu")
assert n("Müller") == n("Muller")
PY
ck "Unicode dashes fold to ASCII (no false MISMATCH)" 0 "$?"

# 2) a genuinely different surname must still MISMATCH — the fix must not blunt the check
python3 -B - "$V" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("vr", sys.argv[1])
m = importlib.util.module_from_spec(spec); sys.modules["vr"] = m; spec.loader.exec_module(m)
n = m._normalize_surname
assert n("Foltyn-Dumitru") != n("Foltyn-Dumitrescu")
assert n("Eckel-Passow") != n("Eckel-Passov")
assert n("Smith") != n("Smyth")
PY
ck "a genuinely different surname still mismatches" 0 "$?"

# 3) BBT brace-protected surnames are PEOPLE — the author check must run, not be skipped
python3 -B - "$V" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("vr", sys.argv[1])
m = importlib.util.module_from_spec(spec); sys.modules["vr"] = m; spec.loader.exec_module(m)
c = m.is_corporate_author_field
assert c("{Eckel-Passow}, Jeanette E. and {Ramos-Fresnedo}, Andres") is False
assert c("{von Deimling}, Andreas") is False
assert c("{Ramos-Fresnedo}, Andres") is False
PY
ck "BBT brace-protected surname is not 'corporate'" 0 "$?"

# 4) real collective authors are STILL skipped — the fix must not open a hole
python3 -B - "$V" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("vr", sys.argv[1])
m = importlib.util.module_from_spec(spec); sys.modules["vr"] = m; spec.loader.exec_module(m)
c = m.is_corporate_author_field
assert c("{{KDIGO Working Group}}") is True
assert c("{{Alzheimer's Disease Neuroimaging Initiative}}") is True
assert c("{{The CRASH-3 Collaborators}}") is True
assert c("{{ADNI}}") is True          # lone braced blob, no name structure -> conservative skip
assert c("Smith, John and Doe, Jane") is False
PY
ck "real collective authors are still skipped" 0 "$?"

echo "----"
echo "test_author_normalization: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

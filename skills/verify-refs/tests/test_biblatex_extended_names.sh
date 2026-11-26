#!/usr/bin/env bash
# Regression test: biblatex extended name format in the author field.
#
# Better BibTeX writes every surname with a particle (de, von, van, ó ...) as
#   family=Elm, given=Erik, prefix=von, useprefix=true
# The plain "Last, First" split read "family=Elm" as the surname, so a correct reference
# (DOI resolves, all authors right) was reported as an author MISMATCH, and render_pandoc.sh's
# gate stopped the build. Five of 33 references in one real bibliography were hit.
#
# The fix reads the extended form and keeps the particle in front of the family ("von Elm"),
# which is how a plain BibTeX name with the particle parses and how CrossRef/PubMed give it.
# A genuinely different surname must still differ.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
V="$REPO_ROOT/skills/verify-refs/scripts/verify_refs.py"

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-60s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-60s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

# 1) extended names parse to "particle family", mixed with plain names
python3 -B - "$V" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("vr", sys.argv[1])
m = importlib.util.module_from_spec(spec); sys.modules["vr"] = m; spec.loader.exec_module(m)
p = m.parse_bib_authors
assert p("family=Elm, given=Erik, prefix=von, useprefix=true and Altman, Douglas G.") == ["von Elm", "Altman"]
assert p("Lee, Jung Hwan and family=Hartaigh, given=Bríain, prefix=ó, useprefix=true and Rizvi, Asim") == ["Lee", "ó Hartaigh", "Rizvi"]
assert p("family=Ferranti, given=Sarah, prefix=de, useprefix=false") == ["de Ferranti"]
assert p("family={Smith}, given={John}") == ["Smith"]
PY
ck "extended names parse to particle + family" 0 "$?"

# 2) the first-author guess reads the same form
python3 -B - "$V" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("vr", sys.argv[1])
m = importlib.util.module_from_spec(spec); sys.modules["vr"] = m; spec.loader.exec_module(m)
assert m.parse_first_author("family=Elm, given=Erik, prefix=von, useprefix=true and Altman, D") == "von Elm"
PY
ck "first-author guess reads the extended form" 0 "$?"

# 3) plain names are unchanged, an extended name is not 'corporate', and a different surname still differs
python3 -B - "$V" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("vr", sys.argv[1])
m = importlib.util.module_from_spec(spec); sys.modules["vr"] = m; spec.loader.exec_module(m)
assert m.parse_bib_authors("Smith, John and Doe, Jane") == ["Smith", "Doe"]
assert m.parse_bib_authors("John Smith and Jane Doe") == ["Smith", "Doe"]
assert m.is_corporate_author_field("family=Elm, given=Erik, prefix=von, useprefix=true") is False
n = m._normalize_surname
assert n(m.parse_bib_authors("family=Elm, given=Erik, prefix=von")[0]) == n("von Elm")
assert n(m.parse_bib_authors("family=Ehm, given=Erik, prefix=von")[0]) != n("von Elm")
PY
ck "plain names unchanged; a different surname still differs" 0 "$?"

echo
echo "  ${pass} passed, ${fail} failed"
[ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Regression test: the audit's `source` field must never carry an absolute path.
#
# `qc/reference_audit.json` is a committed artifact that travels with the manuscript, and its
# `source` was written as `str(source)` — the caller resolves the input, so on a real run that is
# an absolute path. On a maintainer's machine an absolute path contains the home directory, and
# therefore a username. The public-surface PII gate caught it three times between 2026-07-31 and
# 2026-08-01: the field is rewritten on every render, so hand-scrubbing lost twice.
#
# The fix is `portable_source()`. This test pins BOTH directions: the path is relative (so the
# audit is portable and PII-free) AND it still identifies the file (so the field keeps its
# meaning). The last two cases are negative controls — a name that merely *looks* like a home
# directory, and a source outside the project, which must degrade to a bare filename rather than
# leaking the way there.
#
# Network-free: nothing here calls PubMed, CrossRef or OpenAlex.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
V="$REPO_ROOT/skills/verify-refs/scripts/verify_refs.py"

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-52s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-52s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

out="$(python3 - "$V" <<'PY'
import importlib.util, json, os, sys, tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("vr", sys.argv[1])
m = importlib.util.module_from_spec(spec)
sys.modules["vr"] = m
spec.loader.exec_module(m)

results = {}
with tempfile.TemporaryDirectory() as td:
    td = Path(td).resolve()
    # A directory tree shaped like the real thing: a home, a project inside it, a bib inside that.
    home = td / "Users" / "someone"
    project = home / "workspace" / "05_Paper"
    (project / "manuscript").mkdir(parents=True)
    bib = project / "manuscript" / "refs.bib"
    bib.write_text("@article{k,\n  title = {A title}\n}\n", encoding="utf-8")

    results["inside_project"] = m.portable_source(bib, project)

    # Source outside the project entirely — a shared library .bib two levels up.
    shared = home / "shared" / "library.bib"
    shared.parent.mkdir(parents=True)
    shared.write_text("", encoding="utf-8")
    results["outside_project"] = m.portable_source(shared, project)

    # The end-to-end path: write_outputs is what actually produces the committed file.
    m.write_outputs([], project, bib, [])
    audit = json.loads((project / "qc" / "reference_audit.json").read_text(encoding="utf-8"))
    results["written"] = audit["source"]
    results["written_is_absolute"] = str(Path(audit["source"]).is_absolute()).lower()
    # The whole point: the serialized artifact must not contain the tree above the project.
    blob = (project / "qc" / "reference_audit.json").read_text(encoding="utf-8")
    results["home_leaked"] = str("someone" in blob).lower()

    # Relative-to-CWD fallback: a source under the CWD but outside --project-root.
    cwd_before = Path.cwd()
    try:
        os.chdir(home)
        results["under_cwd"] = m.portable_source(shared, project)
    finally:
        os.chdir(cwd_before)

print(json.dumps(results))
PY
)"

get() { python3 -c "import json,sys; print(json.loads(sys.argv[1])[sys.argv[2]])" "$out" "$1"; }

echo "==== the source is relative, and still names the file ===="
ck "source inside the project root"        "manuscript/refs.bib"  "$(get inside_project)"
ck "as written into reference_audit.json"  "manuscript/refs.bib"  "$(get written)"

echo "==== NEGATIVE CONTROLS — nothing above the project may appear ===="
ck "written path is absolute"              "false"                "$(get written_is_absolute)"
ck "home directory name in the artifact"   "false"                "$(get home_leaked)"

echo "==== a source outside the project degrades to a name, not a route ===="
ck "outside project, no CWD match"         "library.bib"          "$(get outside_project)"
ck "outside project, but under the CWD"    "shared/library.bib"   "$(get under_cwd)"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || exit 1
echo "OK: reference_audit.json names its source without naming the machine."

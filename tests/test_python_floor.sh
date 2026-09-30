#!/usr/bin/env bash
# Self-test for scripts/check_python_floor.py.
#
# The gate reported "all 176 shipped scripts parse on Python 3.9" while seven user-facing scripts
# crashed on import there: `def f(x: str | None)` PARSES on 3.9, but the annotation is evaluated
# when the `def` runs, and `type | None` is a TypeError before 3.10. Two of the seven were also
# outside the gate's glob (a skill-root CLI and a `references/` helper). Each case below builds a
# synthetic repository and restores one of those defects; the gate must FAIL on every one and stay
# silent on the code that is safe, so nobody is tempted to switch it off.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GATE="$ROOT/scripts/check_python_floor.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %s\n' "$1"; else printf '  FAIL  %s (want %s got %s)\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }

# case <name> <relative path> <python source> : a fresh repo holding one clean installer plus the file
case_repo() {
  local repo="$TMP/$1"
  mkdir -p "$repo/installers" "$repo/$(dirname "$2")"
  printf 'print("installer")\n' >"$repo/installers/install.py"
  printf '%s\n' "$3" >"$repo/$2"
  echo "$repo"
}
gate() { python3 "$GATE" --strict --root "$1" >"$TMP/out" 2>&1; echo $?; }

# --- must FAIL -----------------------------------------------------------------------------------
r="$(case_repo sig 'skills/demo/scripts/tool.py' 'def f(x: str | None = None) -> int | None:
    return None')"
ck "signature union without the future import fails" 1 "$(gate "$r")"
ck "  ...and names the file and line" yes "$(grep -q 'skills/demo/scripts/tool.py:1' "$TMP/out" && echo yes || echo no)"

r="$(case_repo skillroot 'skills/demo/demo.py' 'def f(x: dict | None): pass')"
ck "a skill-root CLI (deidentify.py's layout) is scanned" 1 "$(gate "$r")"

r="$(case_repo references 'skills/demo/references/helper.py' 'def f() -> list[str] | None: pass')"
ck "a references/ helper (snowball.py's layout) is scanned" 1 "$(gate "$r")"

r="$(case_repo classvar 'skills/demo/scripts/model.py' 'class Row:
    note: str | None = None')"
ck "class-level variable annotation fails" 1 "$(gate "$r")"

r="$(case_repo alias 'skills/demo/scripts/alias.py' 'from __future__ import annotations
MaybeText = str | None')"
ck "runtime alias fails even with the future import" 1 "$(gate "$r")"

r="$(case_repo match 'skills/demo/scripts/syntax.py' 'match 1:
    case _: pass')"
ck "a 3.10 syntax error still fails" 1 "$(gate "$r")"

# --- must PASS -----------------------------------------------------------------------------------
r="$(case_repo lazy 'skills/demo/scripts/tool.py' 'from __future__ import annotations
def f(x: str | None = None) -> int | None:
    return None')"
ck "the same signature with the future import passes" 0 "$(gate "$r")"

r="$(case_repo safe 'skills/demo/scripts/safe.py' 'import re
from typing import Optional
FLAGS = re.I | re.M
def f(x: "str | None", y: Optional[int] = None):
    local: int | None = None
    return 3 | 4')"
ck "string annotations, local annotations and bitwise OR pass" 0 "$(gate "$r")"

r="$(case_repo tests 'skills/demo/tests/test_tool.py' 'def f(x: str | None): pass')"
ck "test directories are not shipped-to-user code" 0 "$(gate "$r")"

r="$(case_repo newfloor 'skills/demo/scripts/tool.py' 'def f(x: str | None): pass')"
python3 "$GATE" --strict --root "$r" --floor 3.10 >/dev/null 2>&1
ck "a 3.10 floor accepts PEP 604" 0 "$?"

echo "test_python_floor: $fail failure(s)"
[ "$fail" -eq 0 ]

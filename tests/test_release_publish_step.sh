#!/usr/bin/env bash
# Regression test for the release job's publish step.
#
# A version tag can only be pushed once. So when the v5.23.0 run failed at
# `gh release create` — the Release object for the tag already existed, and `create` errors rather
# than updates — the job died there, BEFORE the npm publish step that follows it. One error produced
# both live symptoms: the GitHub Release carried zero assets (so the ZIP links README sends
# non-programmers to, `releases/latest/download/...`, 404'd) and npm sat a version behind. There was
# no way to retry, because the tag was already pushed.
#
# This test executes the ACTUAL `run:` block from .github/workflows/release.yml — extracted from the
# shipped YAML, not a copy of it — against a stubbed `gh`, so it cannot drift from what CI runs.
#
# Three properties, the third being the one that turns a silent bad outcome into a red build:
#   1. Release absent  -> `gh release create` with the ZIPs.
#   2. Release present -> `gh release edit` + `gh release upload --clobber` (no failure).
#   3. Either path, but the release ends with fewer than 2 assets -> the step FAILS.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d -t release_publish_test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

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

# --- extract the step's run block from the shipped workflow -------------------------------------
python3 - "$REPO_ROOT/.github/workflows/release.yml" "$WORK/step.sh" <<'PY'
import sys, yaml
wf = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
steps = wf["jobs"]["release"]["steps"]
hits = [s for s in steps if "Create GitHub Release" in (s.get("name") or "")]
if len(hits) != 1:
    sys.exit(f"expected exactly one publish step, found {len(hits)}")
run = hits[0].get("run")
if not run:
    sys.exit("publish step has no run: block")
open(sys.argv[2], "w", encoding="utf-8").write(run)
PY
[ -s "$WORK/step.sh" ] || { echo "FAIL: could not extract the run block" >&2; exit 1; }

# --- stub gh ------------------------------------------------------------------------------------
# RELEASE_EXISTS controls whether `gh release view <tag>` succeeds; ASSET_COUNT is what the final
# assertion reads back. Every invocation is appended to $WORK/calls so we can assert on the verbs.
mkdir -p "$WORK/bin"
cat > "$WORK/bin/gh" <<'STUB'
#!/usr/bin/env bash
echo "$*" >> "$CALLS"
case "$1 $2" in
  "release view")
    if [[ "$*" == *"--json assets"* ]]; then echo "${ASSET_COUNT}"; exit 0; fi
    [ "${RELEASE_EXISTS}" = "1" ] && exit 0 || exit 1 ;;
  "release create")
    # Faithful to the real gh: creating a Release for a tag that already has one is an ERROR.
    # This is the exact failure that killed the v5.23.0 job. A stub that returned 0 here would
    # make the regression untestable — the old code would look fine.
    if [ "${RELEASE_EXISTS}" = "1" ]; then
      echo "HTTP 422: Validation Failed (a release with the same tag name already exists)" >&2
      exit 1
    fi
    exit 0 ;;
  "release edit"|"release upload") exit 0 ;;
  *) exit 0 ;;
esac
STUB
chmod +x "$WORK/bin/gh"

run_step() {  # run_step <exists> <asset_count> ; echoes exit code, writes $WORK/calls
  local exists="$1" assets="$2"
  : > "$WORK/calls"
  mkdir -p "$WORK/dist"
  : > "$WORK/dist/medsci-skills-classroom-macos.zip"
  : > "$WORK/dist/medsci-skills-classroom-windows.zip"
  # Deliberately do NOT create /tmp/release_notes.md: the stub never reads it, and creating it made
  # check_test_wiring crash by pulling an absolute path out of the workflow (fixed separately).
  ( cd "$WORK" \
    && PATH="$WORK/bin:$PATH" CALLS="$WORK/calls" RELEASE_EXISTS="$exists" ASSET_COUNT="$assets" \
       RELEASE_TAG="v9.9.9" bash "$WORK/step.sh" >"$WORK/out" 2>&1 )
  echo $?
}

echo "==== 1. no Release object yet: create ===="
rc="$(run_step 0 2)"
ck "exit 0" 0 "$rc"
ck "used 'release create'" yes "$(grep -q '^release create' "$WORK/calls" && echo yes || echo no)"

echo "==== 2. Release already exists (the v5.23.0 case): update, do not die ===="
rc="$(run_step 1 2)"
ck "exit 0 instead of failing" 0 "$rc"
ck "used 'release upload' with --clobber" yes \
   "$(grep '^release upload' "$WORK/calls" | grep -q -- '--clobber' && echo yes || echo no)"
ck "did NOT call 'release create'" yes \
   "$(grep -q '^release create' "$WORK/calls" && echo no || echo yes)"

echo "==== 3. NEGATIVE CONTROL — a release that ends with no assets must FAIL ===="
rc="$(run_step 1 0)"
ck "exit 1 when 0 assets attached" 1 "$rc"
rc="$(run_step 0 1)"
ck "exit 1 when only 1 of 2 attached" 1 "$rc"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || { echo "--- last step output ---"; cat "$WORK/out"; exit 1; }
echo "OK: publish step is create-or-update, and a release with missing assets is a red build."

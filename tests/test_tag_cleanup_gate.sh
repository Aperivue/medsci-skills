#!/usr/bin/env bash
# Regression test for scripts/tag_cleanup_gate.sh (DI-8 draft-tag submission gate).
#
# The defect this exists for: the gate has two scan backends and they read DIFFERENT file
# sets. ripgrep honours .gitignore/.ignore and skips dotfiles; the `grep -r` fallback reads
# both. A submission package carrying a live TODO inside an ignored build/ directory, or a
# FIXME in a hidden draft, was therefore invisible to the rg backend — and the gate printed
#
#     PASS: 0 hits. Submission package is tag-clean.
#
# and exited 0, while the same package on a machine without ripgrep correctly exited 1. The
# verdict depended on which tool happened to be installed, and the silent side was the one
# that passed. A second, quieter overclaim: the PASS sentence spoke for "the submission
# package" while the scan covers only whichever scaffold directories exist.
#
# So the invariant under test is not "the gate runs" but PARITY: both backends must reach the
# same verdict on the same tree, and the passing sentence must name what it actually read.
#
# Fixtures are built at runtime, so this file ships no live draft-stage tags of its own.
# Stdlib/POSIX tools only.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATE="$HERE/../scripts/tag_cleanup_gate.sh"
TMP="$(mktemp -d -t di8gate_XXXX)"
trap 'rm -rf "$TMP"' EXIT

fail=0
skipped=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}

[[ -f "$GATE" ]] || { echo "ENV-ERR: $GATE missing" >&2; exit 2; }

# A PATH with every directory that provides ripgrep removed, so the gate takes its grep
# branch. Filtering the real PATH (rather than substituting a hand-built minimal one) keeps
# every other tool the script may reach for available.
strip_rg_from_path() {
    local out="" d
    local -a dirs
    IFS=':' read -ra dirs <<< "$PATH"
    for d in "${dirs[@]}"; do
        [[ -n "$d" && -x "$d/rg" ]] && continue
        out="${out:+$out:}$d"
    done
    printf '%s' "$out"
}
NORG_PATH="$(strip_rg_from_path)"
HAVE_RG=0
command -v rg >/dev/null 2>&1 && HAVE_RG=1

# Run the gate on $2 under backend $1 ("rg" | "grep"); capture output and exit code.
GATE_OUT=""; GATE_RC=0
run_gate() {
    local backend="$1" root="$2"
    if [[ "$backend" == "grep" ]]; then
        GATE_OUT="$(PATH="$NORG_PATH" bash "$GATE" "$root" 2>&1)"; GATE_RC=$?
    else
        GATE_OUT="$(bash "$GATE" "$root" 2>&1)"; GATE_RC=$?
    fi
}
rc_is()      { test "$GATE_RC" -eq "$1"; }
out_has()    { printf '%s' "$GATE_OUT" | grep -q -- "$1"; }
out_lacks()  { ! printf '%s' "$GATE_OUT" | grep -q -- "$1"; }

# --- fixture: a package whose only live tags sit where rg used to not look -----------------
TAGGED="$TMP/tagged"
mkdir -p "$TAGGED/7_Manuscript/build"
printf 'build/\n' > "$TAGGED/.gitignore"
# Split the markers so this test file itself carries no live draft tag.
printf 'A hidden working note with FIX%s.\n' "ME" > "$TAGGED/7_Manuscript/.draft_note.md"
printf 'Generated prose with TO%s left in it.\n' "DO" > "$TAGGED/7_Manuscript/build/generated.md"
printf 'Clean prose, nothing to remove.\n' > "$TAGGED/7_Manuscript/main.md"
git init -q "$TAGGED" 2>/dev/null && GIT_OK=1 || GIT_OK=0

# (1) grep backend — always exercisable, and the branch that was already correct.
run_gate grep "$TAGGED"
check "grep backend: exit 1 on a package with hidden/ignored draft tags" rc_is 1
check "grep backend: names the hidden file"    out_has ".draft_note.md"
GREP_RC="$GATE_RC"

# (2) rg backend — the regressed branch. Without --no-ignore --hidden this returned exit 0
#     and the tag-clean sentence.
if [[ "$HAVE_RG" -eq 1 ]]; then
    run_gate rg "$TAGGED"
    check "rg backend: exit 1 on the same package (was 0 before --no-ignore --hidden)" rc_is 1
    check "rg backend: names the hidden file"   out_has ".draft_note.md"
    check "rg backend: never claims tag-clean here" out_lacks "PASS"
    # (3) parity — the property that makes the gate toolchain-independent.
    check "parity: both backends reach the same verdict" test "$GATE_RC" -eq "$GREP_RC"
    # (4) the gitignored hit, when git is available to make .gitignore meaningful to rg.
    if [[ "$GIT_OK" -eq 1 ]]; then
        check "rg backend: reads a gitignored file inside the package" out_has "generated.md"
    else
        printf '  SKIP  gitignored-file case (git unavailable; .gitignore inert for rg)\n'
        skipped=$((skipped+1))
    fi
else
    printf '  SKIP  rg backend NOT exercised (ripgrep not installed on this machine)\n'
    printf '        The regressed branch is unverified here; CI runners carry ripgrep.\n'
    skipped=$((skipped+1))
fi

# --- fixture: clean package, only some scaffold dirs present ------------------------------
CLEAN="$TMP/clean"
mkdir -p "$CLEAN/7_Manuscript"
printf 'Clean prose only.\n' > "$CLEAN/7_Manuscript/main.md"

run_gate grep "$CLEAN"
check "clean package: exit 0"                       rc_is 0
check "PASS names the directory actually scanned"   out_has "0 hits in: 7_Manuscript"
check "PASS discloses the scaffold dirs it did NOT scan" out_has "NOT scanned"
check "PASS no longer claims the whole package is tag-clean" out_lacks "Submission package is tag-clean"

# --- no scaffold dirs at all -> exit 2, not a pass ----------------------------------------
EMPTY="$TMP/empty"; mkdir -p "$EMPTY/some_other_layout"
run_gate grep "$EMPTY"
check "no scaffold dirs: exit 2 (not a silent pass)" rc_is 2

# --- opt-out and exclusion behaviour must survive the widened scan -------------------------
OPTOUT="$TMP/optout"
mkdir -p "$OPTOUT/7_Manuscript"
printf 'DI-8:ignore-file\nThis file quotes TO%s as a convention example.\n' "DO" \
    > "$OPTOUT/7_Manuscript/tag_conventions.md"
run_gate grep "$OPTOUT"
check "DI-8:ignore-file opt-out still honoured (grep)" rc_is 0
if [[ "$HAVE_RG" -eq 1 ]]; then
    run_gate rg "$OPTOUT"
    check "DI-8:ignore-file opt-out still honoured (rg)" rc_is 0
fi

EXCL="$TMP/excluded"
mkdir -p "$EXCL/7_Manuscript"
printf 'Reviewer 2 asked us to remove every TO%s marker.\n' "DO" \
    > "$EXCL/7_Manuscript/peer_review_round1.md"
run_gate grep "$EXCL"
check "meta-discussion exclusion glob still honoured (grep)" rc_is 0
if [[ "$HAVE_RG" -eq 1 ]]; then
    run_gate rg "$EXCL"
    check "meta-discussion exclusion glob still honoured (rg)" rc_is 0
fi

echo "fail=$fail skipped=$skipped"
if [[ "$fail" -eq 0 ]]; then
    [[ "$skipped" -eq 0 ]] && echo "ALL PASS" || echo "ALL PASS ($skipped skipped — see SKIP lines)"
else
    echo "FAILURES: $fail"
fi
exit "$fail"

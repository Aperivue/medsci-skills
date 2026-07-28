#!/usr/bin/env bash
# Self-test for scripts/check_hardcoded_locale.py — no skill gets to pick its user's language.
#
# The rule this gate enforces was not missing. It was written down, in prose, inside the very skill
# whose job is to enforce it: /publish-skill lists "Language hardcoding" among the defects to scrub
# before a skill goes public, and prints the replacement sentence. And for months the package shipped
# /humanize saying "Communicate with the user in Korean" to every person on earth who invoked it.
#
# That is the whole thesis in one file: the difference between the rules that held and the one that
# did not was not importance. It was executability.
#
# So this test does not check that the gate passes. It rebuilds the defect and demands the gate FAIL —
# and, just as hard, it demands the gate stay SILENT on the file that already had it right. A gate
# that punishes good work gets switched off, and takes the honest gates with it.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
G="$REPO_ROOT/scripts/check_hardcoded_locale.py"

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-58s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-58s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

FIX="$(mktemp -d)"
trap 'rm -rf "$FIX"' EXIT
mk() { mkdir -p "$FIX/skills/$1"; cat > "$FIX/skills/$1/SKILL.md"; }

# 1) the live repo: nobody picks the user's language
python3 "$G" --strict >/dev/null 2>&1
ck "live repo: no skill chooses its user's language" 0 "$?"

# 2) REGRESSION — the defect exactly as it shipped
mk regressed <<'EOF'
# Regressed skill
## Communication Rules
- Communicate with the user in Korean (matching their working language).
- All manuscript edits are in English.
EOF
python3 "$G" --root "$FIX" --strict >/dev/null 2>&1
ck "REGRESSION: 'communicate with the user in Korean'" 1 "$?"

# ...and it must be the LINE that is named, not merely the file
python3 "$G" --root "$FIX" 2>&1 | grep -q "skills/regressed/SKILL.md:3" \
  && ck "the offending line is named, with its number" 0 0 \
  || ck "the offending line is named, with its number" 0 1

# 3) the softer form, which is the same defect wearing a hedge
rm -rf "$FIX/skills/regressed"
mk hedged <<'EOF'
# Hedged skill
- Conversation with the user may be in Korean.
EOF
python3 "$G" --root "$FIX" --strict >/dev/null 2>&1
ck "REGRESSION: 'conversation with the user may be in Korean'" 1 "$?"

# 4) NEGATIVE — the correct sentence, which is already in the repo
rm -rf "$FIX/skills/hedged"
mk correct <<'EOF'
# Correct skill
## Communication Rules
- Communicate with the user in their preferred language.
- All manuscript edits are in English.
- Medical terminology stays in English, whatever language the conversation is in.
EOF
python3 "$G" --root "$FIX" --strict >/dev/null 2>&1
ck "NEGATIVE: 'in their preferred language' is silent" 0 "$?"

# 5) NEGATIVE — a language named as the SUBJECT of the work is not the defect
rm -rf "$FIX/skills/correct"
mk subject <<'EOF'
# Subject skill
- The manuscript is written in English.
- Translate the abstract into Japanese for the society submission.
- Medical terminology is always in English, even in Korean communication.
EOF
python3 "$G" --root "$FIX" --strict >/dev/null 2>&1
ck "NEGATIVE: a language as the work's subject is not the defect" 0 "$?"

# 6) NEGATIVE — the file that already knew must not be punished for saying so.
#    /publish-skill names the defect AND prints its cure on the same line. The first draft of this
#    gate flagged it. That is how a gate dies.
rm -rf "$FIX/skills/subject"
mk teaching <<'EOF'
# Teaching skill
### PII scrub
6. **Language hardcoding** ("in Korean", "in Japanese", "in Chinese")
- Replace: `"in Korean"` / `"Korean language"` -> `"in the user's preferred language"`
EOF
python3 "$G" --root "$FIX" --strict >/dev/null 2>&1
ck "NEGATIVE: naming the defect + its cure is teaching, not doing" 0 "$?"

echo
echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ] || exit 1

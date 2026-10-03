#!/usr/bin/env bash
# Regression tests for skills/publish-skill/scripts/audit_skill.sh.
#
# Every defect covered here had the same shape: a check that could not run
# reported RESULT: CLEAN with exit 0. Each POSITIVE case rebuilds such an input
# and demands a non-clean exit; each NEGATIVE control demands the script stays
# CLEAN on an input that has nothing to find.
#
#   F1  `[가-힣]` made grep exit 2 under UTF-8 locales; the error was swallowed,
#       so the whole "Academic Roles" category (English branches too) was inert.
#   F2  an invalid user extra_patterns regex was swallowed the same way.
#   F3  binaries + no exiftool read as CLEAN; with exiftool, EXIF lines were not
#       checked for emails and the user pattern was matched case-sensitively.
#
# Requires exiftool and python3 (CI installs both).
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
A="$HERE/../scripts/audit_skill.sh"

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-66s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-66s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

if ! command -v exiftool >/dev/null 2>&1; then
  echo "FAIL: exiftool is required for this test (apt-get install libimage-exiftool-perl)" >&2
  exit 1
fi

FIX="$(mktemp -d)"
trap 'rm -rf "$FIX"' EXIT
mk() { mkdir -p "$FIX/$1"; printf '# skill\n' > "$FIX/$1/SKILL.md"; cat >> "$FIX/$1/SKILL.md"; echo "$FIX/$1"; }
run() { bash "$A" "$@" >/dev/null 2>&1; echo $?; }
run_loc() { local loc="$1"; shift; LC_ALL="$loc" bash "$A" "$@" >/dev/null 2>&1; echo $?; }

mkdocx() {  # mkdocx <path> <creator> <lastModifiedBy>
  python3 - "$1" "$2" "$3" <<'PY'
import sys, zipfile
p, creator, lmb = sys.argv[1:4]
core = ('<?xml version="1.0" encoding="UTF-8"?><cp:coreProperties '
        'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:creator>%s</dc:creator>'
        '<cp:lastModifiedBy>%s</cp:lastModifiedBy></cp:coreProperties>') % (creator, lmb)
with zipfile.ZipFile(p, "w") as z:
    z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>')
    z.writestr("_rels/.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>')
    z.writestr("docProps/core.xml", core)
PY
}

# A PATH that has everything the script needs except exiftool.
NOEX="$FIX/_noexif_bin"
mkdir -p "$NOEX"
for c in bash grep find sed wc tr cat mktemp basename dirname rm head; do
  ln -s "$(command -v "$c")" "$NOEX/$c"
done
run_noex() { PATH="$NOEX" bash "$A" "$@" >/dev/null 2>&1; echo $?; }

echo "== F1: Academic Roles category must work in every locale"
d=$(mk f1_en <<'EOF'
Ask Dr. Smith and professor Jones; PGY3 rotation.
EOF
)
for L in C POSIX C.UTF-8; do
  ck "POS English roles, LC_ALL=$L" 1 "$(run_loc "$L" "$d")"
done
# Assembled at runtime so this file itself does not trip the repo's precedent gate.
d=$(printf '%s %s님께 회신 받음\n' "김철수" "교수" | mk f1_ko)
for L in C C.UTF-8; do
  ck "POS Hangul name + 교수님, LC_ALL=$L" 1 "$(run_loc "$L" "$d")"
done
d=$(mk f1_neg <<'EOF'
This skill builds a table. 이 스킬은 표를 만든다.
EOF
)
for L in C C.UTF-8; do
  ck "NEG plain English + Korean prose, LC_ALL=$L" 0 "$(run_loc "$L" "$d")"
done
d=$(mk f1_neg_role <<'EOF'
지도 교수 회신을 기다린다.
EOF
)
for L in C C.UTF-8; do
  ck "NEG role words without a name, LC_ALL=$L" 0 "$(run_loc "$L" "$d")"
done

echo "== F2: an invalid user regex is a usage error, not CLEAN"
d=$(mk f2 <<'EOF'
Written by Jane Doe at Acme Hospital
EOF
)
ck "POS unbalanced paren in extra_patterns"   2 "$(run "$d" 'Jane Doe|(Acme Hospital')"
ck "POS trailing backslash in extra_patterns" 2 "$(run "$d" 'Jane Doe\')"
ck "CTRL valid extra_patterns that matches"   1 "$(run "$d" 'Jane Doe|Acme Hospital')"
d=$(mk f2_neg <<'EOF'
Nothing personal here.
EOF
)
ck "NEG valid extra_patterns, no match"       0 "$(run "$d" 'Jane Doe|Acme Hospital')"

# Built from parts so the repo's own email gate does not read this file as a leak.
FAKE_MAIL="jane.doe"'@'"gmail.com"

echo "== F3: EXIF metadata"
d=$(mk f3_pii </dev/null)
mkdocx "$d/draft.docx" "JANE DOE" "$FAKE_MAIL"
ck "POS upper-case creator vs user pattern 'Jane Doe'" 1 "$(run "$d" 'Jane Doe')"
d=$(mk f3_mail </dev/null)
mkdocx "$d/draft.docx" "Template" "$FAKE_MAIL"
ck "POS email in lastModifiedBy, no user pattern"       1 "$(run "$d")"
d=$(mk f3_neg </dev/null)
mkdocx "$d/draft.docx" "Template" "Author"
ck "NEG neutral metadata, user pattern 'Jane Doe'"      0 "$(run "$d" 'Jane Doe')"
d=$(mk f3_neg_ex </dev/null)
mkdocx "$d/draft.docx" "Template" "someone@example.com"
ck "NEG whitelisted example.com email in metadata"      0 "$(run "$d")"

echo "== F3: binaries present, exiftool absent"
d=$(mk f3_noex </dev/null)
mkdocx "$d/draft.docx" "Template" "Author"
ck "POS no exiftool + binary, --strict -> 3 (incomplete)" 3 "$(run_noex --strict "$d")"
ck "CTRL no exiftool + binary, default -> 0"              0 "$(run_noex "$d")"
out=$(PATH="$NOEX" bash "$A" "$d" 2>&1)
case "$out" in
  *"RESULT: INCOMPLETE"*) ck "POS default RESULT line says INCOMPLETE" ok ok ;;
  *) ck "POS default RESULT line says INCOMPLETE" ok "missing" ;;
esac
d=$(mk f3_noex_neg <<'EOF'
Text only.
EOF
)
ck "NEG no exiftool, no binaries, --strict -> 0"          0 "$(run_noex --strict "$d")"

echo "== usage"
ck "missing directory -> 2" 2 "$(run "$FIX/does-not-exist")"

echo
echo "audit_skill tests: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

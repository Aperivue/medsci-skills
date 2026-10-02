#!/usr/bin/env bash
# Regression test: every BibTeX entry header BibTeX accepts must open its own record.
#
# parse_bib split the file only where `@type{` stood at column 0 with no space before the brace. An
# entry written `@article {key,`, an indented entry, or the parenthesised form `@article(key,` was
# merged into the entry before it, so only the first reference was ever looked up while the audit
# still said submission_safe. Headers BibTeX accepts are now split, including one that starts on the
# line where the previous entry ends; @comment/@string/@preamble are skipped. An `@` inside a field
# value is text to BibTeX, so it neither splits an entry nor refuses the file (negative controls).
#
# Network-free: the parser directly, and the CLI under --offline.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/verify_refs.py"
[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 - "$SCRIPT" "$TMP" <<'PY'
import importlib.util, json, subprocess, sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("vr", sys.argv[1])
vr = importlib.util.module_from_spec(spec)
sys.modules["vr"] = vr
spec.loader.exec_module(vr)
tmp = Path(sys.argv[2])

fail = 0
def check(label, cond):
    global fail
    print(f"  {'PASS' if cond else 'FAIL'}  {label}")
    fail += 0 if cond else 1

def entry(head, key, close="}"):
    return (f"{head}{key},\n  author = {{Doe, Jane}},\n  title = {{Synthetic title {key}}},\n"
            f"  doi = {{10.0000/synthetic.{key}}}\n{close}\n")

LAYOUTS = {
    "space before the brace": "".join(entry("@article {", k) for k in ("k1", "k2", "k3")),
    "indented entries": "".join("  " + entry("@article{", k) for k in ("k1", "k2", "k3")),
    "parenthesised form": "".join(entry("@article(", k, close=")") for k in ("k1", "k2", "k3")),
    "brace on the next line": "".join(entry("@article\n{", k) for k in ("k1", "k2", "k3")),
}
for label, text in LAYOUTS.items():
    recs = vr.parse_bib(text)
    check(f"{label}: 3 records, keys k1..k3",
          [r.ref_id for r in recs] == ["k1", "k2", "k3"])
    check(f"{label}: each record keeps its own DOI",
          [r.doi for r in recs] == ["10.0000/synthetic.k1", "10.0000/synthetic.k2",
                                    "10.0000/synthetic.k3"])

# Negative control: the column-0 layout parsed before is unchanged.
plain = "".join(entry("@article{", k) for k in ("k1", "k2", "k3"))
check("column-0 entries: 3 records, unchanged", [r.ref_id for r in vr.parse_bib(plain)] == ["k1", "k2", "k3"])
# Non-entries are not references.
extra = ("@string{jsr = {J Synth Res}}\n@comment{a note}\n@preamble{\"x\"}\n" + plain)
check("@string/@comment/@preamble are skipped", [r.ref_id for r in vr.parse_bib(extra)] == ["k1", "k2", "k3"])
# The freshness check reads the same keys.
sys.path.insert(0, str(Path(sys.argv[1]).parent))
import _claim_evidence as ce
for label, text in LAYOUTS.items():
    keys = [k for kind, k in ce.BIB_KEY_RE.findall(text)]
    check(f"_claim_evidence.BIB_KEY_RE agrees: {label}", keys == ["k1", "k2", "k3"])

# An entry header on the line where the previous one closes is its own record, not merged.
inline = entry("@article{", "k1").rstrip("\n") + " " + entry("@article{", "k2")
recs = vr.parse_bib(inline)
check("same-line entry header: 2 records, each with its own DOI",
      [(r.ref_id, r.doi) for r in recs] == [("k1", "10.0000/synthetic.k1"), ("k2", "10.0000/synthetic.k2")])

# Negative controls: an `@` inside a field value is field text, not an entry header.
AT_IN_FIELD = {
    "braced title with '} @ Home ({'": (
        "@article{k1,\n  author = {Doe, Jane},\n"
        "  title = {Outcomes of the {Hospital} @ Home ({HaH}) model in older adults: a cohort study},\n"
        "  doi = {10.0000/synthetic.k1}\n}\n" + entry("@article{", "k2")),
    "note with '} @example (x)'": (
        "@article{k1,\n  author = {Doe, Jane},\n  title = {Synthetic title k1},\n"
        "  note = {Correspondence: {Doe} @example (x)},\n"
        "  doi = {10.0000/synthetic.k1}\n}\n" + entry("@article{", "k2")),
    "indented '@misc (' line inside an abstract": (
        "@article{k1,\n  author = {Doe, Jane},\n  title = {Synthetic title k1},\n"
        "  abstract = {Posts were collected from\n  @misc (hashtags) online},\n"
        "  doi = {10.0000/synthetic.k1}\n}\n" + entry("@article{", "k2")),
    "quoted title with '@' in a parenthesised entry": (
        "@article(k1,\n  author = \"Doe, Jane\",\n  title = \"Outcomes (x) at {Home} @ Home (HaH)\",\n"
        "  doi = {10.0000/synthetic.k1}\n)\n" + entry("@article{", "k2")),
}
for label, text in AT_IN_FIELD.items():
    recs = vr.parse_bib(text)
    check(f"{label}: 2 records, keys k1,k2, DOIs kept",
          [(r.ref_id, r.doi) for r in recs] == [("k1", "10.0000/synthetic.k1"), ("k2", "10.0000/synthetic.k2")])

# An unbalanced brace does not swallow the rest of the file: a column-0 header still splits.
broken = ("@article{k1,\n  author = {Doe, Jane},\n  title = {Synthetic {title k1},\n"
          "  doi = {10.0000/synthetic.k1}\n}\n" + entry("@article{", "k2"))
check("unclosed body: the next column-0 entry is still its own record",
      [r.ref_id for r in vr.parse_bib(broken)] == ["k1", "k2"])

# End to end: the audit covers every entry.
def cli(name, text):
    bib = tmp / name
    bib.write_text(text, encoding="utf-8")
    root = tmp / (name + ".proj")
    root.mkdir()
    p = subprocess.run([sys.executable, sys.argv[1], str(bib), "--offline", "--project-root", str(root)],
                       capture_output=True, text=True)
    audit = root / "qc" / "reference_audit.json"
    return p, (json.loads(audit.read_text(encoding="utf-8")) if audit.exists() else None)

p, audit = cli("spaced.bib", LAYOUTS["space before the brace"])
check("CLI: spaced .bib audits all 3 references", audit is not None and audit["total_references"] == 3)
p, audit = cli("plain.bib", plain)
check("CLI: column-0 .bib still audits 3 references", audit is not None and audit["total_references"] == 3)
p, audit = cli("inline.bib", inline)
check("CLI: same-line entry header -> rc 0, 2 references audited",
      p.returncode == 0 and audit is not None and audit["total_references"] == 2)
for i, (label, text) in enumerate(AT_IN_FIELD.items()):
    p, audit = cli(f"atfield{i}.bib", text)
    check(f"CLI: {label} -> rc 0, 2 references audited",
          p.returncode == 0 and audit is not None and audit["total_references"] == 2)

print(f"fail={fail}")
print("ALL PASS" if fail == 0 else f"FAILURES: {fail}")
sys.exit(1 if fail else 0)
PY

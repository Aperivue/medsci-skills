#!/usr/bin/env bash
# Regression test for gen_skill_docs.py _ignorable(): a dotted ANCESTOR directory
# (e.g. a git worktree checked out under ~/.local/...) must not make every reference
# file count as 0. Only dot/__pycache__/.pyc components INSIDE the walked tree are excluded.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
echo "== test_gen_skill_docs_ignorable =="

python3 - "$REPO_ROOT" <<'PY'
import sys, tempfile, shutil, importlib.util
from pathlib import Path

repo = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("gsd_under_test", repo / "scripts" / "gen_skill_docs.py")
gsd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gsd)

fails = []
tmp = Path(tempfile.mkdtemp())
try:
    # Skill tree under a DOTTED ancestor dir (mimics a worktree under ~/.local/...).
    base = tmp / ".dotted_ancestor" / "skillX"
    sub = base / "references" / "examples"
    sub.mkdir(parents=True)
    (sub / "real_one.md").write_text("x", encoding="utf-8")
    (sub / "real_two.md").write_text("y", encoding="utf-8")
    (sub / "__pycache__").mkdir()
    (sub / "__pycache__" / "c.pyc").write_text("z", encoding="utf-8")
    (sub / ".hidden.md").write_text("h", encoding="utf-8")

    # _ignorable: a real file must NOT be flagged despite the dotted ancestor; in-tree
    # pycache/.pyc/dotfiles MUST still be flagged.
    if gsd._ignorable(sub / "real_one.md", sub):
        fails.append("real file flagged ignorable despite dotted ancestor (the bug)")
    if not gsd._ignorable(sub / "__pycache__" / "c.pyc", sub):
        fails.append(".pyc inside the tree not flagged")
    if not gsd._ignorable(sub / ".hidden.md", sub):
        fails.append("dotfile inside the tree not flagged")

    # Fallback branch (p NOT under root): judged by basename only, never by absolute
    # ancestors — a dotted ancestor must still not flag a real file.
    outside = Path("/no/such/root")
    if gsd._ignorable(sub / "real_one.md", outside):
        fails.append("out-of-root real file flagged via dotted ancestor (fallback bug)")
    if not gsd._ignorable(sub / ".hidden.md", outside):
        fails.append("out-of-root dotfile not flagged by basename fallback")
    if not gsd._ignorable(sub / "__pycache__" / "c.pyc", outside):
        fails.append("out-of-root .pyc not flagged")

    # list_resources: count must be 2 (the two real .md), not 0.
    res = gsd.list_resources(base)
    entry = next((e for e in res.get("references", []) if e.startswith("`examples/`")), None)
    if entry is None:
        fails.append("examples/ subdir not listed by list_resources")
    elif "(2 files)" not in entry:
        fails.append(f"wrong count under dotted ancestor: {entry!r} (expected '2 files')")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

if fails:
    print("FAIL:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("  ok: dotted-ancestor counts correct; in-tree pycache/.pyc/dotfiles excluded")
PY

# Real-repo behavior must be unchanged.
python3 scripts/gen_skill_docs.py --check >/dev/null 2>&1 \
  && echo "  ok: gen_skill_docs.py --check still passes (counts unchanged on a normal checkout)" \
  || { echo "FAIL: gen_skill_docs.py --check regressed"; exit 1; }

echo "PASS: test_gen_skill_docs_ignorable"

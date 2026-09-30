#!/usr/bin/env python3
"""Everything a user runs must load on the oldest Python we promise them.

The README says **Python 3.9+**. CI runs 3.11. This machine runs 3.14. Nothing checks 3.9 — so a
`match` statement, or a `X | None` in a function signature, would sail through every gate we have
and break only on the computer of a clinician who never tells us, because when a research tool
errors out a physician does not file a bug: they close the window and go back to doing it by hand.

That gap is not hypothetical. On 2026-07-13 a backslash inside an f-string (legal on 3.12+, a
syntax error before it) shipped from a 3.14 machine and was caught only because CI happened to run
3.11. One version lower and it would have been invisible.

Parsing is not loading. A PEP 604 union (`str | None`) PARSES on 3.9, so this gate used to pass it,
but a function annotation is evaluated when the `def` runs, and on 3.9 that is
`TypeError: unsupported operand type(s) for |` the moment the module is imported. Seven user-facing
scripts shipped that way in v6 (stock macOS `/usr/bin/python3` is 3.9), and the gate reported them
clean for two reasons: it only parsed, and its glob (`skills/*/scripts/*.py`) never reached
`skills/deidentify/deidentify.py`, `skills/fulltext-retrieval/*.py` or `skills/*/references/*.py`.
So, below 3.10, it also flags a union that Python evaluates at run time:
  * in a function signature or a module/class-level variable annotation, unless the module has
    `from __future__ import annotations` (which turns every annotation into an unevaluated string);
  * anywhere outside an annotation where an operand is `None` or a builtin type (`x = str | None`,
    `isinstance(v, int | float)`), which the future import does not help.

This checks every Python file that reaches a user — the installers and everything under `skills/`
except test directories — under the promised floor. It does not check the repository's own
maintainer tooling (`scripts/`), which never leaves this repo and may use whatever CI runs.

Usage:
    check_python_floor.py [--floor 3.9] [--strict] [--root DIR]

Stdlib only.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# What actually reaches a user's machine: the classroom ZIP payload (installers/ + skills/) and the
# npm package. `scripts/` is maintainer tooling and is deliberately not shipped. Skill Python lives
# outside `scripts/` too (a skill-root CLI, `references/` helpers and templates), so skills/ is
# walked whole.
SHIPPED = [
    ("installers", "*.py"),
    ("skills", "**/*.py"),
]

SKIP_PARTS = {"__pycache__", "tests", ".pytest_cache"}

# An operand that makes `a | b` a type union rather than bitwise arithmetic.
_TYPE_NAMES = {"None", "bool", "bytearray", "bytes", "complex", "dict", "float", "frozenset", "int",
               "list", "object", "set", "str", "tuple", "type"}


def shipped_files(root: Path = ROOT) -> list[Path]:
    out: list[Path] = []
    for base, pattern in SHIPPED:
        for p in sorted((root / base).glob(pattern)):
            if p.is_file() and not SKIP_PARTS.intersection(p.relative_to(root).parts):
                out.append(p)
    return out


def _unions(node: ast.AST) -> list[ast.BinOp]:
    return [n for n in ast.walk(node) if isinstance(n, ast.BinOp) and isinstance(n.op, ast.BitOr)]


def _is_type(e: ast.AST) -> bool:
    if isinstance(e, ast.Constant):
        return e.value is None
    if isinstance(e, ast.Subscript):
        e = e.value
    return isinstance(e, ast.Name) and e.id in _TYPE_NAMES


def runtime_unions(tree: ast.Module) -> list[tuple[int, str]]:
    """PEP 604 unions that Python evaluates while the module runs (a TypeError before 3.10)."""
    lazy = any(isinstance(n, ast.ImportFrom) and n.module == "__future__"
               and any(a.name == "annotations" for a in n.names) for n in tree.body)
    hits: list[tuple[int, str]] = []
    in_annotation: set[int] = set()

    def annotation(node: ast.AST, evaluated: bool, where: str) -> None:
        in_annotation.update(id(n) for n in ast.walk(node))
        if evaluated and not lazy:
            hits.extend((u.lineno, f"`X | Y` in a {where} is evaluated at run time; add "
                         "`from __future__ import annotations`") for u in _unions(node))

    def visit(node: ast.AST, scope: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                a = child.args
                for arg in a.posonlyargs + a.args + a.kwonlyargs + [a.vararg, a.kwarg]:
                    if arg is not None and arg.annotation is not None:
                        annotation(arg.annotation, True, "function signature")
                if child.returns is not None:
                    annotation(child.returns, True, "function signature")
                visit(child, "function")
            elif isinstance(child, ast.ClassDef):
                visit(child, "class")
            elif isinstance(child, ast.AnnAssign):
                # A local variable's annotation is never evaluated; a module or class one is.
                annotation(child.annotation, scope != "function", f"{scope}-level variable annotation")
                visit(child, scope)
            else:
                visit(child, "function" if isinstance(child, ast.Lambda) else scope)

    visit(tree, "module")
    for u in _unions(tree):
        if id(u) not in in_annotation and (_is_type(u.left) or _is_type(u.right)):
            hits.append((u.lineno, "`X | Y` type union evaluated at run time; use typing.Optional / "
                         "typing.Union (the future import does not cover it)"))
    return sorted(set(hits))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--floor", default="3.9", help="the oldest Python we promise (default: the README's 3.9)")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any violation (CI gate)")
    ap.add_argument("--root", type=Path, default=ROOT, help="repository root to check (default: this one)")
    a = ap.parse_args()

    try:
        major, minor = (int(x) for x in a.floor.split("."))
    except ValueError:
        raise SystemExit(f"--floor must look like 3.9, not {a.floor!r}")

    root = a.root.resolve()
    files = shipped_files(root)
    if not files:
        raise SystemExit("found no shipped python files — the globs are wrong, and this gate is a no-op")

    bad: list[tuple[Path, int, str]] = []
    for p in files:
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"), feature_version=(major, minor))
        except SyntaxError as exc:
            bad.append((p, exc.lineno or 0, exc.msg))
            continue
        if (major, minor) < (3, 10):
            bad.extend((p, line, msg) for line, msg in runtime_unions(tree))

    if bad:
        n = len({p for p, _, _ in bad})
        print(f"PYTHON_FLOOR: {n} shipped file(s) will not load on Python {a.floor}\n")
        for p, line, msg in bad:
            print(f"  {p.relative_to(root)}:{line}")
            print(f"      {msg}")
        print(
            f"\nThe README promises Python {a.floor}+. A file that will not load there does not fail "
            "politely on\na clinician's computer — it fails with a traceback, and they close the window."
        )
        return 1 if a.strict else 0

    print(f"OK: all {len(files)} shipped script(s) load on Python {a.floor} (the floor we promise).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

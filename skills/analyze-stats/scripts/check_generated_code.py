#!/usr/bin/env python3
"""Generated-code quality gate for analysis scripts (analyze-stats Phase 3.5).

AI-generated analysis code carries a recurring set of reproducibility-hygiene
"slop" patterns that pass a casual read but break reproducibility or violate
the data-integrity rules every medsci-skills analysis must follow. This linter
scans emitted .py / .R scripts before they are reported as final and flags:

  MISSING_SEED            randomness is used (sampling, bootstrap, train/test
                          split, shuffling, rng) but no seed is set
                          (np.random.seed / set.seed / random_state= /
                          default_rng / RandomState, each with a real
                          argument), or a generator is explicitly initialised
                          unseeded (default_rng(), RandomState(None),
                          np.random.seed(), set.seed(NULL)) even when a seed
                          is set elsewhere. Non-reproducible. Mentions in
                          comments and (Python) docstrings are ignored. (Major)
  HARDCODED_DATA_LITERAL  a large hand-typed numeric literal that looks like
                          tabular data — either alongside a real data-file read,
                          or very large on its own. The data-integrity rule is
                          "never hand-type CSV data into scripts; use read_csv +
                          subset." (Major)
  HARDCODED_ABS_PATH      an absolute filesystem path literal (/Users/, /home/,
                          C:\\, ~/Documents). Non-portable and a PII risk. (Major)
  INPLACE_SOURCE_OVERWRITE the same path is both read as input and written as
                          output — silently overwriting raw source data. The
                          data-integrity rule is "never modify raw data." (Major)
  DEBUG_LEFTOVER          a debugger/print artifact left in (breakpoint(),
                          pdb.set_trace(), browser(), print("debug"...)) or a
                          TODO/FIXME/XXX marker. (Flag)
  UNUSED_IMPORT           (Python only) an imported name never referenced again;
                          dead dependency. (Flag)

The gate is conservative on the Major checks (it fires HARDCODED_DATA_LITERAL
only on genuinely table-shaped literals, MISSING_SEED only when a real
randomness call is present) so it stays quiet on legitimate analysis code.

INPUTS
  positional   one or more .py / .R / .r files.
  --code-dir   directory to scan recursively for .py / .R / .r files.
  (at least one source must be provided via either form.)

OUTPUT
  A findings table (stdout) and, with --out, a JSON artifact:
    {files[], claims[{verdict, severity, file, line, detail}], summary}
  Exit 1 (with --strict) when any Major claim exists; exit 2 on input error.

Stdlib-only (ast / json / re / argparse / pathlib). Exit codes: 0 clean (or
report-only), 1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import re
import sys
import tokenize
from pathlib import Path

# --- shared regexes (language-agnostic unless noted) ------------------------

ABS_PATH = re.compile(r"""['"](?:/Users/|/home/|~/Documents|~/Desktop|~/Downloads|[A-Za-z]:\\\\)[^'"]*['"]""")

DEBUG_PY = re.compile(
    r"\bbreakpoint\s*\(|\bpdb\.set_trace\s*\(|^\s*import\s+pdb\b|"
    r"\bprint\s*\(\s*['\"](?:debug|here|test|xxx|todo|checkpoint)\b", re.IGNORECASE)
DEBUG_R = re.compile(
    r"\bbrowser\s*\(\s*\)|\bdebug(?:once)?\s*\(|"
    r"\bprint\s*\(\s*paste0?\s*\(\s*['\"](?:debug|here|test)\b|"
    r"\bcat\s*\(\s*['\"](?:debug|here)\b", re.IGNORECASE)
TODO_MARKER = re.compile(r"#\s*(?:TODO|FIXME|XXX)\b", re.IGNORECASE)

# randomness signals vs seed signals
RAND_PY = re.compile(
    r"np\.random\.|numpy\.random\.|\brandom\.(?:sample|shuffle|choice|random|randint|randrange)\b|"
    r"\bRandomState\b|\bdefault_rng\b|\btrain_test_split\b|\bKFold\b|\bStratifiedKFold\b|"
    r"\bShuffleSplit\b|\bresample\s*\(|\bbootstrap\b|\bpermutation\b")
# A seed call counts only with a real argument: `default_rng()`, `RandomState()`,
# `np.random.seed()`, `random.seed(None)` and `random_state=None` all draw fresh OS entropy.
_PY_SEED_ARG = r"\s*(?![\s)]|None\b)"
SEED_PY = re.compile(
    r"(?:np\.random\.seed|numpy\.random\.seed|\brandom\.seed|\bRandomState|\bdefault_rng)"
    r"\s*\(" + _PY_SEED_ARG + r"|\brandom_state\s*=(?!=)" + _PY_SEED_ARG)
# ...and an explicitly UNSEEDED generator is non-reproducible even if a seed is set elsewhere:
# `np.random.seed(42); rng = np.random.default_rng()` draws from `rng` unseeded. (A bare
# `random_state=None` is not flagged on its own: it is the usual default in a `def` signature.)
UNSEEDED_PY = re.compile(
    r"(?:np\.random\.seed|numpy\.random\.seed|\brandom\.seed|\bRandomState|\bdefault_rng)"
    r"\s*\(\s*(?:None\s*)?\)")
RAND_R = re.compile(
    r"\bsample\s*\(|\bsample\.int\s*\(|\brnorm\s*\(|\brunif\s*\(|\brbinom\s*\(|"
    r"\brpois\s*\(|\bboot\s*\(|\bcreateDataPartition\s*\(")
SEED_R = re.compile(r"\bset\.seed\s*\(\s*(?![\s)]|NULL\b)")
UNSEEDED_R = re.compile(r"\bset\.seed\s*\(\s*NULL\s*\)")  # re-initialises from entropy

# data-file reads / writes (for INPLACE_SOURCE_OVERWRITE and the DATA_LITERAL gate)
READ_CALL = re.compile(
    r"(?:read_csv|read\.csv|read_excel|read\.xlsx|read_parquet|read_table|read\.table|"
    r"read_csv2|read_tsv|read_sas|read_stata|read_feather|read_json|loadtxt|genfromtxt)"
    r"\s*\(\s*([^,\)]+)")
WRITE_FN = re.compile(
    r"(?:to_csv|write\.csv|write_csv|write_csv2|to_excel|write\.xlsx|to_parquet|"
    r"write_parquet|to_feather|savetxt|write\.table|write_tsv|fwrite)\s*\(")

STR_LITERAL = re.compile(r"""['"]([^'"]+)['"]""")
# bracketed/paren literal whose body is mostly comma-separated numbers
NUM_LITERAL_BODY = re.compile(r"[\[(]([^\[\]()]*?\d[^\[\]()]*?)[\])]")
NUM_TOKEN = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")

DATA_LITERAL_MIN = 12       # numbers in one literal to look table-shaped (with a read)
DATA_LITERAL_STANDALONE = 24  # numbers in one literal to flag even with no read


def _first_path_literal(arg: str) -> str | None:
    m = STR_LITERAL.search(arg)
    return m.group(1) if m else None


def strip_comments(src: str) -> str:
    """Blank out `#`-to-EOL comments while preserving byte offsets and line count,
    so seed/randomness detection never matches a mention inside a comment (e.g.
    '# no set.seed() used') yet reported line numbers stay correct. Used for R
    sources (and as the Python fallback when tokenize fails). Runs only for
    the seed/randomness checks; path/literal checks keep the full source."""
    out = []
    for line in src.split("\n"):
        i = line.find("#")
        out.append(line if i < 0 else line[:i] + " " * (len(line) - i))
    return "\n".join(out)


def _blank_spans(src: str, spans: list[tuple[tuple[int, int], tuple[int, int]]]) -> str:
    """Replace each ((row, col), (end_row, end_col)) span (tokenize coordinates:
    1-based rows, 0-based character columns) with spaces, keeping newlines, so
    offsets and line numbers of everything outside the spans are unchanged."""
    lines = src.split("\n")
    starts, pos = [], 0
    for line in lines:
        starts.append(pos)
        pos += len(line) + 1
    chars = list(src)
    for (r0, c0), (r1, c1) in spans:
        a, b = starts[r0 - 1] + c0, starts[r1 - 1] + c1
        for i in range(a, min(b, len(chars))):
            if chars[i] != "\n":
                chars[i] = " "
    return "".join(chars)


def strip_py_comments_docstrings(src: str) -> str:
    """Python: blank comments and docstrings / bare string statements using the
    tokenize module (not a regex over raw text), so a mention such as
    '# never call default_rng()' or a docstring explaining 'default_rng() is
    unseeded' is not read as a call. A `#` inside an ordinary string literal is left
    alone. Strings used as values (arguments, assignments) are kept. Falls back to
    the line-based strip_comments() if the source does not tokenize."""
    spans: list[tuple[tuple[int, int], tuple[int, int]]] = []
    trivia = {tokenize.NL, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT,
              tokenize.ENCODING}
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return strip_comments(src)
    prev_sig = None  # type of the previous significant token
    i = 0
    while i < len(toks):
        tok = toks[i]
        if tok.type == tokenize.COMMENT:
            spans.append((tok.start, tok.end))
        elif tok.type == tokenize.STRING and prev_sig in (None, tokenize.NEWLINE):
            # a run of (implicitly concatenated) string tokens at the start of a
            # logical line that ends the line is a docstring / bare string statement
            j = i
            while j + 1 < len(toks) and toks[j + 1].type in (tokenize.STRING, tokenize.NL):
                j += 1
            k = j + 1
            while k < len(toks) and toks[k].type in (tokenize.COMMENT, tokenize.NL):
                k += 1
            if k >= len(toks) or toks[k].type in (tokenize.NEWLINE, tokenize.ENDMARKER):
                spans.extend((t.start, t.end) for t in toks[i:j + 1]
                             if t.type == tokenize.STRING)
        if tok.type not in trivia:
            prev_sig = tok.type
        i += 1
    return _blank_spans(src, spans)


def check_text_common(src: str, lang: str) -> list[dict]:
    claims: list[dict] = []
    lines = src.splitlines()
    has_read = bool(READ_CALL.search(src))
    # comment-free (and, for Python, docstring-free) copy for seed/randomness logic
    code = strip_py_comments_docstrings(src) if lang == "py" else strip_comments(src)

    # MISSING_SEED
    rand, seed, unseeded = ((RAND_PY, SEED_PY, UNSEEDED_PY) if lang == "py"
                            else (RAND_R, SEED_R, UNSEEDED_R))
    rm = rand.search(code)
    um = unseeded.search(code)
    if rm and um:
        ln = src[:um.start()].count("\n") + 1
        claims.append({
            "verdict": "MISSING_SEED", "severity": "Major", "line": ln,
            "detail": (f"a random generator is initialised WITHOUT a seed "
                       f"('{um.group(0).strip()[:30]}' draws fresh OS entropy on every run), "
                       f"so the result is not reproducible even if a seed is set elsewhere; "
                       f"pass a fixed integer seed"),
        })
    elif rm and not seed.search(code):
        ln = src[:rm.start()].count("\n") + 1
        claims.append({
            "verdict": "MISSING_SEED", "severity": "Major", "line": ln,
            "detail": (f"randomness ('{rm.group(0).strip()[:30]}') is used but no seed is set "
                       f"({'np.random.seed/random_state=' if lang == 'py' else 'set.seed()'}); "
                       f"the result is not reproducible"),
        })

    # HARDCODED_ABS_PATH
    am = ABS_PATH.search(src)
    if am:
        ln = src[:am.start()].count("\n") + 1
        claims.append({
            "verdict": "HARDCODED_ABS_PATH", "severity": "Major", "line": ln,
            "detail": f"absolute path literal {am.group(0)[:50]} — non-portable and a PII risk",
        })

    # HARDCODED_DATA_LITERAL
    for m in NUM_LITERAL_BODY.finditer(src):
        body = m.group(1)
        # ignore obvious non-data: ranges, single repeated, function-call args with kwargs
        if "=" in body:  # kwargs like figsize=(8,6) or linspace(0,1,...) — not table data
            continue
        # A list/tuple of string literals (e.g. a hex-color palette
        # ['#000000','#E69F00',...] — exactly the colorblind-safe WONG palette that
        # make-figures recommends) is NOT hand-typed tabular data. Strip quoted
        # substrings before counting numeric tokens, so digits living inside string
        # literals (the "00" in '#E69F00', RGBA codes, category labels) don't make a
        # string list look table-shaped. Genuine numeric data is unquoted.
        nums = NUM_TOKEN.findall(STR_LITERAL.sub("", body))
        if len(nums) >= DATA_LITERAL_STANDALONE or (len(nums) >= DATA_LITERAL_MIN and has_read):
            ln = src[:m.start()].count("\n") + 1
            claims.append({
                "verdict": "HARDCODED_DATA_LITERAL", "severity": "Major", "line": ln,
                "detail": (f"a hand-typed numeric literal with {len(nums)} values"
                           + (" alongside a data-file read" if has_read else "")
                           + "; load tabular data with read_csv()/read.csv() + subset, "
                             "never hand-type it into the script"),
            })
            break  # one report per file is enough to act on

    # INPLACE_SOURCE_OVERWRITE — a write call writing to a path also read as input.
    # Reads capture the first call argument; writes scan the call window for any
    # string literal (the output path is often the 2nd arg, e.g. write.csv(df, "x")).
    reads = {p for a in READ_CALL.findall(src) if (p := _first_path_literal(a))}
    writes: set[str] = set()
    for wm in WRITE_FN.finditer(src):
        window = src[wm.end():wm.end() + 200]
        window = window.split(")")[0]  # stay within this call's arg list
        writes.update(STR_LITERAL.findall(window))
    overlap = reads & writes
    if overlap:
        path = sorted(overlap)[0]
        idx = src.find(path)
        ln = src[:idx].count("\n") + 1 if idx >= 0 else 0
        claims.append({
            "verdict": "INPLACE_SOURCE_OVERWRITE", "severity": "Major", "line": ln,
            "detail": (f"'{path}' is both read as input and written as output; writing to the "
                       f"source path overwrites raw data — write derived outputs to a new path"),
        })

    # DEBUG_LEFTOVER
    debug_re = DEBUG_PY if lang == "py" else DEBUG_R
    for i, line in enumerate(lines, 1):
        if debug_re.search(line) or TODO_MARKER.search(line):
            claims.append({
                "verdict": "DEBUG_LEFTOVER", "severity": "Flag", "line": i,
                "detail": f"debug/marker leftover: {line.strip()[:60]}",
            })
            break  # first occurrence per file

    return claims


def check_unused_imports_py(src: str) -> list[dict]:
    """Python-only, AST-based. An imported name never referenced elsewhere."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []  # don't guess on unparseable files
    imported: list[tuple[str, str, int]] = []  # (bound_name, display, lineno)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound = (alias.asname or alias.name).split(".")[0]
                imported.append((bound, alias.asname or alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            for alias in node.names:
                if alias.name == "*":
                    return []  # star import: cannot reason about usage
                bound = alias.asname or alias.name
                imported.append((bound, f"{node.module or ''}.{alias.name}", node.lineno))
    # collect all Name usages outside the import statements
    used: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            pass  # base Name already captured by the Name walk
    claims = []
    for bound, display, lineno in imported:
        if bound not in used:
            claims.append({
                "verdict": "UNUSED_IMPORT", "severity": "Flag", "line": lineno,
                "detail": f"'{display}' is imported but never used; remove the dead import",
            })
    return claims


def check_file(path: Path) -> list[dict]:
    lang = "py" if path.suffix.lower() == ".py" else "r"
    src = path.read_text(encoding="utf-8", errors="replace")
    claims = check_text_common(src, lang)
    if lang == "py":
        claims += check_unused_imports_py(src)
    for c in claims:
        c["file"] = str(path)
    return claims


def gather_files(positional: list[str], code_dir: str | None) -> list[Path]:
    files: list[Path] = []
    for p in positional:
        pp = Path(p)
        if not pp.is_file():
            sys.stderr.write(f"ERROR: not a file: {p}\n")
            sys.exit(2)
        files.append(pp)
    if code_dir:
        d = Path(code_dir)
        if not d.is_dir():
            sys.stderr.write(f"ERROR: not a directory: {code_dir}\n")
            sys.exit(2)
        for ext in ("*.py", "*.R", "*.r"):
            files.extend(sorted(d.rglob(ext)))
    # dedupe, preserve order
    seen, uniq = set(), []
    for f in files:
        key = str(f.resolve())
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    if not uniq:
        sys.stderr.write("ERROR: no .py/.R source files to scan\n")
        sys.exit(2)
    return uniq


def analyze(positional: list[str], code_dir: str | None) -> dict:
    files = gather_files(positional, code_dir)
    claims: list[dict] = []
    for f in files:
        claims += check_file(f)
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "files": [str(f) for f in files],
        "claims": claims,
        "summary": {
            "n_files": len(files),
            "n_claims": len(claims),
            "n_major": n_major,
            "n_flag": len(claims) - n_major,
            "verdict": "MAJOR_CANDIDATE" if n_major else "OK",
        },
    }


def render(result: dict) -> str:
    lines = ["| File:Line | Check | Severity | Detail |", "|---|---|---|---|"]
    for c in result["claims"]:
        loc = f"{Path(c['file']).name}:{c.get('line', 0)}"
        lines.append(f"| {loc} | {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | — | scripts are reproducibility-clean |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generated-code quality gate (analyze-stats Phase 3.5).")
    ap.add_argument("files", nargs="*", help=".py / .R source files to scan")
    ap.add_argument("--code-dir", help="directory to scan recursively for .py/.R files")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.files, args.code_dir)

    if not args.quiet:
        print("=" * 41)
        print(" Generated-Code Quality (Phase 3.5)")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} reproducibility/integrity issue(s) "
                  f"across {s['n_files']} file(s).")
        else:
            print(f"OK: {s['n_files']} file(s) reproducibility-clean "
                  f"({s['n_flag']} minor flag(s)).")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_generated_code", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Portal-field paste-verbatim gate — a "paste this verbatim" artifact must survive the
paste: markdown lands in the published field literally, and a few characters are silently
EXPANDED to words by some portals.

Portal-field text files (`abstract.txt`, `keywords.txt`, `take_home_points.txt`, …)
are cut from the manuscript markdown so an author can paste them straight into an
Editorial Manager / ScholarOne free-text field. Nothing strips the markdown at that
boundary, so a trailing `---`, a stray `**bold**`, or a `cm^2^` superscript pastes
into — and is published in — the abstract/keyword field literally.

Real instance: three portal-field files each ended with a `---` line; the author is
told to paste the file verbatim, so `---` would have printed in the published abstract.

This gate scans only `.txt` files (the paste-verbatim artifacts — a `.md` is *meant*
to carry markdown, so it is out of scope) for residue that would render literally in a
plain-text field:

  hr           a line that is only `---` / `***` / `___`  (rule / frontmatter delimiter)
  bold         paired `**bold**`
  heading      a line beginning with `#` … `######`
  link         inline `[text](url)`
  superscript  paired `^x^`   (e.g. `cm^2^`)
  subscript    paired `~x~`   (e.g. `H~2~O`, also `~~strike~~`)

Plus one advisory (Minor) — a valid character a portal EXPANDS rather than publishes:

  char_expansion  `≥` / `≤`  (ScholarOne expands "≥" to "{greater than or equal to}",
                  five words, inflating the word count — pre-substitute `>=` / `<=`;
                  `×` and the en-dash are left alone, as they usually paste cleanly)

Deterministic and precision-tuned: the emphasis/super/sub patterns require *paired*
markers with non-space content, so significance stars (`* p<0.05, ** p<0.01`),
approximation tildes (`~5%`), numeric ranges (`1~2`), and `C#` do not fire; headings
require the `#` at line start followed by whitespace, so `#1` does not fire.

INPUT
  --dir DIR      directory of portal-field artifacts; scans `*.txt` recursively.
  --files ...    explicit `.txt` file list (alternative to --dir).

OUTPUT  (--out path)
  {"detector": "check_portal_field_residue", "scanned", "findings":
     [{path, kind, label, line, snippet, severity}], "summary": {"residue": N},
   "submission_safe": bool}

Stdlib-only. Exit codes: 0 clean, 1 residue found, 2 input/usage error.
(Exit-1-on-finding by default so the sync-submission pre-flight gate halts on it,
matching check_checklist_dump_leak.)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Each: (kind, compiled pattern, human label). Multiline patterns are line-anchored;
# inline patterns require PAIRED markers with non-space content to stay precise.
RESIDUE: list[tuple[str, re.Pattern, str]] = [
    ("hr", re.compile(r"^\s*([-*_])\1{2,}\s*$", re.MULTILINE),
     "horizontal rule / frontmatter delimiter"),
    ("bold", re.compile(r"\*\*(?!\s)[^*\n]+?(?<!\s)\*\*"),
     "bold emphasis"),
    ("heading", re.compile(r"^\s{0,3}#{1,6}\s+\S", re.MULTILINE),
     "heading marker"),
    ("link", re.compile(r"\[[^\]\n]+\]\([^)\n]+\)"),
     "inline link"),
    ("superscript", re.compile(r"\^(?!\s)[^\s^]+\^"),
     "superscript marker"),
    ("subscript", re.compile(r"~(?!\s)[^\s~]+~"),
     "subscript / strikethrough marker"),
]

# Characters some portals (ScholarOne / Editorial Manager) verbose-EXPAND in a
# paste-verbatim field: "≥" becomes "{greater than or equal to}" (five words),
# silently inflating the field's word count and mangling the notation. This is a
# different failure from markdown residue — the character is valid, it just does not
# survive the paste — so it is advisory (Minor): pre-substitute ">=" / "<=" before
# pasting. Only "≥"/"≤" are flagged; "×" and the en-dash are usually left alone.
EXPANSION: list[tuple[str, re.Pattern, str]] = [
    ("char_expansion", re.compile(r"[≥≤]"),
     "portal may expand this to words (pre-substitute >= / <=)"),
]


def scan_text(text: str) -> list[dict]:
    findings: list[dict] = []
    for source, severity in ((RESIDUE, "Major"), (EXPANSION, "Minor")):
        for kind, pat, label in source:
            for m in pat.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                ls = text.rfind("\n", 0, m.start()) + 1
                le = text.find("\n", m.end())
                le = len(text) if le == -1 else le
                findings.append({
                    "kind": kind,
                    "label": label,
                    "line": line_no,
                    "snippet": text[ls:le].strip()[:120],
                    "severity": severity,
                })
    seen: set[tuple[str, int]] = set()
    uniq: list[dict] = []
    for f in sorted(findings, key=lambda x: (x["line"], x["kind"])):
        key = (f["kind"], f["line"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(f)
    return uniq


def collect_files(dir_arg: str | None, files_arg: list[str]) -> list[Path]:
    if files_arg:
        return [Path(f) for f in files_arg]
    if dir_arg:
        d = Path(dir_arg)
        if not d.is_dir():
            sys.stderr.write(f"ERROR: --dir not a directory: {dir_arg}\n")
            sys.exit(2)
        return sorted(d.rglob("*.txt"))
    sys.stderr.write("ERROR: pass --dir DIR or --files FILE ...\n")
    sys.exit(2)


def analyze(dir_arg: str | None, files_arg: list[str]) -> dict:
    paths = collect_files(dir_arg, files_arg)
    findings: list[dict] = []
    scanned = 0
    for p in paths:
        if not p.is_file():
            sys.stderr.write(f"ERROR: file not found: {p}\n")
            sys.exit(2)
        if p.suffix.lower() != ".txt":
            continue
        scanned += 1
        for f in scan_text(p.read_text(encoding="utf-8", errors="replace")):
            findings.append({"path": str(p), **f})
    return {
        "scanned": {"txt": scanned},
        "findings": findings,
        "summary": {"residue": len(findings)},
        "submission_safe": not findings,
    }


def render(result: dict) -> str:
    lines = ["| File | Line | Kind | Snippet |", "|---|---|---|---|"]
    for f in result["findings"]:
        lines.append(f"| {Path(f['path']).name} | {f['line']} | {f['kind']} | {f['snippet']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | — | no markdown residue in any portal-field .txt |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Portal-field markdown-residue gate (pre-freeze).")
    ap.add_argument("--dir", help="directory of portal-field artifacts (scans *.txt recursively)")
    ap.add_argument("--files", nargs="+", default=[], help="explicit .txt file list")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.dir, args.files)

    if not args.quiet:
        print("=" * 42)
        print(" Portal-Field Markdown Residue")
        print("=" * 42)
        print(render(result))
        print()
        n = result["summary"]["residue"]
        if n:
            print(f"RESIDUE: {n} markdown token(s) in a paste-verbatim portal field — "
                  "strip them or they publish literally.")
        else:
            print(f"OK: {result['scanned']['txt']} portal-field .txt file(s) are markdown-free.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps({"detector": "check_portal_field_residue", **result}, indent=2, ensure_ascii=False),
            encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if result["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())

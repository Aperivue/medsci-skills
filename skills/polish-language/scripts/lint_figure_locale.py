#!/usr/bin/env python3
"""Figure-SOURCE locale drift — US/UK spelling in a figure that no text gate can see.

A manuscript declares (or consistently uses) one spelling — say US — and every text gate
(polish-language's lint_consistency, a repo-wide locale sweep) enforces it across the prose.
None of them reach the text baked into a FIGURE, because that text lives in a rendered
raster (a PNG/TIFF) that a grep cannot read. So a co-author who builds a panel in PowerPoint
or a plotting script and types "Behavioural alignment" ships a UK word into a US manuscript,
and it is found only by opening the image on submission day.

This gate reads the figure SOURCES instead of the raster — no OCR:

  * `*.pptx` (and `.pptm`) — the `<a:t>` text runs inside `ppt/slides/slide*.xml`;
  * `*.py` / `*.R` / `*.r` figure scripts — the file text (label literals live there).

It compares each source against the manuscript's spelling (declared in a `spelling:` YAML
front-matter field, or inferred from the body's own US/UK majority) and flags any word in the
OPPOSITE variant. It reuses lint_consistency's US↔UK spelling families verbatim, so the two
gates never disagree on what "US" and "UK" mean.

Verdict:
  FIGURE_LOCALE_DRIFT (Minor)  a figure source uses the spelling the manuscript does not
                               (e.g. "Behavioural" in a US manuscript). Copy-edit before
                               the raster is exported; the raster itself stays out of scope.

INPUT
  --figures-dir DIR   directory scanned recursively for figure sources (.pptx/.pptm/.py/.R/.r).
                      Default: <manuscript-dir>/figures, then ./figures.
  --manuscript FILE   manuscript markdown — supplies the spelling target (front matter or body
                      majority) and, if --figures-dir is absent, the default figures directory.
  --spelling us|uk    force the target spelling (overrides front matter / inference).

OUTPUT (--out PATH)
  {"detector": "lint_figure_locale", "spelling", "scanned", "findings":
     [{path, kind, word, expected, line, severity}], "summary", "submission_safe"}

Stdlib-only. Exit codes: 0 clean / no figure sources / spelling undetermined (nothing judged),
1 drift found under --strict, 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

# Reuse the US↔UK spelling families verbatim so this gate and lint_consistency never disagree.
from lint_consistency import SPELLING_FAMILIES, SPELLING_US

FIGURE_SCRIPT_EXTS = {".py", ".r"}          # .R lowercases to .r
PPTX_EXTS = {".pptx", ".pptm"}
AT_RE = re.compile(r"<a:t>(.*?)</a:t>", re.S)
FRONT_SPELLING_RE = re.compile(r"(?im)^\s*spelling\s*:\s*['\"]?(us|uk|american|british)\b")

_US_RES = {k: re.compile(v, re.IGNORECASE) for k, v in SPELLING_US.items()}
_UK_RES = {us: re.compile(uk, re.IGNORECASE) for us, uk, _ in SPELLING_FAMILIES}


def _front_matter(text: str) -> str:
    """Return the leading YAML front-matter block (between the first two '---' lines), or ''."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return m.group(1) if m else ""


def target_spelling(manuscript_text: str) -> "str | None":
    """'us' / 'uk' from a `spelling:` front-matter field, else the body's US/UK majority, else None."""
    fm = _front_matter(manuscript_text)
    m = FRONT_SPELLING_RE.search(fm)
    if m:
        return "uk" if m.group(1).lower().startswith(("uk", "brit")) else "us"
    us = sum(len(r.findall(manuscript_text)) for r in _US_RES.values())
    uk = sum(len(r.findall(manuscript_text)) for r in _UK_RES.values())
    if us == uk:
        return None  # no signal / perfectly split — cannot judge a target
    return "us" if us > uk else "uk"


def _opposite_hits(text: str, spelling: str):
    """Yield (word, expected_us_form) for every word in the variant OPPOSITE to `spelling`."""
    wrong = _UK_RES if spelling == "us" else _US_RES
    for us_form, rx in wrong.items():
        for m in rx.finditer(text):
            yield m.group(0), us_form


def _pptx_runs(path: Path):
    """Text runs from a .pptx/.pptm's slide XML. Returns [] on a corrupt/non-zip file."""
    try:
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist()
                     if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
            runs = []
            for n in sorted(names):
                xml = z.read(n).decode("utf-8", "replace")
                runs += AT_RE.findall(xml)
            return runs
    except (zipfile.BadZipFile, OSError):
        return []


def _collect_sources(figures_dir: Path):
    """(pptx_paths, script_paths) under figures_dir."""
    pptx, scripts = [], []
    for p in sorted(figures_dir.rglob("*")):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext in PPTX_EXTS:
            pptx.append(p)
        elif ext in FIGURE_SCRIPT_EXTS:
            scripts.append(p)
    return pptx, scripts


def analyze(figures_dir: Path, spelling: str) -> dict:
    pptx, scripts = _collect_sources(figures_dir)
    findings: list[dict] = []

    def _emit(path, word, us_form):
        expected = us_form if spelling == "us" else next(
            (uk for us, uk, _ in SPELLING_FAMILIES if us == us_form), us_form)
        findings.append({
            "path": str(path), "kind": "FIGURE_LOCALE_DRIFT", "word": word,
            "expected_variant": spelling.upper(), "family": us_form, "severity": "Minor",
            "label": (f'"{word}" is {"UK" if spelling == "us" else "US"} spelling in a '
                      f'{spelling.upper()} manuscript — copy-edit the figure source '
                      f'(expected the {spelling.upper()} form, e.g. "{expected}")'),
        })

    for p in pptx:
        for run in _pptx_runs(p):
            for word, us_form in _opposite_hits(run, spelling):
                _emit(p, word, us_form)
    for p in scripts:
        text = p.read_text(encoding="utf-8", errors="replace")
        for word, us_form in _opposite_hits(text, spelling):
            _emit(p, word, us_form)

    # de-dup identical (path, word) pairs (a word repeated across runs/lines counts once)
    seen, uniq = set(), []
    for f in findings:
        key = (f["path"], f["word"].lower())
        if key in seen:
            continue
        seen.add(key)
        uniq.append(f)
    return {
        "spelling": spelling,
        "scanned": {"pptx": len(pptx), "scripts": len(scripts)},
        "findings": uniq,
        "summary": {"drift": len(uniq)},
        "submission_safe": not uniq,
    }


def render(result: dict) -> str:
    lines = ["| Figure source | Word | Detail |", "|---|---|---|"]
    for f in result["findings"]:
        lines.append(f"| {Path(f['path']).name} | {f['word']} | {f['label']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | no locale drift in any figure source |")
    return "\n".join(lines)


def _resolve_figures_dir(args) -> "Path | None":
    if args.figures_dir:
        d = Path(args.figures_dir)
        return d if d.is_dir() else None
    if args.manuscript:
        cand = Path(args.manuscript).resolve().parent / "figures"
        if cand.is_dir():
            return cand
    cand = Path("figures")
    return cand if cand.is_dir() else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Figure-source US/UK locale drift gate (no OCR).")
    ap.add_argument("--figures-dir", help="directory of figure sources (.pptx/.py/.R); default <manuscript-dir>/figures")
    ap.add_argument("--manuscript", help="manuscript markdown (spelling target + default figures dir)")
    ap.add_argument("--spelling", choices=["us", "uk"], help="force the target spelling (overrides inference)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any drift is found")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    figures_dir = _resolve_figures_dir(args)
    if figures_dir is None:
        if not args.quiet:
            print("OK: no figure-source directory found — nothing to scan.")
        return 0  # no sources: nothing to judge (also the crossfire-safe path)

    spelling = args.spelling
    if not spelling:
        if not args.manuscript:
            sys.stderr.write("ERROR: need --spelling us|uk or --manuscript to determine the target spelling\n")
            return 2
        mtext = Path(args.manuscript).read_text(encoding="utf-8", errors="replace")
        spelling = target_spelling(mtext)
        if spelling is None:
            if not args.quiet:
                print("OK: manuscript spelling could not be determined (no US/UK signal) — nothing judged.")
            return 0

    result = analyze(figures_dir, spelling)

    if not args.quiet:
        print("=" * 44)
        print(" Figure-Source Locale Drift")
        print("=" * 44)
        print(render(result))
        print()
        n = result["summary"]["drift"]
        if n:
            print(f"DRIFT: {n} figure-source word(s) in the wrong spelling for a "
                  f"{spelling.upper()} manuscript — copy-edit the source before export.")
        else:
            print(f"OK: {result['scanned']['pptx']} pptx + {result['scanned']['scripts']} script "
                  f"source(s) match the {spelling.upper()} spelling.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps({"detector": "lint_figure_locale", **result}, indent=2, ensure_ascii=False),
            encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["findings"]) else 0


if __name__ == "__main__":
    sys.exit(main())

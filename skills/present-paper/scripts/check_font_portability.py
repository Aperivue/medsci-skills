#!/usr/bin/env python3
"""Will this deck still be the deck you reviewed when the venue's computer opens it?

Every other compatibility check in this skill guards the direction where **you** open the file:
TIFF images, 3-D bevels, `app.xml` counts, `srcRect` crops — all of them are about the deck
surviving your own machine. The direction that decides the talk is the other one. You always have
the laptop you built it on; the auditorium often does not.

A font that is not installed is not an error. It is a silent substitution: the text stays, the
metrics change, line breaks move, and a box that fitted stops fitting. Nobody sees it until the
deck is on the screen, which is the one moment nothing can be done about it.

    FONT_NOT_PORTABLE   a typeface bundled with one operating system and absent on the other,
                        named in the deck and not embedded in it.

This found a 47-slide lecture, built the month before and already sent to a hospital auditorium,
carrying `Apple SD Gothic Neo` in 1,033 run-level `typeface=` attributes and `Menlo` in three, with
a Windows house PC waiting for it. It was found the night before, by hand, by someone who happened
to grep the OOXML.

WHY A BLOCKLIST AND NOT AN ALLOWLIST
    An allowlist of "approved" fonts flags every institutional template on earth, and a check that
    fires on good work gets switched off — taking the honest checks with it. So this names only
    fonts that genuinely ship with one platform and not the other, and stays quiet about every
    other choice. Calibri, Arial, Times New Roman, Inter, Noto and a hospital's licensed brand face
    are not this check's business.

NAMED IS NOT THE SAME AS USED
    A font named on a **run** renders. A font named in the **theme, a layout or the master** is a
    default, and a default for a script the deck never writes in is inert. python-pptx's own stock
    template declares a Windows-only Korean face in the theme's East-Asian slot, so a rule of
    "named anywhere" would condemn every deck this toolkit has ever produced — including the clean
    fixtures it tests itself against — for a template default nobody chose. That is not a strict
    check; it is a broken one, and the first fixture written for this check caught it.

    So: a blocklisted typeface on a run is reported. A blocklisted typeface in an inherited slot is
    reported **only when the deck actually contains text of the script that slot serves** — a
    Korean default matters once there is Korean on a slide, and not before. The real incident this
    check comes from was run-level anyway: 1,033 of them.

WHAT IT DOES NOT CLAIM
    Absence from the blocklist is not a promise the font is installed at the venue. A licensed
    corporate face is portable in the sense used here and still missing from a rented laptop. The
    only real guarantee is to embed the fonts (this check exempts what it finds in
    `<p:embeddedFontLst>`), or to carry a PDF.

    And note what the PDF fallback costs: **PDF drops embedded video**. A deck with a clip in it
    needs the MP4s carried separately, or the fallback is not a fallback.

Stdlib only. Reads the .pptx as the ZIP of XML it is, so it runs on a deck from anyone.

Usage:
    check_font_portability.py deck.pptx [--json out.json] [--strict]

Exit: 0 clean (or findings without --strict), 1 findings with --strict, 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

DETECTOR = "check_font_portability"

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"


# Fonts that ship with macOS and are not present on a stock Windows install. Keys are lowercased
# for matching; the value says what the other platform will put there instead, because "it will be
# substituted" is not actionable and "Windows will fall back to a default sans" is.
MACOS_ONLY: Dict[str, str] = {
    "apple sd gothic neo": "Korean UI face bundled with macOS; Windows substitutes a default sans",
    "applegothic": "macOS Korean face; absent on Windows",
    "apple gothic": "macOS Korean face; absent on Windows",
    "applemyungjo": "macOS Korean serif; absent on Windows",
    "apple ligothic": "macOS CJK face; absent on Windows",
    "helvetica": "macOS core face; Windows has no Helvetica and substitutes Arial",
    "helvetica neue": "macOS core face; Windows substitutes Arial and the metrics differ",
    "menlo": "macOS monospace; Windows substitutes Courier New",
    "monaco": "macOS monospace; Windows substitutes Courier New",
    "lucida grande": "macOS UI face; absent on Windows",
    "geneva": "macOS bitmap-era face; absent on Windows",
    "optima": "macOS face; absent on Windows",
    "hiragino sans": "macOS Japanese face; absent on Windows",
    "hiragino kaku gothic pro": "macOS Japanese face; absent on Windows",
    "pingfang sc": "macOS Simplified Chinese face; absent on Windows",
    "pingfang tc": "macOS Traditional Chinese face; absent on Windows",
    "songti sc": "macOS Chinese serif; absent on Windows",
    "heiti sc": "macOS Chinese sans; absent on Windows",
    "sf pro": "macOS system face, not licensed for redistribution; absent on Windows",
    "sf pro display": "macOS system face; absent on Windows",
    "sf pro text": "macOS system face; absent on Windows",
}

# The same failure travelling the other way: a deck built on Windows, opened on the presenter's Mac.
WINDOWS_ONLY: Dict[str, str] = {
    "malgun gothic": "Windows Korean UI face; macOS substitutes a default sans",
    "맑은 고딕": "Windows Korean UI face (Malgun Gothic); macOS substitutes a default sans",
    "gulim": "Windows Korean face; absent on macOS",
    "굴림": "Windows Korean face (Gulim); absent on macOS",
    "dotum": "Windows Korean face; absent on macOS",
    "돋움": "Windows Korean face (Dotum); absent on macOS",
    "batang": "Windows Korean serif; absent on macOS",
    "바탕": "Windows Korean serif (Batang); absent on macOS",
    "gungsuh": "Windows Korean serif; absent on macOS",
    "segoe ui": "Windows UI face; absent on macOS",
    "microsoft yahei": "Windows Chinese face; absent on macOS",
    "simsun": "Windows Chinese serif; absent on macOS",
    "mingliu": "Windows Chinese face; absent on macOS",
    "ms gothic": "Windows Japanese face; absent on macOS",
    "ms mincho": "Windows Japanese serif; absent on macOS",
}


@dataclass
class Finding:
    detector: str
    verdict: str
    slide: Optional[int]
    summary: str
    evidence: List[str] = field(default_factory=list)


# Where a typeface can be named. Slides first because a run-level font is the one that actually
# renders; the theme matters because everything inheriting from it moves at once.
_PART_ORDER = ("slide", "notes", "layout", "master", "theme")


def _part_kind(name: str) -> Optional[str]:
    if re.fullmatch(r"ppt/slides/slide\d+\.xml", name):
        return "slide"
    if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name):
        return "notes"
    if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", name):
        return "layout"
    if re.fullmatch(r"ppt/slideMasters/slideMaster\d+\.xml", name):
        return "master"
    if re.fullmatch(r"ppt/theme/theme\d+\.xml", name):
        return "theme"
    return None


def embedded_fonts(z: zipfile.ZipFile) -> set:
    """Typefaces the deck carries with it. A deck that embedded its fonts solved this problem.

    Not exempting these would make the check fire on the one correct answer to it, which is how a
    detector teaches people to ignore it.
    """
    out = set()
    try:
        pres = ET.fromstring(z.read("ppt/presentation.xml"))
    except (KeyError, ET.ParseError):
        return out
    for lst in pres.iter(f"{P}embeddedFontLst"):
        for font in lst.iter(f"{P}font"):
            tf = font.get("typeface")
            if tf:
                out.add(tf.strip().lower())
    return out


_DIRECT = {"slide", "notes"}          # a run: this renders
_INHERITED = {"theme", "layout", "master"}  # a default: this renders only if something asks for it

# The scripts a font slot serves. `ea` is the East-Asian slot; `latin` the Latin one; `cs` complex
# scripts. A default in a slot the deck never writes in changes nothing on the screen.
_CJK = re.compile(r"[ᄀ-ᇿ぀-ヿ㄰-㆏一-鿿가-힯]")
_LATIN = re.compile(r"[A-Za-z]")


@dataclass
class Usage:
    direct: int = 0
    inherited: int = 0
    kinds: Counter = field(default_factory=Counter)
    slots: set = field(default_factory=set)


def collect_typefaces(path: Path) -> Tuple[Dict[str, Usage], set, Dict[str, bool]]:
    """-> (usage per typeface, embedded typefaces, which scripts the deck's text actually uses)."""
    usage: Dict[str, Usage] = {}
    scripts = {"cjk": False, "latin": False}
    with zipfile.ZipFile(path) as z:
        embedded = embedded_fonts(z)
        for name in z.namelist():
            kind = _part_kind(name)
            if kind is None:
                continue
            try:
                root = ET.fromstring(z.read(name))
            except ET.ParseError:
                continue
            if kind in _DIRECT:
                for t in root.iter(f"{A}t"):
                    txt = t.text or ""
                    if _CJK.search(txt):
                        scripts["cjk"] = True
                    if _LATIN.search(txt):
                        scripts["latin"] = True
            for el in root.iter():
                tf = el.get("typeface")
                if not tf:
                    continue
                tf = tf.strip()
                # "+mn-lt" / "+mj-ea" are references to the theme, not a font name.
                if not tf or tf.startswith("+"):
                    continue
                u = usage.setdefault(tf, Usage())
                u.kinds[kind] += 1
                slot = el.tag.split("}")[-1]
                # A theme's font scheme carries per-script fallbacks as <a:font script="Hang" …>,
                # not as <a:ea …>. Read the script code, or the slot is unclassifiable and the
                # whole rule collapses back into "named anywhere".
                if slot == "font" and el.get("script"):
                    slot = f"font:{el.get('script')}"
                u.slots.add(slot)
                if kind in _DIRECT:
                    u.direct += 1
                else:
                    u.inherited += 1
    return usage, embedded, scripts


# ISO 15924 codes a theme font-scheme fallback can carry, for the two scripts this check can see in
# a deck's text. Anything else (Arab, Hebr, Thai, …) is left alone: the blocklists hold only Latin
# and CJK faces, so an unreadable script code cannot hide one of them.
_CJK_SCRIPTS = {"hang", "hani", "jpan", "hans", "hant", "kore", "hira", "kana", "bopo"}


def _slot_renders(slot: str, scripts: Dict[str, bool]) -> bool:
    if slot == "ea":
        return scripts["cjk"]
    if slot in {"latin", "sym"}:
        return scripts["latin"]
    if slot == "cs":
        return scripts["cjk"] or scripts["latin"]
    if slot.startswith("font:"):
        code = slot.split(":", 1)[1].lower()
        if code in _CJK_SCRIPTS:
            return scripts["cjk"]
        if code == "latn":
            return scripts["latin"]
        return False
    return scripts["cjk"] or scripts["latin"]


def _renders(u: Usage, scripts: Dict[str, bool]) -> bool:
    """Would this typeface reach the screen? A run does. A default does only if asked."""
    if u.direct:
        return True
    return any(_slot_renders(s, scripts) for s in u.slots)


def audit(path: Path) -> List[Finding]:
    usage, embedded, scripts = collect_typefaces(path)
    by_kind = {tf: u.kinds for tf, u in usage.items()}
    hits: List[Tuple[str, str, str, int]] = []  # (typeface, platform, note, count)
    for tf, u in usage.items():
        key = tf.lower()
        if key in embedded:
            continue
        if not _renders(u, scripts):
            continue
        n = u.direct + u.inherited
        if key in MACOS_ONLY:
            hits.append((tf, "macOS-only", MACOS_ONLY[key], n))
        elif key in WINDOWS_ONLY:
            hits.append((tf, "Windows-only", WINDOWS_ONLY[key], n))
    if not hits:
        return []

    # Loudest first: a body font named a thousand times is a different problem from a stray
    # monospace in three code runs, and the report should not make them look alike.
    hits.sort(key=lambda h: -h[3])
    evidence = []
    for tf, platform, note, n in hits:
        where = by_kind.get(tf, Counter())
        spread = ", ".join(f"{k}: {where[k]}" for k in _PART_ORDER if where.get(k))
        evidence.append(f"{tf} — {platform}, {n} reference(s) ({spread}). {note}.")
    evidence.append(
        "Fix by naming a font present on both platforms, or by embedding the fonts (PowerPoint: "
        "Save > Embed fonts in the file). Exporting to PDF is the other portable answer — but PDF "
        "drops embedded video, so a deck with a clip must ship its media separately.")
    return [Finding(
        DETECTOR, "FONT_NOT_PORTABLE", None,
        f"{len(hits)} typeface(s) are bundled with one operating system and are not embedded in "
        "this file. On the other platform the text stays and the metrics change: line breaks move "
        "and boxes that fitted stop fitting.",
        evidence,
    )]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("deck", type=Path)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--list-fonts", action="store_true",
                    help="print every typeface the deck names, with counts, and stop")
    a = ap.parse_args()

    if not a.deck.is_file():
        print(f"cannot read {a.deck}", file=sys.stderr)
        return 2

    try:
        if a.list_fonts:
            usage, embedded, scripts = collect_typefaces(a.deck)
            print(f"deck text uses: "
                  f"{'CJK ' if scripts['cjk'] else ''}{'Latin' if scripts['latin'] else ''}".strip()
                  or "deck text uses: (no text found)")
            for tf, u in sorted(usage.items(), key=lambda kv: -(kv[1].direct + kv[1].inherited)):
                mark = " [embedded]" if tf.lower() in embedded else ""
                if not u.direct:
                    mark += " [inherited default]" + ("" if _renders(u, scripts) else " [inert]")
                where = ", ".join(f"{k}: {u.kinds[k]}" for k in _PART_ORDER if u.kinds.get(k))
                print(f"{u.direct + u.inherited:>6}  {tf}{mark}  ({where})")
            return 0
        findings = audit(a.deck)
    except (zipfile.BadZipFile, ET.ParseError, KeyError) as exc:
        print(f"{a.deck} is not a readable .pptx ({exc})", file=sys.stderr)
        return 2

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(
            {"detector": DETECTOR, "deck": str(a.deck),
             "findings": [f.__dict__ for f in findings]},
            indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not findings:
        print("OK: every typeface this deck names is available on both platforms, or embedded.")
        return 0

    for f in findings:
        print(f"  [{f.verdict}] (deck)")
        print(f"      {f.summary}")
        for e in f.evidence:
            print(f"      - {e}")
    return 1 if a.strict else 0


if __name__ == "__main__":
    sys.exit(main())

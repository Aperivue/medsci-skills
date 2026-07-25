"""Body-prose extraction shared by the prose-rhythm detectors.

`check_aphorism_density.py` and `check_rhetorical_density.py` measure different tells — negative
definitions and short-declarative rhythm on one side, antithesis and cleft constructions on the
other — over *the same text*: the manuscript's body prose with front matter, headings, tables,
block quotes, code fences, list items, citation markers and inline markup removed. Both carried a
byte-identical copy of that extractor. Two copies of one definition is one drift away from two
detectors reporting densities over different denominators and no longer being comparable.

WHAT IS **NOT** SHARED, DELIBERATELY: sentence splitting. The two detectors genuinely differ there
and unifying them would change what they measure:

    aphorism    SENT_SPLIT_RE = (?<=[.!?])\\s+(?=[A-Z"“])          sentences: >= 2 words
    rhetorical  SENT_SPLIT_RE = (?<=[.!?])\\s+(?=["“(]?[A-Z0-9])   sentences: any non-empty

The rhetorical splitter starts a sentence at a digit or an opening parenthesis; the aphorism one
does not, and it drops one-word fragments so a run of them cannot masquerade as clipped
declaratives. Those choices belong to what each gate measures. Folding them together would silently
move every density in both detectors — a behaviour change wearing a refactor's clothes — so each
detector keeps its own splitter and its own sentence filter.

Same-directory import, like `_frontmatter`: skills are self-contained and cross-skill imports are
forbidden, so `humanize/scripts/check_sentence_variety.py` keeps its own extractor by design.

Stdlib only.
"""

from __future__ import annotations

import re

from _frontmatter import strip_frontmatter

FENCE_RE = re.compile(r"```.*?```", re.S)

CITE_RE = re.compile(r"\[@[^\]]+\]|\[\d+(?:[,–-]\d+)*\]")

INLINE_RE = re.compile(r"[*_`]")


def body_text(md: str) -> str:
    """Body prose only: no headings, tables, block quotes, code, citations, markup."""
    md = strip_frontmatter(md)   # a `status:`/build-note YAML block is not prose rhythm
    md = FENCE_RE.sub(" ", md)
    keep = []
    for line in md.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", "|", ">", "!", "---")):
            continue
        if re.match(r"^\s*(?:[-*+]|\d+\.)\s", line):   # list items are not prose rhythm
            continue
        keep.append(s)
    txt = " ".join(keep)
    txt = CITE_RE.sub("", txt)
    txt = INLINE_RE.sub("", txt)
    return re.sub(r"\s+", " ", txt).strip()


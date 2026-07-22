"""Strip a leading YAML front-matter block off a manuscript before prose analysis.

Several `--manuscript` detectors in this skill roll their own body extractor that filters
lines starting with `#`, `|`, `>`, `!`, list markers and code fences. A `---`-fenced YAML
front-matter block matches none of those, so the `status:`, changelog and build-note lines
that projects keep at the top of a pandoc manuscript were read as body prose. Two shipped
detectors fired on it on a live submission: `check_citation_order` reported floats "cited out
of order" from a `status:` block narrating a display-item renumber, and `check_aphorism_density`
listed build notes among the manuscript's "very short declaratives".

`strip_frontmatter` removes exactly the pandoc/YAML front-matter block: an opening `---` fence
on the FIRST line and its matching closing `---` fence. If the first line is not a fence, or the
block is never closed, the whole text is returned unchanged (a lone `---` in the body — a
horizontal rule or a setext underline — is never mistaken for front matter). Same fence semantics
as `sync-submission/scripts/_yaml_frontmatter.py`; kept independent because skills are
self-contained and cross-skill imports are forbidden.

Private helper (leading underscore) so the detector-catalog glob (`check_*` / `detect_*` /
`derive_*` / `verify_refs`) never counts it. Consumers run with their own directory on
sys.path[0] (invoked as `python3 .../scripts/<name>.py`), so a sibling `from _frontmatter import
strip_frontmatter` resolves wherever the skill is installed or vendored.
"""
from __future__ import annotations

import re

_FENCE_RE = re.compile(r"^---\s*$")


def strip_frontmatter(text: str) -> str:
    """Return ``text`` with a leading ``---``-fenced YAML front-matter block removed.

    Returns ``text`` unchanged when there is no opening fence on the first line or the
    block is never closed. The trailing newline layout of the body is preserved so
    character offsets after the front matter shift by a fixed amount only.
    """
    lines = text.splitlines(keepends=True)
    if not lines or not _FENCE_RE.match(lines[0].rstrip("\r\n")):
        return text
    for i in range(1, len(lines)):
        if _FENCE_RE.match(lines[i].rstrip("\r\n")):
            return "".join(lines[i + 1:])
    # Opening fence but no closing fence — not front matter; leave the text intact.
    return text

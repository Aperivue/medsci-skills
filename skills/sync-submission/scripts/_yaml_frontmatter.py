"""Shared YAML front-matter splitter for sync-submission scripts.

Both `check_wordcount_cap.py` and `cover_letter_drift_check.py` need to peel the
`---`-fenced YAML front matter off a manuscript before counting body words. The
two had drifted (one returned just the body as a list, the other returned a
(yaml, body) tuple, with subtly different unclosed-fence handling) despite a
"keep in sync" intent. This is the single canonical implementation, imported by
both. It is a private helper (leading underscore) so the detector-catalog glob
(`check_*` / `detect_*` / `derive_*` / `verify_refs`) never counts it.

Self-contained within this skill's scripts/ dir: both consumers run with their
own directory on sys.path[0] (invoked as `python3 .../scripts/<name>.py`), so a
sibling import resolves wherever the skill is installed/vendored.
"""
from __future__ import annotations

import re

YAML_FENCE_RE = re.compile(r"^---\s*$")


def split_yaml_front_matter(lines: list[str]) -> tuple[list[str], list[str]]:
    """Split ``lines`` into (yaml_lines, body_lines) on the first two ``---`` fences.

    If there is no opening fence, or the front matter is never closed, the whole
    input is treated as body and ``([], lines)`` is returned. Callers that only
    need the body can discard the first element: ``_, body = split_yaml_front_matter(lines)``.
    """
    if not lines or not YAML_FENCE_RE.match(lines[0].rstrip()):
        return [], lines
    for i, line in enumerate(lines[1:], start=1):
        if YAML_FENCE_RE.match(line.rstrip()):
            return lines[1:i], lines[i + 1:]
    # Unclosed front matter — treat as no front matter.
    return [], lines

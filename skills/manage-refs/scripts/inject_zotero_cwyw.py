#!/usr/bin/env python3
"""inject_zotero_cwyw.py — Inject native Zotero CWYW field codes into a .docx.

Wraps the vendored ``_vendor_citation_writer.insert_citations`` and patches its
``zotero_to_csl_json`` to use Zotero's native ``?format=csljson`` endpoint, so
webpage / report / non-journal items map correctly (the upstream
_ITEM_TYPE_MAP fallback to ``"article"`` silently drops URL/accessDate fields).

Workflow:
  1. Document body must already use pandoc-style ``[@KEY]`` markers (use
     ``md_marker_convert.py`` to convert ``[N]`` first).
  2. Local Zotero must be running with the connector API at
     ``http://localhost:23119/api/users/<USER_ID>/items/<KEY>``.
  3. Output .docx contains live ``ADDIN ZOTERO_ITEM`` / ``ADDIN ZOTERO_BIBL``
     field codes. Open in Word → Zotero tab → **Add/Edit Bibliography** once
     to populate the bibliography (see Known limitation #1).

Usage:
  inject_zotero_cwyw.py --input markers.docx --output cwyw.docx \\
    --user-id 16613550 --keys ABC123,DEF456,...
  inject_zotero_cwyw.py --input markers.docx --output cwyw.docx \\
    --user-id 16613550 --keys-from keys.txt

Known limitations (carry-over from RFA-Adjunct validation, 2026-05-01):
  - First build: BIBL field is an empty stub. User must run "Add/Edit
    Bibliography" once in Word; subsequent Refresh keeps it in sync.
  - Surgical post-build patches (regex on ``[N]``) are unsafe — Zotero
    rendered superscripts can collide. For ref additions, regenerate the
    whole .docx from the markdown SSOT.

Anti-Hallucination:
  - Item metadata is fetched live from Zotero — never invented.
  - On any HTTP failure for any key, abort with a non-zero exit so partial
    builds with missing items never reach the user.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import _vendor_citation_writer as _cw  # noqa: E402
from _vendor_citation_writer import insert_citations  # noqa: E402


def _native_zotero_to_csl_json(item_data: dict, user_id: str) -> dict:
    """Replacement for upstream ``zotero_to_csl_json`` — fetches Zotero's own
    CSL-JSON serialization which handles webpage / report / etc. correctly.
    """
    key = item_data.get("key", "")
    if not key:
        raise ValueError("item_data missing 'key' — cannot fetch CSL-JSON.")
    url = f"http://localhost:23119/api/users/{user_id}/items/{key}?format=csljson"
    with urllib.request.urlopen(url, timeout=10) as r:
        payload = json.loads(r.read())
    csl = payload[0] if isinstance(payload, list) else payload
    csl.pop("citation-key", None)
    csl["id"] = int(hashlib.md5(key.encode()).hexdigest()[:8], 16)
    csl["_uris"] = [f"http://zotero.org/users/{user_id}/items/{key}"]
    return csl


# Patch the vendored module's symbol — insert_citations() resolves via global
# lookup so the patched function is used.
_cw.zotero_to_csl_json = _native_zotero_to_csl_json


def fetch_item(user_id: str, key: str) -> dict:
    url = f"http://localhost:23119/api/users/{user_id}/items/{key}"
    with urllib.request.urlopen(url, timeout=10) as r:
        full = json.loads(r.read())
    return full["data"]


def load_keys(args) -> list[str]:
    if args.keys:
        return [k.strip() for k in args.keys.split(",") if k.strip()]
    if args.keys_from:
        text = Path(args.keys_from).read_text(encoding="utf-8")
        return [line.strip() for line in text.splitlines()
                if line.strip() and not line.strip().startswith("#")]
    sys.exit("ERROR: provide --keys or --keys-from.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True, type=Path,
                    help=".docx with [@KEY] markers in body text.")
    ap.add_argument("--output", required=True, type=Path,
                    help="Output .docx with CWYW field codes.")
    ap.add_argument("--user-id", required=True,
                    help="Zotero numeric user ID (see Settings → Sync).")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--keys", help="Comma-separated Zotero item keys.")
    src.add_argument("--keys-from", help="File with one Zotero key per line.")
    args = ap.parse_args()

    if not args.input.exists():
        sys.exit(f"ERROR: input not found: {args.input}")

    keys = load_keys(args)
    if not keys:
        sys.exit("ERROR: no keys supplied.")

    print(f"[inject_cwyw] fetching {len(keys)} items from Zotero...", file=sys.stderr)
    item_data: dict[str, dict] = {}
    for k in keys:
        try:
            item_data[k] = fetch_item(args.user_id, k)
        except Exception as e:
            sys.exit(f"ERROR: Zotero fetch failed for key {k}: {e}")

    saved, n_cited = insert_citations(
        document_path=str(args.input),
        item_data=item_data,
        user_id=args.user_id,
        output_path=str(args.output),
    )
    print(f"[inject_cwyw] {n_cited} unique citations → {saved}", file=sys.stderr)
    print(f"[inject_cwyw] next: open {args.output} in Word → Zotero tab → "
          f"Add/Edit Bibliography (first build only) or Refresh.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

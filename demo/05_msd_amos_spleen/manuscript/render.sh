#!/usr/bin/env bash
# Render the write-up to DOCX, then normalise the one field that leaks a home directory.
#
# /verify-refs records the absolute path it was handed into qc/reference_audit.json. On a
# maintainer's machine that path contains a username, and the repository's PII gate rejects it —
# correctly. Scrubbing it by hand after every render is a step that gets forgotten, and it was
# forgotten twice. Binding the two together makes the leak unable to survive a render.
set -euo pipefail
cd "$(dirname "$0")/.."
MR="../../skills/manage-refs"

bash "$MR/scripts/render_pandoc.sh" -j "${1:-radiology}" \
    -i manuscript/writeup.md -b manuscript/_src/refs.bib -o manuscript/manuscript_final.docx

python3 - <<'PY'
import json, pathlib
p = pathlib.Path("qc/reference_audit.json")
d = json.loads(p.read_text())
if d.get("source", "").startswith("/"):
    d["source"] = "manuscript/_src/refs.bib"
    d["_note"] = ("Path normalised to repository-relative by manuscript/render.sh. verify-refs "
                  "records the absolute path it was handed, which embeds a home directory.")
    p.write_text(json.dumps(d, indent=2) + "\n")
    print("normalised qc/reference_audit.json source path")
else:
    print("qc/reference_audit.json source already relative")
PY

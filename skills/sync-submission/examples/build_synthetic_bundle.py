#!/usr/bin/env python3
"""Original synthetic bundle demo; creates files only in a new/empty directory.

Usage: python build_synthetic_bundle.py --project-root /tmp/submission-demo [--pdf]
Requires pandoc; --pdf also requires render-pdf-doc and its XeLaTeX dependencies.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
from sync_submission import sha256_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--pdf", action="store_true")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    if root.exists() and any(root.iterdir()):
        parser.error("Demo requires a new or empty directory")
    root.mkdir(parents=True, exist_ok=True)
    for directory in ("manuscript", "build"):
        (root / directory).mkdir()
    sources = {
        "manuscript/manuscript.md": "# Synthetic study\n\nThis is original demonstration text, not research evidence.\n\n"
        "| Group | Count |\n|---|---:|\n| A | 12 |\n| B | 18 |\n\nTotal: 30 synthetic observations.\n",
        "manuscript/supplement.md": "# Synthetic supplement\n\nGroup A: 12. Group B: 18. Total: 30.\n",
        "manuscript/cover_letter.md": "Dear Editor,\n\nThis is a synthetic packaging demonstration.\n",
    }
    for name, content in sources.items():
        (root / name).write_text(content, encoding="utf-8")
    before = {name: sha256_file(root / name) for name in sources}
    version = subprocess.run(["pandoc", "--version"], check=True, capture_output=True, text=True).stdout.splitlines()[0]
    entries = []
    for name, stem, role in (("manuscript/manuscript.md", "final", "manuscript"),
                             ("manuscript/supplement.md", "supplement", "supplement"),
                             ("manuscript/cover_letter.md", "cover_letter", "cover_letter")):
        formats = ["docx"] + (["pdf"] if args.pdf else [])
        for extension in formats:
            output = f"build/{stem}.{extension}"
            target = f"{role}/{stem}.{extension}"
            command = ["pandoc", name, "-o", output]
            recorded = list(command)
            if extension == "pdf":
                renderer = SKILL.parent / "render-pdf-doc/scripts/render_pdf.sh"
                command = ["bash", str(renderer), "-i", name, "-o", output]
                recorded = ["render-pdf-doc/scripts/render_pdf.sh", "-i", name, "-o", output]
            subprocess.run(command, cwd=root, check=True)
            entries.append({"id": f"{stem}-{extension}", "role": f"{role}_{extension}",
                            "source": output, "target": target,
                            "derived_from": [{"path": name, "sha256": before[name]}],
                            "transformation": {"kind": "rendered", "command": recorded, "pandoc_version": version},
                            "rights": {"status": "original", "changes": "Rendered original synthetic example"}})
    if before != {name: sha256_file(root / name) for name in sources}:
        raise RuntimeError("Sources changed during rendering")
    (root / "bundle.json").write_text(json.dumps({"schema_version": 1, "artifacts": entries}, indent=2) + "\n")
    subprocess.run([sys.executable, str(SKILL / "scripts/sync_submission.py"), "build",
                    "--project-root", str(root), "--journal", "example", "--bundle-spec", "bundle.json"], check=True)
    print("Synthetic bundle built. Visual, semantic, metadata and preflight checks remain separate.")


if __name__ == "__main__":
    main()

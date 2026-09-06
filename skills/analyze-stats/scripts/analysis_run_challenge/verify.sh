#!/usr/bin/env bash
# Standalone original synthetic normal and stale-result controls.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 - "$HERE/.." <<'PY'
import json
from pathlib import Path
import subprocess
import sys
import tempfile

scripts = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory() as temp:
    project = Path(temp) / "project"
    demo = subprocess.run([sys.executable, str(scripts / "demo_analysis_run.py"),
                           "--out", str(project)], capture_output=True, text=True, check=True)
    result = json.loads(demo.stdout)
    assert result["synthetic_counts"] == {"TP": 8, "FP": 3, "TN": 7, "FN": 2}
    assert result["comparison"]["status"] == "compared"
    assert result["comparison"]["recorded_numeric_results_equal"]
    runner = [sys.executable, str(scripts / "run_analysis.py")]
    audit = runner + ["audit", "--project-root", str(project), "--out", "runs/first"]
    assert subprocess.run(audit, capture_output=True).returncode == 0
    manifest = project / "runs/first/_analysis_outputs.md"
    original = manifest.read_bytes()
    with (project / "data.csv").open("a") as stream:
        stream.write("synthetic_changed,0,1\n")
    for _ in range(2):
        check = subprocess.run(audit, capture_output=True, text=True)
        assert check.returncode == 1
        assert "input:data" in json.loads(check.stdout)["changes"]
        assert manifest.read_bytes() == original
print("PASS: synthetic calculation, repeat, stale-input detection and read-only audit")
PY

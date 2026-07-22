#!/usr/bin/env bash
# Local mirror of the CI `validate` job — see scripts/run_ci_mirror.py for what it does.
# Run before every push; if green, CI's validate job will be too.
exec python3 "$(cd "$(dirname "$0")" && pwd)/run_ci_mirror.py" "$@"

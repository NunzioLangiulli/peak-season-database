#!/bin/sh
# Peak Season Admin Studio: opens in the browser at http://localhost:8765 (or the next free port)
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then exec python3 studio.py; else exec python studio.py; fi

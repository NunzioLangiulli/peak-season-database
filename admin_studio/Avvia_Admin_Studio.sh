#!/bin/sh
# Peak Season Admin Studio: si apre nel browser su http://localhost:8765 (o la porta libera successiva)
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then exec python3 studio.py; else exec python studio.py; fi

#!/bin/sh
# Source this file to export the repo's .env variables into the current shell.
#
# Example:
#   source ./scripts/env/internet-search.env.sh

if [ ! -f "./.env" ]; then
    return 0 2>/dev/null || exit 0
fi

if command -v python3 >/dev/null 2>&1; then
    eval "$(
        python3 - <<'PY'
from dotenv import dotenv_values
import os
from shlex import quote

existing = set(os.environ)
for key, value in dotenv_values(".env").items():
    if value is None or key in existing:
        continue
    print(f"export {key}={quote(value)}")
PY
    )"
    return 0 2>/dev/null || exit 0
fi

set -a
. "./.env"
set +a

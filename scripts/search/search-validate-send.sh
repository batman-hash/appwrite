#!/bin/bash
# Search internet emails, validate/store them in a separate DB, and optionally send the validated batch.
#
# This wrapper auto-loads the repo .env file, clears stale runtime cache by default,
# and forwards every flag to the shared devnavigator CLI.

set -euo pipefail
umask 077

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

if [ -f "./.env" ]; then
    . "./scripts/env/internet-search.env.sh"
fi

run_threshold_guard() {
    if [ "${AUTO_SYSTEM_THRESHOLD_GUARD:-1}" = "0" ] || [ "${AUTO_SYSTEM_THRESHOLD_GUARD:-1}" = "false" ] || [ "${AUTO_SYSTEM_THRESHOLD_GUARD:-1}" = "no" ]; then
        return 0
    fi

    python3 "./search_threshold_guard.py" --root "$PROJECT_ROOT" --warn-only
}

run_threshold_guard

if [ "${AUTO_CLEAR_SEARCH_CACHE:-1}" = "1" ] || [ "${AUTO_CLEAR_SEARCH_CACHE:-1}" = "true" ] || [ "${AUTO_CLEAR_SEARCH_CACHE:-1}" = "yes" ]; then
    bash "./scripts/search/clear-search-cache.sh"
fi

python3 devnavigator.py search-deliver "$@"

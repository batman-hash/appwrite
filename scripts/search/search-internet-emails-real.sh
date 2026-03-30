#!/bin/bash
# Real-mode internet email search helper.
# This wrapper forces validated results into the separate internet-search DB
# while reusing the guarded shared search flow.

set -euo pipefail
umask 077

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

export INTERNET_SEARCH_STORE=1
export INTERNET_SEARCH_DB_PATH="${INTERNET_SEARCH_DB_PATH:-./database/internet_search.db}"

exec bash "./scripts/search/search-internet-emails.sh" "$@"

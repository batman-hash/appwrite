#!/bin/bash
# Print all stored search emails, then run a worldwide refresh search.
# This keeps the current database visible before adding new results.

set -euo pipefail
umask 077

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

if [ -f "./.env" ]; then
    . "./scripts/env/internet-search.env.sh"
fi

if [ -z "${1:-}" ] || [ -z "${2:-}" ]; then
    echo "Usage: $0 <title> <keywords> [remote] [preview_limit] [max_results]"
    echo "Example: $0 \"frontend developer\" \"react,javascript\" remote 1000 1000"
    exit 1
fi

TITLE="$1"
KEYWORDS="$2"
REMOTE_INPUT="${3:-remote}"
PREVIEW_LIMIT="${4:-1000}"
MAX_RESULTS="${5:-1000}"

echo "📬 Current stored emails:"
python3 devnavigator.py list-search-emails --db-path ./database/internet_search.db --emails-only

echo ""
echo "🌍 Running worldwide refresh search..."
INTERNET_SEARCH_MAX_RESULTS="$MAX_RESULTS" \
exec bash "./scripts/search/search-internet-emails-world.sh" "$TITLE" "$KEYWORDS" "$REMOTE_INPUT" "$PREVIEW_LIMIT"

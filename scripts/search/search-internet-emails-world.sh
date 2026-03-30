#!/bin/bash
# Worldwide internet email search helper.
# Forces the search into global mode and stores validated results in the
# separate internet-search database through the real-mode wrapper.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

if [ -z "${1:-}" ] || [ -z "${2:-}" ]; then
    echo "Usage: $0 <title> <keywords> [remote] [preview_limit]"
    echo "Example: $0 \"frontend developer\" \"react,javascript,remote\" remote 10"
    exit 1
fi

TITLE="$1"
KEYWORDS="$2"
REMOTE_INPUT="${3:-remote}"
PREVIEW_LIMIT="${4:-10}"

exec bash "./scripts/search/search-internet-emails-real.sh" "$TITLE" "$KEYWORDS" all "$REMOTE_INPUT" "$PREVIEW_LIMIT"

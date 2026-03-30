#!/bin/bash
# Crawler-style alias for the internet email search pipeline.
# This keeps the shell entrypoint short while the actual crawl logic stays in Python.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

exec bash "./scripts/search/search-internet-emails.sh" "$@"

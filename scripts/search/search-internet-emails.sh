#!/bin/bash
# Internet email search helper
# Usage: ./search-internet-emails.sh "<title>" "<keywords>" [country|all|world] [remote] [preview_limit]
# Optional env:
#   EXTRACT_PROXY_URL=http://REAL_PROXY_HOST:8080
#   INTERNET_SEARCH_STORE=1
#   INTERNET_SEARCH_DB_PATH=./database/internet_search.db
#   INTERNET_SEARCH_EXPORT_PATH=./exports/internet_search_results.csv

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

RUNTIME_DIR="${INTERNET_SEARCH_RUNTIME_DIR:-./runtime/internet-search}"
LOCK_FILE="${RUNTIME_DIR}/search.lock"
PID_FILE="${RUNTIME_DIR}/search.pid"
STATE_FILE="${RUNTIME_DIR}/search.state"
LAST_COMMAND_FILE="${RUNTIME_DIR}/last-command.txt"
mkdir -p "${RUNTIME_DIR}"

exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
    echo "❌ Another internet search process is already running."
    echo "   Check: ${STATE_FILE}"
    exit 1
fi

RUN_STATUS="running"

cleanup() {
    exit_code=$?
    finished_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    if [ "${RUN_STATUS}" = "running" ]; then
        if [ "${exit_code}" -eq 0 ]; then
            RUN_STATUS="completed"
        else
            RUN_STATUS="failed"
        fi
    fi

    {
        echo "status=${RUN_STATUS}"
        echo "pid=$$"
        echo "finished_at=${finished_at}"
        echo "exit_code=${exit_code}"
    } >> "${STATE_FILE}"

    rm -f "${PID_FILE}"
}

trap 'RUN_STATUS=interrupted' INT TERM
trap cleanup EXIT

if [ -z "${1:-}" ] || [ -z "${2:-}" ]; then
    echo "Usage: $0 <title> <keywords> [country|all|world] [remote] [preview_limit]"
    echo "Example: $0 \"frontend developer\" \"react,javascript,remote\" all remote 10"
    echo "Default behavior: preview internet results only, without writing to your main local database."
    exit 1
fi

TITLE="$1"
KEYWORDS="$2"
COUNTRY="${3:-}"
REMOTE_INPUT="${4:-}"
PREVIEW_LIMIT="${5:-10}"
STORE_RESULTS="${INTERNET_SEARCH_STORE:-0}"
TARGET_DB_PATH="${INTERNET_SEARCH_DB_PATH:-}"
EXPORT_PATH="${INTERNET_SEARCH_EXPORT_PATH:-}"

{
    echo "status=running"
    echo "pid=$$"
    echo "started_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "runtime_dir=${RUNTIME_DIR}"
    echo "target_db=${TARGET_DB_PATH:-preview-only}"
} > "${STATE_FILE}"
printf '%s\n' "$$" > "${PID_FILE}"

CMD=(python3 devnavigator.py crawl-emails --title "$TITLE" --keywords "$KEYWORDS" --show-limit "$PREVIEW_LIMIT")

if [ -n "$COUNTRY" ] && [ "$COUNTRY" != "-" ]; then
    case "${COUNTRY,,}" in
        all|world|global|any|anywhere|worldwide|\*)
            ;;
        *)
            CMD+=(--country "$COUNTRY")
            ;;
    esac
fi

if [ "$REMOTE_INPUT" = "remote" ] || [ "$REMOTE_INPUT" = "--remote" ] || [ "$REMOTE_INPUT" = "yes" ]; then
    CMD+=(--remote)
fi

if [ -n "${EXTRACT_PROXY_URL:-}" ]; then
    CMD+=(--proxy-url "$EXTRACT_PROXY_URL")
fi

if [ "$STORE_RESULTS" = "1" ] || [ "$STORE_RESULTS" = "true" ] || [ "$STORE_RESULTS" = "yes" ]; then
    CMD+=(--store)
fi

if [ -n "$TARGET_DB_PATH" ]; then
    CMD+=(--db-path "$TARGET_DB_PATH")
fi

if [ -n "$EXPORT_PATH" ]; then
    CMD+=(--export-path "$EXPORT_PATH")
fi

printf '%q ' "${CMD[@]}" > "${LAST_COMMAND_FILE}"
printf '\n' >> "${LAST_COMMAND_FILE}"

echo "🌐 Searching internet sources for emails..."
"${CMD[@]}"

echo ""
echo "✅ Search complete!"
if [ "$STORE_RESULTS" = "1" ] || [ "$STORE_RESULTS" = "true" ] || [ "$STORE_RESULTS" = "yes" ]; then
    DATABASE_PATH="${TARGET_DB_PATH:-${DATABASE_PATH:-./database/devnav.db}}" python3 devnavigator.py stats
else
    echo "ℹ️  Local database stats skipped because internet extraction ran in preview-only mode."
fi

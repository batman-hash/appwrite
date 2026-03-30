#!/bin/bash
# Docker wrapper for internet email search
# Usage: ./docker-search-internet-emails.sh "<title>" "<keywords>" [country|all|world] [remote] [preview_limit]
# Optional env:
#   DEVNAVIGATOR_IMAGE=devnavigator
#   EXTRACT_PROXY_URL=http://REAL_PROXY_HOST:8080
#   EXTRACT_HTTP_PROXY=http://REAL_HTTP_PROXY:8080
#   EXTRACT_HTTPS_PROXY=http://REAL_HTTPS_PROXY:8443
#   EXTRACT_NO_PROXY=localhost,127.0.0.1
#   INTERNET_SEARCH_STORE=1
#   INTERNET_SEARCH_DB_PATH=/workspace/database/internet_search.db
#   INTERNET_SEARCH_EXPORT_PATH=/workspace/exports/internet_search_results.csv
#   HUNTER_API_KEY=...
#   APOLLO_API_KEY=...

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

RUNTIME_DIR="${INTERNET_SEARCH_RUNTIME_DIR:-./runtime/internet-search-docker}"
LOCK_FILE="${RUNTIME_DIR}/search.lock"
PID_FILE="${RUNTIME_DIR}/search.pid"
STATE_FILE="${RUNTIME_DIR}/search.state"
LAST_COMMAND_FILE="${RUNTIME_DIR}/last-command.txt"
mkdir -p "${RUNTIME_DIR}"

exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
    echo "❌ Another Docker internet search process is already running."
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
IMAGE_NAME="${DEVNAVIGATOR_IMAGE:-devnavigator}"

{
    echo "status=running"
    echo "pid=$$"
    echo "started_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "runtime_dir=${RUNTIME_DIR}"
    echo "target_db=${TARGET_DB_PATH:-preview-only}"
    echo "image=${IMAGE_NAME}"
} > "${STATE_FILE}"
printf '%s\n' "$$" > "${PID_FILE}"

CMD=(
    docker run --rm -it
    -v "$PWD:/workspace"
)

for env_name in EXTRACT_PROXY_URL EXTRACT_HTTP_PROXY EXTRACT_HTTPS_PROXY EXTRACT_NO_PROXY HUNTER_API_KEY APOLLO_API_KEY; do
    if [ -n "${!env_name:-}" ]; then
        CMD+=(-e "${env_name}=${!env_name}")
    fi
done

CMD+=(
    "$IMAGE_NAME"
    crawl-emails
    --title "$TITLE"
    --keywords "$KEYWORDS"
    --show-limit "$PREVIEW_LIMIT"
)

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

echo "🐳 Searching internet sources for emails in Docker..."
"${CMD[@]}"

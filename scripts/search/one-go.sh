#!/bin/bash
# Build the C++ sender, ensure the database exists, then import and preview/send
# only the newly imported approved contacts from one file.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

FILE=""
SOURCE="one_go"
TEMPLATE=""
LIMIT=""
DO_SEND=0
AUTO_YES=0
SKIP_BUILD=0
SKIP_INIT_DB=0

usage() {
    cat <<'EOF'
Usage:
  ./one-go.sh --file contacts.csv [options]

Options:
  --file PATH         Contacts file to import (required)
  --source NAME       Source label stored in the database (default: one_go)
  --template NAME     Template used for the send flow
  --limit N           Maximum number of newly imported contacts to preview/send
  --send              Actually send emails. Without this flag, the script runs in dry-run mode
  --yes               Skip the final confirmation prompt when used with --send
  --skip-build        Skip rebuilding the C++ sender
  --skip-init-db      Skip the database initialization step
  -h, --help          Show this help

Examples:
  ./one-go.sh --file sample_emails.csv
  ./one-go.sh --file sample_emails.csv --template earning_opportunity --limit 5
  ./one-go.sh --file sample_emails.csv --template earning_opportunity --limit 5 --send
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --file)
            FILE="${2:-}"
            shift 2
            ;;
        --source)
            SOURCE="${2:-}"
            shift 2
            ;;
        --template)
            TEMPLATE="${2:-}"
            shift 2
            ;;
        --limit)
            LIMIT="${2:-}"
            shift 2
            ;;
        --send)
            DO_SEND=1
            shift
            ;;
        --yes)
            AUTO_YES=1
            shift
            ;;
        --skip-build)
            SKIP_BUILD=1
            shift
            ;;
        --skip-init-db)
            SKIP_INIT_DB=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo ""
            usage
            exit 1
            ;;
    esac
done

if [[ -z "$FILE" ]]; then
    echo "Missing required option: --file"
    echo ""
    usage
    exit 1
fi

cd "$PROJECT_ROOT"

if [[ ! -f "$FILE" ]]; then
    echo "Contacts file not found: $FILE"
    exit 1
fi

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  DEVNAVIGATOR ONE GO                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [[ "$SKIP_BUILD" -eq 0 ]]; then
    echo "Step 1: Building C++ sender..."
    bash ./scripts/build/build.sh
    echo ""
fi

if [[ "$SKIP_INIT_DB" -eq 0 ]]; then
    echo "Step 2: Ensuring database schema..."
    python3 devnavigator.py init-db
    echo ""
fi

echo "Step 3: Importing contacts and $( [[ "$DO_SEND" -eq 1 ]] && echo "sending" || echo "previewing" ) newly imported approved contacts..."

cmd=(python3 devnavigator.py import-send-approved --file "$FILE" --source "$SOURCE")

if [[ -n "$TEMPLATE" ]]; then
    cmd+=(--template "$TEMPLATE")
fi

if [[ -n "$LIMIT" ]]; then
    cmd+=(--limit "$LIMIT")
fi

if [[ "$DO_SEND" -eq 0 ]]; then
    cmd+=(--dry-run)
fi

if [[ "$AUTO_YES" -eq 1 ]]; then
    cmd+=(--yes)
fi

printf 'Running:'
for arg in "${cmd[@]}"; do
    printf ' %q' "$arg"
done
printf '\n\n'

"${cmd[@]}"

echo ""
if [[ "$DO_SEND" -eq 0 ]]; then
    echo "Dry run complete."
    echo "Use --send to deliver real emails after reviewing the preview."
else
    echo "Send flow complete."
fi

echo ""
echo "Verification is a separate confirmation step if you need it:"
echo "  python3 devnavigator.py send-verification-email --email person@example.com --name \"Person Name\""

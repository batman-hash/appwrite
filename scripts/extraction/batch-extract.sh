#!/bin/bash
# Batch Email Extraction Script
# Extract contacts through the shared DevNavigator CLI flow.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

if [ -f "./.env" ]; then
  . "./scripts/env/internet-search.env.sh"
fi

if [ "${AUTO_SYSTEM_THRESHOLD_GUARD:-1}" != "0" ] && [ "${AUTO_SYSTEM_THRESHOLD_GUARD:-1}" != "false" ] && [ "${AUTO_SYSTEM_THRESHOLD_GUARD:-1}" != "no" ]; then
  python3 "./search_threshold_guard.py" --root "$PROJECT_ROOT" --warn-only
fi

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                  🚀 BATCH EMAIL EXTRACTION SCRIPT                         ║"
echo "║           Extract 500-1000+ emails from GitHub automatically              ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

get_total_count() {
  if [ ! -f "database/devnav.db" ]; then
    echo "0"
    return
  fi

  sqlite3 database/devnav.db "SELECT COUNT(*) FROM contacts WHERE archived = 0;"
}

run_search_auto() {
  local title="$1"
  local keywords="$2"

  if ! python3 devnavigator.py search-auto \
    --title "$title" \
    --keywords "$keywords" \
    --store \
    --show-limit 0 > /dev/null 2>&1; then
    echo "    ✗ Search failed for: $title"
    return 1
  fi
}

run_search_filtered() {
  local label="$1"
  shift

  if ! python3 devnavigator.py search-filtered --store "$@" > /dev/null 2>&1; then
    echo "    ✗ Filtered search failed for: $label"
    return 1
  fi
}

# Initialize database
echo "Step 1: Initializing database..."
python3 devnavigator.py init-db > /dev/null 2>&1

# Show starting count
starting_count="$(get_total_count)"
echo "Starting emails: $starting_count"
echo ""

# Run multiple searches
echo "Step 2: Running GitHub searches..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

queries=(
  "junior developer remote|junior,developer,remote"
  "freelance javascript developer|freelance,javascript,developer"
  "python developer for hire|python,developer,for hire"
  "react developer available|react,developer,available"
  "node js developer freelance|node,js,developer,freelance"
  "frontend engineer remote|frontend,engineer,remote"
  "backend developer hiring|backend,developer,hiring"
  "full stack developer available|full stack,developer,available"
  "looking for project|looking for project,developer,available"
  "open to opportunities|open to opportunities,developer,available"
  "web developer freelance|web,developer,freelance"
  "typescript developer remote|typescript,developer,remote"
)

for i in "${!queries[@]}"; do
  IFS='|' read -r title keywords <<< "${queries[$i]}"
  num=$((i + 1))
  echo "[$num/${#queries[@]}] Searching: $title"
  run_search_auto "$title" "$keywords"
  sleep 1
done

echo ""
echo "Step 3: Running filtered searches..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "[1/3] Searching: Junior + Frontend + Remote"
run_search_filtered "Junior + Frontend + Remote" \
  --title "junior frontend developer" \
  --keywords "junior,frontend,react,javascript,remote" \
  --remote

echo "[2/3] Searching: Job Seekers"
run_search_filtered "Job Seekers" \
  --title "developer seeking opportunities" \
  --keywords "open to work,job seeker,available,opportunities"

echo "[3/3] Searching: Money Motivated Freelancers"
run_search_filtered "Money Motivated Freelancers" \
  --title "freelance developer" \
  --keywords "freelance,contract,for hire,remote" \
  --remote

echo ""
echo "Step 4: Extracting from sample files (if available)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "sample_emails.csv" ]; then
  echo "Found sample_emails.csv - importing..."
  if ! python3 devnavigator.py extract-emails --file sample_emails.csv --store > /dev/null 2>&1; then
    echo "    ✗ Sample file import failed"
  fi
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                        🎉 EXTRACTION COMPLETE                             ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Show final stats
echo "FINAL STATISTICS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 devnavigator.py stats
ending_count="$(get_total_count)"
echo "Added this run: $((ending_count - starting_count))"

echo ""
echo "NEXT STEPS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. View all extracted emails:"
echo "   python3 devnavigator.py queue --queue all --limit 50"
echo ""
echo "2. Export to CSV:"
echo "   python3 devnavigator.py export-contacts --output extracted_emails_export.csv --queue all"
echo ""
echo "3. Send campaigns:"
echo "   python3 send_test_emails.py send --limit 100"
echo ""
echo "4. Open GUI:"
echo "   python3 gui.py"
echo ""
echo "5. Interactive extraction:"
echo "   python3 extract.py"
echo ""

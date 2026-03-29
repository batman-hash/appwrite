#!/bin/bash
# Batch Email Extraction Script
# Extract hundreds of emails automatically with multiple searches

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                  🚀 BATCH EMAIL EXTRACTION SCRIPT                         ║"
echo "║           Extract 500-1000+ emails from GitHub automatically              ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Initialize database
echo "Step 1: Initializing database..."
python3 devnavigator.py init-db > /dev/null 2>&1

# Show starting count
echo "Starting emails: $(python3 extract.py stats 2>&1 | grep "Total" | awk '{print $3}')"
echo ""

# Run multiple searches
echo "Step 2: Running GitHub searches..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

queries=(
  "junior developer remote"
  "freelance javascript developer"
  "python developer for hire"
  "react developer available"
  "node js developer freelance"
  "frontend engineer remote"
  "backend developer hiring"
  "full stack developer available"
  "looking for project"
  "open to opportunities"
  "web developer freelance"
  "typescript developer remote"
)

for i in "${!queries[@]}"; do
  query="${queries[$i]}"
  num=$((i + 1))
  echo "[$num/${#queries[@]}] Searching: $query"
  python3 devnavigator.py search-auto --query "$query" > /dev/null 2>&1
  sleep 1
done

echo ""
echo "Step 3: Running filtered searches..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "[1/3] Searching: Junior + Frontend + Remote"
python3 devnavigator.py search-filtered --junior 70 --frontend 60 --remote 50 > /dev/null 2>&1

echo "[2/3] Searching: Job Seekers"
python3 devnavigator.py search-filtered --job_seeker 80 > /dev/null 2>&1

echo "[3/3] Searching: Money Motivated Freelancers"
python3 devnavigator.py search-filtered --money_motivated 75 --remote 60 > /dev/null 2>&1

echo ""
echo "Step 4: Extracting from sample files (if available)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "sample_emails.csv" ]; then
  echo "Found sample_emails.csv - importing..."
  python3 devnavigator.py extract-emails --file sample_emails.csv --store > /dev/null 2>&1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                        🎉 EXTRACTION COMPLETE                             ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Show final stats
echo "FINAL STATISTICS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 extract.py stats

echo ""
echo "NEXT STEPS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. View all extracted emails:"
echo "   python3 extract.py view"
echo ""
echo "2. Export to CSV:"
echo "   python3 extract.py export"
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

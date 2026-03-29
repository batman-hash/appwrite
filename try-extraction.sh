#!/bin/bash
# 🚀 Try Email Extraction - Interactive Demo

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🚀 EMAIL EXTRACTION - TRY IT NOW!                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Initialize database
echo "STEP 1: Initialize Database"
echo "─────────────────────────────────────────────────────────────"
echo "$ python3 devnavigator.py init-db"
echo ""
python3 devnavigator.py init-db
echo ""

# Step 2: Extract from CSV
echo "STEP 2: Extract Emails from CSV File"
echo "─────────────────────────────────────────────────────────────"
echo "$ python3 devnavigator.py extract-emails --file sample_emails.csv --store"
echo ""
python3 devnavigator.py extract-emails --file sample_emails.csv --store
echo ""

# Step 3: Show stats
echo "STEP 3: Check What Was Imported"
echo "─────────────────────────────────────────────────────────────"
echo "$ python3 devnavigator.py stats"
echo ""
python3 devnavigator.py stats
echo ""

# Step 4: Query database
echo "STEP 4: View Stored Emails in Database"
echo "─────────────────────────────────────────────────────────────"
echo "$ sqlite3 database/devnav.db \"SELECT COUNT(*) as total, email FROM contacts GROUP BY 1\""
echo ""
sqlite3 database/devnav.db "SELECT COUNT(*) as 'Total Emails' FROM contacts;"
echo ""
echo "Sample emails:"
sqlite3 database/devnav.db "SELECT email FROM contacts LIMIT 3;"
echo ""

# Step 5: Export to CSV (optional)
echo "STEP 5: Export Emails to File (Optional)"
echo "─────────────────────────────────────────────────────────────"
echo "Python code to export:"
echo ""

python3 << 'PYEOF'
import sqlite3
import csv

# Export to CSV
conn = sqlite3.connect('database/devnav.db')
cursor = conn.cursor()
cursor.execute('SELECT email FROM contacts')

with open('extracted_emails.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['email'])
    writer.writerows(cursor.fetchall())

print("✓ Exported to: extracted_emails.csv")

# Show file
import os
file_size = os.path.getsize('extracted_emails.csv')
print(f"  File size: {file_size} bytes")

# Show content
with open('extracted_emails.csv', 'r') as f:
    lines = f.readlines()
    print(f"  Total lines: {len(lines)} (1 header + {len(lines)-1} emails)")

conn.close()
PYEOF

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     ✅ EXTRACTION COMPLETE!                                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 WHAT YOU JUST DID:"
echo "   1. Initialized SQLite database"
echo "   2. Extracted 10 emails from sample_emails.csv"
echo "   3. Stored them in database/devnav.db"
echo "   4. Verified import with statistics"
echo "   5. Exported to CSV file"
echo ""
echo "📁 FILES CREATED:"
ls -lh database/devnav.db extracted_emails.csv 2>/dev/null || echo "(Check directory)"
echo ""
echo "🎯 NEXT STEPS:"
echo "   1. Try auto-search: python3 devnavigator.py search-auto --help"
echo "   2. Test filtering: python3 << 'EOF'"
echo "      from python_engine.contact_filters import ContactFilter"
echo "      f = ContactFilter()"
echo "      count, targets = f.filter_junior_developers(min_score=60)"
echo "      EOF"
echo "   3. Read guide: cat QUICK_REFERENCE.md"
echo ""

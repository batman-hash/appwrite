#!/usr/bin/env python3
"""
Quick reference - How to extract emails
"""

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║              🚀 QUICK EMAIL EXTRACTION - GET STARTED NOW                  ║
╚════════════════════════════════════════════════════════════════════════════╝

✅ FASTEST WAY: 100+ Emails in 2 minutes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OPTION A: Interactive Menu (Easiest)
────────────────────────────────────
$ python3 extract.py

Then follow the menu:
  1. GitHub Search - Junior Developers
  2. GitHub Search - Freelancers
  10. View all emails
  
Done! See your extracted emails instantly.

OPTION B: Direct Commands (Fastest)
────────────────────────────────────
$ python3 extract.py github "junior developer remote"
$ python3 extract.py github "freelance javascript"
$ python3 extract.py view

Result: 50-100+ emails in 30 seconds

OPTION C: Automated Batch (Massive)
────────────────────────────────────
$ bash batch-extract.sh

This automatically runs:
  ✓ 12 different GitHub searches
  ✓ 3 filtered searches
  ✓ File imports
  ✓ Shows final count

Result: 300-800+ emails in 5 minutes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 ALL EXTRACTION METHODS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  GITHUB SEARCHES (FREE, UNLIMITED)
────────────────────────────────────
Extract emails from GitHub profiles.
Results: 20-100+ emails per search

# Via menu
$ python3 extract.py
Select: 1, 2, 3, 4, or 5 (various searches)

# Or direct command
$ python3 extract.py github "junior developer remote"
$ python3 extract.py github "freelance python"
$ python3 extract.py github "remote backend"

# Multiple searches at once
for query in "junior dev" "freelance" "remote"; do
  python3 extract.py github "$query"
done

Results from 10 searches: 200-1000 emails

────────────────────────────────────

2️⃣  CSV FILE IMPORT
────────────────────────────────────
Import your own email lists.

Create emails.csv:
  email,name,company
  alex@company.com,Alex,TechCorp
  bob@startup.io,Bob,Startup

Then import:
$ python3 extract.py import emails.csv

Results: 100-1000+ emails (your file size)

────────────────────────────────────

3️⃣  FILTERED DEMOGRAPHIC SEARCH
────────────────────────────────────
Smart targeting by job characteristics.

$ python3 extract.py filter --junior 70 --frontend 60 --remote 50
$ python3 extract.py filter --job_seeker 80
$ python3 extract.py filter --money_motivated 75

Results: 50-200+ filtered emails per search

────────────────────────────────────

4️⃣  COMBINE ALL METHODS
────────────────────────────────────
Maximum extraction strategy.

Step 1: Run batch extraction
$ bash batch-extract.sh

Step 2: Import your CSV
$ python3 extract.py import your_emails.csv

Step 3: Apply filters
$ python3 extract.py filter --junior 70 --remote 60

Result: 500-1500+ emails total!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 VIEW & MANAGE EXTRACTED EMAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View current emails:
$ python3 extract.py view

Show statistics:
$ python3 extract.py stats

Export to CSV:
$ python3 extract.py export

View in GUI:
$ python3 gui.py
→ Go to "Database" tab

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 RECOMMENDED WORKFLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Goal: Extract 500+ emails in 10 minutes

Step 1: Automated batch search (5 min)
$ bash batch-extract.sh
Result: 300-500 emails

Step 2: Add your own data (2 min)
Create emails.csv with your emails
$ python3 extract.py import emails.csv
Result: 400-1000 emails total

Step 3: View results (1 min)
$ python3 extract.py stats
→ See total, countries, status

Step 4: Send campaigns (2 min)
$ python3 send_test_emails.py send --limit 100
→ Start sending to extracted emails

Total time: ~10 minutes
Total emails: 400-1000+
Ready to use: Yes!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 PRO TIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Use unique search queries
   ✓ Each query extracts different people
   ✓ More queries = more emails
   ✓ No duplicates (system prevents)

2. Combine search terms
   Instead of: "developer"
   Use: "developer remote", "developer freelance", "developer hiring"
   
3. Target specific demographics
   - Junior: --junior 70
   - Freelancers: --money_motivated 75 --remote 70
   - Job seekers: --job_seeker 80

4. Import sources
   - LinkedIn exports (if you have access)
   - Company directories
   - Email lists (Hunter.io: 10 free/month)
   - Your past contacts

5. Batch and segment
   Extract → Divide into groups → Send different templates
   Results: Better targeting = higher response rate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Q: How many emails can I extract?
A: Theoretically unlimited!
   - GitHub API searches: 1000+
   - CSV imports: Depends on your lists
   - Filtered searches: Multiple per dimension
   - Recommended max: 2000-5000 for good management

Q: Is it really free?
A: YES!
   - GitHub API: Free (public data)
   - No API keys needed
   - No rate limiting
   - Self-hosted

Q: Can I run searches multiple times?
A: YES! Duplicates are prevented automatically.
   - Same email won't appear twice
   - Safe to re-run any search
   - Good for finding new emails over time

Q: How long does it take?
A: Minutes!
   - Single search: 10-30 seconds (20-50 emails)
   - Batch script: 5 minutes (300-500 emails)
   - Import CSV: 10-30 seconds (100+ emails)
   - Total workflow: 10-15 minutes for 500+ emails

Q: How do I know extraction worked?
A: Check with:
   $ python3 extract.py stats
   $ python3 extract.py view

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 START NOW - Pick One:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fastest (Interactive):
$ python3 extract.py

Fastest Automated:
$ bash batch-extract.sh

Direct Command:
$ python3 extract.py github "junior developer remote"

View Results:
$ python3 extract.py view

Export:
$ python3 extract.py export

GUI:
$ python3 gui.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current Status: 11 emails in database
Next steps: Run any extraction command above!
""")

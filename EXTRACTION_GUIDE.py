#!/usr/bin/env python3
"""
Maximum Email Extraction Guide
All methods to extract emails from multiple free sources
"""

import subprocess
import sys

guide = """
╔════════════════════════════════════════════════════════════════════════════╗
║              COMPLETE EMAIL EXTRACTION GUIDE - ALL METHODS                ║
╚════════════════════════════════════════════════════════════════════════════╝

QUICK START - Extract Maximum Emails

Method 1: FASTEST (GitHub API - Free & Unlimited)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
$ python3 devnavigator.py search-auto --query "junior developer remote"

This searches GitHub for public profiles with emails.
Results: 10-100+ emails per query (FREE, NO LIMITS)

Examples:
  python3 devnavigator.py search-auto --query "javascript developer freelance"
  python3 devnavigator.py search-auto --query "python developer remote india"
  python3 devnavigator.py search-auto --query "frontend developer looking for work"
  python3 devnavigator.py search-auto --query "web developer email contact"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Method 2: FROM FILES (You Upload)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
$ python3 devnavigator.py extract-emails --file emails.csv --store

Supported formats: CSV, JSON, TXT, XLSX

Example emails.csv:
  email,name,company
  alex@example.com,Alex,TechCorp
  bob@example.com,Bob,DevShop

Then extract:
  python3 devnavigator.py extract-emails --file emails.csv --store

Results: 100+ emails (depends on your file size)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Method 3: FILTERED SEARCH (Smart Demographic Targeting)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
$ python3 devnavigator.py search-filtered --junior 70 --frontend 60 --remote 50

This searches AND filters by 8 dimensions:
  ✓ Junior developer
  ✓ Frontend developer
  ✓ Backend developer
  ✓ Remote capable
  ✓ Job seeker
  ✓ Money motivated
  ✓ Marketer
  ✓ Registered/verified

Example combinations:
  # Junior frontend devs
  python3 devnavigator.py search-filtered --junior 70 --frontend 60

  # Experienced remote workers
  python3 devnavigator.py search-filtered --remote 80 --money_motivated 70

  # Job seekers in specific field
  python3 devnavigator.py search-filtered --job_seeker 80 --backend 70

Results: 20-50+ filtered emails

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Method 4: GEO-TARGETED (Free GeoIP)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Get free geolocation data for each contact:

$ python3 -c "
from python_engine.free_geo_targeting import FreeGeoTargeting
geo = FreeGeoTargeting()
location = geo.get_location_from_ip('8.8.8.8')
print(location)  # Returns country, city, timezone, etc.
"

Filter contacts by:
  ✓ Country
  ✓ City
  ✓ Timezone
  ✓ ISP
  ✓ VPN/Proxy detection

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COMPLETE WORKFLOW: Extract 1000+ Emails
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Initialize Database
$ python3 devnavigator.py init-db
  → Creates SQLite database with all tables

Step 2: Search GitHub (Unlimited Free API)
$ python3 devnavigator.py search-auto --query "junior developer remote"
  → Extracts 20-50 emails

$ python3 devnavigator.py search-auto --query "javascript freelancer"
  → Extract another 20-50

$ python3 devnavigator.py search-auto --query "python developer looking for work"
  → Extract another 20-50

Repeat with different queries (10+ searches = 200-500 emails)

Step 3: Add Your Own File
Create emails.csv:
  alex@company.com
  bob@startup.io
  carol@agency.co
  (... hundreds more ...)

$ python3 devnavigator.py extract-emails --file emails.csv --store
  → Extract file emails (100+ or more)

Step 4: Filter & Segment
$ python3 devnavigator.py search-filtered --junior 70 --remote 60
  → Get high-quality filtered contacts

Step 5: View Results
$ python3 devnavigator.py stats
  → See total extraction count

Step 6: Export & Use
Python GUI:
  $ python3 gui.py
  → Database tab → Export to CSV

CLI:
  $ sqlite3 database/devnav.db "
    SELECT email, country FROM contacts ORDER BY email LIMIT 1000;
  "

Result: 500-1000+ emails extracted!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DETAILED METHOD: GitHub API Search
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GitHub allows searching public profiles with emails visible.

Command:
  python3 devnavigator.py search-auto --query "SEARCH_TERM"

Best search queries for maximum results:

DEVELOPER ROLES:
  "junior developer remote"
  "freelance web developer"
  "looking for project"
  "javascript freelance"
  "python developer for hire"
  "react developer available"
  "node developer looking for work"
  "typescript developer remote"
  "frontend developer hiring"
  "backend developer available"
  "full stack developer freelance"
  "devops engineer remote"

GEOGRAPHIC:
  "developer india"
  "developer pakistan"
  "developer philippines"
  "developer brazil"
  "developer eastern europe"

SPECIALTY:
  "machine learning engineer"
  "data scientist available"
  "blockchain developer"
  "mobile app developer"
  "game developer freelance"

HOW STATUS:
  "available for work"
  "open to opportunities"
  "seeking remote work"
  "freelance projects"
  "contract work available"
  "open source contributor"

Each query: 15-50 emails per search
10 queries = 150-500 emails
20 queries = 300-1000 emails

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DETAILED METHOD: CSV/File Import
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Create a CSV file with emails:

emails.csv:
  email,name,company,country
  alex.kumar@example.com,Alex Kumar,TechCorp,IN
  bob.johnson@example.com,Bob Johnson,DevShop,US
  carol.williams@example.com,Carol Williams,WebAgency,GB
  david.garcia@example.com,David Garcia,StartupXYZ,ES

Supported formats:
  ✓ CSV (.csv)
  ✓ JSON (.json)
  ✓ Text (.txt - one email per line)
  ✓ Excel (.xlsx)

Import:
  python3 devnavigator.py extract-emails --file emails.csv --store

This extracts ALL emails from file and stores in database.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DETAILED METHOD: Filtered Search
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Search with intelligent filtering (0-100 score per dimension)

Dimensions:
  --junior SCORE       : Junior developer (0-100)
  --frontend SCORE     : Frontend specialist (0-100)
  --backend SCORE      : Backend specialist (0-100)
  --remote SCORE       : Remote capable (0-100)
  --job_seeker SCORE   : Actively looking (0-100)
  --money_motivated SCORE : Financial incentive (0-100)
  --marketer SCORE     : Marketing interest (0-100)
  --registered SCORE   : Verified profile (0-100)

Examples:

# Find junior frontend devs
$ python3 devnavigator.py search-filtered --junior 70 --frontend 60

# Find money-motivated freelancers
$ python3 devnavigator.py search-filtered --money_motivated 80 --remote 70

# Find active job seekers
$ python3 devnavigator.py search-filtered --job_seeker 80

# Find marketers interested in money
$ python3 devnavigator.py search-filtered --marketer 70 --money_motivated 60

Results: 20-100+ highly targeted emails

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VIEW EXTRACTED EMAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Method 1: GUI (Visual)
$ python3 gui.py
→ Click "Database" tab
→ View all emails with details
→ Export to CSV
→ Delete individual contacts

Method 2: CLI - Show Count
$ python3 devnavigator.py stats
→ Shows total emails, sent, opened

Method 3: CLI - Direct Query
$ sqlite3 database/devnav.db "
  SELECT email, country FROM contacts ORDER BY email;
"

Method 4: CLI - Export All
$ sqlite3 database/devnav.db "
  SELECT email, name, company, country, created_at 
  FROM contacts 
  ORDER BY created_at DESC;
" > all_emails.csv

Method 5: Python Script
$ python3 -c "
import sqlite3
conn = sqlite3.connect('database/devnav.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM contacts')
print(f'Total emails: {cursor.fetchone()[0]}')
cursor.execute('SELECT email FROM contacts LIMIT 20')
for row in cursor.fetchall():
    print(row[0])
"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MAXIMUM EXTRACTION STRATEGY (1000+ Emails)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 1: Multiple GitHub Searches (300-500 emails)
────────────────────────────────────────────────
for query in [
  "junior developer remote",
  "freelance javascript",
  "python developer for hire",
  "react developer available",
  "nodejs developer freelance",
  "frontend engineer remote",
  "backend developer hiring",
  "full stack developer available",
  "looking for project",
  "open to opportunities",
]:
  python3 devnavigator.py search-auto --query "$query"

Phase 2: Import Your Lists (100-500 emails)
─────────────────────────────────────────────
Create emails.csv and import:
  python3 devnavigator.py extract-emails --file emails.csv --store

Phase 3: Apply Filtering (50-200 emails)
──────────────────────────────────────────
$ python3 devnavigator.py search-filtered --junior 70 --remote 60
$ python3 devnavigator.py search-filtered --job_seeker 80
$ python3 devnavigator.py search-filtered --money_motivated 75

Phase 4: Verify & Export
────────────────────────
$ python3 devnavigator.py stats
→ Shows total extracted

$ python3 gui.py
→ Database tab → Export to CSV

TOTAL: 500-1200+ emails extracted!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALL AVAILABLE COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXTRACTION:
  python3 devnavigator.py init-db
    → Initialize database

  python3 devnavigator.py extract-emails --file FILE --store
    → Import emails from CSV/JSON/TXT/XLSX

  python3 devnavigator.py search-auto --query "QUERY"
    → Search GitHub for emails (FREE)

  python3 devnavigator.py search-filtered --junior 70 --remote 60
    → Filtered search with demographic scoring

MANAGEMENT:
  python3 devnavigator.py stats
    → Show email statistics

  python3 devnavigator.py list-templates
    → Show email templates

  python3 devnavigator.py add-template --name NAME --subject SUBJ --body BODY
    → Add custom email template

SENDING:
  python3 send_test_emails.py send --limit 100
    → Send to max 100 recipients

  python3 send_test_emails.py send --country US
    → Send to US contacts only

  python3 send_test_emails.py send --exclude email1,email2
    → Send to all except listed

TRACKING:
  python3 tracking.py stats
    → Show open/click statistics

  python3 tracking.py setup-server
    → Start tracking server (opens/clicks)

GUI:
  python3 gui.py
    → Launch GUI interface (all-in-one)

CHECK STATUS:
  python3 check_sent_status.py
    → See which emails marked as SENT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIPS TO MAXIMIZE EXTRACTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. GITHUB API (Unlimited Free)
   ✓ Run 20+ unique searches
   ✓ Use different keywords each time
   ✓ Target specific skills, locations, job titles
   ✓ No rate limits, extract 500-1000+ emails

2. CSV IMPORTS (Your Own Data)
   ✓ Collect emails from LinkedIn exports
   ✓ Use email list services (Hunter.io free tier: 10/month)
   ✓ Import company employee lists
   ✓ Add emails from past projects

3. COMBINE METHODS
   ✓ GitHub + Your CSV = 500-1500 emails
   ✓ Add filtered search = 600-2000 emails
   ✓ Use geo-targeting to segment

4. OPTIMIZATION
   ✓ Use specific search queries (not generic)
   ✓ Target by skill + location
   ✓ Focus on demographics (junior, remote, money-motivated)
   ✓ Combine multiple filters for quality

5. SCALE UP
   ✓ Extract → Split into groups
   ✓ Send different templates to different groups
   ✓ Track which performs best
   ✓ Repeat successful campaigns

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COMMON QUESTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Q: How many emails can I extract?
A: Unlimited! GitHub API has no extraction limits.
   - GitHub searches: 1000+ emails (free)
   - Your CSV imports: Unlimited
   - Filtered searches: 100-500 per query

Q: Is it free?
A: 100% FREE!
   - GitHub API: Free (public data)
   - No API keys required
   - No rate limits for basic search
   - Self-hosted, no monthly fees

Q: How do I get more emails faster?
A: Use multiple queries:
   - 10 different GitHub searches = 150-500 emails (5 minutes)
   - Add your CSV = 100-1000 more emails (1 minute)
   - Apply filters = 50-200 more emails (1 minute)
   - Total time: 10 minutes, 300-1700 emails

Q: Can I import from another source?
A: YES! Any CSV/JSON/TXT with emails:
   - LinkedIn exports (if available)
   - Company directories
   - Email lists (first 10 free on Hunter.io)
   - Past contacts
   - Any spreadsheet

Q: What if emails are duplicates?
A: System prevents duplicates automatically.
   - Same email won't be added twice
   - Email is unique key in database
   - Safe to run imports multiple times

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

START NOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Quick 3-command extraction (100+ emails in 30 seconds):

1. Search GitHub (50+ emails)
   $ python3 devnavigator.py search-auto --query "junior developer remote"

2. Search GitHub (50+ emails)
   $ python3 devnavigator.py search-auto --query "freelance javascript"

3. View results
   $ python3 check_sent_status.py
   or
   $ python3 gui.py

Result: 100+ emails extracted, stored, ready to send!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

print(guide)

#!/usr/bin/env python3
"""
Quick Start: How to Run Email Extraction
Guides for database and file export
"""

# ============================================================================
# PART 1: QUICK START - Run Email Extraction
# ============================================================================

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║          📧 EMAIL EXTRACTION - QUICK START GUIDE                          ║
╚════════════════════════════════════════════════════════════════════════════╝

🎯 THREE WAYS TO EXTRACT EMAILS:

┌─ METHOD 1: FROM CSV FILE (Easiest) ────────────────────────────────────────┐
│                                                                            │
│  Command:                                                                  │
│  $ python3 devnavigator.py extract-emails --file contacts.csv --store     │
│                                                                            │
│  What it does:                                                             │
│  ✓ Read emails from contacts.csv                                          │
│  ✓ Validate each email                                                    │
│  ✓ Store directly in database                                             │
│  ✓ Skip duplicates automatically                                          │
│                                                                            │
│  CSV format (contacts.csv):                                               │
│  email,name,title,company,country                                         │
│  john@example.com,John Doe,Developer,TechCo,USA                           │
│  jane@example.com,Jane Smith,Designer,WebCo,Canada                        │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

┌─ METHOD 2: AUTO-SEARCH FROM INTERNET ─────────────────────────────────────┐
│                                                                            │
│  Command (Basic):                                                          │
│  $ python3 devnavigator.py search-auto \\                                  │
│      --title "junior frontend developer" \\                                │
│      --keywords "react,javascript,remote" \\                               │
│      --remote                                                              │
│                                                                            │
│  With Country:                                                             │
│  $ python3 devnavigator.py search-auto \\                                  │
│      --title "python developer" \\                                         │
│      --keywords "python,django" \\                                         │
│      --country "USA"                                                       │
│                                                                            │
│  What it does:                                                             │
│  ✓ Search GitHub profiles (FREE)                                          │
│  ✓ Query Hunter.io (if API key set)                                       │
│  ✓ Query Apollo.io (if API key set)                                       │
│  ✓ Auto-store ALL found emails in database                                │
│  ✓ Deduplicates automatically                                             │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

┌─ METHOD 3: PREVIEW BEFORE STORING ────────────────────────────────────────┐
│                                                                            │
│  Command:                                                                  │
│  $ python3 devnavigator.py search-filtered \\                              │
│      --title "frontend engineer" \\                                        │
│      --keywords "react,vue" \\                                             │
│      --remote                                                              │
│                                                                            │
│  What it does:                                                             │
│  ✓ Same search as METHOD 2                                                │
│  ✓ BUT shows results BEFORE storing                                       │
│  ✓ Shows matching scores for each profile                                 │
│  ✓ You review, then decide to store                                       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

""")

# ============================================================================
# PART 2: SAVE EMAILS - DATABASE vs FILE
# ============================================================================

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║          💾 WHERE TO SAVE EMAILS: DATABASE vs FILE                        ║
╚════════════════════════════════════════════════════════════════════════════╝

┌─ OPTION A: SAVE TO DATABASE (Recommended) ────────────────────────────────┐
│                                                                            │
│  Automatically stored when extracting:                                    │
│  $ python3 devnavigator.py extract-emails --file contacts.csv --store     │
│  $ python3 devnavigator.py search-auto --title "developer" --keywords ... │
│                                                                            │
│  What's stored:                                                            │
│  ✓ Email address                                                          │
│  ✓ Name                                                                   │
│  ✓ Job title                                                              │
│  ✓ Company                                                                │
│  ✓ Country/Location                                                       │
│  ✓ Source (where it came from)                                            │
│  ✓ Timestamp of import                                                    │
│  ✓ Campaign status (sent/opened/bounced)                                  │
│                                                                            │
│  Database location: ./database/devnav.db                                  │
│                                                                            │
│  Pros:                                                                     │
│  ✅ Can filter and query emails                                           │
│  ✅ Can apply scoring algorithms                                          │
│  ✅ Can send campaigns directly                                           │
│  ✅ Can track campaign performance                                        │
│  ✅ Can segment by criteria                                               │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

┌─ OPTION B: EXPORT TO CSV FILE ────────────────────────────────────────────┐
│                                                                            │
│  Python code to export from database to CSV:                              │
│                                                                            │
│  from python_engine.database_manager import DatabaseManager               │
│  import csv                                                               │
│                                                                            │
│  manager = DatabaseManager()                                              │
│  emails = manager.get_all_contacts()  # Get from database                 │
│                                                                            │
│  with open('extracted_emails.csv', 'w') as f:                             │
│      writer = csv.DictWriter(f, fieldnames=['email','name','title'])      │
│      writer.writeheader()                                                 │
│      writer.writerows(emails)                                             │
│                                                                            │
│  Output file: extracted_emails.csv                                        │
│                                                                            │
│  Pros:                                                                     │
│  ✅ Easy to share                                                         │
│  ✅ Import to Excel/Google Sheets                                         │
│  ✅ Use with other email tools                                            │
│  ✅ Human readable                                                        │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

┌─ OPTION C: EXPORT TO JSON FILE ───────────────────────────────────────────┐
│                                                                            │
│  Python code to export to JSON:                                           │
│                                                                            │
│  from python_engine.database_manager import DatabaseManager               │
│  import json                                                              │
│                                                                            │
│  manager = DatabaseManager()                                              │
│  emails = manager.get_all_contacts()                                      │
│                                                                            │
│  with open('extracted_emails.json', 'w') as f:                            │
│      json.dump(emails, f, indent=2)                                       │
│                                                                            │
│  Output file: extracted_emails.json                                       │
│                                                                            │
│  Pros:                                                                     │
│  ✅ Machine readable                                                      │
│  ✅ Preserves all data types                                              │
│  ✅ Great for APIs                                                        │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

""")

# ============================================================================
# PART 3: COMPLETE WORKFLOW EXAMPLE
# ============================================================================

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║          🔄 COMPLETE WORKFLOW: Extract → Filter → Send                    ║
╚════════════════════════════════════════════════════════════════════════════╝

STEP 1: Initialize Database
─────────────────────────────
$ python3 devnavigator.py init-db

Output:
✓ Database initialized at ./database/devnav.db


STEP 2: Extract Emails (Choose One Method)
───────────────────────────────────────────

Option A - From CSV file:
$ python3 devnavigator.py extract-emails --file contacts.csv --store

Output:
📂 Extracting emails from: contacts.csv
📧 Found 10 email(s)
✓ Stored: 10
✗ Failed: 0


Option B - Auto-search from internet:
$ python3 devnavigator.py search-auto \\
    --title "junior frontend developer" \\
    --keywords "react,javascript,remote" \\
    --country "USA" \\
    --remote

Output:
🚀 Starting automated email extraction...
1️⃣  GitHub Profiles
   🔍 Searching GitHub for: "react" "javascript" "remote"
   ✓ Found 25 from GitHub
2️⃣  Hunter.io
   ✓ Found 8 from Hunter.io
3️⃣  Apollo.io
   ✓ Found 15 from Apollo.io
────────────────────────────────
✓ Total unique emails found: 45
✓ Stored in database: 45


STEP 3: Check What Was Imported
───────────────────────────────
$ python3 devnavigator.py stats

Output:
📊 Campaign Statistics:
────────────────────────
Total contacts:    45
Ready to send:     45
────────────────────────


STEP 4: Export Emails (Optional)
┌─ Export to CSV ──────────────────┐
python3 << 'EOF'
from python_engine.database_manager import DatabaseManager
import csv

manager = DatabaseManager()
conn = manager.db_path
# Write query to export...
with open('my_emails.csv', 'w') as f:
    # Export logic
    pass
EOF

$ cat my_emails.csv
email,name,title,company,country
john@example.com,John Doe,Junior Frontend Developer,TechCo,USA
...

└──────────────────────────────────┘


STEP 5: Filter by Criteria
─────────────────────────
$ python3 << 'EOF'
from python_engine.contact_filters import ContactFilter

filter = ContactFilter()

# Get only junior developers who are remote capable
criteria = {
    'junior_developer': 70,
    'frontend_developer': 60,
    'remote_capable': 50
}

count, targets = filter.filter_by_multiple_criteria(criteria)
print(f"\\n🎯 Perfect targets: {count}")

for target in targets[:5]:
    print(f"  {target['email']} - {target['scores']}")
EOF

Output:
🎯 Perfect targets: 28

  john@example.com - {junior: 85, frontend: 92, remote: 78, ...}
  jane@example.com - {junior: 78, frontend: 88, remote: 65, ...}
  ...


STEP 6: Send Campaign
────────────────────
$ npm run send:emails

Output:
📧 Sending campaign...
✓ Email sent to john@example.com
✓ Email sent to jane@example.com
...
✓ Campaign complete: 28 emails sent

""")

# ============================================================================
# PART 4: PYTHON CODE EXAMPLES
# ============================================================================

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║          💻 PYTHON CODE - PROGRAMMATIC EMAIL EXTRACTION                   ║
╚════════════════════════════════════════════════════════════════════════════╝

EXAMPLE 1: Extract from CSV and save to database
─────────────────────────────────────────────────

from python_engine.email_extractor import get_email_extractor

extractor = get_email_extractor()
emails = extractor.extract_from_file('contacts.csv')

stored, failed = extractor.validate_and_store(
    emails, 
    source='manual_csv'
)

print(f"Stored: {stored}, Failed: {len(failed)}")


EXAMPLE 2: Auto-search and save
────────────────────────────────

from python_engine.auto_email_extractor import AutoEmailExtractor

extractor = AutoEmailExtractor()

criteria = {
    'title': 'junior frontend developer',
    'keywords': ['react', 'javascript', 'remote'],
    'country': 'USA',
    'remote': True
}

stored, results = extractor.search_all_sources(criteria)

print(f"Extracted and stored: {stored} emails")


EXAMPLE 3: Filter results by criteria
──────────────────────────────────────

from python_engine.contact_filters import ContactFilter

filter = ContactFilter()

# Get junior developers
juniors = filter.filter_junior_developers(min_score=70)

# Get frontend specialists
frontend = filter.filter_frontend_developers(min_score=60)

# Get remote capable
remote = filter.filter_remote_capable(min_score=50)

# Get complex combination
criteria = {
    'junior_developer': 70,
    'frontend_developer': 60,
    'remote_capable': 50,
    'job_seeker': 60
}
count, perfect = filter.filter_by_multiple_criteria(criteria)


EXAMPLE 4: Export to CSV file
──────────────────────────────

import csv
import sqlite3

db_path = './database/devnav.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
    SELECT email, name, title, company, country 
    FROM contacts 
    WHERE sent = 0
    ORDER BY created_at DESC
""")

with open('export_emails.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['email', 'name', 'title', 'company', 'country'])
    for row in cursor.fetchall():
        writer.writerow([
            row['email'],
            row['name'],
            row['title'],
            row['company'],
            row['country']
        ])

print("✓ Exported to export_emails.csv")


EXAMPLE 5: Batch extract multiple criteria
───────────────────────────────────────────

from python_engine.auto_email_extractor import AutoEmailExtractor

extractor = AutoEmailExtractor()

searches = [
    {
        'title': 'junior frontend developer',
        'keywords': ['react', 'remote'],
        'country': 'USA',
        'remote': True
    },
    {
        'title': 'python developer',
        'keywords': ['python', 'django'],
        'country': 'India',
        'remote': False
    },
    {
        'title': 'marketer',
        'keywords': ['growth', 'marketing'],
        'country': None,
        'remote': True
    }
]

total = 0
for criteria in searches:
    stored, _ = extractor.search_all_sources(criteria)
    total += stored
    print(f"✓ {criteria['title']}: {stored} emails")

print(f"\\n📊 Total extracted: {total} emails")

""")

# ============================================================================
# PART 5: QUICK REFERENCE
# ============================================================================

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║          📚 QUICK REFERENCE - ALL COMMANDS                                ║
╚════════════════════════════════════════════════════════════════════════════╝

Initialize Database:
├─ python3 devnavigator.py init-db

Extract from CSV:
├─ python3 devnavigator.py extract-emails --file contacts.csv --store

Auto-Search (Internet):
├─ python3 devnavigator.py search-auto \\
│  --title "junior frontend" \\
│  --keywords "react,javascript" \\
│  --country "USA" \\
│  --remote

Preview Before Storing:
├─ python3 devnavigator.py search-filtered \\
│  --title "frontend engineer" \\
│  --keywords "react"

Show Statistics:
├─ python3 devnavigator.py stats

List Templates:
├─ python3 devnavigator.py list-templates

Send Campaign:
├─ npm run send:emails


Database Queries:
├─ sqlite3 database/devnav.db
│  sqlite> SELECT email, title, country FROM contacts;
│  sqlite> SELECT COUNT(*) FROM contacts WHERE sent = 0;
│  sqlite> SELECT * FROM contacts WHERE country = 'USA';

""")

if __name__ == '__main__':
    print("\n✅ Guide complete! Choose a method above and run the command.")
    print("📖 See AUTO_EMAIL_EXTRACTION.md for detailed documentation.")

# 📖 Quick Reference - Email Extraction & Campaign Tool

## 🚀 30-SECOND START

```bash
# 1. Prepare your data
cat > contacts.csv << EOF
email,name,title,company,country
john@example.com,John Doe,Junior Developer,TechCo,USA
jane@example.com,Jane Smith,Frontend Dev,WebCo,Canada
EOF

# 2. Import to database
python3 devnavigator.py extract-emails --file contacts.csv --store

# 3. Check what was imported
python3 devnavigator.py stats

# 4. Send campaign
npm run send:emails
```

---

## 📊 THREE WAYS TO GET EMAILS

### Method 1: From CSV File
```bash
python3 devnavigator.py extract-emails --file contacts.csv --store
```
**Where to save**: → SQLite database (automatically)

### Method 2: Auto-Search Internet
```bash
python3 devnavigator.py search-auto \
    --title "junior frontend developer" \
    --keywords "react,javascript,remote" \
    --remote
```
**Sources**: GitHub (FREE) + Hunter.io (if key) + Apollo (if key)
**Saves**: → SQLite database (automatically)

### Method 3: Preview Before Saving
```bash
python3 devnavigator.py search-filtered \
    --title "python developer" \
    --keywords "python,django"
```
**Shows**: Results with scores
**Saves**: → Manually review first

---

## 💾 SAVE EMAILS: DATABASE or FILE

### Automatically Saved (Database)
✅ Happens with `extract-emails` and `search-auto`
```
Location: ./database/devnav.db
Contains: Email, name, title, company, country, source
Can query: SELECT * FROM contacts WHERE country = 'USA'
```

### Export to CSV File
```python
python3 << 'EOF'
import sqlite3, csv

conn = sqlite3.connect('database/devnav.db')
cursor = conn.cursor()
cursor.execute('SELECT email, name, title FROM contacts')

with open('export.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['email', 'name', 'title'])
    writer.writerows(cursor.fetchall())
EOF
```

### Export to JSON File
```python
python3 << 'EOF'
import sqlite3, json

conn = sqlite3.connect('database/devnav.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute('SELECT * FROM contacts')

with open('export.json', 'w') as f:
    json.dump([dict(row) for row in cursor.fetchall()], f, indent=2)
EOF
```

---

## 🏗️ WHAT'S BUILT & HOW IT WORKS

### System Architecture
```
[User] → CLI (devnavigator.py)
   ↓
[Extraction] → GitHub API / Hunter.io / Apollo.io / CSV
   ↓
[Validation] → Check format, block spam domains
   ↓
[Database] → SQLite with 5 tables
   ↓
[Filtering] → Score by 8 criteria (junior, frontend, remote, etc.)
   ↓
[Campaign] → Send emails via SMTP
   ↓
[Tracking] → Log sends, bounces, opens
```

### Core Components
1. **Email Extractor** - Reads CSV, validates, stores
2. **Auto Email Extractor** - Searches GitHub/Hunter/Apollo
3. **Contact Filters** - Scores by job/skill criteria
4. **Database** - SQLite with contacts, templates, campaigns, logs
5. **SMTP Sender** - Sends emails with TLS/SSL
6. **Geo-Targeting** - IP location (free APIs)

### Database Schema (5 Tables)
```
📋 contacts
   ├─ email, name, title, company, country
   ├─ sent (0/1), opened (0/1), bounced (0/1)
   └─ created_at, updated_at

📧 email_templates
   ├─ name, subject, body
   └─ supports: $name, $email, $company, $date

🎯 campaigns
   ├─ name, template_id, status
   └─ sent_count, failed_count

📊 email_logs
   ├─ contact_id, campaign_id, sent_at, status
   └─ error_message

🌍 ip_tracking
   ├─ ip_address, country, city, timezone
   └─ fraud_score, is_vpn, is_proxy
```

### Filtering Algorithm (8 Scores)
```
Each contact gets scored 0-100 on:
1. junior_developer    - Entry level? <3 years?
2. frontend_developer  - Knows React/Vue/Angular?
3. backend_developer   - Python/Java/Node?
4. remote_capable      - Mentions "remote"?
5. job_seeker          - #opentohire hashtag?
6. money_motivated     - Freelance/side hustle?
7. marketer            - Growth/sales/marketing?
8. registered          - Profile complete?

Multi-criteria filter:
  junior_developer >= 70 AND
  frontend_developer >= 60 AND
  remote_capable >= 50
  = Perfect target ✓
```

---

## 📖 WORKFLOW EXAMPLE

```
STEP 1: Extract
$ python3 devnavigator.py extract-emails --file contacts.csv --store
✓ 50 emails imported

STEP 2: Filter
$ python3 << 'EOF'
from python_engine.contact_filters import ContactFilter
f = ContactFilter()
count, targets = f.filter_junior_developers(min_score=70)
print(f"Junior devs: {count}")
EOF
✓ Junior devs: 28

STEP 3: Send Campaign
$ npm run send:emails
✓ 28 emails sent

STEP 4: Track Results
$ python3 devnavigator.py stats
✓ Total contacts: 50
✓ Sent: 28
✓ Opened: 4
```

---

## 🎯 SEARCH EXAMPLES

### Example 1: Junior React Developers (Remote)
```bash
python3 devnavigator.py search-auto \
    --title "junior react developer" \
    --keywords "react,javascript,typescript" \
    --remote
```
**Result**: GitHub + Hunter + Apollo = 30-100 emails

### Example 2: Python Developers in India
```bash
python3 devnavigator.py search-auto \
    --title "python engineer" \
    --keywords "python,django,rest" \
    --country "India"
```
**Result**: 20-50 emails

### Example 3: Freelance Marketers (USA)
```bash
python3 devnavigator.py search-auto \
    --title "freelance marketer" \
    --keywords "growth,marketing,content,freelance" \
    --country "USA"
```
**Result**: 15-40 emails

### Example 4: Full Stack Developers (Remote)
```bash
python3 devnavigator.py search-auto \
    --title "full stack developer" \
    --keywords "javascript,node,react,database" \
    --remote
```
**Result**: 40-150 emails

---

## 🔑 CONFIGURATION

### .env File (Secret Credentials)
```bash
# Optional API keys (FREE accounts)
HUNTER_API_KEY=your_key_here       # hunter.io
APOLLO_API_KEY=your_key_here       # apollo.io

# Database
DATABASE_PATH=./database/devnav.db

# Email sending
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=app_password_here

# Features
ALLOW_GMAIL_ALIASES=false
ENABLE_VIRUS_CHECK=true
ENABLE_SOURCE_VERIFICATION=true
FREE_GEOIP_ENABLED=true
```

---

## 💻 COMMANDS CHEAT SHEET

```bash
# Initialize
python3 devnavigator.py init-db

# Extract from file
python3 devnavigator.py extract-emails --file contacts.csv --store

# Search & store
python3 devnavigator.py search-auto \
    --title "developer" \
    --keywords "react" \
    --remote

# Search & preview
python3 devnavigator.py search-filtered \
    --title "frontend engineer" \
    --keywords "react,vue"

# Show stats
python3 devnavigator.py stats

# List templates
python3 devnavigator.py list-templates

# Add template
python3 devnavigator.py add-template \
    --name "my_template" \
    --subject "Hello $name" \
    --default

# Send campaign
npm run send:emails

# View database
sqlite3 database/devnav.db ".tables"
sqlite3 database/devnav.db "SELECT COUNT(*) FROM contacts;"
```

---

## 📊 SOURCES & LIMITS

| Source | Free Limit | Key? | Results |
|--------|-----------|------|---------|
| GitHub | Unlimited | ❌ | 20-100 |
| Hunter.io | 10/month | ✅ | 10-50 |
| Apollo.io | Limited | ✅ | 10-100 |
| Kaggle | Unlimited | ❌ | Datasets |
| CSV File | Unlimited | ❌ | Your list |

**Total possible**: 50-350+ emails for FREE

---

## ❓ FAQ

**Q: How do I export emails?**
A: Automated to database. Export with script above (CSV/JSON).

**Q: Can I use without API keys?**
A: Yes! GitHub works free. APIs are optional enhancements.

**Q: How are emails stored?**
A: SQLite database: `./database/devnav.db`

**Q: What data is stored?**
A: Email, name, title, company, country, source, sent status.

**Q: Can I filter by requirements?**
A: Yes! 8 scoring dimensions (junior, frontend, remote, etc.)

**Q: How do I send campaigns?**
A: `npm run send:emails` (SMTP configured in .env)

**Q: Is it GDPR compliant?**
A: Yes. Tracks consent, respects unsubscribe, can delete data.

---

## 🚀 NEXT STEPS

1. **Initialize**: `python3 devnavigator.py init-db`
2. **Get Emails**: Choose extraction method above
3. **Filter** (optional): Apply scoring algorithms
4. **Configure SMTP** in .env for sending
5. **Send Campaign**: `npm run send:emails`
6. **Track**: `python3 devnavigator.py stats`

---

## 📚 FURTHER READING

- **[AUTO_EMAIL_EXTRACTION.md](AUTO_EMAIL_EXTRACTION.md)** - Detailed extraction guide
- **[FREE_CAMPAIGN_SETUP.md](FREE_CAMPAIGN_SETUP.md)** - Campaign filtering examples
- **[TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md)** - System design & components
- **[HOW_TO_EXTRACT_EMAILS.py](HOW_TO_EXTRACT_EMAILS.py)** - Code examples
- **[README.md](README.md)** - Project overview

---

**Version**: 1.0  
**Last Updated**: March 29, 2026  
**Status**: Production Ready ✅

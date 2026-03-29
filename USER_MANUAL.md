# DevNavigator Campaign Manager - Complete User Manual

## Table of Contents
1. [Quick Start](#quick-start)
2. [GUI Interface](#gui-interface)
3. [Command Line Tools](#command-line-tools)
4. [Email Templates](#email-templates)
5. [Campaign Sending](#campaign-sending)
6. [Email Tracking](#email-tracking)
7. [Database Management](#database-management)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)
10. [Examples & Workflows](#examples--workflows)

---

## Quick Start

### Installation
```bash
cd /home/kali/Desktop/devnavigator
pip install -r requirements.txt
```

### Start the GUI
```bash
python3 gui.py
```

### Or Use Command Line
```bash
# Send emails
python3 send_test_emails.py send --template earning_opportunity --exclude yuki.tanaka@japantech.jp

# View tracking stats
python3 tracking.py stats

# Start tracking server
python3 tracking.py setup-server
```

---

## GUI Interface

### Main Tabs

#### 1. 📧 Send Emails Tab
Send campaigns to selected recipients with advanced filtering.

**Steps:**
1. Select a template from dropdown
2. Choose recipient type:
   - **All**: All unsent emails
   - **Specific emails**: Comma-separated list
   - **By country**: Filter by country code (IN, US, GB, etc)
   - **Exclude**: Send to all except listed emails
3. Enter recipient details (if needed)
4. Set limit (max number of recipients)
5. Check "Dry run" to preview
6. Click "Preview" or "Send Emails!"

**Example:**
- Template: earning_opportunity
- Mode: Exclude
- Input: yuki.tanaka@japantech.jp
- Limit: 100
- Result: Sends to 9 recipients (all except Yuki)

#### 2. 💾 Database Tab
View and manage all email contacts.

**Features:**
- View all contacts with their details
- Status columns show if sent/opened
- Export to CSV
- Delete individual contacts
- Right-click for context menu

**Columns:**
- Email: Recipient email address
- Name: Contact name
- Company: Company/org
- Country: Country code
- Sent: ✓ if email sent
- Opened: ✓ if email opened

#### 3. 📊 Tracking Tab
Monitor email opens and clicks.

**Shows:**
- Total emails sent
- Open count and percentage
- Click count and percentage
- Per-email breakdown with timestamps
- Last open/click time

**To Enable Tracking:**
1. Click "Start Tracking Server" (opens instructions)
2. Run in terminal: `python3 tracking.py setup-server`
3. Send emails (tracking automatically enabled)
4. Check this tab for results

#### 4. 📝 Templates Tab
View all available email templates.

**Templates Provided:**
- ⭐ junior_dev_recruitment (default)
- freelance_opportunities
- marketing_partnership
- learning_program
- earning_opportunity

**Create Custom Template:**
- Edit send_test_emails.py
- Add new entry to setup_templates() function

---

## Command Line Tools

### send_test_emails.py

**Initialize Setup:**
```bash
python3 send_test_emails.py setup
```
Creates 5 default templates in database.

**List Templates:**
```bash
python3 send_test_emails.py list
```

**Send Emails (Full Options):**
```bash
python3 send_test_emails.py send [OPTIONS]
```

**Options:**
- `--template NAME`: Use specific template (default: junior_dev_recruitment)
- `--limit N`: Send to max N recipients
- `--emails email1,email2,...`: Send to specific emails only
- `--country CODE`: Filter by country (US, IN, GB, etc)
- `--exclude email1,email2,...`: Exclude specific emails
- `--dry-run`: Preview without sending

**Examples:**
```bash
# Send to all 10 contacts
python3 send_test_emails.py send --limit 10

# Send to 2 specific people
python3 send_test_emails.py send --emails alex.kumar@startuptech.in,priya.patel@techcorp.com

# Send to India only
python3 send_test_emails.py send --country IN

# Send to all except 2 people
python3 send_test_emails.py send --exclude alex.kumar@startuptech.in,yuki.tanaka@japantech.jp

# Preview first (dry run)
python3 send_test_emails.py send --dry-run --limit 5

# Send to US contacts with freelance template
python3 send_test_emails.py send --template freelance_opportunities --country US

# Test with specific emails before mass send
python3 send_test_emails.py send --emails test@example.com,you@example.com --dry-run
```

### tracking.py

**View Statistics:**
```bash
python3 tracking.py stats
```

Shows:
- Total emails sent
- Emails opened
- Links clicked
- Per-recipient breakdown
- Open/click percentages
- Timestamps of opens/clicks

**Start Tracking Server:**
```bash
python3 tracking.py setup-server
```

Starts HTTP server on port 8888 for tracking.

**Custom Port:**
```bash
python3 tracking.py setup-server --port 9000
```

**Help:**
```bash
python3 tracking.py help
```

### devnavigator.py

**Initialize Database:**
```bash
python3 devnavigator.py init-db
```

**Extract Emails from File:**
```bash
python3 devnavigator.py extract-emails --file emails.csv --store
```

**List Templates:**
```bash
python3 devnavigator.py list-templates
```

**Add Template:**
```bash
python3 devnavigator.py add-template --name "template_name" --subject "Subject" --body "Body text"
```

**Show Statistics:**
```bash
python3 devnavigator.py stats
```

**Search Auto (Automated Extraction):**
```bash
python3 devnavigator.py search-auto --query "junior developer remote"
```

**Search with Filters:**
```bash
python3 devnavigator.py search-filtered --junior 70 --frontend 60 --remote 50
```

---

## Email Templates

### Available Templates

#### 1. junior_dev_recruitment
Career-focused message for junior developers.
```
Subject: Exciting Opportunity: Join Our Development Team! 🚀
From: DevNavigator Jobs 🚀
```

#### 2. freelance_opportunities
Income-focused for freelancers.
```
Subject: Freelance Project Opportunity - We Want You! 💼
From: DevNavigator Projects 💼
```

#### 3. marketing_partnership
B2B partnerships angle.
```
Subject: Let's Collaborate on Something Great 🤝
From: DevNavigator Partnerships 🤝
```

#### 4. learning_program
Education/training angle.
```
Subject: Free Web Development Bootcamp - Limited Spots! 🎓
From: DevNavigator Academy 🎓
```

#### 5. earning_opportunity
Money-focused earning opportunity.
```
Subject: Start Earning From Home - No Hidden Costs! 💰
From: Earning Opportunity Network 💰
```

### Email Aliases (Display Names)

Same email, different sender names visible to recipients:

| Template | Display Name |
|----------|--------------|
| junior_dev_recruitment | DevNavigator Jobs 🚀 |
| freelance_opportunities | DevNavigator Projects 💼 |
| marketing_partnership | DevNavigator Partnerships 🤝 |
| learning_program | DevNavigator Academy 🎓 |
| earning_opportunity | Earning Opportunity Network 💰 |

This allows A/B testing without multiple email accounts!

### Create Custom Template

Edit `send_test_emails.py`, find `setup_templates()` function:

```python
template_name = {
    'name': 'my_template',
    'subject': 'Your Subject Line Here',
    'body': '''Hi,

Your message here.

Best regards,
Your Name

---
Email: $email | Date: $date
''',
    'is_default': False
}
manager.add_template(**template_name)
```

Available variables in body:
- `$email`: Recipient email
- `$date`: Current date
- `$name`: Recipient name (if available)

---

## Campaign Sending

### Basic Workflow

1. **Prepare Recipients**
   - Extract emails from files
   - Or import from database
   - Filter by criteria

2. **Choose Template**
   - Select from 5 pre-made options
   - Or create custom template
   - Preview content

3. **Set Filters**
   - Country filter
   - Email selection
   - Exclude list
   - Recipient limit

4. **Test First**
   - Use `--dry-run` mode
   - Send to self first
   - Verify formatting

5. **Send Campaign**
   - Remove `--dry-run`
   - Confirm send
   - Monitor progress

### Sending Scenarios

**Scenario 1: Send to Everyone**
```bash
python3 gui.py
# GUI: Select template → "All" → Send
# Or CLI:
python3 send_test_emails.py send --template earning_opportunity
```

**Scenario 2: Test with 2 People**
```bash
python3 send_test_emails.py send --template earning_opportunity \
  --emails alex@x.com,jane@x.com --dry-run
```

**Scenario 3: Country-Specific**
```bash
python3 send_test_emails.py send --template freelance_opportunities --country US
```

**Scenario 4: A/B Test Different Templates**
```bash
# Group A: Jobs template to 5 people
python3 send_test_emails.py send --template junior_dev_recruitment --limit 5

# Group B: Freelance template to 5 different people
python3 send_test_emails.py send --template freelance_opportunities --limit 5

# Compare results with tracking
python3 tracking.py stats
```

---

## Email Tracking

### How Tracking Works

1. **Open Tracking**
   - Invisible 1x1 pixel in email
   - Loads when recipient opens
   - Tracked automatically

2. **Click Tracking**
   - Links wrapped with tracking URL
   - Records click, redirects to original
   - Recipient doesn't see tracking

3. **Storage**
   - All data in SQLite database
   - Timestamps for each event
   - Privacy-respecting (no device/location)

### Enable Tracking

**Terminal 1 - Start Server:**
```bash
python3 tracking.py setup-server
```

**Terminal 2 - Send Emails:**
```bash
python3 send_test_emails.py send --template earning_opportunity
```

Emails now have:
- ✅ Open tracking pixel
- ✅ Freelancer link wrapped
- ✅ Auto-recorded in database

### View Results

```bash
python3 tracking.py stats
```

**Output Example:**
```
📧 Total Sent:    10
👁️  Opened:       7 (70.0%)
🔗 Clicked:       4 (40.0%)

📧 alex.kumar@startuptech.in
   Opens:  1/1 | Last: 2026-03-29 14:32:15
   Clicks: 1/1 | Last: 2026-03-29 14:33:02
```

---

## Database Management

### View Database

**GUI Method:**
```bash
python3 gui.py → Database tab
```

**Command Line:**
```bash
sqlite3 database/devnav.db ".tables"
```

### Database Tables

**contacts**
- All email recipients
- Fields: email, name, company, country, sent, opened, etc
- Tracks send/open status

**email_templates**
- All campaign templates
- Fields: name, subject, body, is_default

**campaigns**
- Campaign records
- Fields: name, template_id, status, sent_count, etc

**email_logs**
- Send attempt logs
- Fields: contact_id, campaign_id, sent_at, status

**email_tracking**
- Open/click tracking
- Fields: email, tracking_id, opened, clicked, timestamps

### SQL Queries

**Count total contacts:**
```sql
SELECT COUNT(*) FROM contacts;
```

**Get opened emails:**
```sql
SELECT email FROM contacts WHERE opened = 1;
```

**Get unopened emails:**
```sql
SELECT email FROM contacts WHERE sent = 1 AND opened = 0;
```

**Tracking stats:**
```sql
SELECT 
    COUNT(*) as total,
    SUM(opened) as opens,
    SUM(clicked) as clicks
FROM email_tracking;
```

### Export Database

**CSV Export:**
```bash
python3 gui.py → Database tab → "Export to CSV"
```

**SQL Dump:**
```bash
sqlite3 database/devnav.db ".dump" > backup.sql
```

**Restore:**
```bash
sqlite3 database/devnav.db < backup.sql
```

---

## Configuration

### .env File

Create `.env` in project root:

```
# Database
DATABASE_PATH=./database/devnav.db

# SMTP Configuration
SMTP_URL=smtp://smtp.gmail.com:587
SMTP_USERNAME=matteopennacchia43@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=matteopennacchia43@gmail.com
SMTP_USE_TLS=true

# Tracking Server
TRACKING_SERVER_URL=http://localhost:8888

# Optional API Keys
HUNTER_API_KEY=your_key_here
APOLLO_API_KEY=your_key_here
```

### Gmail Setup

1. Enable 2-Factor Authentication
2. Create App Password
3. Use app password in SMTP_PASSWORD

### Tracking Server URL

Default: `http://localhost:8888`

For remote server:
```
TRACKING_SERVER_URL=http://your-server-ip:8888
```

---

## Troubleshooting

### "No templates found"

**Solution:**
```bash
python3 send_test_emails.py setup
```

### "Email send failed"

**Check:**
1. SMTP credentials in .env
2. Gmail: Enable Less Secure Apps OR use App Password
3. Network connection
4. Port 587 not blocked

**Test SMTP:**
```python
from send_test_emails import EmailSender
s = EmailSender()
success, msg = s.send_test_email('your@email.com', 'Test', 'Test body')
print(success, msg)
```

### "Tracking not working"

**Check:**
1. Is server running? `python3 tracking.py setup-server`
2. Port 8888 available?
3. TRACKING_SERVER_URL correct in .env?

### GUI won't open

**Solution:**
```bash
# Check tkinter installed
python3 -m tkinter

# If error, install:
sudo apt-get install python3-tk

# Then try GUI
python3 gui.py
```

### Database locked

**Solution:**
```bash
# Make sure only one process is accessing DB
pkill -f gui.py
pkill -f tracking.py

# Then try again
python3 gui.py
```

---

## Examples & Workflows

### Workflow 1: Quick Test Campaign

```bash
# 1. Start tracking server
python3 tracking.py setup-server &

# 2. Send to self
python3 send_test_emails.py send --template earning_opportunity \
  --emails matteopennacchia43@gmail.com --dry-run

# 3. Actually send
python3 send_test_emails.py send --template earning_opportunity \
  --emails matteopennacchia43@gmail.com

# 4. Check results (wait for email to arrive + open)
sleep 5
python3 tracking.py stats
```

### Workflow 2: A/B Test Templates

```bash
# Template A to group 1
python3 send_test_emails.py send --template junior_dev_recruitment --limit 5

# Template B to group 2
python3 send_test_emails.py send --template freelance_opportunities --limit 5

# Wait for responses...

# Compare results
python3 tracking.py stats

# Check which template performed better
sqlite3 database/devnav.db "
SELECT template_id, COUNT(*) as opens FROM email_logs 
WHERE status = 'opened' GROUP BY template_id
"
```

### Workflow 3: Regional Campaign

```bash
# Send to North America
python3 send_test_emails.py send --template earning_opportunity --country US --limit 10
python3 send_test_emails.py send --template earning_opportunity --country CA --limit 10

# Send to Europe
python3 send_test_emails.py send --template earning_opportunity --country GB --limit 10
python3 send_test_emails.py send --template earning_opportunity --country DE --limit 10

# Send to Asia
python3 send_test_emails.py send --template earning_opportunity --country IN --limit 10

# Check totals
python3 devnavigator.py stats
```

### Workflow 4: Using GUI for Full Campaign

```bash
# Start GUI
python3 gui.py

# Tab 1: Database - verify contacts loaded
# Tab 2: Send Emails
#   - Select: earning_opportunity
#   - Mode: Exclude
#   - Input: yuki.tanaka@japantech.jp
#   - Check: Dry run ✓
#   - Click: Preview
#   - Uncheck: Dry run
#   - Click: Send Emails!
# Tab 3: Tracking
#   - Click: Start Tracking Server
#   - (follow instructions to run: python3 tracking.py setup-server in terminal)
#   - Click: Refresh Stats (wait 30 seconds for opens)
# Tab 4: Templates - view available options
```

---

## Keyboard Shortcuts (GUI)

- `Ctrl+Q`: Quit
- `Ctrl+R`: Refresh (in each tab)
- `Ctrl+E`: Export CSV (Database tab)
- `Tab`: Move to next field

---

## File Structure

```
devnavigator/
├── gui.py                      # Main GUI application
├── send_test_emails.py         # Email sending tool
├── tracking.py                 # Email tracking system
├── devnavigator.py             # Main CLI tool
├── database/
│   └── devnav.db              # SQLite database
├── .env                        # Configuration
├── USER_MANUAL.md             # This file
└── requirements.txt            # Python dependencies
```

---

## Support

**Having issues?**

1. Check [Troubleshooting](#troubleshooting) section
2. Review [Examples](#examples--workflows)
3. Check `.env` configuration
4. Ensure database exists: `sqlite3 database/devnav.db ".tables"`

**Common Commands Quick Reference:**

```bash
# GUI
python3 gui.py

# Send emails
python3 send_test_emails.py send --template earning_opportunity

# View stats
python3 tracking.py stats

# Start tracking
python3 tracking.py setup-server

# Database info
python3 devnavigator.py stats

# Export to CSV
# Use GUI -> Database tab -> Export
```

---

**Version:** 1.0.0  
**Last Updated:** March 29, 2026  
**Platform:** Python 3.8+  
**Requirements:** SQLite3, tkinter, requests


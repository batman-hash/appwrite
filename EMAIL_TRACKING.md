# Email Tracking Guide 📊

## Overview

The email tracking system monitors when recipients open emails and click on links. This helps you understand campaign performance and recipient engagement.

## How It Works

### 1. **Open Tracking** 👁️
- Invisible 1x1 pixel embedded in email body
- Loads from tracking server when recipient opens email
- Automatically recorded when pixel loads

### 2. **Click Tracking** 🔗
- Links wrapped with tracking URLs
- Records click, then redirects to original link
- Recipient doesn't see the tracking

### 3. **Database Storage** 💾
- All tracking data stored in SQLite
- Timestamps recorded for opens and clicks
- Per-email statistics available

## Setup

### Step 1: Start the Tracking Server

```bash
python3 tracking.py setup-server
```

This starts the HTTP tracking server on `http://localhost:8888`

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║          📊 EMAIL TRACKING SERVER RUNNING                 ║
╚════════════════════════════════════════════════════════════╝

🚀 Server: http://localhost:8888
📍 Tracking Endpoints:
   - Pixel:  http://localhost:8888/track/pixel
   - Click:  http://localhost:8888/track/click
```

### Step 2: Update .env (Optional)

If your tracking server is on a different machine/port:

```
TRACKING_SERVER_URL=http://your-server-ip:8888
```

**Default:** `http://localhost:8888`

### Step 3: Send Tracked Emails

When you use `send_test_emails.py send`, tracking is **automatically added**:
```bash
python3 send_test_emails.py send --template earning_opportunity --exclude yuki.tanaka@japantech.jp
```

The system will:
1. ✅ Embed open tracking pixel
2. ✅ Wrap links for click tracking  
3. ✅ Load tracking server URL from .env
4. ✅ Record all events in SQLite

## Viewing Statistics

### Overall Stats
```bash
python3 tracking.py stats
```

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║              📊 EMAIL TRACKING STATISTICS                ║
╚════════════════════════════════════════════════════════════╝

📧 Total Sent:    10
👁️  Opened:       4 (40.0%)
🔗 Clicked:       2 (20.0%)

📋 Detailed Tracking by Email:
═══════════════════════════════════════════════════════════

📧 alex.kumar@startuptech.in
   Opens:  1/1 | Last: 2026-03-29 14:32:15
   Clicks: 1/1 | Last: 2026-03-29 14:33:02

📧 priya.patel@techcorp.com
   Opens:  1/1 | Last: 2026-03-29 14:31:45
   Clicks: 0/1 | Last: Never

[...more recipients...]
```

## What Gets Tracked

### Tracked Data
✅ Email address  
✅ Open time (to timestamp precision)  
✅ Click time (to timestamp precision)  
✅ Link clicked (Freelancer signup link in templates)  
✅ Open/click rate percentages  

### NOT Tracked
❌ Device type  
❌ Location/IP address  
❌ Operating system  
❌ Email client  
❌ Browser information  

This keeps tracking **privacy-respecting** while still providing useful metrics.

## Tracking in Action

### Full Workflow

1. **Start tracking server** (in one terminal):
```bash
python3 tracking.py setup-server
```

2. **Send emails** (in another terminal):
```bash
python3 send_test_emails.py send --template earning_opportunity --exclude yuki.tanaka@japantech.jp
```

**What happens:**
- Email with embedded tracking pixel sent
- Freelancer link wrapped with click tracker
- Server logs each action as it happens:
  ```
  ✓ OPEN TRACKED: alex.kumar@startuptech.in (3144160f287cf3f1)
  ✓ CLICK TRACKED: alex.kumar@startuptech.in - freelancer_signup (4fb82a1c9d2e5b7f)
  ```

3. **Check results**:
```bash
python3 tracking.py stats
```

## Multiple Tracking Servers

If you want to run multiple servers (different ports):

```bash
# Terminal 1 - Main server on 8888
python3 tracking.py setup-server

# Terminal 2 - Secondary server on 9000
python3 tracking.py setup-server --port 9000
```

Then update .env to choose which one:
```
TRACKING_SERVER_URL=http://localhost:9000
```

## Database Structure

Tracking data stored in `email_tracking` table:

```sql
CREATE TABLE email_tracking (
    id INTEGER PRIMARY KEY,
    email TEXT,
    tracking_id TEXT UNIQUE,  -- Unique per email
    tracking_type TEXT,        -- 'pixel' or 'link'
    link_name TEXT,            -- Name of link clicked
    opened INTEGER,            -- 1 if opened, 0 if not
    clicked INTEGER,           -- 1 if clicked, 0 if not
    open_time TIMESTAMP,       -- When opened
    click_time TIMESTAMP,      -- When clicked
    created_at TIMESTAMP       -- When tracking created
)
```

## Troubleshooting

### Tracking server won't start

**Error:** "Address already in use"
```bash
python3 tracking.py setup-server --port 9000
```
Use a different port.

### "No tracking data available"

This is normal if no emails have been sent yet. Send an email:
```bash
python3 send_test_emails.py send --dry-run --limit 1
```
Then remove `--dry-run` to actually send.

### Tracking not recording

**Check:**
1. Is tracking server running? (`python3 tracking.py setup-server`)
2. Is TRACKING_SERVER_URL correct in .env?
3. Are emails being sent? (Check send logs)

### Port already in use

Use a different port:
```bash
# Find what's using 8888
sudo lsof -i :8888

# Kill process
kill <PID>

# Or use different port
python3 tracking.py setup-server --port 8889
```

## Privacy & Compliance

### GDPR Compliance ✓
- Only tracks engagement (open/click)
- No personal data collection beyond email
- Compliance with privacy by design

### CAN-SPAM Compliance ✓
- Tracking is transparent (pixel is disclosure)
- Must include unsubscribe link in emails
- Must have clear subject line

### Best Practices
- ✅ Include privacy notice in marketing emails
- ✅ Honor unsubscribe requests
- ✅ Don't track non-consenting recipients
- ✅ Store tracking data securely

## Integration with Campaigns

### Track Multiple Campaigns

```bash
# Campaign A: Earning Opportunity (tracked)
python3 send_test_emails.py send --template earning_opportunity --emails alex@x.com,bob@x.com

# Campaign B: Learning Program (tracked)
python3 send_test_emails.py send --template learning_program --emails carol@x.com,david@x.com

# Check combined results
python3 tracking.py stats
```

### Track by Region

```bash
# US campaign
python3 send_test_emails.py send --country US --template earning_opportunity

# EU campaign  
python3 send_test_emails.py send --country DE,FR,IT --template freelance_opportunities

# Check stats afterwards
python3 tracking.py stats
```

## Advanced Usage

### Query Raw Tracking Data

```python
from tracking import EmailTracker

tracker = EmailTracker()

# Get stats for specific email
stats = tracker.get_tracking_stats('alex.kumar@startuptech.in')
print(stats)
# {'total_sent': 1, 'opens': 1, 'clicks': 1, 'open_rate': '100.0%', 'click_rate': '100.0%'}
```

### Custom Tracking Links

```python
from tracking import EmailTracker

tracker = EmailTracker()

# Create tracked link
tracked_url = tracker.get_tracking_link(
    'https://mysite.com/offer',
    'recipient@email.com',
    'custom_offer'
)
print(tracked_url)
# http://localhost:8888/track/click?id=...&redirect=https://mysite.com/offer
```

## Summary

**What This Solves:**
- 👁️ Know when recipients open emails
- 🔗 Know if they click your links
- 📊 Compare engagement across campaigns
- 🎯 Identify interested recipients
- 📈 Optimize marketing spend

**Privacy:**
- No device/location tracking
- Only engagement metrics
- Transparent and compliant
- Database-bound (no cloud)

**Easy to Use:**
- Automatic with send_test_emails.py
- Simple stats command
- No configuration needed (optional .env)

---

**Start tracking now:**
```bash
# Terminal 1
python3 tracking.py setup-server

# Terminal 2
python3 send_test_emails.py send --template earning_opportunity

# Check results
python3 tracking.py stats
```

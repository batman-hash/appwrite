# Quick Start Guide - Network Email Scraper

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies
```bash
# Install Kali Linux tools
sudo apt update
sudo apt install -y nmap netdiscover

# Install Python dependencies
pip install requests python-dotenv
```

### Step 2: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your settings
nano .env
```

**Required settings:**
```bash
# SMTP Configuration
SMTP_URL=smtp.gmail.com:587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your-email@gmail.com

# Database
DATABASE_PATH=./database/devnav.db
```

### Step 3: Test the Setup
```bash
# Run test suite
python3 test_scraper.py
```

### Step 4: Run Your First Scan
```bash
# Quick scan (10 emails)
./quick_scan.sh 192.168.1.0/24 earning_opportunity 10

# Or use Python directly
python3 network_email_scraper.py \
  --scan 192.168.1.0/24 \
  --template earning_opportunity \
  --limit 10
```

### Step 5: View Results
```bash
# Check statistics
python3 devnavigator.py stats

# View contacts
python3 devnavigator.py queue --queue all --limit 50
```

## 📧 Available Email Templates

```bash
# List all templates
python3 devnavigator.py list-templates
```

**Popular templates:**
- `earning_opportunity` - Freelance/earning opportunities
- `junior_dev_recruitment` - Junior developer recruitment
- `freelance_opportunities` - Freelance projects
- `marketing_partnership` - Marketing partnerships
- `learning_program` - Learning/bootcamp programs

## 🔧 Configuration Options

### Rate Limiting (Avoid Bans)
```bash
# .env file
EMAIL_MIN_DELAY=5          # Minimum seconds between emails
EMAIL_MAX_DELAY=15         # Maximum seconds between emails
EMAIL_BATCH_SIZE=10        # Emails per batch
EMAIL_BATCH_DELAY=60       # Seconds between batches
```

### Proxy Rotation (Avoid Blocks)
```bash
# .env file
ROTATING_PROXIES=http://proxy1:8080,http://proxy2:8080,http://proxy3:8080

# Or create proxies.txt file
echo "http://proxy1:8080" > proxies.txt
echo "http://proxy2:8080" >> proxies.txt
```

## 📊 Common Commands

### Scan Network
```bash
# Scan local network
python3 network_email_scraper.py --scan 192.168.1.0/24

# Scan specific URLs
python3 network_email_scraper.py --scan https://example.com

# Scan only (no sending)
python3 network_email_scraper.py --scan 192.168.1.0/24 --scan-only
```

### Send Emails
```bash
# Send to existing contacts
python3 network_email_scraper.py --send-only --template earning_opportunity --limit 20

# Preview before sending
python3 send_test_emails.py send --limit 10 --template earning_opportunity --dry-run
```

### Monitor Status
```bash
# View statistics
python3 devnavigator.py stats

# Check send status
python3 devnavigator.py send-status

# View queue
python3 devnavigator.py queue --queue all --limit 50
```

## 🛡️ Avoiding Bans and Blocks

### 1. Use Rate Limiting
```bash
# Set in .env
EMAIL_MIN_DELAY=5
EMAIL_MAX_DELAY=15
EMAIL_BATCH_SIZE=10
EMAIL_BATCH_DELAY=60
```

### 2. Rotate Proxies
```bash
# Create proxies.txt with multiple proxies
http://proxy1:8080
http://proxy2:8080
http://proxy3:8080
```

### 3. Validate Emails First
```bash
# Always validate before sending
python3 network_email_scraper.py --scan 192.168.1.0/24 --scan-only
```

### 4. Start Small
```bash
# Test with small batch first
./quick_scan.sh 192.168.1.0/24 earning_opportunity 5
```

### 5. Monitor Bounces
```bash
# Check for bounces
python3 devnavigator.py stats
```

## 📁 File Structure

```
devnavigator/
├── network_email_scraper.py    # Main scraper script
├── quick_scan.sh               # Quick start script
├── test_scraper.py             # Test suite
├── rotate_proxy.py             # Proxy rotation utility
├── NETWORK_SCRAPER_README.md   # Full documentation
├── QUICK_START.md              # This file
├── database/
│   └── devnav.db               # SQLite database
├── proxies.txt                 # Proxy list (optional)
└── .env                        # Configuration file
```

## 🆘 Troubleshooting

### Nmap Not Found
```bash
sudo apt install nmap
```

### Netdiscover Not Found
```bash
sudo apt install netdiscover
```

### Permission Denied
```bash
chmod +x network_email_scraper.py
chmod +x quick_scan.sh
```

### SMTP Authentication Failed
```bash
# Use app-specific password for Gmail
# 1. Enable 2-Factor Authentication
# 2. Generate App Password
# 3. Use app password in .env
```

### Emails Going to Spam
```bash
# Use valid SPF/DKIM records
# Warm up IP gradually
# Use reputable SMTP provider
```

## 📞 Support

For issues or questions:
1. Check `NETWORK_SCRAPER_README.md` for detailed documentation
2. Run `python3 test_scraper.py` to verify setup
3. Review `.env` configuration
4. Test with dry-run mode first

## ⚖️ Legal Considerations

- Only scrape public data
- Respect robots.txt
- Include unsubscribe link
- Honor unsubscribe requests
- Comply with CAN-SPAM Act
- Follow GDPR guidelines
- Check local regulations

---

**Ready to start?** Run: `./quick_scan.sh 192.168.1.0/24 earning_opportunity 10`

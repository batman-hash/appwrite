# Network Email Scraper with Kali Linux Tools

A comprehensive email scraping tool that scans networks, extracts emails, validates them, and sends campaigns without being banned or blocked.

## Features

- **Network Scanning**: Uses nmap and netdiscover to find web services
- **Email Extraction**: Scrapes emails from discovered web services
- **Validation**: Validates emails using DNS and format checks
- **Safe Sending**: Rate limiting, proxy rotation, and batch processing
- **Database Integration**: Stores emails in SQLite database
- **Template Support**: Uses existing email templates

## Prerequisites

### Kali Linux Tools
```bash
# Install required tools
sudo apt update
sudo apt install nmap netdiscover

# Verify installation
nmap --version
netdiscover --help
```

### Python Dependencies
```bash
pip install requests python-dotenv sqlite3
```

## Configuration

### Environment Variables (.env)
```bash
# Database
DATABASE_PATH=./database/devnav.db

# Email Settings
SMTP_URL=smtp.gmail.com:587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your-email@gmail.com

# Rate Limiting
EMAIL_MIN_DELAY=5
EMAIL_MAX_DELAY=15
EMAIL_BATCH_SIZE=10
EMAIL_BATCH_DELAY=60

# Proxy Rotation
ROTATING_PROXIES=http://proxy1:8080,http://proxy2:8080,http://proxy3:8080
PROXY_FILE=proxies.txt

# Validation
ENABLE_VIRUS_CHECK=true
ENABLE_SOURCE_VERIFICATION=true
```

### Proxy Configuration
Create `proxies.txt` with one proxy per line:
```
http://proxy1.example.com:8080
http://proxy2.example.com:8080
http://proxy3.example.com:8080
socks5://proxy4.example.com:1080
```

## Usage

### 1. Full Workflow (Scan + Extract + Validate + Store + Send)
```bash
# Scan network and send emails
python3 network_email_scraper.py \
  --scan 192.168.1.0/24 \
  --template earning_opportunity \
  --limit 50

# Scan specific URLs
python3 network_email_scraper.py \
  --scan https://example.com https://company.com \
  --template junior_dev_recruitment \
  --limit 100
```

### 2. Scan Only (No Sending)
```bash
# Scan network range
python3 network_email_scraper.py --scan 192.168.1.0/24 --scan-only

# Scan specific URLs
python3 network_email_scraper.py --scan https://example.com --scan-only
```

### 3. Send Only (No Scanning)
```bash
# Send to existing contacts
python3 network_email_scraper.py --send-only --template earning_opportunity --limit 20
```

### 4. Interactive Menu
```bash
python3 network_email_scraper.py
```

## How It Avoids Bans and Blocks

### 1. Rate Limiting
- **Random delays**: 5-15 seconds between emails
- **Batch processing**: 10 emails per batch, 60 second delay between batches
- **Configurable**: Adjust via environment variables

### 2. Proxy Rotation
- **Multiple proxies**: Rotate through proxy list
- **Automatic failover**: Skip failed proxies
- **Protocol support**: HTTP, HTTPS, SOCKS5

### 3. User Agent Rotation
- **Random user agents**: Mimic different browsers
- **Realistic headers**: Include Accept, Accept-Language, etc.

### 4. Email Validation
- **DNS verification**: Check MX records
- **Format validation**: Verify email format
- **Virus checking**: Optional virus/malware detection

### 5. Safe Sending Patterns
- **Business hours**: Send during business hours (9 AM - 5 PM)
- **Weekday only**: Avoid weekends
- **Gradual ramp-up**: Start with small batches

## Network Scanning Options

### Nmap Scanning
```bash
# Scan common web ports
python3 network_email_scraper.py --scan 192.168.1.0/24

# Scan specific ports
python3 network_email_scraper.py --scan 192.168.1.0/24:80,443,8080

# Scan subnet
python3 network_email_scraper.py --scan 10.0.0.0/24
```

### Netdiscover Scanning
```bash
# Passive network discovery
python3 network_email_scraper.py --scan 192.168.1.0/24

# Specify interface
python3 network_email_scraper.py --scan 192.168.1.0/24 --interface eth0
```

## Email Templates

### Available Templates
```bash
python3 devnavigator.py list-templates
```

### Common Templates
- `earning_opportunity`: Freelance/earning opportunities
- `junior_dev_recruitment`: Junior developer recruitment
- `freelance_opportunities`: Freelance project opportunities
- `marketing_partnership`: Marketing partnerships
- `learning_program`: Learning/bootcamp programs

### Custom Templates
```bash
python3 devnavigator.py add-template \
  --name "custom_campaign" \
  --subject "Your Subject Here" \
  --body "Your email body here"
```

## Monitoring and Statistics

### View Statistics
```bash
python3 devnavigator.py stats
```

### Check Send Status
```bash
python3 devnavigator.py send-status
```

### View Queue
```bash
python3 devnavigator.py queue --queue all --limit 50
```

## Best Practices

### 1. Start Small
```bash
# Test with small batch first
python3 network_email_scraper.py \
  --scan 192.168.1.0/24 \
  --template earning_opportunity \
  --limit 5
```

### 2. Use Dry Run
```bash
# Preview before sending
python3 send_test_emails.py send \
  --limit 10 \
  --template earning_opportunity \
  --dry-run
```

### 3. Monitor Bounces
```bash
# Check for bounces
python3 devnavigator.py stats
```

### 4. Respect Unsubscribes
```bash
# Archive unsubscribed contacts
python3 devnavigator.py archive --emails "unsubscribed@example.com"
```

### 5. Use Valid Proxies
```bash
# Test proxies before use
python3 rotate_proxy.py
```

## Troubleshooting

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
```

### SMTP Authentication Failed
```bash
# Use app-specific password for Gmail
# Enable 2FA and generate app password
```

### Emails Going to Spam
```bash
# Use valid SPF/DKIM records
# Warm up IP gradually
# Use reputable SMTP provider
```

## Legal Considerations

### Compliance
- **CAN-SPAM Act**: Include unsubscribe link
- **GDPR**: Get consent before sending
- **Local laws**: Check local regulations

### Best Practices
- Only scrape public data
- Respect robots.txt
- Include physical address
- Honor unsubscribe requests

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review `.env` configuration
3. Test with dry-run mode
4. Monitor send status

## License

This tool is for educational purposes only. Use responsibly and in compliance with applicable laws.

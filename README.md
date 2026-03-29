# DevNavigator - Email Campaign Platform

Automated email campaign platform for educational initiatives. Extract, validate, and send targeted emails with customizable templates.

## Features

✅ **Email Extraction & Validation**
- Extract emails from multiple sources (files, APIs, web)
- Auto-validate email format and authenticity
- Block suspicious domains and temporary email services
- Source verification for genuine contacts
- Verification email workflow with expiring tokens and codes

✅ **Secure Database Management**
- SQLite database with encrypted credentials
- Contact tracking with consent management
- Campaign performance analytics
- Email send logs and bounce handling

✅ **Email Template System**
- Default campaign templates
- Custom template creation
- Variable substitution ($name, $email, etc)
- Multi-template campaign support

✅ **SMTP Email Sender (C++)**
- High-performance email delivery
- TLS/SSL support
- Batch processing (configurable)
- Environment-based configuration

✅ **Statistics & Monitoring**
- Campaign performance tracking
- Delivery rates and bounce tracking
- Contact engagement metrics

## Project Structure

```
devnavigator/
├── cpp_crawler/          # C++ email sender
│   ├── src/
│   │   ├── main.cpp
│   │   ├── email_sender.cpp
│   │   ├── crawler.cpp
│   │   └── parser.cpp
│   ├── include/
│   ├── CMakeLists.txt
│   └── build/
├── python_engine/        # Python utilities
│   ├── email_extractor.py
│   ├── database_manager.py
│   ├── template_manager.py
│   ├── analyzer.py
│   ├── recommender.py
│   └── tracker.py
├── database/             # SQLite database
├── data/                 # Data files (emails, lists)
├── tests/                # Test suite
├── devnavigator.py       # Main CLI
├── package.json          # Node dependencies
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
├── setup.sh              # Setup script
├── build.sh              # Build script
└── Dockerfile            # Docker configuration
```

## Quick Start

### 1. Setup

```bash
# Make scripts executable
chmod +x setup.sh build.sh extract-emails.sh

# Run setup
./setup.sh
```

This will:
- Install all dependencies (Python & Node)
- Initialize SQLite database
- Create default email templates
- Build C++ email sender

### 2. Configure SMTP

Copy `.env.example` to `.env` and add your email credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
SMTP_URL=smtp://smtp.gmail.com:587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=your_email@gmail.com
```

**For Gmail**: Use [App Passwords](https://myaccount.google.com/apppasswords)

### 3. Extract Emails

```bash
# From a text file
./extract-emails.sh contacts.txt

# From command line
python3 devnavigator.py extract-emails --file emails.txt --store

# View statistics
python3 devnavigator.py stats
```

### 4. Manage Templates

```bash
# List templates
python3 devnavigator.py list-templates

# Add custom template
python3 devnavigator.py add-template --name "my_template"
```

### 5. Send Emails

```bash
# Build C++ sender
./build.sh

# Send emails
npm run send:emails
```

## Usage Examples

### Extract Emails from File

```bash
python3 devnavigator.py extract-emails \
  --file contacts.txt \
  --store \
  --source "manual"
```

### List Email Templates

```bash
python3 devnavigator.py list-templates
```

### Validate One Email

```bash
python3 devnavigator.py validate-email --email person@example.com
```

### Send Verification Email

```bash
python3 devnavigator.py send-verification-email \
  --email person@example.com \
  --name "Jane Doe"
```

### Confirm Verification

```bash
python3 devnavigator.py confirm-verification \
  --email person@example.com \
  --code 123456
```

**Output:**
```
📋 Email Templates:
--------------------------------------------
⭐ [1] default_campaign
    Subject: We're launching a new children's learning app! 🚀
  [2] partnership_opportunity
    Subject: Partnership Opportunity: New Children's Learning App
  [3] educational_app
    Subject: Join us in launching an innovative learning platform 🎓
--------------------------------------------
```

### Get Campaign Statistics

```bash
python3 devnavigator.py stats
```

**Output:**
```
📊 Campaign Statistics:
----------------------------------------
Total contacts:    1,250
Ready to send:     890
----------------------------------------
```

## Database Schema

### contacts table
```
id (PK)           - Contact ID
email (UNIQUE)    - Email address
name              - Contact name
source            - Where email came from
verified          - Email confirmed flag (0/1)
verification_status - Current verification workflow status
verification_sent_at - Last verification email timestamp
verified_at       - When the email was confirmed
consent           - Consent flag (0/1)
sent              - Email sent flag (0/1)
opened            - Email opened flag (0/1)
bounced           - Email bounced flag (0/1)
unsubscribed      - Unsubscribe flag (0/1)
created_at        - Timestamp
updated_at        - Timestamp
```

### email_templates table
```
id (PK)           - Template ID
name (UNIQUE)     - Template name
subject           - Email subject (supports $variables)
body              - Email body (supports $variables)
is_default        - Default template flag
created_at        - Timestamp
updated_at        - Timestamp
```

### email_verification_requests table
```
id (PK)           - Verification request ID
contact_id (FK)   - Related contact
email             - Email being verified
token_hash        - Hashed verification token
verification_code - Six-digit verification code
template_name     - Template used for the verification email
status            - pending/sent/verified/failed/expired/superseded
requested_at      - Request creation timestamp
expires_at        - Expiration timestamp
verified_at       - Verification completion timestamp
```

### campaigns table
```
id (PK)           - Campaign ID
name              - Campaign name
template_id (FK)  - Email template used
started_at        - Campaign start time
completed_at      - Campaign end time
total_emails      - Total emails in campaign
sent_count        - Emails sent
failed_count      - Emails failed
status            - Campaign status
```

## Security Features

✅ **Email Validation**
- RFC 5322 format validation
- Suspicious domain blocking
- Temporary email service detection
- MX record verification (DNS)

✅ **Environment Security**
- Credentials stored in .env (not in code)
- .gitignore prevents accidental commits
- No hardcoded passwords

✅ **Database Security**
- SQLite file permissions
- Prepared statements (SQL injection prevention)
- Backup recommendations

## Environment Variables

```bash
# SMTP Configuration
SMTP_URL                    # SMTP server URL
SMTP_USERNAME              # SMTP username
SMTP_PASSWORD              # SMTP password
SMTP_FROM                  # From email address
SMTP_USE_TLS               # Enable TLS (true/false)
SMTP_SKIP_TLS_VERIFY       # Skip TLS verification
SMTP_VERBOSE               # Enable verbose logging

# Database
DATABASE_PATH              # Path to SQLite database

# Email Extraction
EXTRACT_SOURCES            # Email sources to use
MAX_EMAILS_PER_BATCH       # Batch size for sending

# Security
ENABLE_VIRUS_CHECK         # Enable security scans
ENABLE_SOURCE_VERIFICATION # Verify email sources
ALLOW_GMAIL_ALIASES        # Allow Gmail aliases
EMAIL_VALIDATION_DNS_TIMEOUT
EMAIL_VALIDATION_STRICT_DNS
EMAIL_VERIFICATION_BASE_URL
EMAIL_VERIFICATION_EXPIRY_HOURS
```

## Building from Source

### Prerequisites

- **C++ Compiler** (g++ 7+)
- **CMake** (3.14+)
- **libcurl** development files
- **sqlite3** development files
- **Python** 3.8+
- **Node.js** 14+

### Build C++ Sender

```bash
cd cpp_crawler
mkdir -p build
cd build
cmake ..
make
```

### Run Tests

```bash
npm test
```

## Docker

```bash
# Build image
npm run docker:build

# Show CLI help inside Docker
npm run docker:run
```

```bash
# Or with plain Docker
docker build -t devnavigator .
docker run --rm -it -v "$(pwd):/workspace" devnavigator
```

```bash
# Initialize the database from Docker
docker run --rm -it -v "$(pwd):/workspace" devnavigator init-db
```

```bash
# Extract emails from a file in the current repo
docker run --rm -it -v "$(pwd):/workspace" devnavigator \
  extract-emails --file sample_emails.csv --store --source manual
```

```bash
# Check saved contacts
docker run --rm -it -v "$(pwd):/workspace" devnavigator stats
docker run --rm -it -v "$(pwd):/workspace" devnavigator queue --queue all --limit 20
```

```bash
# Validate one email from Docker
docker run --rm -it -v "$(pwd):/workspace" devnavigator \
  validate-email --email person@example.com
```

The container now runs the real Python CLI, not the placeholder Node entrypoint. Mounting the repo to `/workspace` lets Docker use your local `.env`, `database/`, and input files naturally.

## Configuration Examples

### Gmail SMTP

```env
SMTP_URL=smtp://smtp.gmail.com:587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true
```

### Mailgun SMTP

```env
SMTP_URL=smtp://smtp.mailgun.org:587
SMTP_USERNAME=postmaster@yourdomain.com
SMTP_PASSWORD=your_mailgun_password
SMTP_USE_TLS=true
```

### Custom SMTP

```env
SMTP_URL=smtp://your.server.com:587
SMTP_USERNAME=username
SMTP_PASSWORD=password
SMTP_USE_TLS=true
```

## Troubleshooting

### "Failed to connect to SMTP"
- Check SMTP credentials
- Verify SMTP URL and port
- Check firewall/network access
- Enable less secure apps (Gmail only)

### "Database locked"
- Close other instances
- Check file permissions
- Restart and retry

### "Email validation failed"
- Check email format
- Verify not on suspicious domain list
- Enable/disable source verification
- Set `EMAIL_VALIDATION_STRICT_DNS=false` if DNS is unavailable in your environment

### "Verification link is a placeholder"
- Set `EMAIL_VERIFICATION_BASE_URL` to your real verification endpoint
- Use `python3 devnavigator.py send-verification-email --dry-run ...` to preview the rendered email

## Contributing

1. Fork repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## License

MIT License - See LICENSE file

## Support

For issues and questions:
- Email: matteopennacchia43@gmail.com
- GitHub: https://github.com/batman-hash/campaign_people

## Roadmap

- [ ] Web UI for campaign management
- [ ] Advanced analytics dashboard
- [ ] API endpoint integration
- [ ] Scheduled email campaigns
- [ ] A/B testing support
- [ ] Advanced segmentation
- [ ] Integration with CRM systems

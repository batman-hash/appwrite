# Email Aliases Guide 📛

## What are Email Aliases?

Email aliases allow you to send emails from a **single email address** but with **different sender display names**. This is perfect for advertising campaigns where you want to test different messaging angles or brand names without needing separate email accounts.

## How It Works

Same underlying email:
```
matteopennacchia43@gmail.com
```

Recipients see different names:
```
"DevNavigator Jobs 🚀" <matteopennacchia43@gmail.com>
"DevNavigator Projects 💼" <matteopennacchia43@gmail.com>
"DevNavigator Academy 🎓" <matteopennacchia43@gmail.com>
```

**Result**: Recipient inbox shows the display name, not the actual email address!

## Built-in Aliases

| Template | Alias Display Name | Use Case |
|----------|-------------------|----------|
| `junior_dev_recruitment` | DevNavigator Jobs 🚀 | Recruiting junior developers |
| `freelance_opportunities` | DevNavigator Projects 💼 | Freelance/contract work |
| `marketing_partnership` | DevNavigator Partnerships 🤝 | B2B partnerships |
| `learning_program` | DevNavigator Academy 🎓 | Training/bootcamp offering |

## Quick Start

### 1. Send Test Email with Alias

```bash
# Dry run (preview, no emails sent)
python3 send_test_emails.py send --dry-run --limit 2

# Send to 3 contacts with "DevNavigator Jobs" alias
python3 send_test_emails.py send --limit 3

# Send using specific template & alias
python3 send_test_emails.py send --template freelance_opportunities --limit 5
```

### 2. Customize Your Aliases

Edit `send_test_emails.py` and modify the `EMAIL_ALIASES` dictionary:

```python
EMAIL_ALIASES = {
    'junior_dev_recruitment': 'Your Custom Name 🚀',
    'freelance_opportunities': 'Your Custom Name 💼',
    'marketing_partnership': 'Your Custom Name 🤝',
    'learning_program': 'Your Custom Name 🎓',
}
```

### 3. Create New Templates with Aliases

```bash
# Add template to database
python3 -c "
from send_test_emails import EmailTemplateManager
manager = EmailTemplateManager()
manager.add_template(
    'custom_template',
    'Your Subject Here',
    'Your email body here with \$email variable'
)
"

# Then add to EMAIL_ALIASES dictionary in send_test_emails.py
```

## Advanced Usage

### A/B Testing with Aliases

Send same content with different sender names to test which resonates better:

```bash
# Campaign A: "DevNavigator Jobs" to 10 recipients
python3 send_test_emails.py send --template junior_dev_recruitment --limit 10

# Campaign B: "DevNavigator Projects" to 10 recipients
python3 send_test_emails.py send --template freelance_opportunities --limit 10

# Compare response rates from campaign tracking
```

### Multiple Sender Identities, Zero Extra Accounts

```
Actual Email: matteopennacchia43@gmail.com
├── "DevNavigator HR" <matteopennacchia43@gmail.com>
├── "DevNavigator Sales" <matteopennacchia43@gmail.com>
├── "DevNavigator Support" <matteopennacchia43@gmail.com>
└── "DevNavigator Partnerships" <matteopennacchia43@gmail.com>
```

All from same Gmail account! Perfect for:
- ✅ Testing different brand identities
- ✅ Department-specific outreach
- ✅ Campaign variation testing
- ✅ Reducing costs (no extra email accounts)
- ✅ Simplified management (single SMTP credentials)

## Email Headers

When recipients see your email, the "From" field will show:

```
From: DevNavigator Jobs 🚀 <matteopennacchia43@gmail.com>
```

Or in client settings, often just displays the alias:

```
DevNavigator Jobs 🚀
```

## Is This Legitimate?

✅ **Yes!** Email aliases are a standard, widely-used feature:

- Professional companies use them (marketing@company, support@company, sales@company all from same address)
- Email standards support them (RFC 5321)
- Gmail, Outlook, and all major providers support them
- Most email marketing platforms use them
- Not against any terms of service when used legitimately

⚠️ **Best Practices:**
- Use truthful company names
- Don't impersonate others
- Include clear unsubscribe links
- Honor reply/bounce handling
- Follow CAN-SPAM/GDPR regulations

## Tracking Results

After sending campaigns, check results:

```bash
# View campaign statistics
python3 devnavigator.py stats

# Query database for send records
sqlite3 database/devnav.db "
SELECT template_id, COUNT(*) as count, 
       SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) as sent
FROM email_logs 
GROUP BY template_id;
"
```

## Combining with Filters

Send filtered campaigns with different aliases:

```bash
# Extract junior frontend developers
python3 devnavigator.py search-filtered --junior 70 --frontend 60

# Then send with "DevNavigator Jobs" alias
python3 send_test_emails.py send --template junior_dev_recruitment --limit 20
```

## Troubleshooting

**Q: Will the email be marked as spam?**
A: Using legitimate sender names reduces spam risk. Ensure you have:
- Valid SPF/DKIM records set up
- Clear unsubscribe links
- Legitimate subject matter
- Low bounce rates

**Q: Can I use any sender name?**
A: Most ESPs allow you to change the display name freely. Gmail will send with whatever name you set. Just keep it professional and honest.

**Q: What if recipients reply?**
A: Replies go to the main email address (matteopennacchia43@gmail.com), regardless of the alias used.

## Full Example Script

Create `campaign_by_alias.sh`:

```bash
#!/bin/bash

echo "📧 Running multi-alias campaign test..."

# Campaign 1: Jobs posting
echo "Sending Jobs campaign..."
python3 send_test_emails.py send --template junior_dev_recruitment --limit 5

# Campaign 2: Freelance projects
echo "Sending Projects campaign..."
python3 send_test_emails.py send --template freelance_opportunities --limit 5

# Campaign 3: Learning program
echo "Sending Academy campaign..."
python3 send_test_emails.py send --template learning_program --limit 5

echo "✅ All campaigns sent!"
python3 devnavigator.py stats
```

Run it:
```bash
chmod +x campaign_by_alias.sh
./campaign_by_alias.sh
```

## Next Steps

1. ✅ Set up email aliases (done!)
2. Run test campaigns with different aliases
3. Track response rates/opens per alias
4. Optimize messaging for top performers
5. Scale winning campaigns
6. A/B test new alias names for max engagement

---

**Questions?** Check documentation:
- [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) - System design
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - All commands
- [HOW_TO_EXTRACT_EMAILS.py](HOW_TO_EXTRACT_EMAILS.py) - Code examples

# 📊 Email & Data Sources Integration Guide

## Best Solutions for Email Databases

### Tier 1: HIGH VOLUME (10K+ emails/month)

#### 1. **Hunter.io** ⭐ RECOMMENDED
**Best for**: Targeted B2B email discovery
- Look up emails by domain
- Verify email accuracy
- Department filtering
- **Pricing**: Free 10/month, $99+/month
- **Pros**: Accurate, fast, easy API
- **Cons**: Expensive for bulk operations
- **Integration**: ✅ Included in code

```bash
# Example usage
python3 <<EOF
from python_engine.data_sources import EmailSourceManager
manager = EmailSourceManager()
emails = manager.search_hunter_io('google.com', department='engineering')
for email in emails:
    print(f"✓ {email['email']} - {email['name']}")
EOF
```

---

#### 2. **Apollo.io** ⭐ BEST VALUE
**Best for**: B2B contact database + enrichment
- 50+ million verified contacts
- Search by company, title, keyword
- Email + phone numbers
- **Pricing**: Free tier, $99+/month
- **Pros**: Huge database, affordable
- **Cons**: Requires valid payment method
- **Integration**: ✅ Included in code

```bash
python3 <<EOF
from python_engine.data_sources import EmailSourceManager
manager = EmailSourceManager()
contacts = manager.search_apollo('CEO at Google', limit=50)
for c in contacts:
    print(f"✓ {c['name']} - {c['email']} ({c['title']})")
EOF
```

---

#### 3. **Clearbit** 
**Best for**: Company intelligence + employee emails
- Company data enrichment
- Employee directory
- Technographics
- **Pricing**: Free (100k rows), $500+/month
- **Pros**: High-quality data, company insights
- **Cons**: Expensive for large campaigns
- **Integration**: ✅ Included in code

---

#### 4. **RocketReach**
**Best for**: Executive targeting
- Contact discovery for executives
- Direct dials + personal emails
- Company details
- **Pricing**: $99+/month
- **Pros**: Great for C-level targeting
- **Cons**: Smaller database than Apollo

---

### Tier 2: BULK IMPORT (CSV/Database)

#### 5. **CSV Upload** ⭐ FREE
**Best for**: Your own email lists
- Import from spreadsheets
- Custom data enrichment
- **Pricing**: Free
- **Integration**: ✅ Built-in

```bash
# Create CSV file
cat > contacts.csv << EOF
email,name,company,department,country
john@google.com,John Smith,Google,Engineering,US
jane@microsoft.com,Jane Doe,Microsoft,Marketing,US
EOF

# Import
python3 <<EOF
from python_engine.data_sources import EmailSourceManager
manager = EmailSourceManager()
count, errors = manager.import_csv('contacts.csv')
print(f"✓ Imported {count} emails")
if errors:
    for error in errors[:5]:
        print(f"✗ {error}")
EOF
```

---

#### 6. **Public Email Lists**
Free sources to combine:
- Domain registration records (WHOIS)
- LinkedIn company pages (scrape legally)
- GitHub user profiles
- Company about pages
- Contact forms submission

**Tools**:
- EmailFinder plugins
- Hunter.io free version
- RocketReachAI

---

### Tier 3: SPECIALIZED

#### 7. **PebbleStorm** (Free email list)
- Pre-compiled contact databases
- Free + premium options

#### 8. **Voila Norbert** ($19/month)
- Email verification
- LinkedIn integration

---

## IP Address & Geo-Targeting Solutions

### 1. **MaxMind GeoIP** ⭐ RECOMMENDED
**Best for**: IP geolocation, targeting by country
- Licensed IP database
- Latitude/longitude
- ISP detection
- **Pricing**: Free (GeoLite2), Paid $120/year
- **Integration**: ✅ Included in code

```bash
python3 <<EOF
from python_engine.data_sources import IPGeoTargeting
geo = IPGeoTargeting()
result = geo.get_geoip_maxmind('8.8.8.8')
print(f"📍 IP: 8.8.8.8 → {result['city']}, {result['country_name']}")
EOF
```

---

### 2. **IP Quality Score** ⭐ FRAUD DETECTION
**Best for**: Validating visitor IP quality
- Fraud score (0-100)
- VPN/Proxy detection
- Bot detection
- **Pricing**: Free tier, $15+/month
- **Integration**: ✅ Included in code

```bash
python3 <<EOF
from python_engine.data_sources import IPGeoTargeting
geo = IPGeoTargeting()
result = geo.verify_ip_quality('1.2.3.4')
if result['fraud_score'] > 75:
    print(f"⚠️  Suspicious IP - Risk: {result['fraud_score']}")
EOF
```

---

### 3. **GeoIP2 (MaxMind)**
- Alternative to MaxMind GeoIP
- Smaller database (better for privacy)

---

## Integration Setup

### 1. Update `.env` with API Keys

```bash
# Copy template
cp .env.example .env

# Add to .env
HUNTER_IO_API_KEY=your_key_here
APOLLO_API_KEY=your_key_here
CLEARBIT_API_KEY=your_key_here
ROCKETREACH_API_KEY=your_key_here
MAXMIND_API_KEY=your_key_here
IPQS_API_KEY=your_key_here
```

### 2. Install Dependencies

```bash
pip install requests
# Already in requirements.txt
```

### 3. Test Connection

```bash
python3 <<EOF
from python_engine.data_sources import EmailSourceManager, IPGeoTargeting

# Test email source
manager = EmailSourceManager()
print("✓ Email sources ready")

# Test IP geo
geo = IPGeoTargeting()
print("✓ IP geo-targeting ready")
EOF
```

---

## Quick Comparison Table

| Service | Type | Price | Volume | Quality | Ease |
|---------|------|-------|--------|---------|------|
| **Hunter.io** | Email | $99+/mo | 10K+ | ⭐⭐⭐⭐⭐ | Easy |
| **Apollo** | Email | $99+/mo | 50K+ | ⭐⭐⭐⭐ | Easy |
| **Clearbit** | Email + Data | $500+/mo | 10K+ | ⭐⭐⭐⭐⭐ | Medium |
| **RocketReach** | Email + Phone | $99+/mo | 5K+ | ⭐⭐⭐⭐ | Easy |
| **MaxMind GeoIP** | IP Geo | $120/yr | Unlimited | ⭐⭐⭐⭐ | Easy |
| **IPQS** | IP Risk | $15+/mo | Unlimited | ⭐⭐⭐⭐⭐ | Easy |

---

## Production Workflow

### Step 1: Get Email Lists
```bash
# Option A: Upload your CSV
python3 devnavigator.py extract-emails \
  --file your_contacts.csv \
  --store

# Option B: Query Hunter.io for domain
python3 <<EOF
from python_engine.data_sources import EmailSourceManager
manager = EmailSourceManager()
emails = manager.search_hunter_io('your-target-domain.com')
# Store in database...
EOF

# Option C: Query Apollo
python3 <<EOF
from python_engine.data_sources import EmailSourceManager
manager = EmailSourceManager()
contacts = manager.search_apollo('CEO at Fortune 500')
# Store in database...
EOF
```

### Step 2: Verify & Enrich
```bash
# Check email validity
python3 devnavigator.py extract-emails \
  --file emails.txt \
  --store

# View quality metrics
python3 <<EOF
from python_engine.data_sources import CampaignDataAnalytics
analytics = CampaignDataAnalytics()
quality = analytics.get_source_quality()
for src in quality:
    print(f"{src['source']}: {src['verification_rate']}% verified")
EOF
```

### Step 3: Geo-Target (Optional)
```bash
# Get visitor IPs and geo-target
python3 <<EOF
from python_engine.data_sources import IPGeoTargeting
geo = IPGeoTargeting()

# Get geo for visitor
result = geo.get_geoip_maxmind('visitor_ip')
print(f"Visitor from: {result['country_name']}")

# Check for fraud
quality = geo.verify_ip_quality('visitor_ip')
if quality['is_vpn']:
    print("VPN detected - flag for review")
EOF
```

### Step 4: Send Campaign
```bash
npm run send:emails
```

---

## Cost Optimization

### Budget Option ($0/month)
1. Use Hunter.io free tier (10/month)
2. Build your own list from public sources
3. Use MaxMind GeoLite2 (free)
4. Total: **FREE**

### Startup Option ($99-200/month)
1. Apollo.io: $99/month (50K+ contacts)
2. IPQS: $15/month (fraud detection)
3. Total: **$114/month**

### Pro Option ($500+/month)
1. Apollo.io: $200/month
2. Hunter.io: $99/month
3. Clearbit: $500/month
4. MaxMind: $10/month
5. Total: **$809/month** (but get premium features)

---

## Security Best Practices

⚠️ **Important**:
- Never store passwords in code
- Use .env for all API keys
- .gitignore prevents accidental commits
- Validate all IP addresses
- Check DNS MX records
- Respect GDPR/privacy laws
- Only email with consent

---

## Next Steps

1. **Choose your data source** based on budget
2. **Get API key** (free trial available for most)
3. **Update .env** with API credentials
4. **Test integration** with small batch
5. **Run full campaign**

**Questions?** Check DEPLOYMENT.md or email matteopennacchia43@gmail.com

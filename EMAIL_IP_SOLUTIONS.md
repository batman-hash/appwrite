# 📊 Email & IP Database Solutions - Complete Reference

## TL;DR - Best Solutions

### 🥇 **Best for Emails: Apollo.io**
- **Price**: $99/month  
- **Contacts**: 50M+ verified B2B
- **Search**: CEO, title, company, domain, keyword
- **API**: Fast, reliable, comprehensive
- **Trial**: Free tier available

### 🥈 **Best for Free: Hunter.io**
- **Price**: FREE (10/month), $99/month (unlimited)
- **Contacts**: Domain-based email discovery
- **Search**: By company domain + department
- **Quality**: High verification rates
- **Trial**: 10 searches free

### 🥉 **Best for CSV: Built-in Importer**
- **Price**: FREE
- **Format**: email, name, company, department, country
- **Validation**: Auto-verified
- **Storage**: SQLite database
- **Integration**: Direct integration

### 🌍 **Best for IP Geo: MaxMind**
- **Price**: FREE (GeoLite2) or $120/year (Premium)
- **Coverage**: Global IP geolocation
- **Data**: Country, city, latitude, longitude, ISP
- **Accuracy**: 99%+ for country-level

### 🚨 **Best for Fraud Detection: IP Quality Score**
- **Price**: FREE tier or $15/month
- **Detection**: VPN, Proxy, Bot, Fraud scoring
- **Accuracy**: Real-time risk analysis
- **Use Case**: Block suspicious traffic
- **Score**: 0-100 fraud risk scale

---

## Solutions Comparison Matrix

| Solution | Type | Free Plan | Paid Price | Volume | Data Type | Use Case |
|----------|------|-----------|------------|--------|-----------|----------|
| **Apollo** | Email DB | ✅ Limited | $99/mo | 50M+ | B2B Contacts | **☆ RECOMMENDED** |
| **Hunter.io** | Email API | ✅ 10/mo | $99/mo | 200M+ | Domain emails | By company |
| **Clearbit** | Enrichment | ✅ 100k | $500/mo | 500M+ | Company data | Company intel |
| **RocketReach** | Email DB | ❌ | $99/mo | 10M+ | Executive focused | C-level targeting |
| **CSV Import** | Importer | ✅ ✅ ✅ | FREE | Unlimited | Your lists | **Your data** |
| **MaxMind GeoIP** | Geo DB | ✅ Free | $120/yr | Global | IP locations | Geo-targeting |
| **IPQS** | Fraud Check | ✅ Limited | $15/mo | Global | IP quality | Fraud detection |

---

## Implementation Status in DevNavigator

### ✅ Fully Integrated & Ready

```
✅ data_sources.py
   ├─ EmailSourceManager
   │  ├─ Hunter.io integration
   │  ├─ Apollo integration
   │  ├─ Clearbit integration
   │  ├─ RocketReach integration
   │  └─ CSV import
   │
   ├─ IPGeoTargeting
   │  ├─ MaxMind GeoIP lookup
   │  └─ IP Quality Score verification
   │
   └─ CampaignDataAnalytics
      ├─ Email distribution by domain
      ├─ Email distribution by country
      └─ Source quality metrics

✅ Enhanced Database Schema
   └─ contacts table: Added company, department, title, country, verified fields
   └─ ip_tracking table: New table for IP history

✅ Environment Configuration
   └─ .env: Complete API key placeholders for all services
```

---

## Quick API Usage Examples

### 1️⃣ Hunter.io - Find Company Emails

```python
from python_engine.data_sources import EmailSourceManager
manager = EmailSourceManager()

# Search by domain
emails = manager.search_hunter_io('microsoft.com', department='sales')

for email in emails:
    print(f"Email: {email['email']}")
    print(f"Name: {email['name']}")
    print(f"Department: {email['department']}")
    print(f"Verified: {email['verified']}\n")
```

**Setup**:
1. Go to https://hunter.io
2. Sign up (free 10/month)
3. Get API key: Settings → API
4. Add to .env: `HUNTER_API_KEY=your_key`

---

### 2️⃣ Apollo - Search 50M+ Contacts

```python
from python_engine.data_sources import EmailSourceManager
manager = EmailSourceManager()

# Search by criteria
contacts = manager.search_apollo('CEO at Fortune 500', limit=100)

for c in contacts:
    print(f"Name: {c['name']}")
    print(f"Email: {c['email']}")
    print(f"Title: {c['title']}")
    print(f"Company: {c['company']}")
    print(f"Phone: {c['phone']}")
    print(f"Verified: {c['verified']}\n")
```

**Setup**:
1. Go to https://apollo.io
2. Sign up (free tier available)
3. Get API key: Settings → API
4. Add to .env: `APOLLO_API_KEY=your_key`

---

### 3️⃣ CSV Import - Upload Your Lists

**Create contacts.csv**:
```csv
email,name,company,department,country
john@google.com,John Smith,Google,Engineering,US
jane@microsoft.com,Jane Doe,Microsoft,Marketing,US
bob@apple.com,Bob Johnson,Apple,Design,US
```

**Python Code**:
```python
from python_engine.data_sources import EmailSourceManager
manager = EmailSourceManager()

# Import CSV
imported, errors = manager.import_csv('contacts.csv')

print(f"✓ Imported: {imported}")
print(f"✗ Errors: {len(errors)}")
```

---

### 4️⃣ MaxMind GeoIP - Geolocate IPs

```python
from python_engine.data_sources import IPGeoTargeting
geo = IPGeoTargeting()

# Get geolocation
result = geo.get_geoip_maxmind('8.8.8.8')

print(f"Country: {result['country_name']}")
print(f"City: {result['city']}")
print(f"Timezone: {result['timezone']}")
print(f"ISP: {result['isp']}")
```

**Setup**:
1. Go to https://maxmind.com
2. Download GeoLite2 (free) or get API key
3. Add to .env: `MAXMIND_API_KEY=your_key`

---

### 5️⃣ IP Quality Score - Detect Fraud

```python
from python_engine.data_sources import IPGeoTargeting
geo = IPGeoTargeting()

# Check IP quality
result = geo.verify_ip_quality('1.2.3.4')

print(f"Fraud Score: {result['fraud_score']}/100")
print(f"Is VPN: {result['is_vpn']}")
print(f"Is Proxy: {result['is_proxy']}")
print(f"Is Bot: {result['is_bot']}")
print(f"Threats: {result['threat_types']}")

if result['fraud_score'] > 75:
    print("🚨 BLOCK - High risk IP")
```

**Setup**:
1. Go to https://ipqualityscore.com
2. Free tier available
3. Get API key from dashboard
4. Add to .env: `IPQS_API_KEY=your_key`

---

## Pricing Breakdown

### FREE Option ($0/month)
```
✓ Hunter.io free tier: 10 searches/month
✓ Apollo free tier: Limited but available
✓ CSV imports: Unlimited
✓ MaxMind GeoLite2: Free global GeoIP
✓ Your own database: Free
════════════════════════════
TOTAL: $0/month ✓ BEST FOR STARTUPS
```

### Startup Option ($99/month)
```
✓ Apollo.io: $99/month (50M+ contacts)
✓ Unlimited searches
✓ All API features
✓ Excel for small budgets
════════════════════════════
TOTAL: $99/month ✓ RECOMMENDED
```

### Professional Option ($200+/month)
```
✓ Apollo: $200/month (higher tier)
✓ Hunter.io: $99/month (for specific domains)
✓ MaxMind Premium: $10/month
✓ IPQS: $15/month (fraud checks)
════════════════════════════
TOTAL: $324/month ✓ FOR AGENCIES
```

### Enterprise ($500+/month)
```
✓ Apollo: $500/month (enterprise plan)
✓ Hunter.io: $500/month
✓ Clearbit: $500/month (company data)
✓ RocketReach: $500/month
✓ Plus integrations & support
════════════════════════════
TOTAL: $2,000+/month ✓ FOR LARGE TEAMS
```

---

## How to Get Started (5 Steps)

### Step 1: Update .env
```bash
cp .env.example .env
nano .env
```

### Step 2: Choose Your Data Source

**Option A - Free**: Use CSV import
```bash
# Create contacts.csv with your list
python3 << 'EOF'
from python_engine.data_sources import EmailSourceManager
manager = EmailSourceManager()
count, errors = manager.import_csv('contacts.csv')
print(f"✓ Imported {count}")
EOF
```

**Option B - $99/month**: Use Apollo
```bash
# 1. Sign up at https://apollo.io
# 2. Copy API key to .env: APOLLO_API_KEY=xxx
# 3. Run query
python3 << 'EOF'
from python_engine.data_sources import EmailSourceManager
manager = EmailSourceManager()
contacts = manager.search_apollo('CEO', limit=100)
print(f"✓ Found {len(contacts)}")
EOF
```

### Step 3: View Results
```bash
python3 devnavigator.py stats
```

### Step 4: Geo-Target (Optional)
```python
from python_engine.data_sources import IPGeoTargeting
geo = IPGeoTargeting()
result = geo.get_geoip_maxmind('visitor_ip')
print(f"Target: {result['country']}")
```

### Step 5: Send Campaign
```bash
npm run send:emails
```

---

## File Reference

**Core Files**:
- `python_engine/data_sources.py` - Main integration code (ready to use)
- `python_engine/database_manager.py` - Enhanced schema with new fields
- `.env` - Configuration (update with your API keys)
- `DATA_SOURCES.md` - Detailed integration guide
- `QUICK_START_SOURCES.py` - Example scripts

**Database Tables**:
- `contacts` - Enhanced with company, department, title, country, verified
- `ip_tracking` - New table for IP geolocation and fraud scores
- `email_templates` - For campaign templates
- `campaigns` - Campaign tracking

---

## Troubleshooting

**API key not working?**
```bash
# Check .env is loaded
python3 << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()
print(os.getenv('APOLLO_API_KEY'))  # Should show your key
EOF
```

**Import failed?**
```bash
# Check CSV format
cat contacts.csv | head
# Should have: email,name,company,department,country
```

**Quota exceeded?**
- Apollo free tier: Limited searches
- Hunter.io free: 10/month only
- Solution: Upgrade to paid tier or use CSV import

---

## Next Steps

1. ✅ Choose preferred data source
2. ✅ Get API key (free trial recommended)
3. ✅ Update .env with credentials
4. ✅ Test with small batch
5. ✅ Run campaign

**Need Help?**
- See [DATA_SOURCES.md](DATA_SOURCES.md) for detailed docs
- Run: `python3 QUICK_START_SOURCES.py`
- Email: matteopennacchia43@gmail.com

---

## All Available Solutions

### Email Extraction
✅ Hunter.io - Domain-based
✅ Apollo.io - Search 50M+
✅ Clearbit - Company intel
✅ RocketReach - Executive focused
✅ CSV Import - Your lists

### Enrichment
✅ Apollo - Verified contacts
✅ Clearbit - Company data
✅ LinkedIn API - Public profiles
✅ Your database - Custom

### Geo-Targeting
✅ MaxMind GeoIP - Global locations
✅ IP Quality Score - Fraud detection

### Ready in DevNavigator
✅ Built-in database (SQLite)
✅ Template system
✅ Bulk sender (C++)
✅ Analytics & reporting
✅ Security checks

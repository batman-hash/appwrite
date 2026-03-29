# 🌍 Free Tier Geo-Targeting Guide

**NO API KEYS. NO COSTS. UNLIMITED USAGE.**

DevNavigator includes completely free geo-targeting using three reliable APIs:
- **IP-API.COM** - 45 requests/minute
- **IPify** - Unlimited  
- **GeoIP-DB** - Unlimited
- **MaxMind GeoLite2** - Offline database (optional)

---

## Quick Start (2 Minutes)

### 1. Geolocate a Single IP

```python
from python_engine.free_geo_targeting import FreeGeoTargeting

geo = FreeGeoTargeting()

# Get location from IP (no API key needed!)
result = geo.get_free_geoip('8.8.8.8')

print(f"Country: {result['country']}")
print(f"City: {result['city']}")
print(f"Timezone: {result['timezone']}")
print(f"ISP: {result['isp']}")
```

### 2. Target Contacts by Country

```python
from python_engine.free_geo_targeting import FreeGeoTargeting

geo = FreeGeoTargeting()

# Find all contacts in US, UK, Canada
count, contacts = geo.target_by_country(['US', 'UK', 'CA'])

print(f"Found {count} contacts")
for c in contacts[:5]:
    print(f"  {c['email']} - {c['country']}")
```

### 3. Send to Specific Region Only

```python
# Update your contacts with country data
python3 devnavigator.py extract-emails --file contacts.csv --store

# Import your contacts with country field
# email,name,country
# john@google.com,John,US
# jane@bbc.co.uk,Jane,UK

# Then run the campaign
npm run send:emails
```

---

## Available Free Services

### ✅ IP-API.COM (Primary)

**Best for**: General purpose, most accurate

```
Rate limit: 45 requests/minute
Cost: FREE
API Key: None required
Accuracy: 99%+ country, 95% city
```

**Returns**:
- Country, Country Code
- City
- Latitude, Longitude
- Timezone
- ISP

### ✅ IPify (Fallback)

**Best for**: Redundancy, unlimited usage

```
Rate limit: Unlimited (free tier)
Cost: FREE
API Key: None required
Accuracy: 99%+ country
```

### ✅ GeoIP-DB (Fallback)

**Best for**: Stability, fully independent

```
Rate limit: Unlimited
Cost: FREE
API Key: None required
Accuracy: 99%+ country
```

### ✅ MaxMind GeoLite2 (Optional)

**Best for**: 100% offline, highest accuracy

```
Download: FREE from maxmind.com
Cost: FREE
Setup: 5 minutes
Accuracy: 99.75% country-level
```

---

## Use Cases

### 📧 Segment by Country

```python
geo = FreeGeoTargeting()

# English-speaking countries
count, contacts = geo.target_by_country(['US', 'UK', 'CA', 'AU', 'NZ'])
print(f"English speakers: {count}")

# Europe only
count, contacts = geo.target_by_country(['GB', 'DE', 'FR', 'IT', 'ES'])
print(f"Europe: {count}")

# APAC
count, contacts = geo.target_by_country(['AU', 'SG', 'JP', 'CN'])
print(f"APAC: {count}")
```

### 🕐 Schedule by Timezone

Send emails during business hours in their timezone:

```python
geo = FreeGeoTargeting()

# Handle all timezones
timezones = [
    'America/New_York',    # 9 AM EST
    'America/Chicago',     # 9 AM CST
    'America/Los_Angeles', # 9 AM PST
    'Europe/London',       # 9 AM GMT
    'Asia/Tokyo'           # 9 AM JST
]

count, contacts = geo.target_by_timezone(timezones)
print(f"Found {count} in business hours zones")
```

### 🔍 Look Up Visitor Location

```python
geo = FreeGeoTargeting()

# Check if cached first
cached = geo.get_cached_geoip('visitor_ip')

if cached:
    print(f"From cache: {cached['country']}")
else:
    # Look up and cache
    result = geo.get_free_geoip('visitor_ip')
    if result.get('status') == 'success':
        geo.cache_geoip('visitor_ip', result)
        print(f"Looked up: {result['country']}")
```

### 📊 View Statistics

```python
geo = FreeGeoTargeting()

stats = geo.get_statistics()

print("Top countries:")
for c in stats['top_countries']:
    print(f"  {c['country']}: {c['count']} contacts")

print("\\nTop timezones:")
for tz in stats['top_timezones']:
    print(f"  {tz['timezone']}: {tz['count']}")

print(f"\\nCached IPs: {stats['total_cached_ips']}")
```

---

## Database Schema

### Enhanced `contacts` Table

```sql
CREATE TABLE contacts (
    ...
    country TEXT,        -- 'US', 'UK', 'CA', etc
    city TEXT,           -- City name
    ...
);
```

### New `ip_tracking` Table

```sql
CREATE TABLE ip_tracking (
    ip_address TEXT PRIMARY KEY,
    country TEXT,
    city TEXT,
    latitude REAL,
    longitude REAL,
    timezone TEXT,
    isp TEXT,
    fraud_score INTEGER,
    is_vpn INTEGER,
    is_proxy INTEGER,
    is_bot INTEGER,
    threat_types TEXT,
    data_source TEXT,    -- 'ip-api.com', 'ipify', etc
    last_verified TIMESTAMP,
    created_at TIMESTAMP
);
```

---

## Complete Workflow Example

### Step 1: Create Your Contact List with Countries

```bash
cat > contacts.csv << EOF
email,name,company,country
john@google.com,John Smith,Google,US
jane@bbc.co.uk,Jane Doe,BBC,UK
bob@maple.com,Bob Johnson,Maple,CA
alice@optus.com.au,Alice Brown,Optus,AU
EOF
```

### Step 2: Import Contacts

```bash
python3 << 'EOF'
from python_engine.data_sources import EmailSourceManager
manager = EmailSourceManager()

count, errors = manager.import_csv('contacts.csv')
print(f"✓ Imported {count} contacts")
EOF
```

### Step 3: View by Country

```bash
python3 << 'EOF'
from python_engine.free_geo_targeting import FreeGeoTargeting
geo = FreeGeoTargeting()

# Target English-speaking countries
count, contacts = geo.target_by_country(['US', 'UK', 'CA', 'AU'])

print(f"📍 Found {count} in English-speaking countries:")
for c in contacts:
    print(f"   {c['email']} ({c['country']})")
EOF
```

### Step 4: Send Campaign

```bash
npm run send:emails
```

### Step 5: Check Stats

```bash
python3 << 'EOF'
from python_engine.free_geo_targeting import FreeGeoTargeting
geo = FreeGeoTargeting()

stats = geo.get_statistics()
print(f"Contacts by country: {stats['top_countries']}")
EOF
```

---

## Advanced: MaxMind GeoLite2 (100% Offline)

For maximum speed and 100% offline operation:

### 1. Download GeoLite2

```bash
# Go to: https://www.maxmind.com/en/geolite2-country-csv
# Sign up (free)
# Download: GeoLite2-Country-Blocks-IPv4.csv
```

### 2. Load into Database

```python
from python_engine.free_geo_targeting import FreeGeoTargeting

geo = FreeGeoTargeting()

# Load MaxMind GeoLite2 CSV
success = geo.load_geolite2_csv('./GeoLite2-Country-Blocks-IPv4.csv')

if success:
    print("✓ Loaded MaxMind GeoLite2")
    # Now all lookups use local database, no API calls!
```

### 3. Now All Queries Use Local DB

```python
# This no longer makes API calls - uses local database
result = geo.get_free_geoip('123.45.67.89')
# Instant results, no rate limits!
```

---

## Performance Tips

### Use Caching

```python
geo = FreeGeoTargeting()

# First time: API lookup (~100ms)
result1 = geo.get_free_geoip('8.8.8.8')
geo.cache_geoip('8.8.8.8', result1)

# Second time: Cache lookup (~1ms)
cached = geo.get_cached_geoip('8.8.8.8')
```

### Batch Processing

```python
import time

geo = FreeGeoTargeting()
ips = ['8.8.8.8', '1.1.1.1', '208.67.222.222']

for ip in ips:
    result = geo.get_free_geoip(ip)
    geo.cache_geoip(ip, result)
    time.sleep(2)  # Respect 45 req/min limit
```

---

## Troubleshooting

### "All services failed"

```python
# Check internet connection
import requests
response = requests.get('https://ip-api.com/json/8.8.8.8', timeout=5)
print(response.status_code)
```

### Rate Limited

```
Error: 429 Too Many Requests

Solution: Wait 60 seconds or switch to MaxMind GeoLite2 offline
```

### Inaccurate Results

```python
# Use MaxMind GeoLite2 for highest accuracy
geo.load_geolite2_csv('./geolite2.csv')
```

---

## Cost Comparison

| Service | Method | Cost/Month | Accuracy |
|---------|--------|-----------|----------|
| **Free Tier (This)** | 3 APIs + Caching | **$0** | ⭐⭐⭐⭐ |
| ip-api.com | API | $0 | ⭐⭐⭐⭐ |
| MaxMind GeoIP2 | Paid API | $120/year | ⭐⭐⭐⭐⭐ |
| IP Quality Score | API | $15/mo | ⭐⭐⭐⭐⭐ |
| Clearbit | API | $500/mo | ⭐⭐⭐⭐⭐ |

**✅ Win with FREE TIER**

---

## Limits & Quotas

| Service | Limit | Solution |
|---------|-------|----------|
| IP-API.COM | 45/min | Cache, use IPify fallback |
| IPify | Unlimited | Use as primary backup |
| GeoIP-DB | Unlimited | Use as secondary backup |
| MaxMind | Unlimited | Download free database |

**Total: Effectively unlimited with caching**

---

## Files Reference

- **`python_engine/free_geo_targeting.py`** - Main module (100% complete)
- **`FREE_GEO_TARGETING_GUIDE.py`** - Quick reference examples
- **`.env`** - Configuration (no API keys needed!)
- **`python_engine/database_manager.py`** - Enhanced schema with country fields

---

## What You Get

✅ **Completely Free**
- No API keys required
- No rate limit breaker needed
- No monthly costs

✅ **Unlimited Functionality**
- Geolocate any IP
- Target by country
- Target by timezone
- Intelligent caching
- Offline support (with GeoLite2)

✅ **Production Ready**
- 3 fallback services
- Automatic retry logic
- Cached results
- Database integration

---

## Next Steps

1. ✅ Your system already has everything installed
2. ✅ No configuration needed
3. ✅ Just use it:

```python
from python_engine.free_geo_targeting import FreeGeoTargeting
geo = FreeGeoTargeting()
result = geo.get_free_geoip('8.8.8.8')
print(result)
```

That's it! **Geo-targeting is now ready to use.**

---

**Questions?** See `FREE_GEO_TARGETING_GUIDE.py` for more examples or email matteopennacchia43@gmail.com

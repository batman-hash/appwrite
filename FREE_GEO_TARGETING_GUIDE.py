#!/usr/bin/env python3
"""
Free Tier Geo-Targeting Quick Start
Copy-paste examples - no API keys needed!
"""

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║              FREE TIER GEO-TARGETING - NO API KEYS REQUIRED               ║
║                     Works Completely Free Forever                          ║
╚════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AVAILABLE FREE SERVICES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ IP-API.COM (Primary)
   • 45 requests/minute
   • NO API KEY NEEDED
   • Accurate: Country, city, timezone, ISP
   • https://ip-api.com

✅ IPify (Fallback)
   • Unlimited requests
   • NO API KEY NEEDED
   • Country, city, timezone
   • https://ipify.org

✅ GeoIP-DB (Fallback)
   • Unlimited requests
   • NO API KEY NEEDED
   • Country, city, coordinates
   • https://geoip-db.com

✅ MaxMind GeoLite2 (Optional)
   • FREE database download
   • 100% local, unlimited
   • More accurate than APIs
   • https://maxmind.com

Bonus: Caching = Never repeat lookups!


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLE 1: Geolocate a Single IP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from python_engine.free_geo_targeting import FreeGeoTargeting

geo = FreeGeoTargeting()

# Geolocate an IP
result = geo.get_free_geoip('8.8.8.8')

print(f"📍 IP: {result['ip']}")
print(f"   Country: {result['country']}")
print(f"   City: {result['city']}")
print(f"   Timezone: {result['timezone']}")
print(f"   ISP: {result['isp']}")
print(f"   Coordinates: {result['latitude']}, {result['longitude']}")

# Cache it for next time
geo.cache_geoip('8.8.8.8', result)
print("✓ Cached for reuse")


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLE 2: Target Contacts by Country
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from python_engine.free_geo_targeting import FreeGeoTargeting

geo = FreeGeoTargeting()

# Find all contacts in US, UK, Canada
target_countries = ['US', 'UK', 'CA']
count, contacts = geo.target_by_country(target_countries)

print(f"📧 Found {count} contacts in {', '.join(target_countries)}")
for contact in contacts[:5]:
    print(f"  {contact['email']} - {contact['name']} ({contact['country']})")


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLE 3: Target by Timezone (Best Send Times)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from python_engine.free_geo_targeting import FreeGeoTargeting
from datetime import datetime, timezone

geo = FreeGeoTargeting()

# Send during business hours in their timezone
# 9 AM EST = 2 PM GMT = 12 PM CST
target_timezones = [
    'America/New_York',     # Eastern
    'America/Chicago',      # Central
    'Europe/London'         # GMT
]

count, contacts = geo.target_by_timezone(target_timezones)

print(f"🕐 Found {count} contacts in target timezones")
for contact in contacts[:5]:
    print(f"  {contact['email']} - {contact['timezone']}")


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLE 4: Batch Geolocate Multiple IPs with Caching
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from python_engine.free_geo_targeting import FreeGeoTargeting

geo = FreeGeoTargeting()

ips_to_check = [
    '8.8.8.8',
    '1.1.1.1',
    '208.67.222.222'
]

for ip in ips_to_check:
    # Check cache first
    cached = geo.get_cached_geoip(ip)
    
    if cached:
        print(f"✓ {ip} → {cached['country']} (cached)")
    else:
        # Lookup if not cached
        result = geo.get_free_geoip(ip)
        if result.get('status') == 'success':
            print(f"✓ {ip} → {result['country']}")
            geo.cache_geoip(ip, result)
        else:
            print(f"✗ {ip} → {result.get('reason')}")


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLE 5: View Geo Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from python_engine.free_geo_targeting import FreeGeoTargeting

geo = FreeGeoTargeting()

stats = geo.get_statistics()

print("📊 Top Countries:")
for country in stats['top_countries'][:10]:
    print(f"  {country['country']}: {country['count']} contacts")

print("\\n🕐 Top Timezones:")
for tz in stats['top_timezones'][:10]:
    print(f"  {tz['timezone']}: {tz['count']} cached")

print(f"\\n💾 Cached IPs: {stats['total_cached_ips']}")


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPLETE WORKFLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 1. Add contacts with countries
python3 << 'EOF'
from python_engine.data_sources import EmailSourceManager
manager = EmailSourceManager()

# Create CSV with country data
import csv
with open('contacts.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['email', 'name', 'company', 'country'])
    writer.writerow(['john@google.com', 'John', 'Google', 'US'])
    writer.writerow(['jane@bbc.co.uk', 'Jane', 'BBC', 'UK'])
    writer.writerow(['bob@azure.com', 'Bob', 'Microsoft', 'CA'])

# Import
count, errors = manager.import_csv('contacts.csv')
print(f"✓ Imported {count}")
EOF

# 2. Geolocate IPs (optional)
python3 << 'EOF'
from python_engine.free_geo_targeting import FreeGeoTargeting
geo = FreeGeoTargeting()

# Geolocate some IPs
ips = ['123.45.67.89', '98.76.54.32']
for ip in ips:
    result = geo.get_free_geoip(ip)
    if result.get('status') == 'success':
        geo.cache_geoip(ip, result)
        print(f"✓ {ip} → {result['country']}")
EOF

# 3. Segment by country
python3 << 'EOF'
from python_engine.free_geo_targeting import FreeGeoTargeting
geo = FreeGeoTargeting()

# Target English-speaking countries
count, contacts = geo.target_by_country(['US', 'UK', 'CA', 'AU'])
print(f"📍 Found {count} in English-speaking countries")

for c in contacts[:3]:
    print(f"   {c['email']}")
EOF

# 4. Send campaign to specific region
npm run send:emails
# Only sends to filtered contacts


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRICING COMPARISON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ MaxMind Premium:  $120/year
❌ IP Quality Score: $15+/month
❌ Clearbit:         $500+/month

✅ FREE TIER:        $0/month ← YOU WIN!

• IP-API.COM:  45 req/min, unlimited IPs
• IPify:       Unlimited requests
• GeoIP-DB:    Unlimited requests
• MaxMind GeoLite2: FREE database
• Caching:     Unlimited (local)

TOTAL COST: $0


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FAQ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Q: Do I need API keys?
A: NO! All services are completely free with no registration needed.

Q: How accurate is it?
A: 95%+ accurate for country/city level. Good enough for targeting.

Q: Rate limits?
A: IP-API.COM = 45/min. Just use caching to never repeat lookups!

Q: Can I use offline?
A: Yes! Download MaxMind GeoLite2 CSV for 100% offline operation.

Q: What's the difference from paid APIs?
A: No rate limits breaker, slightly less accuracy, but FREE forever.

Q: How do I enable MaxMind GeoLite2?
A: 1. Download: https://maxmind.com/geoip-lite
   2. Convert CSV
   3. Call: geo.load_geolite2_csv('path/to/file.csv')


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILES REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Main module:        python_engine/free_geo_targeting.py
This guide:         FREE_GEO_TARGETING_GUIDE.py

Usage in your code:

    from python_engine.free_geo_targeting import FreeGeoTargeting
    geo = FreeGeoTargeting()
    
    # No config needed!
    result = geo.get_free_geoip('visitor_ip')


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUICK START (30 SECONDS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

cd devnavigator

python3 << 'EOF'
from python_engine.free_geo_targeting import FreeGeoTargeting
geo = FreeGeoTargeting()

# Try it
result = geo.get_free_geoip('8.8.8.8')
print(f"✓ {result['country']} - No API key needed!")

# Find contacts by location
count, contacts = geo.target_by_country(['US', 'UK'])
print(f"✓ Found {count} contacts in US & UK")
EOF


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FREE TIER = ENTERPRISE FEATURES AT $0 COST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

""")

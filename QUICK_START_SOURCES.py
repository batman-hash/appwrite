#!/usr/bin/env python3
"""
Quick Start Guide for Email Data Sources
Copy-paste examples to get started
"""

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    DEVNAVIGATOR - DATA SOURCE GUIDE                        ║
║                  Reference Examples & Commands                             ║
╚════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. HUNTER.IO - Find emails by company domain
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Setup:
  1. Go to: https://hunter.io
  2. Sign up (10 free searches/month)
  3. Copy API key from dashboard
  4. Add to .env: HUNTER_IO_API_KEY=your_key

Example Code:
  from python_engine.data_sources import EmailSourceManager
  manager = EmailSourceManager()
  
  # Find all engineers at Google
  emails = manager.search_hunter_io('google.com', department='engineering')
  
  # Store in database
  for email in emails:
      print(f"✓ {email['email']} - {email['name']}")

Cost: $99/month = ~3,300 searches


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. APOLLO.IO - Search 50M+ verified contacts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Setup:
  1. Go to: https://apollo.io
  2. Sign up (Free tier available)
  3. Get API key from settings
  4. Add to .env: APOLLO_API_KEY=your_key

Example Code:
  from python_engine.data_sources import EmailSourceManager
  manager = EmailSourceManager()
  
  # Find all CEOs in San Francisco
  contacts = manager.search_apollo('CEO at San Francisco', limit=100)
  
  for c in contacts:
      if c['verified']:
          print(f"✓ {c['name']} - {c['email']} ({c['title']})")

Cost: $99/month = Unlimited (within plan limits)
Best For: CEO/executive targeting


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. CSV IMPORT - Upload your own list
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Create CSV File (contacts.csv):
  email,name,company,department,country
  john@apple.com,John Smith,Apple,Engineering,US
  jane@microsoft.com,Jane Doe,Microsoft,Marketing,US
  admin@github.com,Admin User,GitHub,DevOps,US

Example Code:
  from python_engine.data_sources import EmailSourceManager
  manager = EmailSourceManager()
  
  count, errors = manager.import_csv('contacts.csv')
  print(f"✓ Imported {count} emails")
  
  if errors:
      for error in errors[:5]:
          print(f"✗ {error}")

Cost: FREE
Best For: Your existing contact lists


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. MAXMIND GEOIP - Get location from IP address
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Setup:
  1. Go to: https://maxmind.com
  2. Download GeoLite2 (free) or get API key
  3. Add to .env: MAXMIND_API_KEY=your_key

Example Code:
  from python_engine.data_sources import IPGeoTargeting
  geo = IPGeoTargeting()
  
  # Geolocate an IP address
  result = geo.get_geoip_maxmind('8.8.8.8')
  
  print(f"📍 IP: 8.8.8.8")
  print(f"   Country: {result['country_name']}")
  print(f"   City: {result['city']}")
  print(f"   Timezone: {result['timezone']}")
  print(f"   ISP: {result['isp']}")

Cost: FREE (GeoLite2) or $120/year (Premium)
Use Case: Geographic targeting, traffic analysis


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5. IP QUALITY SCORE - Detect fraud & bots
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Setup:
  1. Go to: https://ipqualityscore.com
  2. Free tier available
  3. Copy API key
  4. Add to .env: IPQS_API_KEY=your_key

Example Code:
  from python_engine.data_sources import IPGeoTargeting
  geo = IPGeoTargeting()
  
  # Check if IP is suspicious
  result = geo.verify_ip_quality('visitor_ip')
  
  print(f"Fraud Score: {result['fraud_score']}/100")
  
  if result['is_vpn']:
      print("⚠️  VPN detected")
  if result['is_bot']:
      print("⚠️  Bot detected")
      
  if result['fraud_score'] > 75:
      print("🔴 BLOCK - High risk IP")

Cost: FREE tier or $15/month
Use Case: Block bots, VPNs, fraud


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUICK SETUP SCRIPT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 1. Get API keys (free trials)
#    Hunter.io: https://hunter.io/try
#    Apollo: https://app.apollo.io/
#    MaxMind: https://www.maxmind.com/
#    IPQS: https://ipqualityscore.com/

# 2. Update .env
nano .env
# Add your API keys:
# HUNTER_IO_API_KEY=...
# APOLLO_API_KEY=...
# MAXMIND_API_KEY=...
# IPQS_API_KEY=...

# 3. Test one source
python3 << 'EOF'
from python_engine.data_sources import EmailSourceManager
manager = EmailSourceManager()

# Test Hunter.io
try:
    emails = manager.search_hunter_io('google.com')
    print(f"✓ Hunter.io: {len(emails)} emails found")
except Exception as e:
    print(f"✗ Hunter.io error: {e}")

# Test Apollo
try:
    contacts = manager.search_apollo('CEO', limit=5)
    print(f"✓ Apollo: {len(contacts)} contacts found")
except Exception as e:
    print(f"✗ Apollo error: {e}")
EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRICING COMPARISON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Budget Option ($0/month):
  • Hunter.io free: 10 searches/month
  • Apollo free tier: Limited searches
  • MaxMind GeoLite2: Free GeoIP
  • Your own CSV: Free imports
  Total: $0 ✓

Startup Option ($99/month):
  • Apollo.io: $99/month
  • Unlimited searches from 50M+ contacts
  Total: $99 ✓ RECOMMENDED

Pro Option ($500+/month):
  • Apollo: $200/month
  • Hunter.io: $99/month  
  • Clearbit: $500/month (company data)
  Total: $799+

Enterprise Custom Pricing:
  • Volume discounts available
  • Custom integrations
  Contact sales teams directly


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKFLOW EXAMPLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Extract Emails:
   python3 devnavigator.py extract-emails --file my_contacts.csv --store

2. Check Quality:
   python3 << 'EOF'
   from python_engine.data_sources import CampaignDataAnalytics
   analytics = CampaignDataAnalytics()
   stats = analytics.get_source_quality()
   for s in stats:
       print(f"{s['source']}: {s['verification_rate']}% verified")
   EOF

3. View Statistics:
   python3 devnavigator.py stats

4. Send Campaign:
   npm run send:emails


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEED HELP?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 See DATA_SOURCES.md for detailed docs
📧 Email: matteopennacchia43@gmail.com
🐙 GitHub: https://github.com/batman-hash/campaign_people

""")

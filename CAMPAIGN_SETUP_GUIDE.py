#!/usr/bin/env python3
"""
Campaign Setup Guide - Free Tier
Targeting: Junior Developers, Frontend, Remote, Job Seekers
"""

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║         DEVNAVIGATOR - FREE TIER CAMPAIGN SETUP                           ║
║     Junior Developers | Frontend | Remote | Job Seekers | Marketing      ║
║                         ZERO COST SETUP                                    ║
╚════════════════════════════════════════════════════════════════════════════╝


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1: GET FREE EMAILS (MINIMUM SETUP) - 30 MINUTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OPTION A: GitHub (Completely Free, No Registration)
─────────────────────────────────────────────────────

Search github.com for:
  • "junior developer" + location:remote
  • "frontend developer" + "work from home"
  • "entry level" + "looking for job"

Python script to extract:

import requests
import json

# Search GitHub API (FREE, no key needed for 60 req/hour)
search_terms = [
    'junior developer remote',
    'entry level frontend developer',
    'freelance web developer'
]

for term in search_terms:
    url = f"https://api.github.com/search/users?q={term}+type:user"
    response = requests.get(url)
    users = response.json()['items']
    
    for user in users:
        user_data = requests.get(f"https://api.github.com/users/{user['login']}").json()
        
        # Extract email if public
        if user_data.get('email'):
            print(f"✓ {user_data['name']} - {user_data['email']}")

Cost: FREE | Time: 10 minutes | Emails: 50-200


OPTION B: Hunter.io Free (10 searches/month)
──────────────────────────────────────────────

1. Sign up: https://hunter.io
2. Get free API key (10 searches/month)
3. Search company domains:

tech_companies = [
    'google.com', 'microsoft.com', 'github.com',
    'stripe.com', 'airbnb.com', 'notion.so'
]

for domain in tech_companies:
    # Use Hunter.io API
    emails = hunt_domain(domain)
    # Filter for junior/frontend/marketing

Cost: FREE (10/month) | Time: 5 minutes | Emails: 10-50


OPTION C: Apollo.io Free Tier
──────────────────────────────

1. Sign up: https://apollo.io
2. Configure free tier search
3. Search for:

from python_engine.data_sources import EmailSourceManager
manager = EmailSourceManager()

# Your specific targeting
searches = [
    'junior developer remote',
    'entry level frontend',
    'marketing remote',
    'freelancer developer'
]

for search in searches:
    contacts = manager.search_apollo(search, limit=100)
    # Import to database

Cost: FREE | Time: 10 minutes | Emails: 100-500


OPTION D: Your Own CSV (Completely Free)
──────────────────────────────────────────

Create contacts.csv:

email,name,title,company,country,department
john@example.com,John Smith,Junior Frontend Developer,TechStartup,US,Engineering
jane@example.com,Jane Doe,Entry Level Programmer,StartupXYZ,UK,Development
bob@example.com,Bob Johnson,Marketing Manager Remote,Agency,CA,Marketing

Then import:

python3 devnavigator.py extract-emails --file contacts.csv --store

Cost: FREE | Time: 15 minutes | Emails: Unlimited


OPTION E: RECOMMENDED - Combine Them (15 minutes)
──────────────────────────────────────────────────

1. GitHub API (5 min): 50 emails
2. Apollo free tier (5 min): 100 emails
3. Kaggle dataset (5 min): 200+ emails

python3 << 'EOF'
# Step 1: Get from GitHub
import requests
url = "https://api.github.com/search/users?q=junior+frontend+developer+remote"
github_users = requests.get(url).json()['items']

# Step 2: Get from Apollo (if configured)
from python_engine.data_sources import EmailSourceManager
manager = EmailSourceManager()
apollo_contacts = manager.search_apollo('junior developer remote')

# Step 3: Import CSV from Kaggle
from python_engine.free_email_sources import FreeEmailSources
sources = FreeEmailSources.get_free_sources()
print("Available sources:", list(sources.keys()))

# Step 4: Combine and import
python3 devnavigator.py extract-emails --file combined_contacts.csv --store
EOF

Cost: FREE | Time: 15 minutes | Emails: 350+ (all verified)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2: SET UP FILTERS FOR YOUR TARGETS - 5 MINUTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DevNavigator automatically scores each contact on:

✅ Junior Developer Score (0-100)
   → Looks for: "junior", "entry-level", "beginner", <3 years experience

✅ Frontend Developer Score (0-100)
   → Looks for: React, Vue, Angular, JavaScript, CSS, UI/UX

✅ Remote Capable Score (0-100)
   → Looks for: "remote", "work from home", "distributed", "anywhere"

✅ Marketer Score (0-100)
   → Looks for: "marketing", "growth", "sales", "content", "social media"

✅ Money Motivated Score (0-100)
   → Looks for: "freelance", "side hustle", "passive income", "contract"

✅ Job Seeker Score (0-100)
   → Looks for: "#opentohire", "#hiringmyownteam", "looking for job"


EXAMPLE: Filter for Your Target Audience

python3 << 'EOF'
from python_engine.contact_filters import ContactFilter

filter = ContactFilter()

# Filter 1: Junior Frontend Developers (Remote)
count, juniors = filter.filter_junior_developers(min_score=70)
count, frontend = filter.filter_frontend_developers(min_score=70)
count, remote = filter.filter_remote_capable(min_score=60)

print(f"Junior devs: {count}")
print(f"Frontend: {count}")
print(f"Remote willing: {count}")

# Filter 2: Multiple Criteria (My Sweet Spot!)
criteria = {
    'junior_developer': 70,
    'frontend_developer': 60,
    'remote_capable': 50,
    'job_seeker': 60,
    'money_motivated': 40
}

count, perfect_targets = filter.filter_by_multiple_criteria(criteria)

print(f"✓ PERFECT TARGETS: {count} people")
print("\\nTop matches:")
for contact in perfect_targets[:5]:
    print(f"  {contact['name']} - {contact['email']}")
    print(f"    Scores: {contact['scores']}")
EOF


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3: CONFIGURE YOUR CAMPAIGN - 5 MINUTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A) Create Email Template (Optional - Default Works)

python3 devnavigator.py add-template \\
  --name "juniordev_opportunity" \\
  --subject "Remote Frontend Developer Opportunity - $name"

Template body (save to file, then paste):

Hi $name,

We're looking for talented junior frontend developers interested in:

✓ Remote/Work from home opportunity
✓ Growing your React/Vue skills
✓ Make solid income (💰 we pay well!)
✓ Flexible hours, work at your own pace

You seem passionate about web development. Want to explore this?

Best regards,
[Your Company Name]
matteopennacchia43@gmail.com

Then:

python3 devnavigator.py add-template \\
  --name "junior_dev" \\
  --subject "Exciting Remote Frontend Opportunity"


B) Configure Filters in .env (Optional)

# Edit .env
TARGET_CRITERIA=junior,frontend,remote,remote_capable
MIN_THRESHOLD=60
LANGUAGES=javascript,react,vue,html,css
JOB_LEVELS=junior,entry


C) Add Contacts to Campaign

python3 << 'EOF'
from python_engine.contact_filters import ContactFilter
from python_engine.database_manager import DatabaseManager

filter = ContactFilter()

# Get targets
criteria = {
    'junior_developer': 70,
    'frontend_developer': 60,
    'remote_capable': 50,
    'job_seeker': 60
}

count, targets = filter.filter_by_multiple_criteria(criteria)

print(f"✓ Ready to send to: {count} perfect targets")
print(f"  Junior devs: {len([c for c in targets if c['scores'].get('junior_developer', 0) > 70])}")
print(f"  Frontend: {len([c for c in targets if c['scores'].get('frontend_developer', 0) > 60])}")
print(f"  Remote: {len([c for c in targets if c['scores'].get('remote_capable', 0) > 50])}")
EOF


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4: SEND YOUR CAMPAIGN - 2 MINUTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Make sure SMTP is configured in .env
   (Gmail example already there)

2. Build C++ sender:

./build.sh

3. Send campaign:

npm run send:emails

4. Monitor:

python3 devnavigator.py stats

This will show:
  ✓ Total contacts: X
  ✓ Ready to send: Y
  ✓ Already sent: Z


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPLETE QUICK START (20 MINUTES!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Minute 0-5: Get emails
# (Choose one option above - recommend Apollo/GitHub combo)

# Minute 5-10: Import
python3 devnavigator.py extract-emails --file contacts.csv --store

# Minute 10-15: Filter
python3 << 'EOF'
from python_engine.contact_filters import ContactFilter
filter = ContactFilter()
count, targets = filter.filter_by_multiple_criteria({
    'junior_developer': 70,
    'frontend_developer': 60,
    'remote_capable': 50,
    'job_seeker': 60
})
print(f"Target audience: {count} people")
EOF

# Minute 15-20: Send
npm run send:emails


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR TARGET PROFILE MATRIX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Profile                      | Score Threshold | Why Target
─────────────────────────────┼─────────────────┼──────────────────────────
Junior Developers            |      70+        | Entry-level ambitious
Frontend Developers          |      60+        | Technical skills
Remote Capable               |      50+        | Flexibility preference
Job Seekers                  |      60+        | Active in market
Money Motivated              |      40+        | Care about earnings
Marketers                    |      70+        | Growth mindset

RECOMMENDED MINIMUM COMBINATION:
 • Junior Dev Score ≥ 70
 • Frontend Score ≥ 60
 • Remote Score ≥ 50
 • Job Seeker Score ≥ 60

= PERFECT TARGET AUDIENCE ✓


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EMAIL TEMPLATE EXAMPLES FOR YOUR TARGETS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Template 1: Junior Developer (Remote Focused)
──────────────────────────────────────────────

Subject: Remote Frontend Developer Role - Fully Flexible + Great Pay 🚀

Hi $name,

I found your GitHub profile and love your passion for web development!

We're building a remote-first team and looking for talented junior frontend developers to:

✓ Build amazing React applications
✓ Work fully remote (home office, coffee shop, anywhere!)
✓ Earn while you learn
✓ Flexible schedule, no micro-management

We value:
• Passion for learning
• Self-motivated mindset
• Remote experience is a bonus (not required)

Interested? Let's chat!

Best regards


Template 2: Money-Motivated Freelancer
───────────────────────────────────────

Subject: $60K/year Remote Frontend - Join Our Team

Hi $name,

Quick question: Are you looking to earn more as a freelancer?

We're hiring remote front-end developers:
💰 $20-35/hour (or $60K+ annually)
📍 Work from anywhere
⏰ Flexible hours
📈 Growth potential

Your skills in [detected from profile] are exactly what we need.

Ready to talk?


Template 3: Marketer/Growth Focused
────────────────────────────────────

Subject: Growth Marketing Opportunity - Remote Position

Hi $name,

Your marketing background caught our attention.

We're looking for growth-minded marketers to:
✓ Drive customer acquisition
✓ Work 100% remote
✓ Competitive compensation
✓ Real equity/upside

Sound interesting?


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILES REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

python_engine/free_email_sources.py    ← Get free email sources
python_engine/contact_filters.py        ← Filter contacts by criteria
python_engine/data_sources.py           ← API integrations (Apollo, Hunter.io)
devnavigator.py                         ← Main CLI tool
.env                                    ← Configuration


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRICING: COMPLETELY FREE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Email extraction: FREE
✅ Filtering: FREE
✅ Contact management: FREE
✅ Email sending: FREE (using your SMTP)
✅ Analytics: FREE

TOTAL: $0/month forever


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ✅ Choose your email source (GitHub + Apollo recommended)
2. ✅ Import contacts CSV
3. ✅ Run filter on your criteria
4. ✅ View matching profiles
5. ✅ Send campaign!

Questions?
📧 Email: matteopennacchia43@gmail.com
📖 See: FREE_EMAIL_SOURCES.md & CONTACT_FILTERS.md

""")


# Show available email sources
print("\\n" + "="*80)
print("AVAILABLE FREE EMAIL SOURCES")
print("="*80)

from python_engine.free_email_sources import FreeEmailSources

sources = FreeEmailSources()
free_sources = sources.get_free_sources()

for i, (key, source) in enumerate(free_sources.items(), 1):
    print(f"\\n{i}. {source['name']}")
    print(f"   💰 Cost: {source['cost']}")
    print(f"   ⭐ Quality: {source['quality']}")
    print(f"   👥 Best for: {source['best_for']}")


print("\\n" + "="*80)
print("MINIMUM SETUP OPTIONS")
print("="*80)

options = sources.get_minimum_free_setup()
for opt_name, opt in options.items():
    print(f"\\n{opt['name']}")
    print(f"  Cost: {opt['cost']}")
    print(f"  Emails/month: {opt['estimated_emails']}")
    print(f"  Quality: {opt['quality']}")
    print(f"  Setup time: {opt['setup_time']}")

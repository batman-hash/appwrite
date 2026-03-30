# 🤖 Automated Email Extraction from Internet

Extract emails directly from internet sources with specific job requirements - IT jobs, remote work, junior developers, etc.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Flow Map](#flow-map)
3. [Features](#features)
4. [Requirements Setup](#requirements-setup)
5. [CLI Commands](#cli-commands)
6. [Examples](#examples)
7. [Supported Sources](#supported-sources)
8. [Advanced Usage](#advanced-usage)

---

## 🚀 Quick Start

### Basic Search (No API Keys Needed)

```bash
# Preview internet results only
./scripts/search/search-internet-emails.sh \
    "junior frontend developer" \
    "react,javascript,remote" \
    all \
    remote \
    10
```

```bash
# Store internet results in a separate SQLite file
INTERNET_SEARCH_STORE=1 \
INTERNET_SEARCH_DB_PATH=./database/internet_search.db \
./scripts/search/search-internet-emails.sh \
    "junior frontend developer" \
    "react,javascript,remote" \
    all \
    remote \
    10
```

```bash
# Export validated preview results to CSV without storing them in SQLite
INTERNET_SEARCH_EXPORT_PATH=./exports/internet_search_results.csv \
./scripts/search/search-internet-emails.sh \
    "junior frontend developer" \
    "react,javascript,remote" \
    all \
    remote \
    10
```

```bash
# Print current stored emails first, then refresh with a worldwide 1000-result search
./scripts/search/search-list-and-refresh-world.sh \
    "junior frontend developer" \
    "react,javascript,remote" \
    remote \
    1000 \
    1000
```

### With Filtering

```bash
# Search and automatically filter by criteria
python3 devnavigator.py search-filtered \
    --title "junior frontend developer" \
    --keywords "react,vue,angular" \
    --country all \
    --remote
```

---

## 🗺️ Flow Map

```text
Search criteria
    ↓
Approved internet sources
    ↓
Candidate emails + source URLs
    ↓
Validation
    ↓
Deduplication
    ↓
Store in separate internet-search DB
    ↓
Review / export
    ↓
Send only after approval
```

In practice, the main path looks like this:

- `scripts/search/search-internet-emails.sh` or `scripts/search/search-internet-emails-world.sh` for discovery
- `scripts/extraction/crawl-emails.sh` as a shorter crawler alias that points to the same Python pipeline
- `search_threshold_guard.py` for system-health warnings before the search starts
- `python_engine/auto_email_extractor.py` for source lookup, validation, and dedupe
- `python_engine/database_manager.py` for storing validated results
- `devnavigator.py list-search-emails` for review
- `scripts/search/search-validate-send.sh` for the final send step

By default, the internet search wrappers run in preview-only mode. Turn on `INTERNET_SEARCH_STORE=1` when you want validated results written to `./database/internet_search.db`.

---

## ✨ Features

### ✅ Automated Search Across Multiple Sources
- GitHub public profiles (FREE - no key needed)
- Hunter.io (FREE tier: 10/month with API key)
- Apollo.io (FREE tier with API key)
- Kaggle datasets (FREE)
- LinkedIn-like searches (public data)

### ✅ Filter by Job Requirements
During extraction, automatically filter for:
- Job title (junior, senior, full-stack, etc.)
- Skills (React, Vue, Python, Node, etc.)
- Location/Country
- Remote work preference
- Employment type (freelance, full-time, etc.)

### ✅ Automatic Deduplication
- Removes duplicate emails
- Combines results from multiple sources
- Scores profiles by match criteria

### ✅ Direct Database Storage
- Automatically stores in SQLite
- Ready for immediate campaigning
- Tracks source of each email

---

## 🔑 Requirements Setup

### 1. GitHub Search (FREE - No Key Needed)
Built-in support. Uses GitHub public API.

```bash
# No configuration needed!
```

### 2. Hunter.io (FREE Tier)
**10 emails/month free**

```bash
# Sign up: https://hunter.io
# Get API key from dashboard
# Add to .env:

HUNTER_API_KEY=your_api_key_here
```

### 3. Apollo.io (FREE Tier)
**Limited searches free**

```bash
# Sign up: https://apollo.io
# Get API key from settings
# Add to .env:

APOLLO_API_KEY=your_api_key_here
```

### 4. Check Your Setup

```bash
# View current environment config
cat .env
```

Or use the reusable export file:

```bash
cp scripts/env/internet-search.env.example.sh scripts/env/internet-search.env.sh
source ./scripts/env/internet-search.env.sh
```

The internet search wrapper also loads `.env` automatically now, so you only need to source it manually when you want the keys in your current shell session.

For the full validate-then-send flow, use:

```bash
./scripts/search/search-validate-send.sh \
  --title "frontend developer" \
  --keywords "react,javascript" \
  --country all \
  --remote \
  --template earning_opportunity \
  --send
```

The internet search wrappers now run `search_threshold_guard.py` first in warn-only mode, so they report CPU, memory, disk, process count, listening ports, and any single current-user process that is over threshold without stopping the search. Override the defaults with `SEARCH_MAX_CPU_PERCENT`, `SEARCH_MAX_MEMORY_PERCENT`, `SEARCH_MAX_DISK_PERCENT`, `SEARCH_MAX_PROCESS_COUNT`, `SEARCH_MAX_LISTENING_PORTS`, `SEARCH_MAX_SINGLE_PROCESS_CPU_PERCENT`, `SEARCH_MAX_SINGLE_PROCESS_MEMORY_PERCENT`, `SEARCH_MAX_SINGLE_PROCESS_IO_MBPS`, and `SEARCH_WARN_ONLY_PROCESS_NAMES` if you want specific busy desktop apps to stay in the warning list.

---

## 📝 CLI Commands

### Command 1: Search & Store

```bash
python3 devnavigator.py search-auto \
    --title <job_title> \
    --keywords <keywords> \
    [--country <country>] \
    [--remote]
```

**Options:**
- `--title`: Job title to search (e.g., "junior frontend developer")
- `--keywords`: Search keywords comma-separated (e.g., "react,javascript")
- `--country`: Target country (optional, or `all`/`world`/`global` for worldwide search)
- `--remote`: Filter for remote jobs only (flag)

**Stores**: All found emails in database automatically

**Output**: Shows count of emails stored

---

### Command 2: Search & Filter

```bash
python3 devnavigator.py search-filtered \
    --title <job_title> \
    --keywords <keywords> \
    [--country <country>] \
    [--remote]
```

**Options:** Same as search-auto

**Difference**: Shows filtered results BEFORE storing

**Output**: Lists matching profiles with scores

---

## 💡 Examples

### Example 1: Find Junior React Developers (Remote)

```bash
python3 devnavigator.py search-auto \
    --title "junior react developer" \
    --keywords "react,javascript,typescript,remote" \
    --remote
```

**What it does:**
1. Searches GitHub for profiles matching keywords
2. Queries Hunter.io (if configured)
3. Queries Apollo.io (if configured)
4. Deduplicates results
5. Stores in database
6. Shows count found

**Expected result**: 10-50 emails (varies by APIs configured)

---

### Example 2: Find Python Developers in Germany

```bash
python3 devnavigator.py search-auto \
    --title "python developer" \
    --keywords "python,django,flask" \
    --country "Germany"
```

---

### Example 3: Find Freelance Marketers Worldwide

```bash
python3 devnavigator.py search-auto \
    --title "freelance marketer" \
    --keywords "growth,marketing,content,freelance" \
    --country all
```

---

### Example 4: Search & Filter (Show Results First)

```bash
python3 devnavigator.py search-filtered \
    --title "frontend engineer" \
    --keywords "react,vue,angular" \
    --country "USA"
```

**Output**: Shows top 10 matches with:
- Name
- Email
- Title
- Company
- Matching scores

---

## 🌐 Supported Sources

| Source | Free? | Limit | Key Needed? | Returns |
|--------|-------|-------|------------|---------|
| **GitHub** | ✅ | 30/search | ❌ No | 20-100 profiles |
| **Hunter.io** | ✅ | 10/month | ✅ Yes | 10-50 per domain |
| **Apollo.io** | ✅ | Limited | ✅ Yes | 10-100 per search |
| **Kaggle** | ✅ | Unlimited* | ❌ No | Datasets to download |
| **LinkedIn Data** | ✅ | Public data | ❌ No | Via scraping |

*Requires manual dataset download

---

## 🔧 Advanced Usage

### Python Script Integration

```python
from python_engine.auto_email_extractor import AutoEmailExtractor

# Create extractor
extractor = AutoEmailExtractor(db_path='./database/devnav.db')

# Define search criteria
criteria = {
    'title': 'junior frontend developer',
    'keywords': ['react', 'javascript', 'remote'],
    'country': 'USA',
    'remote': True
}

# Search & store
stored, results = extractor.search_all_sources(criteria, limit=50)

print(f"✓ Stored {stored} emails")

# Or: Search with filtering
filtered_results = extractor.search_with_filters(criteria)

for contact in filtered_results:
    print(f"{contact['email']}: {contact['name']}")
```

---

### Batch Search Multiple Criteria

```python
from python_engine.auto_email_extractor import AutoEmailExtractor

extractor = AutoEmailExtractor()

searches = [
    {
        'title': 'junior frontend developer',
        'keywords': ['react', 'remote'],
        'country': 'USA',
        'remote': True
    },
    {
        'title': 'python developer',
        'keywords': ['python', 'django'],
        'country': 'India',
        'remote': False
    },
    {
        'title': 'marketer',
        'keywords': ['growth', 'marketing'],
        'country': None,
        'remote': True
    }
]

for criteria in searches:
    stored, _ = extractor.search_all_sources(criteria)
    print(f"Search '{criteria['title']}': {stored} emails stored")
```

---

### Combining with Filters

```python
from python_engine.auto_email_extractor import AutoEmailExtractor
from python_engine.contact_filters import ContactFilter

# Extract
extractor = AutoEmailExtractor()
criteria = {
    'title': 'junior developer',
    'keywords': ['javascript'],
    'country': 'USA',
    'remote': True
}

stored, results = extractor.search_all_sources(criteria)

# Filter further
filter = ContactFilter()
junior = filter.filter_junior_developers(min_score=75)
remote = filter.filter_remote_capable(min_score=60)

print(f"Found {len(junior)} junior devs")
print(f"Found {len(remote)} remote capable")
```

---

## 📊 Results Format

### Stored Contact Format

Each extracted email is stored with:

```python
{
    'email': 'john@example.com',
    'name': 'John Doe',
    'title': 'Junior React Developer',
    'company': 'TechStartup Inc',
    'country': 'USA',
    'source': 'github.com',  # or 'hunter.io', 'apollo.io'
    'data_source': 'github.com'
}
```

---

### Filter Results Format

When using `search-filtered`, results include scores:

```python
{
    'email': 'john@example.com',
    'name': 'John Doe',
    'title': 'Junior React Developer',
    'company': 'TechStartup Inc',
    'country': 'USA',
    'scores': {
        'junior_developer': 85.0,
        'frontend_developer': 92.0,
        'remote_capable': 78.0,
        'job_seeker': 65.0,
        ...
    }
}
```

---

## 🎯 Search Tips

### Tip 1: Use Specific Keywords
❌ Bad: `--keywords "developer"`
✅ Good: `--keywords "react,javascript,typescript"`

### Tip 2: Combine Multiple Skills
✅ `--keywords "python,django,rest,api"`
✅ `--keywords "react,typescript,next"`

### Tip 3: Use Remote Flag
✅ `--remote` - Only remote positions
✅ Without flag - All locations

### Tip 4: Target by Country
✅ `--country "USA"` - Only USA
✅ `--country "India"` - Only India
✅ `--country all` - Worldwide search
✅ Without flag - All countries

### Tip 5: Search by Job Level
- Junior: `--title "junior developer"`
- Mid: `--title "developer"` or `--title "engineer"`
- Senior: `--title "senior developer"`

---

## ❓ FAQ

**Q: Do I need API keys?**
A: No! GitHub search is free. Add API keys to get more results.

**Q: How many emails can I get free?**
A: 30/search from GitHub (no limit if you keep searching)
   10/month from Hunter.io (with key)

**Q: Can I search without country?**
A: Yes, omit `--country` or use `all`, `world`, or `global` for a worldwide search

**Q: How does filtering work?**
A: It scores each profile against criteria (0-100 points) then shows top matches

**Q: Are results stored automatically?**
A: Yes with `search-auto`. Use `search-filtered` to preview first.

**Q: Can I export search results?**
A: Yes, check database: `SELECT * FROM contacts`

---

## 🚀 Next Steps

After extraction:

```bash
# 1. View statistics
python3 devnavigator.py stats

# 2. Filter by specific criteria
python3 << 'EOF'
from python_engine.contact_filters import ContactFilter
f = ContactFilter()
count, targets = f.filter_junior_developers(min_score=70)
print(f"Junior devs: {count}")
EOF

# 3. Send campaign
npm run send:emails
```

---

## 🔗 References

- [GitHub API Docs](https://docs.github.com/en/rest)
- [Hunter.io API](https://hunter.io/api)
- [Apollo.io API](https://apollo.io/developers)
- [Contact Filters](./FREE_CAMPAIGN_SETUP.md)
- [Campaign Setup Guide](./CAMPAIGN_SETUP_GUIDE.py)

---

**Questions?** Email: matteopennacchia43@gmail.com

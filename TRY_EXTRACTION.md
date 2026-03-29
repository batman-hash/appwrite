# 🚀 How to Try Email Extraction - 3 Quick Methods

## ⚡ The Easiest Way (30 seconds)

Run this one command to see everything work:

```bash
cd /home/kali/Desktop/devnavigator
./try-extraction.sh
```

**What it does:**
✓ Initialize database  
✓ Extract 10 sample emails  
✓ Show statistics  
✓ Export to file  

**Done in 30 seconds!**

---

## 🎯 Method 1: Extract from CSV File (Your Data)

### Step 1: Prepare CSV file
Create `contacts.csv` with your emails:

```csv
email,name,title,company
john@example.com,John Doe,Developer,TechCo
jane@example.com,Jane Smith,Designer,WebCo
```

### Step 2: Initialize database (one time)
```bash
python3 devnavigator.py init-db
```

Output:
```
✓ Database initialized at ./database/devnav.db
✓ Default template inserted
```

### Step 3: Extract emails
```bash
python3 devnavigator.py extract-emails --file contacts.csv --store
```

Output:
```
📂 Extracting emails from: contacts.csv
📧 Found 2 email(s)
✓ Stored: john@example.com
✓ Stored: jane@example.com
✓ Stored: 2
```

### Step 4: See what was imported
```bash
python3 devnavigator.py stats
```

Output:
```
📊 Campaign Statistics:
Total contacts:    2
Ready to send:     0
```

---

## 🔍 Method 2: Using Sample Data (Ready to Go!)

### Already prepared for you:

```bash
# File: sample_emails.csv (10 test emails)

python3 devnavigator.py extract-emails --file sample_emails.csv --store
```

This will extract 10 sample emails immediately.

---

## 🤖 Method 3: Auto-Search from Internet (No CSV!)

### Search GitHub for developers (FREE - No API key needed)

```bash
python3 devnavigator.py search-auto \
    --title "junior developer" \
    --keywords "javascript,react" \
    --remote
```

**What it does:**
1. Searches GitHub public profiles
2. Finds matching developers
3. Extracts emails
4. Stores to database automatically

**Expected result:**
```
🚀 Starting automated email extraction...
1️⃣  GitHub Profiles
   🔍 Searching GitHub...
   ✓ Found 15 from GitHub

✓ Total unique emails found: 15
✓ Stored in database: 15
```

---

## 📊 Verify Your Data

### Check statistics
```bash
python3 devnavigator.py stats
```

### Query database directly
```bash
# Count all emails
sqlite3 database/devnav.db "SELECT COUNT(*) FROM contacts;"

# See first 5 emails
sqlite3 database/devnav.db "SELECT email FROM contacts LIMIT 5;"

# See all with country
sqlite3 database/devnav.db "SELECT email, country FROM contacts;"
```

---

## 💾 Export Extracted Emails

### To CSV file
```bash
python3 << 'EOF'
import sqlite3, csv

conn = sqlite3.connect('database/devnav.db')
cursor = conn.cursor()
cursor.execute('SELECT email FROM contacts')

with open('my_extracted_emails.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['email'])
    writer.writerows(cursor.fetchall())

print("✓ Exported to: my_extracted_emails.csv")
conn.close()
EOF
```

### To JSON file
```bash
python3 << 'EOF'
import sqlite3, json

conn = sqlite3.connect('database/devnav.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute('SELECT * FROM contacts')

with open('my_emails.json', 'w') as f:
    json.dump([dict(row) for row in cursor.fetchall()], f, indent=2)

print("✓ Exported to: my_emails.json")
conn.close()
EOF
```

---

## 📋 All Commands in One Place

```bash
# Initialize (run once)
python3 devnavigator.py init-db

# Extract from CSV
python3 devnavigator.py extract-emails --file contacts.csv --store

# Auto-search from internet
python3 devnavigator.py search-auto --title "junior frontend" --keywords "react" 

# Preview search results
python3 devnavigator.py search-filtered --title "developer" --keywords "python"

# Show statistics
python3 devnavigator.py stats

# List templates
python3 devnavigator.py list-templates

# Show help
python3 devnavigator.py --help
```

---

## 🎯 Complete Example (Copy & Paste)

### 1. Quick start (30 seconds)
```bash
cd /home/kali/Desktop/devnavigator
./try-extraction.sh
```

### 2. Or manual extraction
```bash
# Initialize
python3 devnavigator.py init-db

# Extract sample data
python3 devnavigator.py extract-emails --file sample_emails.csv --store

# Check results
python3 devnavigator.py stats

# Export
python3 << 'EOF'
import sqlite3, csv
conn = sqlite3.connect('database/devnav.db')
cursor = conn.cursor()
cursor.execute('SELECT email FROM contacts')
with open('output.csv', 'w') as f:
    csv.writer(f).writerows(cursor.fetchall())
print("✓ Exported to output.csv")
EOF
```

---

## ❓ Common Questions

**Q: Do I need API keys?**  
A: No! CSV and GitHub search are completely free.

**Q: Where are emails stored?**  
A: SQLite database at `./database/devnav.db`

**Q: How many emails can I extract?**  
A: Limited by your data. Free tier APIs allow 10-100+ per search.

**Q: Can I use my own data?**  
A: Yes! Put emails in a CSV file and use `extract-emails --file yourfile.csv --store`

**Q: Can I filter by job type?**  
A: Yes! After extraction, use filtering: `search-filtered --title "junior frontend"`

---

## 📚 More Information

- **QUICK_REFERENCE.md** - Commands cheat sheet
- **AUTO_EMAIL_EXTRACTION.md** - Detailed extraction guide
- **TECHNICAL_ARCHITECTURE.md** - How system works
- **HOW_TO_EXTRACT_EMAILS.py** - Code examples

---

## ✅ You're Ready!

🚀 **Run this now:**

```bash
cd /home/kali/Desktop/devnavigator
./try-extraction.sh
```

That's it! You'll see emails extracted, stored, and exported in 30 seconds.

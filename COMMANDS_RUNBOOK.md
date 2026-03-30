# DevNavigator Commands Runbook

This file collects the commands we used so far, with short comments, so you can quickly see what to run and in what order.

## Recommended Order

Run these first if you want the safest flow:

```bash
# 1) Initialize the database and create default templates
python3 devnavigator.py init-db

# 2) Extract emails from a local file and save valid results to the database
python3 devnavigator.py extract-emails --file your_file.txt --store --source manual

# 3) Check what was saved
python3 devnavigator.py stats
python3 devnavigator.py queue --queue all --limit 20

# 4) Validate a single email manually
python3 devnavigator.py validate-email --email person@example.com
```

## Setup

```bash
# Optional: create and edit your environment file
cp .env.example .env
```

```bash
# Load the database structure and default templates
python3 devnavigator.py init-db
```

Comment:
Use this once before running extraction, import, or verification commands on a new database.

## VS Code Tasks

Open the Command Palette in VS Code and run a task from `.vscode/tasks.json`. The most useful ones are:

- `DevNavigator: Crawl Emails`
- `DevNavigator: Crawl Emails (Store)`
- `DevNavigator: Crawl Emails (World Store)`
- `DevNavigator: Search Deliver (Dry Run)`
- `DevNavigator: List Stored Search Emails`
- `DevNavigator: Search Guard`
- `DevNavigator: Extract Emails From File`
- `DevNavigator: Build C++ Sender`

The same flows are also available through npm:

```bash
npm run crawl:emails -- "frontend developer" "react,javascript" all remote 10
npm run crawl:emails:store -- "frontend developer" "react,javascript" all remote 10
npm run crawl:emails:world -- "frontend developer" "react,javascript" remote 10
npm run search:deliver:dry-run -- --title "frontend developer" --keywords "react,javascript" --country all --remote
npm run search:list:emails
npm run search:guard:warn
npm run build:sender
```

## Docker Workflow

```bash
# Build the Docker image
docker build -t devnavigator .
```

```bash
# Show the CLI help from inside Docker
docker run --rm -it -v "$(pwd):/workspace" devnavigator
```

```bash
# Initialize the database in the mounted project folder
docker run --rm -it -v "$(pwd):/workspace" devnavigator init-db
```

```bash
# Extract and save emails from a local file using Docker
docker run --rm -it -v "$(pwd):/workspace" devnavigator \
  extract-emails --file sample_emails.csv --store --source manual
```

```bash
# Check stats and queue using Docker
docker run --rm -it -v "$(pwd):/workspace" devnavigator stats
docker run --rm -it -v "$(pwd):/workspace" devnavigator queue --queue all --limit 20
```

```bash
# Validate one email using Docker
docker run --rm -it -v "$(pwd):/workspace" devnavigator \
  validate-email --email person@example.com
```

Comment:
The Docker image routes commands through a small entrypoint helper. Standard email CLI commands go to `devnavigator.py`, while `monitor`, `toy-server`, and `toy-client` run the Python monitor script. Mounting the repo to `/workspace` gives the container access to your local `.env`, files, and database folder.

```bash
# Run the Python network monitor from the main Docker image
docker run --rm -it --network host -v "$(pwd):/workspace" devnavigator \
  monitor --interface auto --target 192.168.1.254 --samples 1
```

```bash
# Run the Python monitor continuously until you stop it
docker run --rm -it --network host -v "$(pwd):/workspace" devnavigator \
  monitor --interface auto --target 192.168.1.254 --loop
```

## Extract Emails From a File

```bash
# Extract emails from any text-like file and store them in the database
python3 devnavigator.py extract-emails --file your_file.txt --store --source manual
```

```bash
# Example using the helper shell script
./scripts/extraction/extract-emails.sh your_file.txt
```

Comment:
This path validates emails before saving them. Invalid addresses are skipped and shown in the output.

## Import a Structured CSV

```bash
# Import a CSV file that has an email column
python3 devnavigator.py import-contacts --file your_contacts.csv --source csv_upload
```

```bash
# Import and mark contacts as approved/sendable immediately
python3 devnavigator.py import-contacts --file your_contacts.csv --source csv_upload --consent
```

Comment:
Use this when your file already has columns like `email,name,company,country`.

## Check What Was Saved

```bash
# Show high-level contact counts
python3 devnavigator.py stats
```

```bash
# Show the queue with a few rows
python3 devnavigator.py queue --queue all --limit 20
```

```bash
# List every stored email from the internet-search database, including archived rows
python3 devnavigator.py list-search-emails --db-path ./database/internet_search.db --emails-only
```

```bash
# Show only contacts ready to send
python3 devnavigator.py queue --queue ready --limit 20
```

```bash
# Show only contacts needing review
python3 devnavigator.py queue --queue review --limit 20
```

```bash
# Show only recent contacts
python3 devnavigator.py queue --queue recent --limit 20 --recent-hours 24
```

Comment:
These commands are the quickest way to confirm extraction/import worked.

## Validate Emails

```bash
# Full validation for one email
python3 devnavigator.py validate-email --email person@example.com
```

```bash
# Format-only validation if DNS checks are not wanted
python3 devnavigator.py validate-email --email person@example.com --skip-dns
```

Comment:
Validation checks syntax and, by default, also tries DNS/MX validation when available.

## Automated Search From Internet

```bash
# Preview internet results only, without writing to the main local database
./scripts/search/search-internet-emails.sh "frontend developer" "react,javascript" all remote 10
```

```bash
# Real mode: store validated results in the separate internet-search database
./scripts/search/search-internet-emails-real.sh "frontend developer" "react,javascript" all remote 10
```

```bash
# Worldwide mode helper: global search plus separate-db storage
./scripts/search/search-internet-emails-world.sh "frontend developer" "react,javascript" remote 10
```

```bash
# Print all stored emails first, then refresh with a worldwide 1000-result search
./scripts/search/search-list-and-refresh-world.sh "frontend developer" "react,javascript" remote 1000 1000
```

```bash
# Store internet results in a separate SQLite file
INTERNET_SEARCH_STORE=1 \
INTERNET_SEARCH_DB_PATH=./database/internet_search.db \
./scripts/search/search-internet-emails.sh "python developer" "django,backend,remote" all remote 10
```

```bash
# Export validated preview results to CSV without storing them in SQLite
INTERNET_SEARCH_EXPORT_PATH=./exports/internet_search_results.csv \
./scripts/search/search-internet-emails.sh "frontend developer" "react,javascript" all remote 10
```

```bash
# Show every validated result instead of only the first N
./scripts/search/search-internet-emails.sh "frontend developer" "react,javascript" all remote 0
```

```bash
# Load provider API keys and optional search env vars from a reusable file
cp scripts/env/internet-search.env.example.sh scripts/env/internet-search.env.sh
source ./scripts/env/internet-search.env.sh
```

```bash
# Run the same internet search flow through Docker
EXTRACT_PROXY_URL=http://REAL_PROXY_HOST:8080 \
./scripts/search/docker-search-internet-emails.sh "frontend developer" "react,javascript" all remote 10
```

```bash
# Use npm command wrappers with pass-through arguments
npm run search:internet -- "frontend developer" "react,javascript" all remote 10
npm run search:internet:real -- "frontend developer" "react,javascript" all remote 10
npm run search:internet:world -- "frontend developer" "react,javascript" remote 10
npm run search:internet:refresh -- "frontend developer" "react,javascript" remote 1000 1000
npm run docker:search:internet -- "frontend developer" "react,javascript" all remote 10
npm run search:deliver -- --title "frontend developer" --keywords "react,javascript" --country all --remote --send
```

```bash
# List every stored email from the separate internet-search database
python3 devnavigator.py queue --db-path ./database/internet_search.db --queue all --limit 0
```

Comment:
Internet extraction is preview-only by default. The wrapper now auto-loads `.env`, clears stale runtime cache, and then runs the search. Add `INTERNET_SEARCH_STORE=1` and point `INTERNET_SEARCH_DB_PATH` to a separate file if you want to save results without touching the main local database.

```bash
# Check whether the machine is under the search thresholds before starting
python3 search_threshold_guard.py
```

```bash
# Short crawler alias for the same Python internet-search pipeline
./scripts/extraction/crawl-emails.sh "frontend developer" "react,javascript" all remote 10
```

```bash
# Tune thresholds with env vars
SEARCH_MAX_CPU_PERCENT=90 \
SEARCH_MAX_MEMORY_PERCENT=85 \
SEARCH_MAX_PROCESS_COUNT=800 \
SEARCH_MAX_SINGLE_PROCESS_CPU_PERCENT=25 \
SEARCH_WARN_ONLY_PROCESS_NAMES=code,gnome-shell \
SEARCH_MAX_SINGLE_PROCESS_IO_MBPS=25 \
python3 search_threshold_guard.py
```

```bash
# Bypass the guard when you are debugging the pipeline
AUTO_SYSTEM_THRESHOLD_GUARD=0 ./scripts/search/search-internet-emails.sh "frontend developer" "react,javascript" all remote 10
```

Comment:
The internet-search wrappers run the guard in warn-only mode, so they report local CPU, memory, disk, process count, and listening-port pressure but do not stop the lookup.

```bash
# Search, validate, store, approve, and send the validated batch from a separate DB
./scripts/search/search-validate-send.sh \
  --title "frontend developer" \
  --keywords "react,javascript" \
  --country all \
  --remote \
  --template earning_opportunity \
  --send
```

```bash
# Preview the same pipeline without sending
./scripts/search/search-validate-send.sh \
  --title "frontend developer" \
  --keywords "react,javascript" \
  --country all \
  --remote \
  --template earning_opportunity \
  --dry-run
```

Comment:
`search-deliver` stores the validated batch in `./database/internet_search.db` by default, marks exactly that batch as sendable when `--send` is present, and then sends only those validated emails. Use `--dry-run` first if you want to review the template and recipients before delivery.

## Cache Cleanup

```bash
# Clear runtime search state only
bash scripts/search/clear-search-cache.sh
```

```bash
# Also clear cached IP geolocation rows
CLEAR_GEO_CACHE=1 bash scripts/search/clear-search-cache.sh
```

```bash
# Run it every hour with cron
0 * * * * cd /home/kali/Desktop/devnavigator && /bin/bash scripts/search/clear-search-cache.sh >> /home/kali/Desktop/devnavigator/runtime/cache-clear.log 2>&1
```

Comment:
Use the default command for the safe runtime cleanup. Add `CLEAR_GEO_CACHE=1` only if you want to wipe the IP lookup cache too.

## Approve or Review Contacts

```bash
# Approve the newest review contacts
python3 devnavigator.py approve-recent-contacts --limit 20 --recent-hours 24
```

```bash
# Archive sent contacts
python3 devnavigator.py archive-contacts --sent
```

```bash
# Restore all archived contacts
python3 devnavigator.py unarchive-contacts --all
```

Comment:
These are useful after extraction, once you start managing sendable contacts.

## Verification Email Workflow

```bash
# Send a verification email to one contact
python3 devnavigator.py send-verification-email --email person@example.com --name "Jane Doe"
```

```bash
# Preview the verification email without saving or sending
python3 devnavigator.py send-verification-email --email person@example.com --name "Jane Doe" --dry-run
```

```bash
# Confirm verification using email + code
python3 devnavigator.py confirm-verification --email person@example.com --code 123456
```

```bash
# Check verification status
python3 devnavigator.py verification-status --email person@example.com
```

Comment:
Set `EMAIL_VERIFICATION_BASE_URL` in `.env` if you want a real clickable verification link in the message.

## Current Safe Workflow

If your goal is:

1. Extract emails
2. Save them to the database
3. Check validation

Run this:

```bash
python3 devnavigator.py init-db
python3 devnavigator.py extract-emails --file your_file.txt --store --source manual
python3 devnavigator.py stats
python3 devnavigator.py queue --queue all --limit 20
python3 devnavigator.py validate-email --email person@example.com
```

## Notes About Older Helper Files

```bash
# Interactive helper
python3 extract.py
```

```bash
# Older batch helper
bash scripts/extraction/batch-extract.sh
```

Comment:
These helpers now forward into the main `python3 devnavigator.py ...` workflow for extraction, queue inspection, export, and send-status reporting. The direct CLI is still the clearest source of truth.

## Create PDF Version of This Runbook

```bash
# Generate a PDF from this markdown file
./scripts/pdf/create-commands-runbook-pdf.sh
```

Comment:
This requires `pandoc` and a PDF engine like `xelatex` or `wkhtmltopdf`.

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
The Docker image runs `devnavigator.py` directly. Mounting the repo to `/workspace` gives the container access to your local `.env`, files, and database folder.

## Extract Emails From a File

```bash
# Extract emails from any text-like file and store them in the database
python3 devnavigator.py extract-emails --file your_file.txt --store --source manual
```

```bash
# Example using the helper shell script
./extract-emails.sh your_file.txt
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

## Automated Search and Save to Database

```bash
# Search automatically and store results in the database
python3 devnavigator.py search-auto --title "frontend developer" --keywords "react,javascript" --country US --remote
```

```bash
# Another automatic search example
python3 devnavigator.py search-auto --title "python developer" --keywords "django,backend,remote" --remote
```

```bash
# Search and filter results using the current filtered workflow
python3 devnavigator.py search-filtered --title "frontend developer" --keywords "react,javascript" --country US --remote
```

Comment:
`search-auto` stores results in the database. After running it, check with `stats` and `queue`.

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
bash batch-extract.sh
```

Comment:
These helpers are older wrappers. The most reliable commands right now are the direct `python3 devnavigator.py ...` commands listed above.

## Create PDF Version of This Runbook

```bash
# Generate a PDF from this markdown file
./create-commands-runbook-pdf.sh
```

Comment:
This requires `pandoc` and a PDF engine like `xelatex` or `wkhtmltopdf`.

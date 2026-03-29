#!/bin/bash
# Email extraction script
# Usage: ./extract-emails.sh input_file.txt

if [ -z "$1" ]; then
    echo "Usage: $0 <email_file>"
    echo "Example: $0 contacts.txt"
    exit 1
fi

echo "📧 Extracting emails from $1..."
python3 devnavigator.py extract-emails --file "$1" --store --source "manual"

echo ""
echo "✅ Import complete!"
python3 devnavigator.py stats

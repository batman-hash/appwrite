#!/bin/bash
# Convert COMMANDS_RUNBOOK.md to PDF

set -e

SOURCE_FILE="COMMANDS_RUNBOOK.md"
OUTPUT_FILE="COMMANDS_RUNBOOK.pdf"

echo "📄 Converting ${SOURCE_FILE} to PDF..."

if ! command -v pandoc &> /dev/null; then
    echo "ℹ️  pandoc not found. Using the built-in Python PDF generator instead..."
    python3 create_commands_runbook_pdf.py
    exit 0
fi

if command -v wkhtmltopdf &> /dev/null; then
    echo "Using wkhtmltopdf..."
    pandoc "${SOURCE_FILE}" -t html -o /tmp/commands_runbook.html
    wkhtmltopdf /tmp/commands_runbook.html "${OUTPUT_FILE}"
elif command -v xelatex &> /dev/null; then
    echo "Using xelatex..."
    pandoc "${SOURCE_FILE}" -o "${OUTPUT_FILE}" \
        --from markdown \
        --to pdf \
        --pdf-engine=xelatex \
        --toc \
        --toc-depth=2 \
        -V geometry:margin=1in \
        -V fontsize=11pt
else
    echo "ℹ️  No external PDF engine found. Using the built-in Python PDF generator instead..."
    python3 create_commands_runbook_pdf.py
    exit 0
fi

echo "✅ PDF created: ${OUTPUT_FILE}"

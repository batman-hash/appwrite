#!/bin/bash
# Convert USER_MANUAL.md to PDF

echo "📄 Converting USER_MANUAL.md to PDF..."

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "⚠️  pandoc not found. Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y pandoc texlive-latex-base texlive-fonts-recommended texlive-latex-extra
    else
        echo "Please install pandoc: brew install pandoc (Mac) or apt-get install pandoc (Linux)"
        exit 1
    fi
fi

# Check if wkhtmltopdf is available (better for formatting)
if command -v wkhtmltopdf &> /dev/null; then
    echo "Using wkhtmltopdf for better formatting..."
    pandoc USER_MANUAL.md -t html > /tmp/manual.html
    wkhtmltopdf /tmp/manual.html USER_MANUAL.pdf
else
    # Fallback to pandoc PDF
    echo "Using pandoc to generate PDF..."
    pandoc USER_MANUAL.md -o USER_MANUAL.pdf \
        -f markdown \
        -t pdf \
        --pdf-engine=xelatex \
        --variable geometry:margin=1in \
        --variable fontsize=11pt \
        --table-of-contents
fi

if [ -f USER_MANUAL.pdf ]; then
    echo "✅ PDF created: USER_MANUAL.pdf"
    ls -lh USER_MANUAL.pdf
else
    echo "❌ PDF creation failed"
    exit 1
fi

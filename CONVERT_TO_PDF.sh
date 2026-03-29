#!/bin/bash
# Convert Markdown documentation to PDF

echo "📖 Converting documentation to PDF..."
echo ""

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "❌ pandoc not installed. Install it:"
    echo "   Ubuntu/Debian: sudo apt install pandoc texlive-xetex"
    echo "   macOS: brew install pandoc basictex"
    echo "   Windows: choco install pandoc"
    exit 1
fi

# Convert each markdown file to PDF
echo "1️⃣  Converting QUICK_REFERENCE.md..."
pandoc QUICK_REFERENCE.md -o QUICK_REFERENCE.pdf \
    --from markdown \
    --to pdf \
    --pdf-engine=xelatex \
    --toc \
    --toc-depth=2 \
    -V geometry:margin=1in \
    -V fontsize=11pt

echo "✓ QUICK_REFERENCE.pdf created"
echo ""

echo "2️⃣  Converting TECHNICAL_ARCHITECTURE.md..."
pandoc TECHNICAL_ARCHITECTURE.md -o TECHNICAL_ARCHITECTURE.pdf \
    --from markdown \
    --to pdf \
    --pdf-engine=xelatex \
    --toc \
    --toc-depth=2 \
    -V geometry:margin=1in \
    -V fontsize=10pt \
    -V colorlinks=true

echo "✓ TECHNICAL_ARCHITECTURE.pdf created"
echo ""

echo "3️⃣  Converting AUTO_EMAIL_EXTRACTION.md..."
pandoc AUTO_EMAIL_EXTRACTION.md -o AUTO_EMAIL_EXTRACTION.pdf \
    --from markdown \
    --to pdf \
    --pdf-engine=xelatex \
    --toc \
    --toc-depth=2 \
    -V geometry:margin=1in \
    -V fontsize=11pt

echo "✓ AUTO_EMAIL_EXTRACTION.pdf created"
echo ""

echo "4️⃣  Converting FREE_CAMPAIGN_SETUP.md..."
pandoc FREE_CAMPAIGN_SETUP.md -o FREE_CAMPAIGN_SETUP.pdf \
    --from markdown \
    --to pdf \
    --pdf-engine=xelatex \
    --toc \
    --toc-depth=2 \
    -V geometry:margin=1in \
    -V fontsize=11pt

echo "✓ FREE_CAMPAIGN_SETUP.pdf created"
echo ""

echo "═════════════════════════════════════════════"
echo "✅ All PDFs created successfully!"
echo ""
echo "📎 Generated files:"
ls -lh *.pdf
echo ""
echo "📦 Create combined PDF:"
echo "   pdfunite QUICK_REFERENCE.pdf TECHNICAL_ARCHITECTURE.pdf combined.pdf"

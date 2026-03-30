#!/bin/bash
# Convert Markdown documentation to PDF using Pandoc

echo "📖 Converting Documentation to PDF"
echo "===================================="
echo ""

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "❌ Pandoc not installed. Install using:"
    echo ""
    echo "   Ubuntu/Debian:"
    echo "   $ sudo apt install pandoc texlive-xetex"
    echo ""
    echo "   macOS:"
    echo "   $ brew install pandoc basictex"
    echo ""
    echo "   Then run: sudo tlmgr install collection-xetex"
    echo ""
    exit 1
fi

echo "✓ Pandoc found. Converting files..."
echo ""

# Conversion settings
MARGIN="1in"
FONT="11pt"
TOC_DEPTH="2"

# Convert QUICK_REFERENCE.md
echo "1️⃣  QUICK_REFERENCE.md → QUICK_REFERENCE.pdf"
pandoc QUICK_REFERENCE.md -o QUICK_REFERENCE.pdf \
    --from markdown \
    --to pdf \
    --pdf-engine=xelatex \
    --toc \
    --toc-depth=$TOC_DEPTH \
    -V geometry:margin=$MARGIN \
    -V fontsize=$FONT

# Convert TECHNICAL_ARCHITECTURE.md
echo "2️⃣  TECHNICAL_ARCHITECTURE.md → TECHNICAL_ARCHITECTURE.pdf"
pandoc TECHNICAL_ARCHITECTURE.md -o TECHNICAL_ARCHITECTURE.pdf \
    --from markdown \
    --to pdf \
    --pdf-engine=xelatex \
    --toc \
    --toc-depth=$TOC_DEPTH \
    -V geometry:margin=$MARGIN \
    -V fontsize=10pt \
    -V colorlinks

# Convert AUTO_EMAIL_EXTRACTION.md
echo "3️⃣  AUTO_EMAIL_EXTRACTION.md → AUTO_EMAIL_EXTRACTION.pdf"
pandoc AUTO_EMAIL_EXTRACTION.md -o AUTO_EMAIL_EXTRACTION.pdf \
    --from markdown \
    --to pdf \
    --pdf-engine=xelatex \
    --toc \
    --toc-depth=$TOC_DEPTH \
    -V geometry:margin=$MARGIN \
    -V fontsize=$FONT

# Convert FREE_CAMPAIGN_SETUP.md
echo "4️⃣  FREE_CAMPAIGN_SETUP.md → FREE_CAMPAIGN_SETUP.pdf"
pandoc FREE_CAMPAIGN_SETUP.md -o FREE_CAMPAIGN_SETUP.pdf \
    --from markdown \
    --to pdf \
    --pdf-engine=xelatex \
    --toc \
    --toc-depth=$TOC_DEPTH \
    -V geometry:margin=$MARGIN \
    -V fontsize=$FONT

# Convert DEPLOYMENT.md
echo "5️⃣  DEPLOYMENT.md → DEPLOYMENT.pdf"
pandoc DEPLOYMENT.md -o DEPLOYMENT.pdf \
    --from markdown \
    --to pdf \
    --pdf-engine=xelatex \
    --toc \
    --toc-depth=$TOC_DEPTH \
    -V geometry:margin=$MARGIN \
    -V fontsize=$FONT

echo ""
echo "======================================"
echo "✅ PDF Conversion Complete!"
echo "======================================"
echo ""
echo "📄 Generated PDFs:"
ls -lh *.pdf 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
echo ""
echo "📦 Create combined PDF (requires pdfunite):"
echo "   $ pdfunite QUICK_REFERENCE.pdf TECHNICAL_ARCHITECTURE.pdf OUTPUT.pdf"
echo ""
echo "📊 Total pages:"
for pdf in *.pdf; do
    pages=$(pdfinfo "$pdf" 2>/dev/null | grep Pages | awk '{print $2}')
    printf "   %-40s %3d pages\n" "$pdf" "$pages"
done
echo ""

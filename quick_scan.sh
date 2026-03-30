#!/bin/bash
# Quick Network Email Scan Script
# Usage: ./quick_scan.sh [network_range] [template] [limit]

set -e

# Default values
NETWORK=${1:-"192.168.1.0/24"}
TEMPLATE=${2:-"earning_opportunity"}
LIMIT=${3:-"10"}

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         🚀 QUICK NETWORK EMAIL SCAN                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📡 Network: $NETWORK"
echo "📧 Template: $TEMPLATE"
echo "📊 Limit: $LIMIT emails"
echo ""

# Check if nmap is installed
if ! command -v nmap &> /dev/null; then
    echo "❌ nmap not found. Installing..."
    sudo apt update
    sudo apt install -y nmap
fi

# Check if netdiscover is installed
if ! command -v netdiscover &> /dev/null; then
    echo "❌ netdiscover not found. Installing..."
    sudo apt update
    sudo apt install -y netdiscover
fi

# Run the scanner
echo "🔍 Starting scan..."
python3 network_email_scraper.py \
    --scan "$NETWORK" \
    --template "$TEMPLATE" \
    --limit "$LIMIT"

echo ""
echo "✅ Scan complete!"
echo ""
echo "📊 View statistics:"
echo "   python3 devnavigator.py stats"
echo ""
echo "📤 Send more emails:"
echo "   python3 network_email_scraper.py --send-only --template $TEMPLATE --limit 20"

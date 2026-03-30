#!/bin/bash
#
# Full Scan Workflow Script
# 
# Searches all databases for emails, identifies vulnerable IPs/devices,
# and integrates with Metasploit, Nmap, and other Kali tools.
#
# Usage:
#   ./full_scan.sh --range 192.168.1.0/24 [OPTIONS]
#
# Examples:
#   # Scan IP range for databases and extract emails
#   ./full_scan.sh --range 192.168.1.0/24 --extract-emails
#
#   # Full workflow with exploits
#   ./full_scan.sh --range 192.168.1.0/24 --extract-emails --assess-vulnerabilities --run-exploits
#
#   # Use Metasploit for exploitation
#   ./full_scan.sh --range 192.168.1.0/24 --run-exploits --use-metasploit
#
#   # Run Kali Linux tools
#   ./full_scan.sh --range 192.168.1.0/24 --run-kali-tools --kali-tools nmap,hydra
#

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

# Check if required tools are installed
echo "[*] Checking tool availability..."

# Check Nmap
if command -v nmap &> /dev/null; then
    echo "[+] Nmap is available"
else
    echo "[-] Nmap is not available"
fi

# Check Metasploit
if command -v msfconsole &> /dev/null; then
    echo "[+] Metasploit is available"
else
    echo "[-] Metasploit is not available"
fi

# Check other Kali tools
for tool in sqlmap nikto hydra john hashcat tshark; do
    if command -v $tool &> /dev/null; then
        echo "[+] $tool is available"
    else
        echo "[-] $tool is not available"
    fi
done

echo ""

# Run the full scan workflow
python3 -m python_engine.ip_database_scanner.full_scan_workflow "$@"

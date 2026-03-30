#!/usr/bin/env python3
"""
Full Scan Workflow Runner

Searches all databases for emails, identifies vulnerable IPs/devices,
and integrates with Metasploit, Nmap, and other Kali tools.

Usage:
    python run_full_scan.py --range 192.168.1.0/24 [OPTIONS]

Examples:
    # Scan IP range for databases and extract emails
    python run_full_scan.py --range 192.168.1.0/24 --extract-emails

    # Full workflow with exploits
    python run_full_scan.py --range 192.168.1.0/24 --extract-emails --assess-vulnerabilities --run-exploits

    # Use Metasploit for exploitation
    python run_full_scan.py --range 192.168.1.0/24 --run-exploits --use-metasploit

    # Run Kali Linux tools
    python run_full_scan.py --range 192.168.1.0/24 --run-kali-tools --kali-tools nmap,hydra
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from python_engine.ip_database_scanner.full_scan_workflow import main

if __name__ == '__main__':
    sys.exit(main())

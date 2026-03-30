#!/bin/bash
#
# Network Stability Kernel Mode Wrapper Script
#
# This script provides a convenient interface for managing network stability
# and security during potential hacking attacks.
#
# Usage:
#   ./network_stability.sh [OPTIONS]
#
# Examples:
#   # Apply all configurations
#   sudo ./network_stability.sh --apply-all
#
#   # Setup firewall only
#   sudo ./network_stability.sh --setup-firewall
#
#   # Disable watchers
#   sudo ./network_stability.sh --disable-watchers
#
#   # Check status
#   sudo ./network_stability.sh --status
#

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/network_stability_kernel.py"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root"
    echo "Usage: sudo $0 [OPTIONS]"
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

# Run Python script with all arguments
python3 "$PYTHON_SCRIPT" "$@"

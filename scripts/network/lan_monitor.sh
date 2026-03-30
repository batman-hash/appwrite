#!/bin/bash
#
# LAN Monitor - Network Device Discovery and Suspicious IP Monitoring
#
# This script discovers all devices on your LAN and monitors suspicious IPs
# using ncat to detect unauthorized access attempts.
#
# Usage:
#   ./lan_monitor.sh [OPTIONS]
#
# Examples:
#   # Quick scan and monitor
#   ./lan_monitor.sh
#
#   # Scan only (no monitoring)
#   ./lan_monitor.sh --scan-only
#
#   # Monitor for 5 minutes
#   ./lan_monitor.sh --duration 300
#
#   # Monitor specific IPs
#   ./lan_monitor.sh --ips 192.168.1.100,192.168.1.101
#
#   # Use nmap for comprehensive scan
#   ./lan_monitor.sh --scan-method nmap
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default values
INTERFACE=""
SCAN_ONLY=false
MONITOR_ONLY=false
DURATION=0
SCAN_METHOD="ping"
SCAN_PORTS=false
SUSPICIOUS_IPS=""
NCAT_PORTS=""
OUTPUT="lan_devices.json"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
LAN Monitor - Network Device Discovery and Suspicious IP Monitoring

Usage: $0 [OPTIONS]

Options:
    -i, --interface INTERFACE    Network interface to use (auto-detected if not specified)
    -s, --scan-only             Only scan network, do not monitor
    -m, --monitor-only          Only monitor, do not scan
    -d, --duration SECONDS      Monitoring duration in seconds (0 = indefinite)
    --scan-method METHOD        Scan method: arp, ping, or nmap (default: ping)
    --scan-ports                Scan common ports on discovered devices
    --ips IP1,IP2,...            Comma-separated list of IPs to monitor
    --ncat-ports PORT1,PORT2,... Comma-separated list of ports to monitor with ncat
    -o, --output FILE           Output file for device list (default: lan_devices.json)
    -h, --help                  Show this help message

Examples:
    # Quick scan and monitor
    $0

    # Scan only (no monitoring)
    $0 --scan-only

    # Monitor for 5 minutes
    $0 --duration 300

    # Monitor specific IPs
    $0 --ips 192.168.1.100,192.168.1.101

    # Use nmap for comprehensive scan
    $0 --scan-method nmap --scan-ports

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--interface)
            INTERFACE="$2"
            shift 2
            ;;
        -s|--scan-only)
            SCAN_ONLY=true
            shift
            ;;
        -m|--monitor-only)
            MONITOR_ONLY=true
            shift
            ;;
        -d|--duration)
            DURATION="$2"
            shift 2
            ;;
        --scan-method)
            SCAN_METHOD="$2"
            shift 2
            ;;
        --scan-ports)
            SCAN_PORTS=true
            shift
            ;;
        --ips)
            SUSPICIOUS_IPS="$2"
            shift 2
            ;;
        --ncat-ports)
            NCAT_PORTS="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    print_warning "Not running as root. Some operations may require sudo."
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "python3 is not installed"
    exit 1
fi

# Check if required tools are available
print_info "Checking required tools..."

# Check ncat
if command -v ncat &> /dev/null; then
    print_success "ncat is available"
else
    print_warning "ncat is not available. Install with: sudo apt-get install ncat"
fi

# Check nmap if using nmap scan method
if [[ "$SCAN_METHOD" == "nmap" ]]; then
    if command -v nmap &> /dev/null; then
        print_success "nmap is available"
    else
        print_error "nmap is not installed. Install with: sudo apt-get install nmap"
        exit 1
    fi
fi

# Check netstat
if command -v netstat &> /dev/null; then
    print_success "netstat is available"
else
    print_warning "netstat is not available. Install with: sudo apt-get install net-tools"
fi

echo ""

# Build Python command
PYTHON_CMD="python3 $SCRIPT_DIR/lan_monitor.py"

# Add arguments
if [[ -n "$INTERFACE" ]]; then
    PYTHON_CMD="$PYTHON_CMD --interface $INTERFACE"
fi

if [[ "$SCAN_ONLY" == true ]]; then
    PYTHON_CMD="$PYTHON_CMD --scan-only"
fi

if [[ "$MONITOR_ONLY" == true ]]; then
    PYTHON_CMD="$PYTHON_CMD --monitor-only"
fi

if [[ "$DURATION" -gt 0 ]]; then
    PYTHON_CMD="$PYTHON_CMD --monitor-duration $DURATION"
fi

PYTHON_CMD="$PYTHON_CMD --scan-method $SCAN_METHOD"

if [[ "$SCAN_PORTS" == true ]]; then
    PYTHON_CMD="$PYTHON_CMD --scan-ports"
fi

if [[ -n "$SUSPICIOUS_IPS" ]]; then
    PYTHON_CMD="$PYTHON_CMD --suspicious-ips $SUSPICIOUS_IPS"
fi

if [[ -n "$NCAT_PORTS" ]]; then
    PYTHON_CMD="$PYTHON_CMD --ncat-ports $NCAT_PORTS"
fi

PYTHON_CMD="$PYTHON_CMD --output $OUTPUT"

# Print banner
echo "============================================================"
echo "  LAN MONITOR - Network Device Discovery & Monitoring"
echo "============================================================"
echo ""

# Run the Python script
print_info "Starting LAN monitor..."
print_info "Command: $PYTHON_CMD"
echo ""

# Execute with proper error handling
if eval "$PYTHON_CMD"; then
    print_success "LAN monitor completed successfully"
else
    EXIT_CODE=$?
    print_error "LAN monitor failed with exit code $EXIT_CODE"
    exit $EXIT_CODE
fi

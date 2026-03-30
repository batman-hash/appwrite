# LAN Monitor - Quick Start Guide

## Installation

```bash
# Make scripts executable
chmod +x scripts/network/lan_monitor.sh
chmod +x scripts/network/lan_monitor.py

# Install dependencies (if not already installed)
sudo apt-get update
sudo apt-get install -y python3 ncat net-tools nmap
```

## Quick Usage

### 1. Scan Your Network

```bash
# Discover all devices on your LAN
./scripts/network/lan_monitor.sh --scan-only
```

### 2. Monitor Suspicious IPs

```bash
# Monitor specific IPs for 5 minutes
./scripts/network/lan_monitor.sh --ips 192.168.1.100,192.168.1.101 --duration 300
```

### 3. Full Scan and Monitor

```bash
# Scan network and monitor all discovered devices
./scripts/network/lan_monitor.sh
```

### 4. Comprehensive Scan with Port Scanning

```bash
# Use nmap and scan ports
./scripts/network/lan_monitor.sh --scan-method nmap --scan-ports
```

## Common Commands

```bash
# Scan only (no monitoring)
./scripts/network/lan_monitor.sh --scan-only

# Monitor for 10 minutes
./scripts/network/lan_monitor.sh --duration 600

# Monitor specific IPs indefinitely
./scripts/network/lan_monitor.sh --monitor-only --ips 192.168.1.100

# Use specific network interface
./scripts/network/lan_monitor.sh --interface eth0

# Monitor specific ports
./scripts/network/lan_monitor.sh --ncat-ports 22,80,443,3389
```

## Output Files

- `lan_devices.json` - List of discovered devices
- `lan_monitor.log` - Main log file
- `ncat_monitor.log` - NCAT monitoring log
- `connection_monitor.log` - Connection monitoring log

## Example Workflow

```bash
# Step 1: Scan network
./scripts/network/lan_monitor.sh --scan-only

# Step 2: Review discovered devices
cat lan_devices.json

# Step 3: Monitor suspicious IPs
./scripts/network/lan_monitor.sh --ips 192.168.1.100,192.168.1.101 --duration 300

# Step 4: Check logs
tail -f lan_monitor.log
```

## Compile C++ Executable (Optional)

```bash
cd compilation_cpp
make -f Makefile.lan_monitor
sudo make -f Makefile.lan_monitor install

# Now you can run:
./lan_monitor --help
```

## Troubleshooting

### "ncat is not installed"
```bash
sudo apt-get install ncat
```

### "Permission denied"
```bash
sudo ./scripts/network/lan_monitor.sh
```

### "No devices found"
```bash
# Try nmap scan
./scripts/network/lan_monitor.sh --scan-method nmap
```

## Security Notes

- Only use on networks you own or have permission to monitor
- Run with sudo for full functionality
- May trigger firewall alerts
- Use in controlled environments

## More Information

See `scripts/network/README.md` for detailed documentation.

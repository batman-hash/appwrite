# LAN Monitor - Network Device Discovery and Suspicious IP Monitoring

This tool discovers all devices on your local network and monitors suspicious IPs using ncat to detect unauthorized access attempts.

## Overview

The LAN Monitor consists of three main components:

1. **Python Script** (`lan_monitor.py`) - Full-featured network discovery and monitoring
2. **Bash Wrapper** (`lan_monitor.sh`) - Easy-to-use command-line interface
3. **C++ Executable** (`lan_monitor.cpp`) - Standalone compiled executable

## Features

- **Network Discovery**: Automatically discovers all devices on your LAN
- **Multiple Scan Methods**: ARP table, ping sweep, or nmap
- **Port Scanning**: Scan common ports on discovered devices
- **Connection Monitoring**: Monitor active connections in real-time
- **NCAT Integration**: Use ncat to monitor suspicious IPs
- **Logging**: Comprehensive logging of all activities
- **JSON Export**: Save device information to JSON file

## Installation

### Prerequisites

```bash
# Install required tools
sudo apt-get update
sudo apt-get install -y python3 ncat net-tools nmap

# For C++ executable (optional)
sudo apt-get install -y g++ make
```

### Quick Start (Python)

```bash
# Make scripts executable
chmod +x scripts/network/lan_monitor.sh
chmod +x scripts/network/lan_monitor.py

# Run quick scan and monitor
./scripts/network/lan_monitor.sh

# Or run Python script directly
python3 scripts/network/lan_monitor.py
```

### Compile C++ Executable

```bash
cd compilation_cpp
make -f Makefile.lan_monitor
sudo make -f Makefile.lan_monitor install
```

## Usage

### Basic Usage

```bash
# Quick scan and monitor (default)
./scripts/network/lan_monitor.sh

# Scan only (no monitoring)
./scripts/network/lan_monitor.sh --scan-only

# Monitor for 5 minutes
./scripts/network/lan_monitor.sh --duration 300

# Monitor specific IPs
./scripts/network/lan_monitor.sh --ips 192.168.1.100,192.168.1.101
```

### Advanced Usage

```bash
# Use nmap for comprehensive scan
./scripts/network/lan_monitor.sh --scan-method nmap --scan-ports

# Specify network interface
./scripts/network/lan_monitor.sh --interface eth0

# Monitor specific ports with ncat
./scripts/network/lan_monitor.sh --ncat-ports 22,80,443,3389

# Save to custom output file
./scripts/network/lan_monitor.sh --output my_devices.json
```

### Python Script Options

```bash
python3 scripts/network/lan_monitor.py [OPTIONS]

Options:
  --interface, -i INTERFACE    Network interface to use
  --scan-only                 Only scan network, do not monitor
  --monitor-only              Only monitor, do not scan
  --monitor-duration, -d SEC  Monitoring duration (0 = indefinite)
  --scan-method METHOD        Scan method: arp, ping, or nmap
  --scan-ports                Scan common ports on discovered devices
  --suspicious-ips IPS        Comma-separated list of IPs to monitor
  --ncat-ports PORTS          Comma-separated list of ports to monitor
  --output, -o FILE           Output file for device list
```

### C++ Executable Options

```bash
./lan_monitor [OPTIONS]

Options:
  -i, --interface INTERFACE    Network interface to use
  -s, --scan-only             Only scan network, do not monitor
  -m, --monitor-only          Only monitor, do not scan
  -d, --duration SECONDS      Monitoring duration (0 = indefinite)
  --scan-method METHOD        Scan method: arp or ping
  --scan-ports                Scan common ports on discovered devices
  --ips IP1,IP2,...            Comma-separated list of IPs to monitor
  --ncat-ports PORT1,PORT2,... Comma-separated list of ports to monitor
  -o, --output FILE           Output file (default: lan_devices.json)
  -h, --help                  Show this help message
```

## Examples

### Example 1: Quick Network Scan

```bash
# Discover all devices on your network
./scripts/network/lan_monitor.sh --scan-only

# Output:
# [INFO] Scanning network 192.168.1.0/255.255.255.0
# [INFO] Self IP: 192.168.1.10
# [FOUND] 192.168.1.1 (aa:bb:cc:dd:ee:ff) - router.local
# [FOUND] 192.168.1.20 (11:22:33:44:55:66) - laptop.local
# [SUCCESS] Found 2 devices
```

### Example 2: Monitor Suspicious IPs

```bash
# Monitor specific IPs for 10 minutes
./scripts/network/lan_monitor.sh --monitor-only --ips 192.168.1.100,192.168.1.101 --duration 600

# Output:
# [INFO] Starting ncat monitoring for 2 IPs
# [INFO] Monitoring ports: 80, 443, 8080, 8443, 22, 23, 21, 3389
# [MONITOR] Starting ncat listener for 192.168.1.100:80
# [MONITOR] Starting ncat listener for 192.168.1.100:443
# ...
```

### Example 3: Full Scan with Port Scanning

```bash
# Comprehensive scan with port scanning
./scripts/network/lan_monitor.sh --scan-method nmap --scan-ports

# Output:
# [INFO] Running nmap scan...
# [FOUND] 192.168.1.1 (aa:bb:cc:dd:ee:ff) - router.local
# [PORTS] 192.168.1.1 has open ports: 80, 443
# [FOUND] 192.168.1.20 (11:22:33:44:55:66) - laptop.local
# [PORTS] 192.168.1.20 has open ports: 22, 80, 443
```

### Example 4: Monitor All Discovered Devices

```bash
# Scan and monitor all discovered devices
./scripts/network/lan_monitor.sh --duration 300

# This will:
# 1. Scan the network for devices
# 2. Monitor all discovered IPs
# 3. Run for 5 minutes
```

## Output Files

The tool generates several output files:

- `lan_devices.json` - List of discovered devices with details
- `lan_monitor.log` - Main log file
- `ncat_monitor.log` - NCAT monitoring log
- `connection_monitor.log` - Connection monitoring log

### Example JSON Output

```json
{
  "scan_time": "2024-03-30T18:54:53.075Z",
  "network_info": {
    "interface": "eth0",
    "ip_address": "192.168.1.10",
    "netmask": "255.255.255.0",
    "network": "192.168.1.0",
    "broadcast": "192.168.1.255",
    "gateway": "192.168.1.1",
    "mac_address": "00:11:22:33:44:55"
  },
  "self_ip": "192.168.1.10",
  "devices": [
    {
      "ip": "192.168.1.1",
      "mac": "aa:bb:cc:dd:ee:ff",
      "hostname": "router.local",
      "is_self": false,
      "open_ports": [80, 443],
      "last_seen": "2024-03-30T18:54:53.075Z"
    }
  ]
}
```

## How It Works

### 1. Network Discovery

The tool discovers devices using one of three methods:

- **ARP Table**: Fast, passive scan using existing ARP cache
- **Ping Sweep**: Active scan by pinging all IPs in the network
- **Nmap**: Comprehensive scan using nmap's host discovery

### 2. Device Identification

For each discovered device, the tool:

- Gets the MAC address from ARP table
- Resolves hostname using DNS
- Optionally scans common ports

### 3. Connection Monitoring

The tool monitors active connections to detect:

- Connections to sensitive ports (SSH, RDP, VNC, etc.)
- Multiple connections from the same IP
- Unusual connection patterns

### 4. NCAT Monitoring

For suspicious IPs, the tool uses ncat to:

- Listen on common ports
- Allow connections only from specified IPs
- Log all connection attempts
- Detect unauthorized access attempts

## Security Considerations

### Running as Root

Some operations require root privileges:

- Raw socket access for packet capture
- Port scanning below 1024
- Network interface configuration

**Recommendation**: Run with sudo for full functionality.

```bash
sudo ./scripts/network/lan_monitor.sh
```

### Firewall Rules

The tool may trigger firewall alerts. Consider:

- Adding exceptions for the monitoring tool
- Using the tool in a controlled environment
- Notifying network administrators

### Legal Considerations

**Important**: Only use this tool on networks you own or have explicit permission to monitor. Unauthorized network monitoring may violate laws and regulations.

## Troubleshooting

### Issue: "ncat is not installed"

```bash
# Install ncat
sudo apt-get install ncat
```

### Issue: "nmap is not installed"

```bash
# Install nmap
sudo apt-get install nmap
```

### Issue: "Permission denied"

```bash
# Run with sudo
sudo ./scripts/network/lan_monitor.sh
```

### Issue: "No devices found"

```bash
# Try different scan method
./scripts/network/lan_monitor.sh --scan-method nmap

# Specify interface
./scripts/network/lan_monitor.sh --interface eth0
```

### Issue: "Cannot get network information"

```bash
# Check interface name
ip addr show

# Specify interface manually
./scripts/network/lan_monitor.sh --interface wlan0
```

## Integration with Existing Tools

The LAN monitor integrates with your existing network monitoring infrastructure:

- **Network Monitor Module**: Uses existing `python_engine/network_monitor/` components
- **Full Scan Workflow**: Can be combined with `scripts/search/full_scan.sh`
- **IP Database Scanner**: Compatible with `python_engine/ip_database_scanner/`

## Performance

### Scan Speed

- **ARP**: ~1-2 seconds (fastest, uses existing cache)
- **Ping**: ~10-30 seconds (depends on network size)
- **Nmap**: ~30-60 seconds (most comprehensive)

### Resource Usage

- **CPU**: Low to moderate during scanning
- **Memory**: ~50-100 MB
- **Network**: Minimal (only scanning traffic)

## Contributing

To extend the LAN monitor:

1. Add new scan methods in `LANDiscovery` class
2. Implement additional monitoring techniques
3. Add support for more protocols
4. Improve detection algorithms

## License

This tool is part of the devnavigator project.

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review log files for errors
3. Verify network configuration
4. Ensure all dependencies are installed

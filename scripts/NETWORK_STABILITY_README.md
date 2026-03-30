# Network Stability Kernel Mode Script

A comprehensive Python script for managing network stability and security during potential hacking attacks. This script provides kernel-level network management with strict security rules for webcoding environments.

## Features

- **Firewall Management**: iptables/nftables configuration with strict rules
- **eBPF/XDP Integration**: Kernel-level packet filtering for network stability
- **Port Management**: Control which ports can send/receive bytes
- **User-Specific Rules**: Apply rules only to specific username (webcoder)
- **Watcher Management**: Disable unnecessary system watchers
- **DDoS Protection**: Built-in protection against common attacks
- **Connection Tracking**: Advanced connection state management
- **Fail2Ban Integration**: Intrusion prevention system
- **Network Monitoring**: Real-time monitoring of network activity

## Requirements

- Linux operating system (Kali Linux recommended)
- Root privileges
- Python 3.6+
- Required packages (automatically installed):
  - iptables
  - nftables
  - ebpf/bpfcc-tools
  - linux-headers
  - build-essential
  - clang/llvm
  - libbpf-dev
  - tcpdump
  - wireshark/tshark
  - net-tools
  - iproute2
  - conntrack
  - fail2ban
  - ufw/firewalld

## Installation

```bash
# Make script executable
chmod +x scripts/network_stability_kernel.py

# Run with root privileges
sudo python3 scripts/network_stability_kernel.py --apply-all
```

## Usage

### Apply All Configurations

```bash
sudo python3 scripts/network_stability_kernel.py --apply-all
```

This will:
1. Install required packages
2. Disable unnecessary watchers
3. Setup firewall with strict rules
4. Setup eBPF/XDP for network stability
5. Configure port forwarding
6. Setup connection tracking
7. Configure fail2ban
8. Setup DDoS protection
9. Enable network monitoring

### Setup Firewall Only

```bash
sudo python3 scripts/network_stability_kernel.py --setup-firewall
```

### Disable Watchers

```bash
sudo python3 scripts/network_stability_kernel.py --disable-watchers
```

### Check Status

```bash
sudo python3 scripts/network_stability_kernel.py --status
```

### Custom Configuration

```bash
# Custom username and ports
sudo python3 scripts/network_stability_kernel.py \
  --username webcoder \
  --allowed-ports 22,80,443,8080,3000,5000,8000,9000 \
  --denied-ports 23,25,135,137,138,139,445,1433,3306,3389,5432,5900,6379

# Verbose output
sudo python3 scripts/network_stability_kernel.py --apply-all --verbose

# Dry run (show commands without executing)
sudo python3 scripts/network_stability_kernel.py --apply-all --dry-run
```

## Default Configuration

### Allowed Ports (for webcoding)

- 22: SSH
- 80: HTTP
- 443: HTTPS
- 8080: HTTP alternate
- 8443: HTTPS alternate
- 3000: Node.js
- 5000: Python Flask
- 8000: Python Django
- 9000: PHP

### Denied Ports (common attack vectors)

- 23: Telnet
- 25: SMTP
- 135: MSRPC
- 137-139: NetBIOS
- 445: SMB
- 1433-1434: MSSQL
- 3306: MySQL
- 3389: RDP
- 5432: PostgreSQL
- 5900: VNC
- 6379: Redis

## Security Features

### Firewall Rules

- Default policy: DROP all traffic
- Allow loopback interface
- Allow established connections
- Allow specific user (webcoder) outgoing traffic
- Allow specific ports for webcoding
- Deny common attack vector ports
- Rate limiting for SSH (3 attempts/min)
- SYN flood protection
- ICMP rate limiting
- Log dropped packets

### eBPF/XDP

- Kernel-level packet filtering
- Port-based access control
- High-performance packet processing
- Minimal overhead

### DDoS Protection

- SYN flood protection
- Connection rate limiting
- Concurrent connection limits
- New connection rate limiting

### Connection Tracking

- Increased connection tracking limits
- Optimized timeout values
- SYN cookies enabled
- ICMP redirects disabled
- Source routing disabled
- Reverse path filtering enabled

### Fail2Ban

- SSH brute force protection
- Nginx authentication protection
- Nginx rate limit protection
- Nginx bot search protection

## Monitoring

The script automatically sets up network monitoring that logs:
- Active connections count
- Port usage
- Firewall rules
- System resources

Logs are stored in `/var/log/network_stability/`

## File Locations

- Script: `scripts/network_stability_kernel.py`
- Logs: `/var/log/network_stability/`
- eBPF programs: `/etc/network_stability/ebpf/`
- Fail2ban config: `/etc/fail2ban/jail.local`
- Monitoring script: `/usr/local/bin/network_monitor.sh`
- Systemd service: `/etc/systemd/system/network-monitor.service`

## Examples

### Basic Setup for Webcoding

```bash
# Apply all configurations with default settings
sudo python3 scripts/network_stability_kernel.py --apply-all
```

### Custom Port Configuration

```bash
# Allow only specific ports for web development
sudo python3 scripts/network_stability_kernel.py \
  --username webcoder \
  --allowed-ports 22,80,443,3000,5000,8000,9000 \
  --apply-all
```

### Verbose Mode for Debugging

```bash
# See all commands being executed
sudo python3 scripts/network_stability_kernel.py --apply-all --verbose
```

### Dry Run Mode

```bash
# See what would be done without making changes
sudo python3 scripts/network_stability_kernel.py --apply-all --dry-run
```

### Check Current Status

```bash
# View current firewall rules and connection status
sudo python3 scripts/network_stability_kernel.py --status
```

## Troubleshooting

### Script fails with permission error

Make sure you're running with root privileges:
```bash
sudo python3 scripts/network_stability_kernel.py --apply-all
```

### Firewall rules not persisting

The script automatically saves rules to `/etc/iptables/rules.v4`. To restore on boot:
```bash
sudo apt-get install iptables-persistent
sudo systemctl enable netfilter-persistent
```

### eBPF program fails to load

Make sure you have the required kernel headers:
```bash
sudo apt-get install linux-headers-$(uname -r)
```

### Watchers still running after disable

Some watchers may be masked. Check status:
```bash
sudo systemctl status systemd-journald
```

## Security Considerations

1. **Root Required**: This script must be run as root
2. **Firewall Rules**: Default policy is DROP - make sure to allow necessary ports
3. **User Specific**: Rules are applied to specific username (webcoder)
4. **Logging**: All dropped packets are logged
5. **Monitoring**: Network activity is continuously monitored

## License

This script is part of the DevNavigator project.

## Support

For issues or questions, please refer to the main project documentation.

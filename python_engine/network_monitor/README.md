# Network Monitor Module

A comprehensive network monitoring and packet capture module for DevNavigator. Provides multiple packet capture methods with unified interface.

## Features

- **Multiple Capture Methods**: Scapy, Raw Sockets, libpcap, eBPF, CLI tools, NetfilterQueue
- **Packet Analysis**: Ethernet, IP, TCP, UDP, ICMP header parsing
- **Filtering**: Protocol, IP, port-based packet filtering
- **File Operations**: PCAP file reading/writing
- **Statistics**: Capture statistics and metrics
- **CLI Interface**: Command-line tool for packet capture

## Installation

### Basic Installation

```bash
pip install -r requirements.txt
```

### Full Installation (All Features)

```bash
# Core dependencies
pip install scapy netifaces

# libpcap wrapper (choose one)
pip install pcapy
# OR
pip install pylibpcap
# OR
pip install pypcap

# eBPF support (requires kernel headers)
# Ubuntu/Debian
sudo apt-get install bpfcc-tools python3-bcc

# NetfilterQueue support (requires root)
pip install NetfilterQueue
```

## Quick Start

### Python API

```python
from python_engine.network_monitor import NetworkMonitor

# Initialize monitor
monitor = NetworkMonitor()

# Capture 10 packets with Scapy
packets = monitor.capture(method='scapy', count=10)

# Print packet summaries
for packet in packets:
    print(monitor.get_packet_summary(packet))

# Capture with raw sockets (requires root)
packets = monitor.capture(method='raw_socket', interface='eth0', count=50)

# Capture with eBPF (requires root and BCC)
packets = monitor.capture(method='ebpf', interface='eth0', count=100)

# Filter packets
tcp_packets = monitor.filter_packets(packets, protocol='tcp')
http_packets = monitor.filter_packets(packets, dst_port=80)

# Export to JSON
monitor.export_to_json('packets.json', packets)
```

### Command-Line Interface

```bash
# List available capture methods
python -m python_engine.network_monitor.cli methods

# List available network interfaces
python -m python_engine.network_monitor.cli interfaces

# Capture 10 packets with Scapy
python -m python_engine.network_monitor.cli capture --method scapy --count 10

# Capture with raw sockets on eth0
sudo python -m python_engine.network_monitor.cli capture --method raw_socket --interface eth0 --count 50

# Capture with tcpdump
python -m python_engine.network_monitor.cli capture --method cli --tool tcpdump --interface eth0 --count 20

# Capture to PCAP file
python -m python_engine.network_monitor.cli capture --method scapy --output capture.pcap --count 100

# Read PCAP file
python -m python_engine.network_monitor.cli read capture.pcap

# Analyze PCAP file
python -m python_engine.network_monitor.cli stats capture.pcap
```

## Capture Methods

### 1. Scapy (High-Level API)

**Best for**: Quick prototyping, packet manipulation, protocol analysis

```python
from python_engine.network_monitor import ScapyCapture

capture = ScapyCapture(interface='eth0')

# Live capture
packets = capture.capture_live(count=10, filter_expr='tcp port 80')

# Capture to file
stats = capture.capture_to_file('capture.pcap', count=100)

# Read PCAP file
packets = capture.read_pcap('capture.pcap')

# Filter packets
tcp_packets = capture.filter_packets(packets, protocol='tcp')
```

**Pros**:
- Easy to use
- Powerful packet manipulation
- Cross-platform

**Cons**:
- Slower than raw sockets
- Requires Scapy installation

### 2. Raw Sockets (AF_PACKET)

**Best for**: High-performance capture, Linux-specific applications

```python
from python_engine.network_monitor import RawSocketCapture

capture = RawSocketCapture(interface='eth0', buffer_size=65535)

# Capture packets
packets = capture.capture(count=100, timeout=10)

# Continuous capture with callback
def packet_handler(packet_info):
    print(f"Captured: {packet_info['ip']['src_ip']} -> {packet_info['ip']['dst_ip']}")

capture.capture_continuous(callback=packet_handler)
```

**Pros**:
- Very fast
- Direct kernel access
- Minimal overhead

**Cons**:
- Linux only
- Requires root privileges
- Manual header parsing

### 3. libpcap Wrappers

**Best for**: Cross-platform capture, production applications

```python
from python_engine.network_monitor import LibpcapCapture

capture = LibpcapCapture(interface='eth0')

# Capture packets
packets = capture.capture(count=100, filter_expr='tcp port 80')

# Read PCAP file
packets = capture.read_pcap('capture.pcap')
```

**Pros**:
- Industry standard
- Cross-platform
- BPF filter support

**Cons**:
- Requires libpcap installation
- Multiple Python wrappers available

### 4. eBPF (Kernel-Level)

**Best for**: High-performance filtering, kernel-level monitoring

```python
from python_engine.network_monitor import EBpfCapture

capture = EBpfCapture(interface='eth0', backend='bcc')

# XDP capture (highest performance)
packets = capture.capture_xdp(count=1000)

# kprobe capture (fallback)
packets = capture.capture_kprobe(count=1000)
```

**Pros**:
- Extremely fast
- Kernel-level filtering
- Minimal CPU overhead

**Cons**:
- Requires root privileges
- Requires kernel headers (BCC) or CO-RE (libbpf)
- Linux only

### 5. CLI Tools (TShark/tcpdump)

**Best for**: Leveraging existing tools, protocol analysis

```python
from python_engine.network_monitor import CliCapture

# Using tshark
capture = CliCapture(interface='eth0', tool='tshark')
packets = capture.capture(count=50, filter_expr='tcp port 80')

# Using tcpdump
capture = CliCapture(interface='eth0', tool='tcpdump')
packets = capture.capture(count=50)
```

**Pros**:
- Powerful protocol analysis
- No Python dependencies
- Leverages existing tools

**Cons**:
- Requires tshark/tcpdump installation
- Slower than kernel-level methods
- Subprocess overhead

### 6. NetfilterQueue

**Best for**: Packet filtering, firewall integration

```python
from python_engine.network_monitor import NetfilterCapture

capture = NetfilterCapture(queue_num=1)

# Capture and filter packets
def packet_handler(packet_info):
    # Drop packets from specific IP
    if packet_info['ip']['src_ip'] == '192.168.1.100':
        return capture.NF_DROP
    return capture.NF_ACCEPT

packets = capture.capture(count=100, callback=packet_handler)
```

**Pros**:
- Userspace packet processing
- Can modify packets
- Integrates with iptables/nftables

**Cons**:
- Requires root privileges
- Linux only
- Requires iptables rules

## Packet Analysis

### Packet Structure

```python
{
    'packet_number': 1,
    'timestamp': '2024-01-01T12:00:00',
    'raw_length': 1514,
    'protocols': ['Ethernet', 'IP', 'TCP'],
    'ethernet': {
        'src_mac': '00:11:22:33:44:55',
        'dst_mac': '66:77:88:99:aa:bb',
        'ethertype': '0x800'
    },
    'ip': {
        'src_ip': '192.168.1.100',
        'dst_ip': '192.168.1.200',
        'protocol': 6,
        'ttl': 64,
        'total_length': 1500
    },
    'tcp': {
        'src_port': 12345,
        'dst_port': 80,
        'flags': {'SYN': True, 'ACK': False},
        'sequence': 1234567890,
        'acknowledgment': 0
    }
}
```

### Filtering Packets

```python
# Filter by protocol
tcp_packets = monitor.filter_packets(packets, protocol='tcp')
udp_packets = monitor.filter_packets(packets, protocol='udp')

# Filter by IP address
from_ip = monitor.filter_packets(packets, src_ip='192.168.1.100')
to_ip = monitor.filter_packets(packets, dst_ip='192.168.1.200')

# Filter by port
http_packets = monitor.filter_packets(packets, dst_port=80)
https_packets = monitor.filter_packets(packets, dst_port=443)

# Combine filters
filtered = monitor.filter_packets(
    packets,
    protocol='tcp',
    dst_ip='192.168.1.200',
    dst_port=80
)
```

## File Operations

### Writing PCAP Files

```python
# Using Scapy
capture = ScapyCapture(interface='eth0')
stats = capture.capture_to_file('capture.pcap', count=100)

# Using CLI tools
capture = CliCapture(interface='eth0', tool='tshark')
stats = capture.capture_to_file('capture.pcap', count=100)
```

### Reading PCAP Files

```python
# Using Scapy
capture = ScapyCapture()
packets = capture.read_pcap('capture.pcap')

# Using CLI tools
capture = CliCapture(tool='tshark')
packets = capture.read_pcap('capture.pcap')
```

### Exporting to JSON

```python
monitor = NetworkMonitor()
packets = monitor.capture(method='scapy', count=100)
monitor.export_to_json('packets.json', packets)
```

## Statistics

```python
monitor = NetworkMonitor()
packets = monitor.capture(method='scapy', count=100)

stats = monitor.get_stats()
print(f"Packets captured: {stats['packets_captured']}")
print(f"Bytes captured: {stats['bytes_captured']}")
print(f"Duration: {stats['duration_seconds']} seconds")
print(f"Packets/second: {stats['packets_per_second']}")
```

## Performance Comparison

| Method | Packets/Second | CPU Usage | Memory Usage | Root Required |
|--------|---------------|-----------|--------------|---------------|
| Scapy | 1,000-5,000 | Low | Medium | No |
| Raw Sockets | 10,000-50,000 | Low | Low | Yes |
| libpcap | 5,000-20,000 | Low | Low | No |
| eBPF (XDP) | 100,000+ | Very Low | Low | Yes |
| CLI Tools | 500-2,000 | Medium | Medium | No |
| NetfilterQueue | 5,000-20,000 | Low | Low | Yes |

## Troubleshooting

### Permission Denied

```bash
# Raw sockets and eBPF require root
sudo python -m python_engine.network_monitor.cli capture --method raw_socket

# Or grant capabilities
sudo setcap cap_net_raw+ep /usr/bin/python3
```

### Module Not Found

```bash
# Install missing dependencies
pip install scapy netifaces pcapy

# For eBPF
sudo apt-get install bpfcc-tools python3-bcc

# For NetfilterQueue
pip install NetfilterQueue
```

### Interface Not Found

```bash
# List available interfaces
python -m python_engine.network_monitor.cli interfaces

# Or use ip command
ip link show
```

## Examples

### Example 1: HTTP Traffic Monitor

```python
from python_engine.network_monitor import NetworkMonitor

monitor = NetworkMonitor()

# Capture HTTP traffic
http_packets = monitor.capture(
    method='scapy',
    filter_expr='tcp port 80',
    count=100
)

# Analyze HTTP requests
for packet in http_packets:
    if packet.get('tcp', {}).get('dst_port') == 80:
        print(f"HTTP Request: {packet['ip']['src_ip']} -> {packet['ip']['dst_ip']}")
```

### Example 2: Network Statistics

```python
from python_engine.network_monitor import NetworkMonitor

monitor = NetworkMonitor()

# Capture for 60 seconds
packets = monitor.capture(
    method='scapy',
    timeout=60
)

# Calculate statistics
protocols = {}
for packet in packets:
    for proto in packet.get('protocols', []):
        protocols[proto] = protocols.get(proto, 0) + 1

print("Protocol distribution:")
for proto, count in protocols.items():
    print(f"  {proto}: {count}")
```

### Example 3: Packet Filtering

```python
from python_engine.network_monitor import NetworkMonitor

monitor = NetworkMonitor()

# Capture packets
packets = monitor.capture(method='scapy', count=1000)

# Filter by various criteria
tcp_packets = monitor.filter_packets(packets, protocol='tcp')
udp_packets = monitor.filter_packets(packets, protocol='udp')
http_packets = monitor.filter_packets(packets, dst_port=80)
https_packets = monitor.filter_packets(packets, dst_port=443)

print(f"Total packets: {len(packets)}")
print(f"TCP packets: {len(tcp_packets)}")
print(f"UDP packets: {len(udp_packets)}")
print(f"HTTP packets: {len(http_packets)}")
print(f"HTTPS packets: {len(https_packets)}")
```

## License

Part of DevNavigator project. See main project LICENSE for details.

## Support

For issues and questions, please refer to the main DevNavigator documentation.

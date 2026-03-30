"""
Network Monitor CLI Interface

Command-line interface for network monitoring and packet capture.
"""

import argparse
import sys
import json
from typing import Optional, List
from datetime import datetime

from .network_monitor import NetworkMonitor, CaptureConfig


def create_parser() -> argparse.ArgumentParser:
    """
    Create command-line argument parser.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        prog='network-monitor',
        description='Network Monitor - Packet Capture and Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Capture 10 packets with Scapy
  network-monitor capture --method scapy --count 10
  
  # Capture with raw sockets on eth0
  network-monitor capture --method raw_socket --interface eth0 --count 50
  
  # Capture with eBPF (XDP)
  network-monitor capture --method ebpf --interface eth0 --count 100
  
  # Capture with tcpdump
  network-monitor capture --method cli --tool tcpdump --interface eth0 --count 20
  
  # Capture to PCAP file
  network-monitor capture --method scapy --output capture.pcap --count 100
  
  # Read PCAP file
  network-monitor read capture.pcap
  
  # List available methods
  network-monitor methods
  
  # List available interfaces
  network-monitor interfaces
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Capture command
    capture_parser = subparsers.add_parser(
        'capture',
        help='Capture packets from network interface'
    )
    capture_parser.add_argument(
        '--method', '-m',
        choices=['scapy', 'raw_socket', 'libpcap', 'ebpf', 'cli', 'netfilter'],
        default='scapy',
        help='Capture method to use (default: scapy)'
    )
    capture_parser.add_argument(
        '--interface', '-i',
        help='Network interface to capture from (e.g., eth0, wlan0)'
    )
    capture_parser.add_argument(
        '--count', '-c',
        type=int,
        default=0,
        help='Number of packets to capture (0 = unlimited, default: 0)'
    )
    capture_parser.add_argument(
        '--timeout', '-t',
        type=int,
        help='Timeout in seconds (default: None)'
    )
    capture_parser.add_argument(
        '--filter', '-f',
        help='BPF filter expression (e.g., "tcp port 80")'
    )
    capture_parser.add_argument(
        '--output', '-o',
        help='Output PCAP filename'
    )
    capture_parser.add_argument(
        '--tool',
        choices=['tshark', 'tcpdump'],
        default='tshark',
        help='CLI tool to use (default: tshark)'
    )
    capture_parser.add_argument(
        '--backend',
        choices=['bcc', 'libbpf'],
        default='bcc',
        help='eBPF backend to use (default: bcc)'
    )
    capture_parser.add_argument(
        '--queue-num',
        type=int,
        default=1,
        help='Netfilter queue number (default: 1)'
    )
    capture_parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )
    capture_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    # Read command
    read_parser = subparsers.add_parser(
        'read',
        help='Read packets from PCAP file'
    )
    read_parser.add_argument(
        'filename',
        help='PCAP filename to read'
    )
    read_parser.add_argument(
        '--method', '-m',
        choices=['scapy', 'cli'],
        default='scapy',
        help='Method to use for reading (default: scapy)'
    )
    read_parser.add_argument(
        '--tool',
        choices=['tshark', 'tcpdump'],
        default='tshark',
        help='CLI tool to use (default: tshark)'
    )
    read_parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )
    
    # Methods command
    subparsers.add_parser(
        'methods',
        help='List available capture methods'
    )
    
    # Interfaces command
    subparsers.add_parser(
        'interfaces',
        help='List available network interfaces'
    )
    
    # Stats command
    stats_parser = subparsers.add_parser(
        'stats',
        help='Show capture statistics'
    )
    stats_parser.add_argument(
        'filename',
        help='PCAP filename to analyze'
    )
    
    return parser


def print_packet(packet_info: dict, verbose: bool = False):
    """
    Print packet information.
    
    Args:
        packet_info: Packet information dictionary
        verbose: Whether to print verbose output
    """
    protocols = ' -> '.join(packet_info.get('protocols', []))
    
    print(f"\n{'='*60}")
    print(f"Packet #{packet_info.get('packet_number', '?')}")
    print(f"{'='*60}")
    print(f"Timestamp: {packet_info.get('timestamp', 'N/A')}")
    print(f"Length: {packet_info.get('raw_length', 0)} bytes")
    print(f"Protocols: {protocols}")
    
    if packet_info.get('ethernet'):
        eth = packet_info['ethernet']
        print(f"\nEthernet:")
        print(f"  Source MAC: {eth.get('src_mac', 'N/A')}")
        print(f"  Dest MAC: {eth.get('dst_mac', 'N/A')}")
        print(f"  EtherType: {eth.get('ethertype', 'N/A')}")
    
    if packet_info.get('ip'):
        ip = packet_info['ip']
        print(f"\nIP:")
        print(f"  Source IP: {ip.get('src_ip', 'N/A')}")
        print(f"  Dest IP: {ip.get('dst_ip', 'N/A')}")
        print(f"  Protocol: {ip.get('protocol', 'N/A')}")
        print(f"  TTL: {ip.get('ttl', 'N/A')}")
        print(f"  Length: {ip.get('total_length', 'N/A')}")
    
    if packet_info.get('tcp'):
        tcp = packet_info['tcp']
        print(f"\nTCP:")
        print(f"  Source Port: {tcp.get('src_port', 'N/A')}")
        print(f"  Dest Port: {tcp.get('dst_port', 'N/A')}")
        print(f"  Flags: {tcp.get('flags', 'N/A')}")
        print(f"  Sequence: {tcp.get('sequence', 'N/A')}")
        print(f"  Acknowledgment: {tcp.get('acknowledgment', 'N/A')}")
    
    if packet_info.get('udp'):
        udp = packet_info['udp']
        print(f"\nUDP:")
        print(f"  Source Port: {udp.get('src_port', 'N/A')}")
        print(f"  Dest Port: {udp.get('dst_port', 'N/A')}")
        print(f"  Length: {udp.get('length', 'N/A')}")
    
    if packet_info.get('icmp'):
        icmp = packet_info['icmp']
        print(f"\nICMP:")
        print(f"  Type: {icmp.get('type', 'N/A')}")
        print(f"  Code: {icmp.get('code', 'N/A')}")
    
    if verbose and packet_info.get('raw_output'):
        print(f"\nRaw Output:")
        print(packet_info['raw_output'])


def print_stats(stats: dict):
    """
    Print capture statistics.
    
    Args:
        stats: Statistics dictionary
    """
    print(f"\n{'='*60}")
    print("Capture Statistics")
    print(f"{'='*60}")
    
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")


def cmd_capture(args):
    """
    Execute capture command.
    
    Args:
        Parsed command-line arguments
    """
    try:
        monitor = NetworkMonitor()
        
        print(f"Starting capture with method: {args.method}")
        if args.interface:
            print(f"Interface: {args.interface}")
        print(f"Count: {args.count if args.count > 0 else 'unlimited'}")
        if args.timeout:
            print(f"Timeout: {args.timeout} seconds")
        if args.filter:
            print(f"Filter: {args.filter}")
        
        print("\nCapturing packets... (Press Ctrl+C to stop)\n")
        
        # Capture packets
        if args.output:
            # Capture to file
            stats = monitor.capture_to_file(
                filename=args.output,
                method=args.method,
                interface=args.interface,
                count=args.count,
                timeout=args.timeout,
                filter_expr=args.filter,
                tool=args.tool,
                backend=args.backend,
                queue_num=args.queue_num
            )
            print(f"\nCaptured to file: {args.output}")
            print_stats(stats)
        else:
            # Capture and display
            packets = monitor.capture(
                method=args.method,
                interface=args.interface,
                count=args.count,
                timeout=args.timeout,
                filter_expr=args.filter,
                tool=args.tool,
                backend=args.backend,
                queue_num=args.queue_num
            )
            
            if args.json:
                # Output as JSON
                output = []
                for packet in packets:
                    packet_copy = packet.copy()
                    if 'raw_data' in packet_copy:
                        del packet_copy['raw_data']
                    output.append(packet_copy)
                print(json.dumps(output, indent=2, default=str))
            else:
                # Print packets
                for packet in packets:
                    print_packet(packet, verbose=args.verbose)
                
                # Print statistics
                stats = monitor.get_stats()
                print_stats(stats)
        
    except KeyboardInterrupt:
        print("\n\nCapture stopped by user")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_read(args):
    """
    Execute read command.
    
    Args:
        Parsed command-line arguments
    """
    try:
        monitor = NetworkMonitor()
        
        print(f"Reading PCAP file: {args.filename}")
        
        packets = monitor.read_pcap(
            filename=args.filename,
            method=args.method,
            tool=args.tool
        )
        
        if args.json:
            # Output as JSON
            output = []
            for packet in packets:
                packet_copy = packet.copy()
                if 'raw_data' in packet_copy:
                    del packet_copy['raw_data']
                output.append(packet_copy)
            print(json.dumps(output, indent=2, default=str))
        else:
            # Print packets
            for packet in packets:
                print_packet(packet)
            
            # Print statistics
            print(f"\nTotal packets: {len(packets)}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_methods(args):
    """
    Execute methods command.
    
    Args:
        Parsed command-line arguments
    """
    available = NetworkMonitor.get_available_methods()
    all_methods = NetworkMonitor.SUPPORTED_METHODS
    
    print("\nAvailable Capture Methods:")
    print("="*60)
    
    for method in all_methods:
        status = "✓ Available" if method in available else "✗ Not available"
        print(f"  {method:15} {status}")
    
    print(f"\nTotal: {len(available)}/{len(all_methods)} methods available")


def cmd_interfaces(args):
    """
    Execute interfaces command.
    
    Args:
        Parsed command-line arguments
    """
    interfaces = NetworkMonitor.get_interfaces()
    
    print("\nAvailable Network Interfaces:")
    print("="*60)
    
    for iface in interfaces:
        print(f"  {iface}")
    
    print(f"\nTotal: {len(interfaces)} interfaces")


def cmd_stats(args):
    """
    Execute stats command.
    
    Args:
        Parsed command-line arguments
    """
    try:
        monitor = NetworkMonitor()
        
        print(f"Analyzing PCAP file: {args.filename}")
        
        packets = monitor.read_pcap(
            filename=args.filename,
            method='scapy'
        )
        
        # Calculate statistics
        total_packets = len(packets)
        total_bytes = sum(p.get('raw_length', 0) for p in packets)
        
        protocols = {}
        for packet in packets:
            for proto in packet.get('protocols', []):
                protocols[proto] = protocols.get(proto, 0) + 1
        
        src_ips = {}
        dst_ips = {}
        for packet in packets:
            if packet.get('ip'):
                src_ip = packet['ip'].get('src_ip')
                dst_ip = packet['ip'].get('dst_ip')
                if src_ip:
                    src_ips[src_ip] = src_ips.get(src_ip, 0) + 1
                if dst_ip:
                    dst_ips[dst_ip] = dst_ips.get(dst_ip, 0) + 1
        
        # Print statistics
        print(f"\n{'='*60}")
        print("PCAP File Statistics")
        print(f"{'='*60}")
        print(f"Total Packets: {total_packets}")
        print(f"Total Bytes: {total_bytes}")
        print(f"Average Packet Size: {total_bytes / total_packets if total_packets > 0 else 0:.2f} bytes")
        
        print(f"\nProtocol Distribution:")
        for proto, count in sorted(protocols.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_packets * 100) if total_packets > 0 else 0
            print(f"  {proto:15} {count:6} ({percentage:.1f}%)")
        
        print(f"\nTop Source IPs:")
        for ip, count in sorted(src_ips.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {ip:20} {count:6}")
        
        print(f"\nTop Destination IPs:")
        for ip, count in sorted(dst_ips.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {ip:20} {count:6}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Execute command
    if args.command == 'capture':
        cmd_capture(args)
    elif args.command == 'read':
        cmd_read(args)
    elif args.command == 'methods':
        cmd_methods(args)
    elif args.command == 'interfaces':
        cmd_interfaces(args)
    elif args.command == 'stats':
        cmd_stats(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

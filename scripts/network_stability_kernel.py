#!/usr/bin/env python3
"""
Network Stability Kernel Mode Script

Enables minimum requirements to ensure network stability during hacking attack risks.
Manages remote ports, disables unnecessary watchers, and applies strict security rules
for webcoding username.

Features:
- iptables/nftables firewall management
- eBPF/XDP for network stability
- Port management for send/receive
- User-specific rules
- Strict security policies
- Package installation
- Watcher management
"""

import os
import sys
import subprocess
import argparse
import json
import time
import signal
import threading
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime


@dataclass
class NetworkRule:
    """Network rule configuration"""
    name: str
    port: int
    protocol: str
    direction: str  # 'in', 'out', 'both'
    action: str  # 'allow', 'deny', 'limit'
    source: Optional[str] = None
    destination: Optional[str] = None
    rate_limit: Optional[str] = None
    enabled: bool = True


@dataclass
class SecurityConfig:
    """Security configuration"""
    username: str
    allowed_ports: List[int]
    denied_ports: List[int]
    enable_firewall: bool = True
    enable_ebpf: bool = True
    enable_watchers: bool = False
    strict_mode: bool = True
    log_level: str = 'INFO'


class NetworkStabilityKernel:
    """
    Network stability kernel mode manager.

    Provides comprehensive network security and stability management
    for webcoding environment.
    """

    # Required packages for network stability
    REQUIRED_PACKAGES = [
        'iptables',
        'nftables',
        'ebpf',
        'bpfcc-tools',
        'linux-headers-$(uname -r)',
        'build-essential',
        'clang',
        'llvm',
        'libbpf-dev',
        'tcpdump',
        'wireshark',
        'tshark',
        'net-tools',
        'iproute2',
        'conntrack',
        'fail2ban',
        'ufw',
        'firewalld',
    ]

    # Default allowed ports for webcoding
    DEFAULT_ALLOWED_PORTS = [
        22,    # SSH
        80,    # HTTP
        443,   # HTTPS
        8080,  # HTTP alternate
        8443,  # HTTPS alternate
        3000,  # Node.js
        5000,  # Python Flask
        8000,  # Python Django
        9000,  # PHP
    ]

    # Default denied ports (common attack vectors)
    DEFAULT_DENIED_PORTS = [
        23,    # Telnet
        25,    # SMTP
        135,   # MSRPC
        137,   # NetBIOS
        138,   # NetBIOS
        139,   # NetBIOS
        445,   # SMB
        1433,  # MSSQL
        1434,  # MSSQL
        3306,  # MySQL
        3389,  # RDP
        5432,  # PostgreSQL
        5900,  # VNC
        6379,  # Redis
    ]

    def __init__(
        self,
        config: SecurityConfig,
        verbose: bool = False,
        dry_run: bool = False
    ):
        """
        Initialize network stability kernel manager.

        Args:
            config: Security configuration
            verbose: Enable verbose output
            dry_run: Show commands without executing
        """
        self.config = config
        self.verbose = verbose
        self.dry_run = dry_run
        self.rules: List[NetworkRule] = []
        self.ebpf_program = None
        self.running = False

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging configuration"""
        import logging

        # For dry-run mode, only use console logging
        if self.dry_run:
            logging.basicConfig(
                level=getattr(logging, self.config.log_level),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )
            self.logger = logging.getLogger(__name__)
            return

        # For normal mode, try to create log directory
        try:
            log_dir = Path('/var/log/network_stability')
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / f'network_stability_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

            logging.basicConfig(
                level=getattr(logging, self.config.log_level),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler(sys.stdout)
                ]
            )
        except PermissionError:
            # Fall back to console-only logging if we can't create log directory
            logging.basicConfig(
                level=getattr(logging, self.config.log_level),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )

        self.logger = logging.getLogger(__name__)

    def check_root(self) -> bool:
        """Check if running as root"""
        return os.geteuid() == 0

    def run_command(
        self,
        cmd: List[str],
        check: bool = True,
        capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run shell command.

        Args:
            cmd: Command to run
            check: Raise exception on failure
            capture_output: Capture output

        Returns:
            CompletedProcess object
        """
        if self.verbose:
            self.logger.info(f"Running command: {' '.join(cmd)}")

        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would run: {' '.join(cmd)}")
            return subprocess.CompletedProcess(cmd, 0, '', '')

        try:
            result = subprocess.run(
                cmd,
                check=check,
                capture_output=capture_output,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {e}")
            raise

    def install_packages(self) -> bool:
        """
        Install required packages for network stability.

        Returns:
            True if successful
        """
        self.logger.info("Installing required packages...")

        # Update package list
        self.run_command(['apt-get', 'update'], check=False)

        # Install packages
        for package in self.REQUIRED_PACKAGES:
            try:
                self.logger.info(f"Installing {package}...")
                self.run_command(
                    ['apt-get', 'install', '-y', package],
                    check=False
                )
            except Exception as e:
                self.logger.warning(f"Failed to install {package}: {e}")

        return True

    def disable_watchers(self) -> bool:
        """
        Disable unnecessary watchers and monitoring services.

        Returns:
            True if successful
        """
        self.logger.info("Disabling unnecessary watchers...")

        watchers_to_disable = [
            'systemd-journald',
            'rsyslog',
            'auditd',
            'syslog',
            'klogd',
            'watchdog',
            'thermald',
            'powerd',
            'acpid',
            'cron',
            'atd',
            'anacron',
        ]

        for watcher in watchers_to_disable:
            try:
                self.logger.info(f"Disabling {watcher}...")
                self.run_command(
                    ['systemctl', 'stop', watcher],
                    check=False
                )
                self.run_command(
                    ['systemctl', 'disable', watcher],
                    check=False
                )
                self.run_command(
                    ['systemctl', 'mask', watcher],
                    check=False
                )
            except Exception as e:
                self.logger.warning(f"Failed to disable {watcher}: {e}")

        return True

    def setup_firewall(self) -> bool:
        """
        Setup firewall with strict rules.

        Returns:
            True if successful
        """
        self.logger.info("Setting up firewall...")

        # Flush existing rules
        self.run_command(['iptables', '-F'], check=False)
        self.run_command(['iptables', '-X'], check=False)
        self.run_command(['iptables', '-t', 'nat', '-F'], check=False)
        self.run_command(['iptables', '-t', 'nat', '-X'], check=False)

        # Set default policies (IPv4)
        self.run_command(['iptables', '-P', 'INPUT', 'DROP'])
        self.run_command(['iptables', '-P', 'FORWARD', 'DROP'])
        self.run_command(['iptables', '-P', 'OUTPUT', 'DROP'])

        # Set default policies (IPv6)
        self.run_command(['ip6tables', '-P', 'INPUT', 'DROP'], check=False)
        self.run_command(['ip6tables', '-P', 'FORWARD', 'DROP'], check=False)
        self.run_command(['ip6tables', '-P', 'OUTPUT', 'DROP'], check=False)

        # Allow loopback (IPv4)
        self.run_command(['iptables', '-A', 'INPUT', '-i', 'lo', '-j', 'ACCEPT'])
        self.run_command(['iptables', '-A', 'OUTPUT', '-o', 'lo', '-j', 'ACCEPT'])

        # Allow loopback (IPv6)
        self.run_command(['ip6tables', '-A', 'INPUT', '-i', 'lo', '-j', 'ACCEPT'], check=False)
        self.run_command(['ip6tables', '-A', 'OUTPUT', '-o', 'lo', '-j', 'ACCEPT'], check=False)

        # Allow established connections (IPv4)
        self.run_command([
            'iptables', '-A', 'INPUT',
            '-m', 'conntrack',
            '--ctstate', 'ESTABLISHED,RELATED',
            '-j', 'ACCEPT'
        ])
        self.run_command([
            'iptables', '-A', 'OUTPUT',
            '-m', 'conntrack',
            '--ctstate', 'ESTABLISHED,RELATED',
            '-j', 'ACCEPT'
        ])

        # Allow established connections (IPv6)
        self.run_command([
            'ip6tables', '-A', 'INPUT',
            '-m', 'conntrack',
            '--ctstate', 'ESTABLISHED,RELATED',
            '-j', 'ACCEPT'
        ], check=False)
        self.run_command([
            'ip6tables', '-A', 'OUTPUT',
            '-m', 'conntrack',
            '--ctstate', 'ESTABLISHED,RELATED',
            '-j', 'ACCEPT'
        ], check=False)

        # Allow specific user
        self.run_command([
            'iptables', '-A', 'OUTPUT',
            '-m', 'owner',
            '--uid-owner', self.config.username,
            '-j', 'ACCEPT'
        ])

        # Allow specific ports
        for port in self.config.allowed_ports:
            self.logger.info(f"Allowing port {port}...")

            # Allow incoming (IPv4)
            self.run_command([
                'iptables', '-A', 'INPUT',
                '-p', 'tcp',
                '--dport', str(port),
                '-j', 'ACCEPT'
            ])

            # Allow outgoing (IPv4)
            self.run_command([
                'iptables', '-A', 'OUTPUT',
                '-p', 'tcp',
                '--sport', str(port),
                '-j', 'ACCEPT'
            ])

            # Allow incoming (IPv6)
            self.run_command([
                'ip6tables', '-A', 'INPUT',
                '-p', 'tcp',
                '--dport', str(port),
                '-j', 'ACCEPT'
            ], check=False)

            # Allow outgoing (IPv6)
            self.run_command([
                'ip6tables', '-A', 'OUTPUT',
                '-p', 'tcp',
                '--sport', str(port),
                '-j', 'ACCEPT'
            ], check=False)

        # Deny specific ports
        for port in self.config.denied_ports:
            self.logger.info(f"Denying port {port}...")

            # Deny incoming (IPv4)
            self.run_command([
                'iptables', '-A', 'INPUT',
                '-p', 'tcp',
                '--dport', str(port),
                '-j', 'DROP'
            ])

            # Deny outgoing (IPv4)
            self.run_command([
                'iptables', '-A', 'OUTPUT',
                '-p', 'tcp',
                '--sport', str(port),
                '-j', 'DROP'
            ])

            # Deny incoming (IPv6)
            self.run_command([
                'ip6tables', '-A', 'INPUT',
                '-p', 'tcp',
                '--dport', str(port),
                '-j', 'DROP'
            ], check=False)

            # Deny outgoing (IPv6)
            self.run_command([
                'ip6tables', '-A', 'OUTPUT',
                '-p', 'tcp',
                '--sport', str(port),
                '-j', 'DROP'
            ], check=False)

        # Rate limiting for SSH (IPv4)
        self.run_command([
            'iptables', '-A', 'INPUT',
            '-p', 'tcp',
            '--dport', '22',
            '-m', 'limit',
            '--limit', '3/min',
            '--limit-burst', '3',
            '-j', 'ACCEPT'
        ])

        # Rate limiting for SSH (IPv6)
        self.run_command([
            'ip6tables', '-A', 'INPUT',
            '-p', 'tcp',
            '--dport', '22',
            '-m', 'limit',
            '--limit', '3/min',
            '--limit-burst', '3',
            '-j', 'ACCEPT'
        ], check=False)

        # SYN flood protection (IPv4)
        self.run_command([
            'iptables', '-A', 'INPUT',
            '-p', 'tcp',
            '--syn',
            '-m', 'limit',
            '--limit', '1/s',
            '--limit-burst', '3',
            '-j', 'ACCEPT'
        ])

        # SYN flood protection (IPv6)
        self.run_command([
            'ip6tables', '-A', 'INPUT',
            '-p', 'tcp',
            '--syn',
            '-m', 'limit',
            '--limit', '1/s',
            '--limit-burst', '3',
            '-j', 'ACCEPT'
        ], check=False)

        # ICMP rate limiting (IPv4)
        self.run_command([
            'iptables', '-A', 'INPUT',
            '-p', 'icmp',
            '--icmp-type', 'echo-request',
            '-m', 'limit',
            '--limit', '1/s',
            '--limit-burst', '4',
            '-j', 'ACCEPT'
        ])

        # ICMPv6 rate limiting (IPv6)
        self.run_command([
            'ip6tables', '-A', 'INPUT',
            '-p', 'ipv6-icmp',
            '--icmpv6-type', 'echo-request',
            '-m', 'limit',
            '--limit', '1/s',
            '--limit-burst', '4',
            '-j', 'ACCEPT'
        ], check=False)

        # Log dropped packets (IPv4)
        self.run_command([
            'iptables', '-A', 'INPUT',
            '-j', 'LOG',
            '--log-prefix', 'IPTABLES_INPUT_DROPPED: ',
            '--log-level', '4'
        ])

        self.run_command([
            'iptables', '-A', 'OUTPUT',
            '-j', 'LOG',
            '--log-prefix', 'IPTABLES_OUTPUT_DROPPED: ',
            '--log-level', '4'
        ])

        # Log dropped packets (IPv6)
        self.run_command([
            'ip6tables', '-A', 'INPUT',
            '-j', 'LOG',
            '--log-prefix', 'IP6TABLES_INPUT_DROPPED: ',
            '--log-level', '4'
        ], check=False)

        self.run_command([
            'ip6tables', '-A', 'OUTPUT',
            '-j', 'LOG',
            '--log-prefix', 'IP6TABLES_OUTPUT_DROPPED: ',
            '--log-level', '4'
        ], check=False)

        # Save rules
        try:
            result = self.run_command(['iptables-save'], check=False)
            if result.returncode == 0:
                rules_file = Path('/etc/iptables/rules.v4')
                rules_file.parent.mkdir(parents=True, exist_ok=True)
                with open(rules_file, 'w') as f:
                    f.write(result.stdout)
                self.logger.info(f"Firewall rules saved to {rules_file}")
        except Exception as e:
            self.logger.warning(f"Failed to save firewall rules: {e}")

        return True

    def setup_ebpf(self) -> bool:
        """
        Setup eBPF/XDP for network stability.

        Returns:
            True if successful
        """
        if not self.config.enable_ebpf:
            self.logger.info("eBPF disabled in configuration")
            return True

        self.logger.info("Setting up eBPF/XDP...")

        # Create eBPF program directory
        ebpf_dir = Path('/etc/network_stability/ebpf')
        ebpf_dir.mkdir(parents=True, exist_ok=True)

        # Create eBPF program
        ebpf_program = '''
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/in.h>

#define MAX_PORTS 1024

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_PORTS);
    __type(key, __u16);
    __type(value, __u8);
} allowed_ports SEC(".maps");

SEC("xdp")
int xdp_filter(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    if (eth->h_proto != htons(ETH_P_IP))
        return XDP_PASS;

    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;

    if (ip->protocol != IPPROTO_TCP)
        return XDP_PASS;

    struct tcphdr *tcp = (void *)(ip + 1);
    if ((void *)(tcp + 1) > data_end)
        return XDP_PASS;

    __u16 dest_port = ntohs(tcp->dest);
    __u16 src_port = ntohs(tcp->source);

    // Check if port is allowed
    __u8 *allowed = bpf_map_lookup_elem(&allowed_ports, &dest_port);
    if (!allowed) {
        // Port not in allowed list, drop packet
        return XDP_DROP;
    }

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
'''

        # Write eBPF program
        ebpf_file = ebpf_dir / 'filter.c'
        with open(ebpf_file, 'w') as f:
            f.write(ebpf_program)

        # Compile eBPF program
        self.logger.info("Compiling eBPF program...")
        self.run_command([
            'clang', '-O2', '-target', 'bpf',
            '-c', str(ebpf_file),
            '-o', str(ebpf_dir / 'filter.o')
        ], check=False)

        # Load eBPF program
        self.logger.info("Loading eBPF program...")
        self.run_command([
            'ip', 'link', 'set', 'dev', 'lo', 'xdp', 'obj',
            str(ebpf_dir / 'filter.o'), 'sec', 'xdp'
        ], check=False)

        return True

    def setup_port_forwarding(self) -> bool:
        """
        Setup port forwarding for specific services.

        Returns:
            True if successful
        """
        self.logger.info("Setting up port forwarding...")

        # Enable IP forwarding
        self.run_command(['sysctl', '-w', 'net.ipv4.ip_forward=1'])

        # Setup NAT for outgoing traffic
        # Detect default network interface
        try:
            result = self.run_command(['ip', 'route', 'show', 'default'], check=False)
            if result.returncode == 0 and result.stdout:
                # Parse default interface from route output
                # Example: default via 192.168.1.1 dev eth0 proto dhcp metric 100
                parts = result.stdout.split()
                if 'dev' in parts:
                    iface_idx = parts.index('dev') + 1
                    if iface_idx < len(parts):
                        default_iface = parts[iface_idx]
                        self.logger.info(f"Detected default interface: {default_iface}")
                        self.run_command([
                            'iptables', '-t', 'nat', '-A', 'POSTROUTING',
                            '-o', default_iface,
                            '-j', 'MASQUERADE'
                        ], check=False)
                    else:
                        self.logger.warning("Could not parse default interface from route output")
                else:
                    self.logger.warning("No 'dev' found in route output")
            else:
                self.logger.warning("Failed to detect default interface, skipping NAT setup")
        except Exception as e:
            self.logger.warning(f"Failed to setup NAT: {e}")

        # Port forwarding for specific services
        port_forwards = [
            (8080, 80),    # Forward 8080 to 80
            (8443, 443),   # Forward 8443 to 443
        ]

        for src_port, dst_port in port_forwards:
            self.logger.info(f"Forwarding port {src_port} to {dst_port}...")
            self.run_command([
                'iptables', '-t', 'nat', '-A', 'PREROUTING',
                '-p', 'tcp',
                '--dport', str(src_port),
                '-j', 'REDIRECT',
                '--to-port', str(dst_port)
            ], check=False)

        return True

    def setup_connection_tracking(self) -> bool:
        """
        Setup connection tracking for stability.

        Returns:
            True if successful
        """
        self.logger.info("Setting up connection tracking...")

        # Increase connection tracking limits
        self.run_command([
            'sysctl', '-w',
            'net.netfilter.nf_conntrack_max=1000000'
        ], check=False)

        self.run_command([
            'sysctl', '-w',
            'net.netfilter.nf_conntrack_tcp_timeout_established=86400'
        ], check=False)

        self.run_command([
            'sysctl', '-w',
            'net.netfilter.nf_conntrack_tcp_timeout_time_wait=30'
        ], check=False)

        # Enable SYN cookies
        self.run_command([
            'sysctl', '-w', 'net.ipv4.tcp_syncookies=1'
        ], check=False)

        # Disable ICMP redirects
        self.run_command([
            'sysctl', '-w', 'net.ipv4.conf.all.accept_redirects=0'
        ], check=False)

        self.run_command([
            'sysctl', '-w', 'net.ipv4.conf.default.accept_redirects=0'
        ], check=False)

        # Disable source routing
        self.run_command([
            'sysctl', '-w', 'net.ipv4.conf.all.accept_source_route=0'
        ], check=False)

        self.run_command([
            'sysctl', '-w', 'net.ipv4.conf.default.accept_source_route=0'
        ], check=False)

        # Enable reverse path filtering
        self.run_command([
            'sysctl', '-w', 'net.ipv4.conf.all.rp_filter=1'
        ], check=False)

        self.run_command([
            'sysctl', '-w', 'net.ipv4.conf.default.rp_filter=1'
        ], check=False)

        return True

    def setup_fail2ban(self) -> bool:
        """
        Setup fail2ban for intrusion prevention.

        Returns:
            True if successful
        """
        self.logger.info("Setting up fail2ban...")

        # Create fail2ban configuration
        fail2ban_config = '''
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
port = http,https
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-botsearch]
enabled = true
port = http,https
filter = nginx-botsearch
logpath = /var/log/nginx/access.log
maxretry = 2
'''

        # Write fail2ban configuration
        fail2ban_dir = Path('/etc/fail2ban')
        fail2ban_dir.mkdir(parents=True, exist_ok=True)

        with open(fail2ban_dir / 'jail.local', 'w') as f:
            f.write(fail2ban_config)

        # Restart fail2ban
        self.run_command(['systemctl', 'restart', 'fail2ban'], check=False)
        self.run_command(['systemctl', 'enable', 'fail2ban'], check=False)

        return True

    def setup_ddos_protection(self) -> bool:
        """
        Setup DDoS protection mechanisms.

        Returns:
            True if successful
        """
        self.logger.info("Setting up DDoS protection...")

        # SYN flood protection (IPv4)
        self.run_command([
            'iptables', '-A', 'INPUT',
            '-p', 'tcp',
            '--syn',
            '-m', 'limit',
            '--limit', '1/s',
            '--limit-burst', '3',
            '-j', 'ACCEPT'
        ], check=False)

        # SYN flood protection (IPv6)
        self.run_command([
            'ip6tables', '-A', 'INPUT',
            '-p', 'tcp',
            '--syn',
            '-m', 'limit',
            '--limit', '1/s',
            '--limit-burst', '3',
            '-j', 'ACCEPT'
        ], check=False)

        # Limit concurrent connections (IPv4)
        self.run_command([
            'iptables', '-A', 'INPUT',
            '-p', 'tcp',
            '--dport', '80',
            '-m', 'connlimit',
            '--connlimit-above', '20',
            '-j', 'REJECT'
        ], check=False)

        self.run_command([
            'iptables', '-A', 'INPUT',
            '-p', 'tcp',
            '--dport', '443',
            '-m', 'connlimit',
            '--connlimit-above', '20',
            '-j', 'REJECT'
        ], check=False)

        # Limit concurrent connections (IPv6)
        self.run_command([
            'ip6tables', '-A', 'INPUT',
            '-p', 'tcp',
            '--dport', '80',
            '-m', 'connlimit',
            '--connlimit-above', '20',
            '-j', 'REJECT'
        ], check=False)

        self.run_command([
            'ip6tables', '-A', 'INPUT',
            '-p', 'tcp',
            '--dport', '443',
            '-m', 'connlimit',
            '--connlimit-above', '20',
            '-j', 'REJECT'
        ], check=False)

        # Limit new connections per second (IPv4)
        self.run_command([
            'iptables', '-A', 'INPUT',
            '-p', 'tcp',
            '--dport', '80',
            '-m', 'state',
            '--state', 'NEW',
            '-m', 'limit',
            '--limit', '60/s',
            '--limit-burst', '20',
            '-j', 'ACCEPT'
        ], check=False)

        self.run_command([
            'iptables', '-A', 'INPUT',
            '-p', 'tcp',
            '--dport', '443',
            '-m', 'state',
            '--state', 'NEW',
            '-m', 'limit',
            '--limit', '60/s',
            '--limit-burst', '20',
            '-j', 'ACCEPT'
        ], check=False)

        # Limit new connections per second (IPv6)
        self.run_command([
            'ip6tables', '-A', 'INPUT',
            '-p', 'tcp',
            '--dport', '80',
            '-m', 'state',
            '--state', 'NEW',
            '-m', 'limit',
            '--limit', '60/s',
            '--limit-burst', '20',
            '-j', 'ACCEPT'
        ], check=False)

        self.run_command([
            'ip6tables', '-A', 'INPUT',
            '-p', 'tcp',
            '--dport', '443',
            '-m', 'state',
            '--state', 'NEW',
            '-m', 'limit',
            '--limit', '60/s',
            '--limit-burst', '20',
            '-j', 'ACCEPT'
        ], check=False)

        return True

    def setup_monitoring(self) -> bool:
        """
        Setup network monitoring.

        Returns:
            True if successful
        """
        self.logger.info("Setting up network monitoring...")

        # Create monitoring script
        monitor_script = '''#!/bin/bash
# Network monitoring script

LOG_FILE="/var/log/network_stability/monitor.log"
MAX_LOG_SIZE=10485760  # 10MB

# Rotate log if it exceeds max size
rotate_log() {
    if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null) -gt $MAX_LOG_SIZE ]; then
        mv "$LOG_FILE" "${LOG_FILE}.old"
        echo "Log rotated at $(date)" > "$LOG_FILE"
    fi
}

while true; do
    rotate_log

    echo "=== $(date) ===" >> $LOG_FILE

    # Connection count
    echo "Active connections:" >> $LOG_FILE
    netstat -an | grep ESTABLISHED | wc -l >> $LOG_FILE

    # Port usage
    echo "Port usage:" >> $LOG_FILE
    netstat -tuln >> $LOG_FILE

    # Firewall rules
    echo "Firewall rules:" >> $LOG_FILE
    iptables -L -n -v >> $LOG_FILE

    # System resources
    echo "System resources:" >> $LOG_FILE
    top -bn1 | head -20 >> $LOG_FILE

    sleep 60
done
'''

        # Write monitoring script
        monitor_dir = Path('/usr/local/bin')
        monitor_file = monitor_dir / 'network_monitor.sh'

        with open(monitor_file, 'w') as f:
            f.write(monitor_script)

        # Make executable
        self.run_command(['chmod', '+x', str(monitor_file)])

        # Create systemd service
        service_config = '''[Unit]
Description=Network Stability Monitor
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/network_monitor.sh
Restart=always
User=root

[Install]
WantedBy=multi-user.target
'''

        service_file = Path('/etc/systemd/system/network-monitor.service')
        with open(service_file, 'w') as f:
            f.write(service_config)

        # Enable and start service
        self.run_command(['systemctl', 'daemon-reload'], check=False)
        self.run_command(['systemctl', 'enable', 'network-monitor'], check=False)
        self.run_command(['systemctl', 'start', 'network-monitor'], check=False)

        return True

    def apply_all(self) -> bool:
        """
        Apply all network stability configurations.

        Returns:
            True if successful
        """
        self.logger.info("Applying all network stability configurations...")

        try:
            # Check root
            if not self.check_root():
                self.logger.error("This script must be run as root")
                return False

            # Install packages
            if not self.install_packages():
                self.logger.error("Failed to install packages")
                return False

            # Disable watchers
            if not self.config.enable_watchers:
                if not self.disable_watchers():
                    self.logger.error("Failed to disable watchers")
                    return False

            # Setup firewall
            if self.config.enable_firewall:
                if not self.setup_firewall():
                    self.logger.error("Failed to setup firewall")
                    return False

            # Setup eBPF
            if self.config.enable_ebpf:
                if not self.setup_ebpf():
                    self.logger.error("Failed to setup eBPF")
                    return False

            # Setup port forwarding
            if not self.setup_port_forwarding():
                self.logger.error("Failed to setup port forwarding")
                return False

            # Setup connection tracking
            if not self.setup_connection_tracking():
                self.logger.error("Failed to setup connection tracking")
                return False

            # Setup fail2ban
            if not self.setup_fail2ban():
                self.logger.error("Failed to setup fail2ban")
                return False

            # Setup DDoS protection
            if not self.setup_ddos_protection():
                self.logger.error("Failed to setup DDoS protection")
                return False

            # Setup monitoring
            if not self.setup_monitoring():
                self.logger.error("Failed to setup monitoring")
                return False

            self.logger.info("All network stability configurations applied successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error applying configurations: {e}")
            return False

    def status(self) -> Dict[str, Any]:
        """
        Get current network stability status.

        Returns:
            Status dictionary
        """
        status = {
            'firewall_enabled': self.config.enable_firewall,
            'ebpf_enabled': self.config.enable_ebpf,
            'watchers_enabled': self.config.enable_watchers,
            'strict_mode': self.config.strict_mode,
            'username': self.config.username,
            'allowed_ports': self.config.allowed_ports,
            'denied_ports': self.config.denied_ports,
        }

        # Check iptables rules
        try:
            result = self.run_command(
                ['iptables', '-L', '-n', '--line-numbers'],
                check=False
            )
            status['iptables_rules'] = result.stdout
        except Exception:
            status['iptables_rules'] = 'Unable to retrieve'

        # Check active connections
        try:
            result = self.run_command(
                ['netstat', '-an'],
                check=False
            )
            status['active_connections'] = result.stdout.count('ESTABLISHED')
        except Exception:
            status['active_connections'] = 'Unable to retrieve'

        return status


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Network Stability Kernel Mode Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Apply all configurations
  sudo python3 network_stability_kernel.py --apply-all

  # Setup firewall only
  sudo python3 network_stability_kernel.py --setup-firewall

  # Disable watchers
  sudo python3 network_stability_kernel.py --disable-watchers

  # Check status
  sudo python3 network_stability_kernel.py --status

  # Custom configuration
  sudo python3 network_stability_kernel.py --username webcoder --allowed-ports 22,80,443,8080
        '''
    )

    parser.add_argument(
        '--apply-all',
        action='store_true',
        help='Apply all network stability configurations'
    )

    parser.add_argument(
        '--setup-firewall',
        action='store_true',
        help='Setup firewall with strict rules'
    )

    parser.add_argument(
        '--setup-ebpf',
        action='store_true',
        help='Setup eBPF/XDP for network stability'
    )

    parser.add_argument(
        '--disable-watchers',
        action='store_true',
        help='Disable unnecessary watchers'
    )

    parser.add_argument(
        '--install-packages',
        action='store_true',
        help='Install required packages'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current network stability status'
    )

    parser.add_argument(
        '--username',
        type=str,
        default='webcoder',
        help='Username for webcoding (default: webcoder)'
    )

    parser.add_argument(
        '--allowed-ports',
        type=str,
        help='Comma-separated list of allowed ports'
    )

    parser.add_argument(
        '--denied-ports',
        type=str,
        help='Comma-separated list of denied ports'
    )

    parser.add_argument(
        '--enable-firewall',
        action='store_true',
        default=True,
        help='Enable firewall (default: True)'
    )

    parser.add_argument(
        '--disable-firewall',
        action='store_true',
        help='Disable firewall'
    )

    parser.add_argument(
        '--enable-ebpf',
        action='store_true',
        default=True,
        help='Enable eBPF (default: True)'
    )

    parser.add_argument(
        '--disable-ebpf',
        action='store_true',
        help='Disable eBPF'
    )

    parser.add_argument(
        '--enable-watchers',
        action='store_true',
        help='Enable watchers (default: False)'
    )

    parser.add_argument(
        '--strict-mode',
        action='store_true',
        default=True,
        help='Enable strict mode (default: True)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show commands without executing'
    )

    args = parser.parse_args()

    # Parse ports
    allowed_ports = NetworkStabilityKernel.DEFAULT_ALLOWED_PORTS
    if args.allowed_ports:
        allowed_ports = [int(p.strip()) for p in args.allowed_ports.split(',')]

    denied_ports = NetworkStabilityKernel.DEFAULT_DENIED_PORTS
    if args.denied_ports:
        denied_ports = [int(p.strip()) for p in args.denied_ports.split(',')]

    # Create configuration
    config = SecurityConfig(
        username=args.username,
        allowed_ports=allowed_ports,
        denied_ports=denied_ports,
        enable_firewall=not args.disable_firewall,
        enable_ebpf=not args.disable_ebpf,
        enable_watchers=args.enable_watchers,
        strict_mode=args.strict_mode,
        log_level='DEBUG' if args.verbose else 'INFO'
    )

    # Create kernel manager
    kernel = NetworkStabilityKernel(
        config=config,
        verbose=args.verbose,
        dry_run=args.dry_run
    )

    # Execute requested action
    if args.apply_all:
        success = kernel.apply_all()
        sys.exit(0 if success else 1)

    elif args.setup_firewall:
        success = kernel.setup_firewall()
        sys.exit(0 if success else 1)

    elif args.setup_ebpf:
        success = kernel.setup_ebpf()
        sys.exit(0 if success else 1)

    elif args.disable_watchers:
        success = kernel.disable_watchers()
        sys.exit(0 if success else 1)

    elif args.install_packages:
        success = kernel.install_packages()
        sys.exit(0 if success else 1)

    elif args.status:
        status = kernel.status()
        print(json.dumps(status, indent=2))
        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

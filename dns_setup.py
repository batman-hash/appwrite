#!/usr/bin/env python3
"""
Cloudflare DNS Setup Tool with DoH Client
Supports primary, secondary, tertiary DNS providers and encrypted DNS-over-HTTPS
"""

import os
import subprocess
import sys
import json
import socket
import struct
import requests
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# ============================================================================
# DNS PROVIDER CONFIGURATION
# ============================================================================

DNS_PROVIDERS = {
    "primary": {
        "name": "Cloudflare",
        "ipv4_primary": "1.1.1.1",
        "ipv4_secondary": "1.0.0.1",
        "doh_url": "https://cloudflare-dns.com/dns-query",
        "port": 443,
        "notes": "Fast, privacy-focused"
    },
    "secondary": {
        "name": "Google Public DNS",
        "ipv4_primary": "8.8.8.8",
        "ipv4_secondary": "8.8.4.4",
        "doh_url": "https://dns.google/dns-query",
        "port": 443,
        "notes": "Very reliable, widely supported"
    },
    "tertiary": {
        "name": "Quad9",
        "ipv4_primary": "9.9.9.9",
        "ipv4_secondary": "149.112.112.112",
        "doh_url": "https://dns.quad9.net/dns-query",
        "port": 443,
        "notes": "Security-focused, threat blocking"
    }
}

CLOUDFLARE_MODES = {
    "default": {
        "primary_dns": "1.1.1.1",
        "secondary_dns": "1.0.0.1",
        "doh": "https://cloudflare-dns.com/dns-query",
        "description": "Standard Cloudflare DNS"
    },
    "malware_blocking": {
        "primary_dns": "1.1.1.2",
        "secondary_dns": "1.0.0.2",
        "doh": "https://security.cloudflare-dns.com/dns-query",
        "description": "Malware blocking enabled"
    },
    "malware_and_adult_blocking": {
        "primary_dns": "1.1.1.3",
        "secondary_dns": "1.0.0.3",
        "doh": "https://family.cloudflare-dns.com/dns-query",
        "description": "Malware + adult content blocking"
    }
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def run(cmd: str) -> subprocess.CompletedProcess:
    """Execute shell command and return result"""
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def require_root():
    """Check if script is running with root privileges"""
    if os.geteuid() != 0:
        print("❌ Error: This script requires root privileges")
        print("Please run as root: sudo python3 dns_setup.py")
        sys.exit(1)


def get_active_connection() -> Optional[str]:
    """Get active NetworkManager connection name"""
    result = run("nmcli -t -f NAME,DEVICE connection show --active")
    if result.returncode != 0:
        return None

    for line in result.stdout.strip().split("\n"):
        if ":" in line:
            name, device = line.split(":")
            if device:
                return name
    return None


def get_default_interface() -> Optional[str]:
    """Get default network interface"""
    result = run("ip route | awk '/default/ {print $5; exit}'")
    return result.stdout.strip() if result.returncode == 0 else None


# ============================================================================
# DNS SETUP METHODS
# ============================================================================

def setup_with_resolvectl(primary_dns: str, secondary_dns: str) -> bool:
    """Configure DNS using resolvectl (systemd-resolved)"""
    iface = get_default_interface()
    if not iface:
        return False

    print(f"📡 Using resolvectl on interface: {iface}")
    
    commands = [
        f"resolvectl dns {iface} {primary_dns} {secondary_dns}",
        f"resolvectl domain {iface} '~.'",
        "resolvectl flush-caches || true"
    ]
    
    for cmd in commands:
        result = run(cmd)
        if result.returncode != 0:
            print(f"⚠️  Warning: {cmd} failed")
    
    return True


def setup_with_nmcli(primary_dns: str, secondary_dns: str) -> bool:
    """Configure DNS using NetworkManager (nmcli)"""
    conn = get_active_connection()
    if not conn:
        return False

    print(f"📡 Using NetworkManager connection: {conn}")
    
    commands = [
        f"nmcli connection modify '{conn}' ipv4.ignore-auto-dns yes",
        f"nmcli connection modify '{conn}' ipv4.dns '{primary_dns} {secondary_dns}'",
        f"nmcli connection modify '{conn}' ipv4.method auto",
        f"nmcli connection up '{conn}'"
    ]
    
    for cmd in commands:
        result = run(cmd)
        if result.returncode != 0:
            print(f"⚠️  Warning: {cmd} failed")
    
    return True


def setup_with_resolv_conf(primary_dns: str, secondary_dns: str) -> bool:
    """Configure DNS by editing /etc/resolv.conf directly"""
    print("📡 Falling back to /etc/resolv.conf")
    
    backup = f"/etc/resolv.conf.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        if os.path.exists("/etc/resolv.conf"):
            os.rename("/etc/resolv.conf", backup)
            print(f"💾 Backup saved to {backup}")
    except Exception as e:
        print(f"⚠️  Backup failed: {e}")

    try:
        with open("/etc/resolv.conf", "w") as f:
            f.write(f"# Cloudflare DNS Setup - {datetime.now().isoformat()}\n")
            f.write(f"nameserver {primary_dns}\n")
            f.write(f"nameserver {secondary_dns}\n")
        return True
    except Exception as e:
        print(f"❌ Failed to write /etc/resolv.conf: {e}")
        return False


def setup_dns(primary_dns: str, secondary_dns: str, method: str = "auto") -> bool:
    """
    Setup DNS using specified method or auto-detect
    
    Methods:
    - auto: Try resolvectl → nmcli → resolv.conf
    - resolvectl: Force systemd-resolved
    - nmcli: Force NetworkManager
    - resolvconf: Force direct /etc/resolv.conf edit
    """
    print(f"\n🔧 Setting DNS to {primary_dns} and {secondary_dns}")
    
    if method == "auto" or method == "resolvectl":
        if command_exists("resolvectl"):
            if setup_with_resolvectl(primary_dns, secondary_dns):
                print("✅ Configured via systemd-resolved")
                return True
    
    if method == "auto" or method == "nmcli":
        if command_exists("nmcli"):
            if setup_with_nmcli(primary_dns, secondary_dns):
                print("✅ Configured via NetworkManager")
                return True
    
    if method == "auto" or method == "resolvconf":
        if setup_with_resolv_conf(primary_dns, secondary_dns):
            print("✅ Configured via /etc/resolv.conf")
            return True
    
    return False


def command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH"""
    result = run(f"which {cmd}")
    return result.returncode == 0


# ============================================================================
# DNS VERIFICATION
# ============================================================================

def verify_dns() -> bool:
    """Verify DNS is working correctly"""
    print("\n🔍 Verification:")
    
    # Test basic DNS resolution
    result = run("getent hosts cloudflare.com")
    if result.stdout:
        print(f"✅ DNS resolution working: {result.stdout.strip()}")
        return True
    else:
        print("❌ DNS resolution failed")
        return False


def show_dns_status():
    """Show current DNS configuration status"""
    print("\n📊 Current DNS Status:")
    
    if command_exists("resolvectl"):
        result = run("resolvectl status")
        if result.returncode == 0:
            print(result.stdout[:500])  # Show first 500 chars
    
    # Show /etc/resolv.conf
    try:
        with open("/etc/resolv.conf", "r") as f:
            print("\n📄 /etc/resolv.conf:")
            print(f.read())
    except Exception as e:
        print(f"⚠️  Cannot read /etc/resolv.conf: {e}")


# ============================================================================
# DNS-OVER-HTTPS (DoH) CLIENT
# ============================================================================

class DoHClient:
    """DNS-over-HTTPS client for encrypted DNS queries"""
    
    def __init__(self, doh_url: str = "https://cloudflare-dns.com/dns-query"):
        self.doh_url = doh_url
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/dns-json"
        })
    
    def query(self, domain: str, record_type: str = "A") -> Optional[Dict]:
        """
        Query DNS record using DoH (JSON API)
        
        Supported record types: A, AAAA, MX, NS, TXT, CNAME, SOA, etc.
        """
        params = {
            "name": domain,
            "type": record_type
        }
        
        try:
            response = self.session.get(
                self.doh_url,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ DoH query failed: {e}")
            return None
    
    def resolve(self, domain: str, record_type: str = "A") -> List[str]:
        """Resolve domain and return list of records"""
        result = self.query(domain, record_type)
        
        if not result or "Answer" not in result:
            return []
        
        return [answer["data"] for answer in result["Answer"]]
    
    def resolve_ipv4(self, domain: str) -> List[str]:
        """Resolve domain to IPv4 addresses"""
        return self.resolve(domain, "A")
    
    def resolve_ipv6(self, domain: str) -> List[str]:
        """Resolve domain to IPv6 addresses"""
        return self.resolve(domain, "AAAA")
    
    def get_mx_records(self, domain: str) -> List[str]:
        """Get MX (mail) records for domain"""
        return self.resolve(domain, "MX")
    
    def get_txt_records(self, domain: str) -> List[str]:
        """Get TXT records for domain"""
        return self.resolve(domain, "TXT")


class DoHClientRFC8484:
    """
    DNS-over-HTTPS client using RFC 8484 wire format
    More standards-compliant than JSON API
    """
    
    def __init__(self, doh_url: str = "https://cloudflare-dns.com/dns-query"):
        self.doh_url = doh_url
        self.session = requests.Session()
    
    def _build_dns_query(self, domain: str, record_type: int = 1) -> bytes:
        """
        Build DNS query packet (simplified)
        
        Record types:
        1 = A (IPv4)
        28 = AAAA (IPv6)
        15 = MX
        16 = TXT
        """
        # Transaction ID
        tx_id = b'\x12\x34'
        
        # Flags: standard query
        flags = b'\x01\x00'
        
        # Questions: 1
        questions = b'\x00\x01'
        
        # Answer/Authority/Additional RRs: 0
        answers = b'\x00\x00'
        authority = b'\x00\x00'
        additional = b'\x00\x00'
        
        # Build question section
        qname = b''
        for part in domain.split('.'):
            qname += bytes([len(part)]) + part.encode()
        qname += b'\x00'  # End of domain name
        
        # Query type and class
        qtype = struct.pack('>H', record_type)
        qclass = b'\x00\x01'  # IN (Internet)
        
        return tx_id + flags + questions + answers + authority + additional + qname + qtype + qclass
    
    def query(self, domain: str, record_type: str = "A") -> Optional[bytes]:
        """
        Query DNS using RFC 8484 wire format
        
        Returns raw DNS response bytes
        """
        type_map = {
            "A": 1,
            "AAAA": 28,
            "MX": 15,
            "TXT": 16,
            "NS": 2,
            "CNAME": 5,
            "SOA": 6
        }
        
        type_num = type_map.get(record_type.upper(), 1)
        query_packet = self._build_dns_query(domain, type_num)
        
        try:
            response = self.session.post(
                self.doh_url,
                data=query_packet,
                headers={
                    "Content-Type": "application/dns-message",
                    "Accept": "application/dns-message"
                },
                timeout=10
            )
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            print(f"❌ DoH query failed: {e}")
            return None


# ============================================================================
# DNS LATENCY TESTING
# ============================================================================

def test_dns_latency(dns_ip: str, timeout: int = 2) -> Optional[float]:
    """
    Test latency to DNS server using UDP socket
    
    Returns latency in milliseconds or None if failed
    """
    try:
        # Create DNS query for google.com
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        # Simple DNS query packet
        query = b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00'
        query += b'\x06google\x03com\x00\x00\x01\x00\x01'
        
        start = datetime.now()
        sock.sendto(query, (dns_ip, 53))
        
        try:
            sock.recv(512)
            latency = (datetime.now() - start).total_seconds() * 1000
            return round(latency, 2)
        except socket.timeout:
            return None
    except Exception:
        return None
    finally:
        sock.close()


def find_fastest_dns() -> Tuple[str, str, str]:
    """
    Test all DNS providers and return fastest
    
    Returns: (provider_key, primary_dns, secondary_dns)
    """
    print("\n⏱️  Testing DNS latency...")
    
    results = []
    
    for key, provider in DNS_PROVIDERS.items():
        latency = test_dns_latency(provider["ipv4_primary"])
        if latency:
            results.append((key, provider, latency))
            print(f"  {provider['name']}: {latency}ms")
        else:
            print(f"  {provider['name']}: Timeout ❌")
    
    if not results:
        print("⚠️  All DNS servers timed out, using Cloudflare as default")
        return ("primary", "1.1.1.1", "1.0.0.1")
    
    # Sort by latency
    results.sort(key=lambda x: x[2])
    fastest = results[0]
    
    print(f"\n🏆 Fastest: {fastest[1]['name']} ({fastest[2]}ms)")
    
    return (
        fastest[0],
        fastest[1]["ipv4_primary"],
        fastest[1]["ipv4_secondary"]
    )


# ============================================================================
# MAIN CLI INTERFACE
# ============================================================================

def print_banner():
    """Print tool banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           🌐 Cloudflare DNS Setup Tool 🌐                  ║
║       with DNS-over-HTTPS (DoH) Client Support             ║
╚══════════════════════════════════════════════════════════════╝
    """)


def print_menu():
    """Print main menu"""
    print("""
📋 Available Commands:

  1. setup          - Setup DNS (default: Cloudflare 1.1.1.1)
  2. setup-fastest  - Auto-detect and setup fastest DNS
  3. setup-mode     - Setup Cloudflare with specific mode
  4. doh-query      - Query DNS using DoH (encrypted)
  5. doh-resolve    - Resolve domain using DoH
  6. test-latency   - Test latency to all DNS providers
  7. status         - Show current DNS configuration
  8. verify         - Verify DNS is working
  9. providers      - List all DNS providers
  10. modes         - List Cloudflare modes
  11. help          - Show this help
  12. exit          - Exit program

Environment Variables:
  PRIMARY_DNS       - Custom primary DNS (e.g., 1.1.1.1)
  SECONDARY_DNS     - Custom secondary DNS (e.g., 1.0.0.1)
  DOH_URL           - Custom DoH endpoint URL
  DNS_MODE          - Cloudflare mode (default/malware_blocking/malware_and_adult_blocking)
  DNS_METHOD        - Setup method (auto/resolvectl/nmcli/resolvconf)
    """)


def list_providers():
    """List all available DNS providers"""
    print("\n📡 Available DNS Providers:")
    print("=" * 70)
    
    for key, provider in DNS_PROVIDERS.items():
        print(f"\n🔹 {provider['name']} ({key})")
        print(f"   Primary DNS:   {provider['ipv4_primary']}")
        print(f"   Secondary DNS: {provider['ipv4_secondary']}")
        print(f"   DoH Endpoint:  {provider['doh_url']}")
        print(f"   Notes:         {provider['notes']}")


def list_modes():
    """List all Cloudflare modes"""
    print("\n🛡️  Cloudflare DNS Modes:")
    print("=" * 70)
    
    for mode, config in CLOUDFLARE_MODES.items():
        print(f"\n🔹 {mode}")
        print(f"   Description:    {config['description']}")
        print(f"   Primary DNS:    {config['primary_dns']}")
        print(f"   Secondary DNS:  {config['secondary_dns']}")
        print(f"   DoH Endpoint:   {config['doh']}")


def interactive_setup():
    """Interactive DNS setup"""
    print("\n🔧 Interactive DNS Setup")
    print("=" * 70)
    
    # Get provider choice
    print("\nSelect DNS Provider:")
    for i, (key, provider) in enumerate(DNS_PROVIDERS.items(), 1):
        print(f"  {i}. {provider['name']}")
    
    choice = input("\nEnter choice (1-3) [1]: ").strip() or "1"
    
    try:
        provider_key = list(DNS_PROVIDERS.keys())[int(choice) - 1]
        provider = DNS_PROVIDERS[provider_key]
    except (ValueError, IndexError):
        print("⚠️  Invalid choice, using Cloudflare")
        provider = DNS_PROVIDERS["primary"]
    
    # Get Cloudflare mode if Cloudflare selected
    if provider["name"] == "Cloudflare":
        print("\nSelect Cloudflare Mode:")
        for i, (mode, config) in enumerate(CLOUDFLARE_MODES.items(), 1):
            print(f"  {i}. {mode} - {config['description']}")
        
        mode_choice = input("\nEnter choice (1-3) [1]: ").strip() or "1"
        
        try:
            mode_key = list(CLOUDFLARE_MODES.keys())[int(mode_choice) - 1]
            mode_config = CLOUDFLARE_MODES[mode_key]
            primary_dns = mode_config["primary_dns"]
            secondary_dns = mode_config["secondary_dns"]
        except (ValueError, IndexError):
            primary_dns = provider["ipv4_primary"]
            secondary_dns = provider["ipv4_secondary"]
    else:
        primary_dns = provider["ipv4_primary"]
        secondary_dns = provider["ipv4_secondary"]
    
    # Get setup method
    print("\nSelect Setup Method:")
    print("  1. Auto-detect (recommended)")
    print("  2. systemd-resolved (resolvectl)")
    print("  3. NetworkManager (nmcli)")
    print("  4. Direct /etc/resolv.conf")
    
    method_choice = input("\nEnter choice (1-4) [1]: ").strip() or "1"
    
    method_map = {
        "1": "auto",
        "2": "resolvectl",
        "3": "nmcli",
        "4": "resolvconf"
    }
    
    method = method_map.get(method_choice, "auto")
    
    # Confirm
    print(f"\n📋 Configuration Summary:")
    print(f"   Provider:       {provider['name']}")
    print(f"   Primary DNS:    {primary_dns}")
    print(f"   Secondary DNS:  {secondary_dns}")
    print(f"   Method:         {method}")
    
    confirm = input("\nProceed? (y/N) [y]: ").strip().lower() or "y"
    
    if confirm != "y":
        print("❌ Setup cancelled")
        return
    
    # Setup DNS
    if setup_dns(primary_dns, secondary_dns, method):
        verify_dns()
    else:
        print("❌ DNS setup failed")


def doh_query_interactive():
    """Interactive DoH query"""
    print("\n🔐 DNS-over-HTTPS Query")
    print("=" * 70)
    
    # Select DoH provider
    print("\nSelect DoH Provider:")
    for i, (key, provider) in enumerate(DNS_PROVIDERS.items(), 1):
        print(f"  {i}. {provider['name']}")
    
    choice = input("\nEnter choice (1-3) [1]: ").strip() or "1"
    
    try:
        provider_key = list(DNS_PROVIDERS.keys())[int(choice) - 1]
        doh_url = DNS_PROVIDERS[provider_key]["doh_url"]
    except (ValueError, IndexError):
        doh_url = DNS_PROVIDERS["primary"]["doh_url"]
    
    # Get domain
    domain = input("\nEnter domain to query: ").strip()
    if not domain:
        print("❌ Domain required")
        return
    
    # Get record type
    record_type = input("Enter record type (A/AAAA/MX/TXT/NS) [A]: ").strip().upper() or "A"
    
    # Query
    client = DoHClient(doh_url)
    print(f"\n🔍 Querying {domain} ({record_type}) via {doh_url}...")
    
    result = client.query(domain, record_type)
    
    if result:
        print("\n✅ Response:")
        print(json.dumps(result, indent=2))
    else:
        print("❌ Query failed")


def doh_resolve_interactive():
    """Interactive DoH resolve"""
    print("\n🔐 DNS-over-HTTPS Resolve")
    print("=" * 70)
    
    domain = input("\nEnter domain to resolve: ").strip()
    if not domain:
        print("❌ Domain required")
        return
    
    client = DoHClient()
    
    print(f"\n🔍 Resolving {domain}...")
    
    # IPv4
    ipv4 = client.resolve_ipv4(domain)
    if ipv4:
        print(f"\n📍 IPv4 Addresses:")
        for ip in ipv4:
            print(f"   • {ip}")
    
    # IPv6
    ipv6 = client.resolve_ipv6(domain)
    if ipv6:
        print(f"\n📍 IPv6 Addresses:")
        for ip in ipv6:
            print(f"   • {ip}")
    
    # MX
    mx = client.get_mx_records(domain)
    if mx:
        print(f"\n📧 MX Records:")
        for record in mx:
            print(f"   • {record}")
    
    # TXT
    txt = client.get_txt_records(domain)
    if txt:
        print(f"\n📝 TXT Records:")
        for record in txt:
            print(f"   • {record}")


def test_latency_interactive():
    """Test latency to all DNS providers"""
    print("\n⏱️  DNS Latency Test")
    print("=" * 70)
    
    results = []
    
    for key, provider in DNS_PROVIDERS.items():
        print(f"\nTesting {provider['name']}...")
        latency = test_dns_latency(provider["ipv4_primary"])
        
        if latency:
            results.append((provider["name"], latency))
            print(f"  ✅ {latency}ms")
        else:
            print(f"  ❌ Timeout")
    
    if results:
        print("\n📊 Results Summary:")
        print("-" * 40)
        for name, latency in sorted(results, key=lambda x: x[1]):
            print(f"  {name}: {latency}ms")


def main():
    """Main entry point"""
    print_banner()
    
    # Check for environment variables
    primary_dns = os.environ.get("PRIMARY_DNS", "1.1.1.1")
    secondary_dns = os.environ.get("SECONDARY_DNS", "1.0.0.1")
    doh_url = os.environ.get("DOH_URL", "https://cloudflare-dns.com/dns-query")
    dns_mode = os.environ.get("DNS_MODE", "default")
    dns_method = os.environ.get("DNS_METHOD", "auto")
    
    # Apply Cloudflare mode if specified
    if dns_mode in CLOUDFLARE_MODES:
        mode_config = CLOUDFLARE_MODES[dns_mode]
        primary_dns = mode_config["primary_dns"]
        secondary_dns = mode_config["secondary_dns"]
        doh_url = mode_config["doh"]
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "setup":
            require_root()
            if setup_dns(primary_dns, secondary_dns, dns_method):
                verify_dns()
        
        elif command == "setup-fastest":
            require_root()
            _, fastest_primary, fastest_secondary = find_fastest_dns()
            if setup_dns(fastest_primary, fastest_secondary, dns_method):
                verify_dns()
        
        elif command == "setup-mode":
            require_root()
            if len(sys.argv) > 2:
                mode = sys.argv[2].lower()
                if mode in CLOUDFLARE_MODES:
                    mode_config = CLOUDFLARE_MODES[mode]
                    if setup_dns(mode_config["primary_dns"], mode_config["secondary_dns"], dns_method):
                        verify_dns()
                else:
                    print(f"❌ Unknown mode: {mode}")
                    print(f"Available modes: {', '.join(CLOUDFLARE_MODES.keys())}")
            else:
                print("❌ Please specify mode: default, malware_blocking, malware_and_adult_blocking")
        
        elif command == "doh-query":
            if len(sys.argv) > 2:
                domain = sys.argv[2]
                record_type = sys.argv[3] if len(sys.argv) > 3 else "A"
                client = DoHClient(doh_url)
                result = client.query(domain, record_type)
                if result:
                    print(json.dumps(result, indent=2))
            else:
                print("❌ Usage: dns_setup.py doh-query <domain> [record_type]")
        
        elif command == "doh-resolve":
            if len(sys.argv) > 2:
                domain = sys.argv[2]
                client = DoHClient(doh_url)
                
                ipv4 = client.resolve_ipv4(domain)
                if ipv4:
                    print(f"IPv4: {', '.join(ipv4)}")
                
                ipv6 = client.resolve_ipv6(domain)
                if ipv6:
                    print(f"IPv6: {', '.join(ipv6)}")
            else:
                print("❌ Usage: dns_setup.py doh-resolve <domain>")
        
        elif command == "test-latency":
            test_latency_interactive()
        
        elif command == "status":
            show_dns_status()
        
        elif command == "verify":
            verify_dns()
        
        elif command == "providers":
            list_providers()
        
        elif command == "modes":
            list_modes()
        
        elif command == "help":
            print_menu()
        
        else:
            print(f"❌ Unknown command: {command}")
            print_menu()
    
    else:
        # Interactive mode
        require_root()
        
        while True:
            print_menu()
            choice = input("\nEnter command (or 'exit'): ").strip().lower()
            
            if choice in ["exit", "quit", "q"]:
                print("👋 Goodbye!")
                break
            
            elif choice in ["1", "setup"]:
                if setup_dns(primary_dns, secondary_dns, dns_method):
                    verify_dns()
            
            elif choice in ["2", "setup-fastest"]:
                _, fastest_primary, fastest_secondary = find_fastest_dns()
                if setup_dns(fastest_primary, fastest_secondary, dns_method):
                    verify_dns()
            
            elif choice in ["3", "setup-mode"]:
                interactive_setup()
            
            elif choice in ["4", "doh-query"]:
                doh_query_interactive()
            
            elif choice in ["5", "doh-resolve"]:
                doh_resolve_interactive()
            
            elif choice in ["6", "test-latency"]:
                test_latency_interactive()
            
            elif choice in ["7", "status"]:
                show_dns_status()
            
            elif choice in ["8", "verify"]:
                verify_dns()
            
            elif choice in ["9", "providers"]:
                list_providers()
            
            elif choice in ["10", "modes"]:
                list_modes()
            
            elif choice in ["11", "help"]:
                print_menu()
            
            else:
                print("❌ Invalid choice")
            
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()

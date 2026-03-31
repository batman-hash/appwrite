#!/usr/bin/env python3
"""
Example usage of the DNS Setup Tool
Demonstrates programmatic API usage
"""

from dns_setup import (
    DoHClient,
    setup_dns,
    verify_dns,
    test_dns_latency,
    find_fastest_dns,
    DNS_PROVIDERS,
    CLOUDFLARE_MODES
)
import json


def example_doh_queries():
    """Example: DNS-over-HTTPS queries"""
    print("=" * 70)
    print("🔐 Example: DNS-over-HTTPS Queries")
    print("=" * 70)
    
    # Create DoH client with Cloudflare
    client = DoHClient("https://cloudflare-dns.com/dns-query")
    
    # Query different record types
    domains = ["example.com", "google.com", "github.com"]
    
    for domain in domains:
        print(f"\n🔍 Querying {domain}:")
        
        # IPv4
        ipv4 = client.resolve_ipv4(domain)
        if ipv4:
            print(f"  IPv4: {', '.join(ipv4)}")
        
        # IPv6
        ipv6 = client.resolve_ipv6(domain)
        if ipv6:
            print(f"  IPv6: {', '.join(ipv6)}")
        
        # MX records
        mx = client.get_mx_records(domain)
        if mx:
            print(f"  MX: {', '.join(mx)}")


def example_provider_comparison():
    """Example: Compare different DNS providers"""
    print("\n" + "=" * 70)
    print("📊 Example: DNS Provider Comparison")
    print("=" * 70)
    
    domain = "example.com"
    
    for key, provider in DNS_PROVIDERS.items():
        print(f"\n🔹 {provider['name']}:")
        
        client = DoHClient(provider["doh_url"])
        ipv4 = client.resolve_ipv4(domain)
        
        if ipv4:
            print(f"  Resolved {domain}: {', '.join(ipv4)}")
        else:
            print(f"  Failed to resolve {domain}")


def example_cloudflare_modes():
    """Example: Different Cloudflare modes"""
    print("\n" + "=" * 70)
    print("🛡️  Example: Cloudflare DNS Modes")
    print("=" * 70)
    
    domain = "example.com"
    
    for mode, config in CLOUDFLARE_MODES.items():
        print(f"\n🔹 Mode: {mode}")
        print(f"   Description: {config['description']}")
        print(f"   DNS: {config['primary_dns']} / {config['secondary_dns']}")
        
        client = DoHClient(config["doh"])
        ipv4 = client.resolve_ipv4(domain)
        
        if ipv4:
            print(f"   Resolved: {', '.join(ipv4)}")


def example_latency_testing():
    """Example: Test DNS latency"""
    print("\n" + "=" * 70)
    print("⏱️  Example: DNS Latency Testing")
    print("=" * 70)
    
    print("\nTesting latency to all DNS providers...")
    
    for key, provider in DNS_PROVIDERS.items():
        latency = test_dns_latency(provider["ipv4_primary"])
        
        if latency:
            print(f"  {provider['name']}: {latency}ms")
        else:
            print(f"  {provider['name']}: Timeout")


def example_find_fastest():
    """Example: Find fastest DNS"""
    print("\n" + "=" * 70)
    print("🏆 Example: Find Fastest DNS")
    print("=" * 70)
    
    key, primary, secondary = find_fastest_dns()
    provider = DNS_PROVIDERS[key]
    
    print(f"\nFastest DNS provider: {provider['name']}")
    print(f"Primary: {primary}")
    print(f"Secondary: {secondary}")


def example_custom_doh_client():
    """Example: Custom DoH client usage"""
    print("\n" + "=" * 70)
    print("⚙️  Example: Custom DoH Client")
    print("=" * 70)
    
    # Create client with custom DoH endpoint
    client = DoHClient("https://dns.google/dns-query")
    
    # Query with full response
    result = client.query("example.com", "A")
    
    if result:
        print("\nFull DNS response:")
        print(json.dumps(result, indent=2))


def example_programmatic_setup():
    """Example: Programmatic DNS setup (requires root)"""
    print("\n" + "=" * 70)
    print("🔧 Example: Programmatic DNS Setup")
    print("=" * 70)
    
    print("\n⚠️  This example requires root privileges!")
    print("Uncomment the code below to run:")
    print()
    print("# Setup Cloudflare DNS")
    print('setup_dns("1.1.1.1", "1.0.0.1", method="auto")')
    print()
    print("# Verify DNS is working")
    print("verify_dns()")
    print()
    print("# Setup with malware blocking")
    print('setup_dns("1.1.1.2", "1.0.0.2", method="auto")')
    print()
    print("# Setup with Google DNS")
    print('setup_dns("8.8.8.8", "8.8.4.4", method="auto")')


def main():
    """Run all examples"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         🌐 DNS Setup Tool - Usage Examples 🌐              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Run examples (no root required)
    example_doh_queries()
    example_provider_comparison()
    example_cloudflare_modes()
    example_latency_testing()
    example_custom_doh_client()
    example_programmatic_setup()
    
    print("\n" + "=" * 70)
    print("✅ All examples completed!")
    print("=" * 70)
    
    print("\n💡 To actually setup DNS, run:")
    print("   sudo python3 dns_setup.py setup")
    print()
    print("💡 For interactive mode, run:")
    print("   sudo python3 dns_setup.py")


if __name__ == "__main__":
    main()

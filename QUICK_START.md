# 🚀 Quick Start Guide - Cloudflare DNS Setup Tool

## ⚡ Fastest Setup

```bash
# Make executable
chmod +x dns_setup.py

# Setup Cloudflare DNS (1.1.1.1)
sudo python3 dns_setup.py setup
```

## 📋 Common Commands

### Setup DNS
```bash
# Default Cloudflare (1.1.1.1)
sudo python3 dns_setup.py setup

# Malware blocking (1.1.1.2)
sudo python3 dns_setup.py setup-mode malware_blocking

# Malware + adult content blocking (1.1.1.3)
sudo python3 dns_setup.py setup-mode malware_and_adult_blocking

# Auto-detect fastest DNS
sudo python3 dns_setup.py setup-fastest
```

### DoH Queries (Encrypted DNS)
```bash
# Query A record
python3 dns_setup.py doh-query example.com A

# Query AAAA record (IPv6)
python3 dns_setup.py doh-query example.com AAAA

# Query MX records
python3 dns_setup.py doh-query example.com MX

# Resolve domain (IPv4 + IPv6)
python3 dns_setup.py doh-resolve example.com
```

### Information
```bash
# Show current DNS status
python3 dns_setup.py status

# Verify DNS is working
python3 dns_setup.py verify

# List all DNS providers
python3 dns_setup.py providers

# List Cloudflare modes
python3 dns_setup.py modes

# Test latency to all providers
python3 dns_setup.py test-latency
```

## 🔧 Environment Variables

```bash
# Custom DNS servers
sudo PRIMARY_DNS=1.1.1.2 SECONDARY_DNS=1.0.0.2 python3 dns_setup.py setup

# Custom DoH endpoint
DOH_URL=https://dns.google/dns-query python3 dns_setup.py doh-query example.com

# Force setup method
sudo DNS_METHOD=nmcli python3 dns_setup.py setup
```

## 📊 DNS Providers

| Provider | Primary | Secondary | DoH Endpoint |
|----------|---------|-----------|--------------|
| Cloudflare | 1.1.1.1 | 1.0.0.1 | https://cloudflare-dns.com/dns-query |
| Google | 8.8.8.8 | 8.8.4.4 | https://dns.google/dns-query |
| Quad9 | 9.9.9.9 | 149.112.112.112 | https://dns.quad9.net/dns-query |

## 🛡️ Cloudflare Modes

| Mode | DNS | Description |
|------|-----|-------------|
| default | 1.1.1.1 / 1.0.0.1 | Standard DNS |
| malware_blocking | 1.1.1.2 / 1.0.0.2 | Blocks malware |
| malware_and_adult_blocking | 1.1.1.3 / 1.0.0.3 | Blocks malware + adult content |

## 🐍 Python API

```python
from dns_setup import DoHClient, setup_dns

# Setup DNS programmatically
setup_dns("1.1.1.1", "1.0.0.1", method="auto")

# Use DoH client
client = DoHClient("https://cloudflare-dns.com/dns-query")
ipv4 = client.resolve_ipv4("example.com")
print(f"IPv4: {ipv4}")
```

## 📚 Full Documentation

See [README_DNS_SETUP.md](README_DNS_SETUP.md) for complete documentation.

## 🧪 Examples

Run the example script:
```bash
python3 example_usage.py
```

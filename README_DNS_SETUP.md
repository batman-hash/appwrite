# 🌐 Cloudflare DNS Setup Tool with DoH Client

A comprehensive Python tool for configuring system DNS to use Cloudflare (1.1.1.1) with support for DNS-over-HTTPS (DoH) encrypted queries.

## ✨ Features

- **Multiple DNS Providers**: Cloudflare, Google Public DNS, Quad9
- **Cloudflare Modes**: Standard, Malware Blocking, Malware + Adult Content Blocking
- **Setup Methods**: systemd-resolved, NetworkManager, direct /etc/resolv.conf
- **DoH Client**: DNS-over-HTTPS queries (JSON API & RFC 8484)
- **Latency Testing**: Auto-detect fastest DNS server
- **Interactive CLI**: User-friendly menu interface
- **Environment Variables**: Customizable configuration

## 📋 DNS Providers

| Provider | Primary DNS | Secondary DNS | DoH Endpoint |
|----------|-------------|---------------|--------------|
| **Cloudflare** | 1.1.1.1 | 1.0.0.1 | https://cloudflare-dns.com/dns-query |
| **Google** | 8.8.8.8 | 8.8.4.4 | https://dns.google/dns-query |
| **Quad9** | 9.9.9.9 | 149.112.112.112 | https://dns.quad9.net/dns-query |

## 🛡️ Cloudflare Modes

| Mode | Primary | Secondary | Description |
|------|---------|-----------|-------------|
| **default** | 1.1.1.1 | 1.0.0.1 | Standard Cloudflare DNS |
| **malware_blocking** | 1.1.1.2 | 1.0.0.2 | Blocks malware domains |
| **malware_and_adult_blocking** | 1.1.1.3 | 1.0.0.3 | Blocks malware + adult content |

## 🚀 Quick Start

### Basic Setup (Cloudflare 1.1.1.1)

```bash
# Make executable
chmod +x dns_setup.py

# Run with sudo
sudo python3 dns_setup.py setup
```

### Setup with Malware Blocking

```bash
sudo python3 dns_setup.py setup-mode malware_blocking
```

### Auto-detect Fastest DNS

```bash
sudo python3 dns_setup.py setup-fastest
```

### Interactive Mode

```bash
sudo python3 dns_setup.py
```

## 📖 Usage Examples

### Command Line Interface

```bash
# Setup DNS (default: Cloudflare 1.1.1.1)
sudo python3 dns_setup.py setup

# Setup with specific mode
sudo python3 dns_setup.py setup-mode default
sudo python3 dns_setup.py setup-mode malware_blocking
sudo python3 dns_setup.py setup-mode malware_and_adult_blocking

# Auto-detect fastest DNS
sudo python3 dns_setup.py setup-fastest

# Query DNS using DoH
python3 dns_setup.py doh-query example.com A
python3 dns_setup.py doh-query example.com AAAA
python3 dns_setup.py doh-query example.com MX

# Resolve domain using DoH
python3 dns_setup.py doh-resolve example.com

# Test latency to all DNS providers
python3 dns_setup.py test-latency

# Show current DNS status
python3 dns_setup.py status

# Verify DNS is working
python3 dns_setup.py verify

# List all providers
python3 dns_setup.py providers

# List Cloudflare modes
python3 dns_setup.py modes
```

### Environment Variables

```bash
# Custom primary/secondary DNS
sudo PRIMARY_DNS=1.1.1.2 SECONDARY_DNS=1.0.0.2 python3 dns_setup.py setup

# Custom DoH endpoint
DOH_URL=https://dns.google/dns-query python3 dns_setup.py doh-query example.com

# Use specific Cloudflare mode
sudo DNS_MODE=malware_blocking python3 dns_setup.py setup

# Force specific setup method
sudo DNS_METHOD=nmcli python3 dns_setup.py setup
```

### Python API Usage

```python
from dns_setup import DoHClient, setup_dns, DNS_PROVIDERS, CLOUDFLARE_MODES

# Setup DNS programmatically
setup_dns("1.1.1.1", "1.0.0.1", method="auto")

# Use DoH client
client = DoHClient("https://cloudflare-dns.com/dns-query")

# Resolve IPv4
ipv4 = client.resolve_ipv4("example.com")
print(f"IPv4: {ipv4}")

# Resolve IPv6
ipv6 = client.resolve_ipv6("example.com")
print(f"IPv6: {ipv6}")

# Get MX records
mx = client.get_mx_records("example.com")
print(f"MX: {mx}")

# Get TXT records
txt = client.get_txt_records("example.com")
print(f"TXT: {txt}")

# Custom query
result = client.query("example.com", "A")
print(result)

# Use different provider
google_doh = DoHClient(DNS_PROVIDERS["secondary"]["doh_url"])
result = google_doh.resolve_ipv4("example.com")

# Use Cloudflare malware blocking mode
mode_config = CLOUDFLARE_MODES["malware_blocking"]
client = DoHClient(mode_config["doh"])
result = client.resolve_ipv4("example.com")
```

## 🔧 Setup Methods

The tool automatically detects and uses the best available method:

1. **systemd-resolved** (resolvectl) - Modern Linux systems
2. **NetworkManager** (nmcli) - Desktop Linux systems
3. **/etc/resolv.conf** - Direct file edit (fallback)

### Force Specific Method

```bash
sudo DNS_METHOD=resolvectl python3 dns_setup.py setup
sudo DNS_METHOD=nmcli python3 dns_setup.py setup
sudo DNS_METHOD=resolvconf python3 dns_setup.py setup
```

## 🔐 DNS-over-HTTPS (DoH)

### JSON API (Default)

```python
from dns_setup import DoHClient

client = DoHClient("https://cloudflare-dns.com/dns-query")

# Query any record type
result = client.query("example.com", "A")
result = client.query("example.com", "AAAA")
result = client.query("example.com", "MX")
result = client.query("example.com", "TXT")
result = client.query("example.com", "NS")
```

### RFC 8484 Wire Format

```python
from dns_setup import DoHClientRFC8484

client = DoHClientRFC8484("https://cloudflare-dns.com/dns-query")
response = client.query("example.com", "A")
```

## ⏱️ Latency Testing

Test latency to all DNS providers:

```bash
python3 dns_setup.py test-latency
```

Example output:
```
⏱️  DNS Latency Test
======================================================================

Testing Cloudflare...
  ✅ 12.34ms

Testing Google Public DNS...
  ✅ 23.45ms

Testing Quad9...
  ✅ 34.56ms

📊 Results Summary:
----------------------------------------
  Cloudflare: 12.34ms
  Google Public DNS: 23.45ms
  Quad9: 34.56ms
```

## 📊 Status and Verification

### Show Current DNS Status

```bash
sudo python3 dns_setup.py status
```

### Verify DNS is Working

```bash
sudo python3 dns_setup.py verify
```

## 🎯 Use Cases

### Gaming
```bash
# Use fastest DNS
sudo python3 dns_setup.py setup-fastest
```

### Privacy
```bash
# Use Cloudflare with DoH
sudo python3 dns_setup.py setup
python3 dns_setup.py doh-query example.com
```

### Security
```bash
# Use Quad9 (threat blocking)
sudo PRIMARY_DNS=9.9.9.9 SECONDARY_DNS=149.112.112.112 python3 dns_setup.py setup

# Or Cloudflare malware blocking
sudo python3 dns_setup.py setup-mode malware_blocking
```

### Family Safety
```bash
# Block malware + adult content
sudo python3 dns_setup.py setup-mode malware_and_adult_blocking
```

## ⚠️ Important Notes

1. **Root Required**: DNS setup requires root privileges
2. **Backup**: The tool automatically backs up `/etc/resolv.conf` before editing
3. **NetworkManager**: May override `/etc/resolv.conf` - use nmcli method to prevent this
4. **systemd-resolved**: Modern systems use this instead of direct `/etc/resolv.conf`
5. **DoH Port**: Uses HTTPS port 443 (not DNS port 53)

## 🔄 Failover Support

The tool supports automatic failover through multiple DNS servers:

```python
# Primary: 1.1.1.1
# Secondary: 1.0.0.1
# System will automatically use secondary if primary fails
```

## 📦 Requirements

- Python 3.6+
- `requests` library (for DoH client)
- Root privileges (for DNS setup)

### Install Dependencies

```bash
pip install requests
```

## 🐛 Troubleshooting

### DNS Not Working After Setup

```bash
# Check status
sudo python3 dns_setup.py status

# Verify DNS
sudo python3 dns_setup.py verify

# Flush DNS cache
sudo resolvectl flush-caches
```

### NetworkManager Overrides Settings

```bash
# Use nmcli method
sudo DNS_METHOD=nmcli python3 dns_setup.py setup
```

### Permission Denied

```bash
# Run with sudo
sudo python3 dns_setup.py setup
```

## 📝 License

This tool is provided as-is for educational and utility purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📚 References

- [Cloudflare DNS Documentation](https://developers.cloudflare.com/1.1.1.1/)
- [DNS-over-HTTPS RFC 8484](https://tools.ietf.org/html/rfc8484)
- [Google Public DNS](https://developers.google.com/speed/public-dns)
- [Quad9 DNS](https://www.quad9.net/)

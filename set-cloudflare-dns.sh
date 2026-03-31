#!/usr/bin/env bash
#
# Cloudflare DNS Setup Script with DoH Support
# Supports primary, secondary, tertiary DNS providers and encrypted DNS-over-HTTPS
#
# Usage:
#   sudo ./set-cloudflare-dns.sh [command] [options]
#
# Commands:
#   setup           - Setup DNS (default: Cloudflare 1.1.1.1)
#   setup-fastest   - Auto-detect and setup fastest DNS
#   setup-mode      - Setup Cloudflare with specific mode
#   doh-query       - Query DNS using DoH (encrypted)
#   doh-resolve     - Resolve domain using DoH
#   test-latency    - Test latency to all DNS providers
#   status          - Show current DNS configuration
#   verify          - Verify DNS is working
#   providers       - List all DNS providers
#   modes           - List Cloudflare modes
#   help            - Show this help
#
# Environment Variables:
#   PRIMARY_DNS       - Custom primary DNS (e.g., 1.1.1.1)
#   SECONDARY_DNS     - Custom secondary DNS (e.g., 1.0.0.1)
#   DOH_URL           - Custom DoH endpoint URL
#   DNS_MODE          - Cloudflare mode (default/malware_blocking/malware_and_adult_blocking)
#   DNS_METHOD        - Setup method (auto/resolvectl/nmcli/resolvconf)
#

set -euo pipefail

# ============================================================================
# DNS PROVIDER CONFIGURATION
# ============================================================================

# Primary DNS Providers
declare -A DNS_PROVIDERS=(
    ["cloudflare_name"]="Cloudflare"
    ["cloudflare_primary"]="1.1.1.1"
    ["cloudflare_secondary"]="1.0.0.1"
    ["cloudflare_doh"]="https://cloudflare-dns.com/dns-query"
    ["cloudflare_notes"]="Fast, privacy-focused"
    
    ["google_name"]="Google Public DNS"
    ["google_primary"]="8.8.8.8"
    ["google_secondary"]="8.8.4.4"
    ["google_doh"]="https://dns.google/dns-query"
    ["google_notes"]="Very reliable, widely supported"
    
    ["quad9_name"]="Quad9"
    ["quad9_primary"]="9.9.9.9"
    ["quad9_secondary"]="149.112.112.112"
    ["quad9_doh"]="https://dns.quad9.net/dns-query"
    ["quad9_notes"]="Security-focused, threat blocking"
)

# Cloudflare Modes
declare -A CLOUDFLARE_MODES=(
    ["default_primary"]="1.1.1.1"
    ["default_secondary"]="1.0.0.1"
    ["default_doh"]="https://cloudflare-dns.com/dns-query"
    ["default_description"]="Standard Cloudflare DNS"
    
    ["malware_blocking_primary"]="1.1.1.2"
    ["malware_blocking_secondary"]="1.0.0.2"
    ["malware_blocking_doh"]="https://security.cloudflare-dns.com/dns-query"
    ["malware_blocking_description"]="Malware blocking enabled"
    
    ["malware_and_adult_blocking_primary"]="1.1.1.3"
    ["malware_and_adult_blocking_secondary"]="1.0.0.3"
    ["malware_and_adult_blocking_doh"]="https://family.cloudflare-dns.com/dns-query"
    ["malware_and_adult_blocking_description"]="Malware + adult content blocking"
)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

print_banner() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║           🌐 Cloudflare DNS Setup Tool 🌐                  ║
║       with DNS-over-HTTPS (DoH) Client Support             ║
╚══════════════════════════════════════════════════════════════╝
EOF
}

print_menu() {
    cat << 'EOF'

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
EOF
}

require_root() {
    if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
        echo "❌ Error: This script requires root privileges"
        echo "Please run as root: sudo $0"
        exit 1
    fi
}

get_default_interface() {
    ip route | awk '/default/ {print $5; exit}'
}

get_active_connection() {
    nmcli -t -f NAME,DEVICE connection show --active | awk -F: '$2 != "" {print $1; exit}'
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============================================================================
# DNS SETUP METHODS
# ============================================================================

setup_with_resolvectl() {
    local primary_dns="$1"
    local secondary_dns="$2"
    local iface
    iface="$(get_default_interface || true)"
    
    if [[ -z "${iface:-}" ]]; then
        return 1
    fi
    
    echo "📡 Using resolvectl on interface: $iface"
    
    resolvectl dns "$iface" "$primary_dns" "$secondary_dns" || true
    resolvectl domain "$iface" "~." || true
    resolvectl flush-caches || true
    
    return 0
}

setup_with_nmcli() {
    local primary_dns="$1"
    local secondary_dns="$2"
    local conn
    conn="$(get_active_connection)"
    
    if [[ -z "${conn:-}" ]]; then
        return 1
    fi
    
    echo "📡 Using NetworkManager connection: $conn"
    
    nmcli connection modify "$conn" ipv4.ignore-auto-dns yes || true
    nmcli connection modify "$conn" ipv4.dns "$primary_dns $secondary_dns" || true
    nmcli connection modify "$conn" ipv4.method auto || true
    nmcli connection up "$conn" || true
    
    return 0
}

setup_with_resolv_conf() {
    local primary_dns="$1"
    local secondary_dns="$2"
    local backup="/etc/resolv.conf.backup.$(date +%Y%m%d%H%M%S)"
    
    echo "📡 Falling back to /etc/resolv.conf"
    
    if [[ -f "/etc/resolv.conf" ]]; then
        cp /etc/resolv.conf "$backup" 2>/dev/null || true
        echo "💾 Backup saved to $backup"
    fi
    
    cat > /etc/resolv.conf << EOF
# Cloudflare DNS Setup - $(date -Iseconds)
nameserver $primary_dns
nameserver $secondary_dns
EOF
    
    return 0
}

setup_dns() {
    local primary_dns="${1:-1.1.1.1}"
    local secondary_dns="${2:-1.0.0.1}"
    local method="${3:-auto}"
    
    echo ""
    echo "🔧 Setting DNS to $primary_dns and $secondary_dns"
    
    if [[ "$method" == "auto" || "$method" == "resolvectl" ]]; then
        if command_exists resolvectl; then
            if setup_with_resolvectl "$primary_dns" "$secondary_dns"; then
                echo "✅ Configured via systemd-resolved"
                return 0
            fi
        fi
    fi
    
    if [[ "$method" == "auto" || "$method" == "nmcli" ]]; then
        if command_exists nmcli; then
            if setup_with_nmcli "$primary_dns" "$secondary_dns"; then
                echo "✅ Configured via NetworkManager"
                return 0
            fi
        fi
    fi
    
    if [[ "$method" == "auto" || "$method" == "resolvconf" ]]; then
        if setup_with_resolv_conf "$primary_dns" "$secondary_dns"; then
            echo "✅ Configured via /etc/resolv.conf"
            return 0
        fi
    fi
    
    return 1
}

# ============================================================================
# DNS VERIFICATION
# ============================================================================

verify_dns() {
    echo ""
    echo "🔍 Verification:"
    
    local result
    result="$(getent hosts cloudflare.com 2>/dev/null || true)"
    
    if [[ -n "$result" ]]; then
        echo "✅ DNS resolution working: $result"
        return 0
    else
        echo "❌ DNS resolution failed"
        return 1
    fi
}

show_dns_status() {
    echo ""
    echo "📊 Current DNS Status:"
    
    if command_exists resolvectl; then
        echo ""
        resolvectl status 2>/dev/null | head -50 || true
    fi
    
    echo ""
    echo "📄 /etc/resolv.conf:"
    if [[ -f "/etc/resolv.conf" ]]; then
        cat /etc/resolv.conf
    else
        echo "⚠️  Cannot read /etc/resolv.conf"
    fi
}

# ============================================================================
# DNS-OVER-HTTPS (DoH) CLIENT
# ============================================================================

doh_query() {
    local doh_url="${1:-https://cloudflare-dns.com/dns-query}"
    local domain="$2"
    local record_type="${3:-A}"
    
    if [[ -z "$domain" ]]; then
        echo "❌ Domain required"
        return 1
    fi
    
    echo "🔍 Querying $domain ($record_type) via $doh_url..."
    
    local response
    response="$(curl -s -H "Accept: application/dns-json" \
        "${doh_url}?name=${domain}&type=${record_type}" 2>/dev/null || true)"
    
    if [[ -n "$response" ]]; then
        echo ""
        echo "✅ Response:"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        return 0
    else
        echo "❌ Query failed"
        return 1
    fi
}

doh_resolve() {
    local domain="$1"
    local doh_url="${2:-https://cloudflare-dns.com/dns-query}"
    
    if [[ -z "$domain" ]]; then
        echo "❌ Domain required"
        return 1
    fi
    
    echo "🔍 Resolving $domain..."
    
    # IPv4
    local ipv4
    ipv4="$(curl -s -H "Accept: application/dns-json" \
        "${doh_url}?name=${domain}&type=A" 2>/dev/null | \
        python3 -c "import sys, json; data=json.load(sys.stdin); print('\n'.join([a['data'] for a in data.get('Answer', [])]))" 2>/dev/null || true)"
    
    if [[ -n "$ipv4" ]]; then
        echo ""
        echo "📍 IPv4 Addresses:"
        echo "$ipv4" | while read -r ip; do
            echo "   • $ip"
        done
    fi
    
    # IPv6
    local ipv6
    ipv6="$(curl -s -H "Accept: application/dns-json" \
        "${doh_url}?name=${domain}&type=AAAA" 2>/dev/null | \
        python3 -c "import sys, json; data=json.load(sys.stdin); print('\n'.join([a['data'] for a in data.get('Answer', [])]))" 2>/dev/null || true)"
    
    if [[ -n "$ipv6" ]]; then
        echo ""
        echo "📍 IPv6 Addresses:"
        echo "$ipv6" | while read -r ip; do
            echo "   • $ip"
        done
    fi
    
    # MX
    local mx
    mx="$(curl -s -H "Accept: application/dns-json" \
        "${doh_url}?name=${domain}&type=MX" 2>/dev/null | \
        python3 -c "import sys, json; data=json.load(sys.stdin); print('\n'.join([a['data'] for a in data.get('Answer', [])]))" 2>/dev/null || true)"
    
    if [[ -n "$mx" ]]; then
        echo ""
        echo "📧 MX Records:"
        echo "$mx" | while read -r record; do
            echo "   • $record"
        done
    fi
    
    # TXT
    local txt
    txt="$(curl -s -H "Accept: application/dns-json" \
        "${doh_url}?name=${domain}&type=TXT" 2>/dev/null | \
        python3 -c "import sys, json; data=json.load(sys.stdin); print('\n'.join([a['data'] for a in data.get('Answer', [])]))" 2>/dev/null || true)"
    
    if [[ -n "$txt" ]]; then
        echo ""
        echo "📝 TXT Records:"
        echo "$txt" | while read -r record; do
            echo "   • $record"
        done
    fi
}

# ============================================================================
# DNS LATENCY TESTING
# ============================================================================

test_dns_latency() {
    local dns_ip="$1"
    local timeout="${2:-2}"
    
    # Create DNS query for google.com
    local query
    query="$(printf '\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01')"
    
    local start_time
    start_time="$(date +%s%N)"
    
    # Send UDP query and measure response time
    if echo "$query" | timeout "$timeout" nc -u -w1 "$dns_ip" 53 >/dev/null 2>&1; then
        local end_time
        end_time="$(date +%s%N)"
        local latency_ms
        latency_ms="$(echo "scale=2; ($end_time - $start_time) / 1000000" | bc 2>/dev/null || echo "0")"
        echo "$latency_ms"
        return 0
    else
        return 1
    fi
}

find_fastest_dns() {
    echo ""
    echo "⏱️  Testing DNS latency..."
    
    local fastest_provider=""
    local fastest_primary=""
    local fastest_secondary=""
    local fastest_latency=999999
    
    for provider in cloudflare google quad9; do
        local name="${DNS_PROVIDERS[${provider}_name]}"
        local primary="${DNS_PROVIDERS[${provider}_primary]}"
        local secondary="${DNS_PROVIDERS[${provider}_secondary]}"
        
        echo "  Testing $name..."
        
        local latency
        latency="$(test_dns_latency "$primary" 2 || true)"
        
        if [[ -n "$latency" ]]; then
            echo "    ✅ ${latency}ms"
            
            # Compare latency (using bc for float comparison)
            if echo "$latency < $fastest_latency" | bc -l 2>/dev/null | grep -q "1"; then
                fastest_latency="$latency"
                fastest_provider="$provider"
                fastest_primary="$primary"
                fastest_secondary="$secondary"
            fi
        else
            echo "    ❌ Timeout"
        fi
    done
    
    if [[ -z "$fastest_provider" ]]; then
        echo "⚠️  All DNS servers timed out, using Cloudflare as default"
        echo "cloudflare 1.1.1.1 1.0.0.1"
        return 0
    fi
    
    local fastest_name="${DNS_PROVIDERS[${fastest_provider}_name]}"
    echo ""
    echo "🏆 Fastest: $fastest_name (${fastest_latency}ms)"
    echo "$fastest_provider $fastest_primary $fastest_secondary"
}

test_latency_interactive() {
    echo ""
    echo "⏱️  DNS Latency Test"
    echo "======================================================================"
    
    for provider in cloudflare google quad9; do
        local name="${DNS_PROVIDERS[${provider}_name]}"
        local primary="${DNS_PROVIDERS[${provider}_primary]}"
        
        echo ""
        echo "Testing $name..."
        
        local latency
        latency="$(test_dns_latency "$primary" 2 || true)"
        
        if [[ -n "$latency" ]]; then
            echo "  ✅ ${latency}ms"
        else
            echo "  ❌ Timeout"
        fi
    done
}

# ============================================================================
# LIST FUNCTIONS
# ============================================================================

list_providers() {
    echo ""
    echo "📡 Available DNS Providers:"
    echo "======================================================================"
    
    for provider in cloudflare google quad9; do
        local name="${DNS_PROVIDERS[${provider}_name]}"
        local primary="${DNS_PROVIDERS[${provider}_primary]}"
        local secondary="${DNS_PROVIDERS[${provider}_secondary]}"
        local doh="${DNS_PROVIDERS[${provider}_doh]}"
        local notes="${DNS_PROVIDERS[${provider}_notes]}"
        
        echo ""
        echo "🔹 $name ($provider)"
        echo "   Primary DNS:   $primary"
        echo "   Secondary DNS: $secondary"
        echo "   DoH Endpoint:  $doh"
        echo "   Notes:         $notes"
    done
}

list_modes() {
    echo ""
    echo "🛡️  Cloudflare DNS Modes:"
    echo "======================================================================"
    
    for mode in default malware_blocking malware_and_adult_blocking; do
        local primary="${CLOUDFLARE_MODES[${mode}_primary]}"
        local secondary="${CLOUDFLARE_MODES[${mode}_secondary]}"
        local doh="${CLOUDFLARE_MODES[${mode}_doh]}"
        local description="${CLOUDFLARE_MODES[${mode}_description]}"
        
        echo ""
        echo "🔹 $mode"
        echo "   Description:    $description"
        echo "   Primary DNS:    $primary"
        echo "   Secondary DNS:  $secondary"
        echo "   DoH Endpoint:   $doh"
    done
}

# ============================================================================
# INTERACTIVE SETUP
# ============================================================================

interactive_setup() {
    echo ""
    echo "🔧 Interactive DNS Setup"
    echo "======================================================================"
    
    # Get provider choice
    echo ""
    echo "Select DNS Provider:"
    echo "  1. Cloudflare"
    echo "  2. Google Public DNS"
    echo "  3. Quad9"
    
    read -rp "Enter choice (1-3) [1]: " provider_choice
    provider_choice="${provider_choice:-1}"
    
    case "$provider_choice" in
        1) provider="cloudflare" ;;
        2) provider="google" ;;
        3) provider="quad9" ;;
        *) echo "⚠️  Invalid choice, using Cloudflare"; provider="cloudflare" ;;
    esac
    
    local primary_dns="${DNS_PROVIDERS[${provider}_primary]}"
    local secondary_dns="${DNS_PROVIDERS[${provider}_secondary]}"
    
    # Get Cloudflare mode if Cloudflare selected
    if [[ "$provider" == "cloudflare" ]]; then
        echo ""
        echo "Select Cloudflare Mode:"
        echo "  1. default - Standard Cloudflare DNS"
        echo "  2. malware_blocking - Malware blocking enabled"
        echo "  3. malware_and_adult_blocking - Malware + adult content blocking"
        
        read -rp "Enter choice (1-3) [1]: " mode_choice
        mode_choice="${mode_choice:-1}"
        
        case "$mode_choice" in
            1) mode="default" ;;
            2) mode="malware_blocking" ;;
            3) mode="malware_and_adult_blocking" ;;
            *) echo "⚠️  Invalid choice, using default"; mode="default" ;;
        esac
        
        primary_dns="${CLOUDFLARE_MODES[${mode}_primary]}"
        secondary_dns="${CLOUDFLARE_MODES[${mode}_secondary]}"
    fi
    
    # Get setup method
    echo ""
    echo "Select Setup Method:"
    echo "  1. Auto-detect (recommended)"
    echo "  2. systemd-resolved (resolvectl)"
    echo "  3. NetworkManager (nmcli)"
    echo "  4. Direct /etc/resolv.conf"
    
    read -rp "Enter choice (1-4) [1]: " method_choice
    method_choice="${method_choice:-1}"
    
    case "$method_choice" in
        1) method="auto" ;;
        2) method="resolvectl" ;;
        3) method="nmcli" ;;
        4) method="resolvconf" ;;
        *) echo "⚠️  Invalid choice, using auto"; method="auto" ;;
    esac
    
    # Confirm
    echo ""
    echo "📋 Configuration Summary:"
    echo "   Provider:       ${DNS_PROVIDERS[${provider}_name]}"
    echo "   Primary DNS:    $primary_dns"
    echo "   Secondary DNS:  $secondary_dns"
    echo "   Method:         $method"
    
    read -rp "Proceed? (y/N) [y]: " confirm
    confirm="${confirm:-y}"
    
    if [[ "$confirm" != "y" ]]; then
        echo "❌ Setup cancelled"
        return 1
    fi
    
    # Setup DNS
    if setup_dns "$primary_dns" "$secondary_dns" "$method"; then
        verify_dns
        return 0
    else
        echo "❌ DNS setup failed"
        return 1
    fi
}

doh_query_interactive() {
    echo ""
    echo "🔐 DNS-over-HTTPS Query"
    echo "======================================================================"
    
    # Select DoH provider
    echo ""
    echo "Select DoH Provider:"
    echo "  1. Cloudflare"
    echo "  2. Google Public DNS"
    echo "  3. Quad9"
    
    read -rp "Enter choice (1-3) [1]: " provider_choice
    provider_choice="${provider_choice:-1}"
    
    local doh_url
    case "$provider_choice" in
        1) doh_url="${DNS_PROVIDERS[cloudflare_doh]}" ;;
        2) doh_url="${DNS_PROVIDERS[google_doh]}" ;;
        3) doh_url="${DNS_PROVIDERS[quad9_doh]}" ;;
        *) doh_url="${DNS_PROVIDERS[cloudflare_doh]}" ;;
    esac
    
    # Get domain
    read -rp "Enter domain to query: " domain
    if [[ -z "$domain" ]]; then
        echo "❌ Domain required"
        return 1
    fi
    
    # Get record type
    read -rp "Enter record type (A/AAAA/MX/TXT/NS) [A]: " record_type
    record_type="${record_type:-A}"
    
    # Query
    doh_query "$doh_url" "$domain" "$record_type"
}

doh_resolve_interactive() {
    echo ""
    echo "🔐 DNS-over-HTTPS Resolve"
    echo "======================================================================"
    
    read -rp "Enter domain to resolve: " domain
    if [[ -z "$domain" ]]; then
        echo "❌ Domain required"
        return 1
    fi
    
    doh_resolve "$domain"
}

# ============================================================================
# MAIN CLI INTERFACE
# ============================================================================

main() {
    print_banner
    
    # Check for environment variables
    local primary_dns="${PRIMARY_DNS:-1.1.1.1}"
    local secondary_dns="${SECONDARY_DNS:-1.0.0.1}"
    local doh_url="${DOH_URL:-https://cloudflare-dns.com/dns-query}"
    local dns_mode="${DNS_MODE:-default}"
    local dns_method="${DNS_METHOD:-auto}"
    
    # Apply Cloudflare mode if specified
    if [[ -n "$dns_mode" && "$dns_mode" != "default" ]]; then
        if [[ -n "${CLOUDFLARE_MODES[${dns_mode}_primary]:-}" ]]; then
            primary_dns="${CLOUDFLARE_MODES[${dns_mode}_primary]}"
            secondary_dns="${CLOUDFLARE_MODES[${dns_mode}_secondary]}"
            doh_url="${CLOUDFLARE_MODES[${dns_mode}_doh]}"
        fi
    fi
    
    # Check for command line arguments
    if [[ $# -gt 0 ]]; then
        local command="$1"
        shift
        
        case "$command" in
            setup)
                require_root
                if setup_dns "$primary_dns" "$secondary_dns" "$dns_method"; then
                    verify_dns
                fi
                ;;
            
            setup-fastest)
                require_root
                local fastest_result
                fastest_result="$(find_fastest_dns)"
                local fastest_primary fastest_secondary
                fastest_primary="$(echo "$fastest_result" | awk '{print $2}')"
                fastest_secondary="$(echo "$fastest_result" | awk '{print $3}')"
                if setup_dns "$fastest_primary" "$fastest_secondary" "$dns_method"; then
                    verify_dns
                fi
                ;;
            
            setup-mode)
                require_root
                if [[ $# -gt 0 ]]; then
                    local mode="$1"
                    if [[ -n "${CLOUDFLARE_MODES[${mode}_primary]:-}" ]]; then
                        local mode_primary="${CLOUDFLARE_MODES[${mode}_primary]}"
                        local mode_secondary="${CLOUDFLARE_MODES[${mode}_secondary]}"
                        if setup_dns "$mode_primary" "$mode_secondary" "$dns_method"; then
                            verify_dns
                        fi
                    else
                        echo "❌ Unknown mode: $mode"
                        echo "Available modes: default, malware_blocking, malware_and_adult_blocking"
                    fi
                else
                    echo "❌ Please specify mode: default, malware_blocking, malware_and_adult_blocking"
                fi
                ;;
            
            doh-query)
                if [[ $# -gt 0 ]]; then
                    local domain="$1"
                    local record_type="${2:-A}"
                    doh_query "$doh_url" "$domain" "$record_type"
                else
                    echo "❌ Usage: $0 doh-query <domain> [record_type]"
                fi
                ;;
            
            doh-resolve)
                if [[ $# -gt 0 ]]; then
                    local domain="$1"
                    doh_resolve "$domain" "$doh_url"
                else
                    echo "❌ Usage: $0 doh-resolve <domain>"
                fi
                ;;
            
            test-latency)
                test_latency_interactive
                ;;
            
            status)
                show_dns_status
                ;;
            
            verify)
                verify_dns
                ;;
            
            providers)
                list_providers
                ;;
            
            modes)
                list_modes
                ;;
            
            help)
                print_menu
                ;;
            
            *)
                echo "❌ Unknown command: $command"
                print_menu
                ;;
        esac
    else
        # Interactive mode
        require_root
        
        while true; do
            print_menu
            read -rp "Enter command (or 'exit'): " choice
            choice="${choice,,}"  # Convert to lowercase
            
            case "$choice" in
                exit|quit|q)
                    echo "👋 Goodbye!"
                    break
                    ;;
                
                1|setup)
                    if setup_dns "$primary_dns" "$secondary_dns" "$dns_method"; then
                        verify_dns
                    fi
                    ;;
                
                2|setup-fastest)
                    local fastest_result
                    fastest_result="$(find_fastest_dns)"
                    local fastest_primary fastest_secondary
                    fastest_primary="$(echo "$fastest_result" | awk '{print $2}')"
                    fastest_secondary="$(echo "$fastest_result" | awk '{print $3}')"
                    if setup_dns "$fastest_primary" "$fastest_secondary" "$dns_method"; then
                        verify_dns
                    fi
                    ;;
                
                3|setup-mode)
                    interactive_setup
                    ;;
                
                4|doh-query)
                    doh_query_interactive
                    ;;
                
                5|doh-resolve)
                    doh_resolve_interactive
                    ;;
                
                6|test-latency)
                    test_latency_interactive
                    ;;
                
                7|status)
                    show_dns_status
                    ;;
                
                8|verify)
                    verify_dns
                    ;;
                
                9|providers)
                    list_providers
                    ;;
                
                10|modes)
                    list_modes
                    ;;
                
                11|help)
                    print_menu
                    ;;
                
                *)
                    echo "❌ Invalid choice"
                    ;;
            esac
            
            read -rp "Press Enter to continue..."
        done
    fi
}

# Run main function
main "$@"

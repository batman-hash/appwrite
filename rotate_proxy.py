#!/usr/bin/env python3
"""
Rotating Proxy Manager for Email Extraction
Provides rotating IP proxies to avoid rate limiting and IP blocks
"""
import os
import random
import time
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class RotatingProxyManager:
    """Manages rotating proxies for email extraction"""

    def __init__(self):
        self.proxies = self._load_proxies()
        self.current_index = 0
        self.failed_proxies = set()

    def _load_proxies(self) -> List[str]:
        """Load proxies from environment or file"""
        proxies = []

        # Load from environment variable (comma-separated)
        env_proxies = os.getenv('ROTATING_PROXIES', '')
        if env_proxies:
            proxies.extend([p.strip() for p in env_proxies.split(',') if p.strip()])

        # Load from file if exists
        proxy_file = os.getenv('PROXY_FILE', 'proxies.txt')
        if os.path.exists(proxy_file):
            with open(proxy_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        proxies.append(line)

        # Add some free public proxies as fallback (these may not always work)
        if not proxies:
            proxies = [
                'http://proxy1.example.com:8080',
                'http://proxy2.example.com:8080',
                'http://proxy3.example.com:8080',
            ]
            print("⚠️  No proxies configured. Using placeholder proxies.")
            print("   Set ROTATING_PROXIES env var or create proxies.txt with real proxies.")

        return proxies

    def get_proxy(self) -> Optional[str]:
        """Get next working proxy with rotation"""
        if not self.proxies:
            return None

        # Try to find a working proxy
        attempts = 0
        while attempts < len(self.proxies):
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)

            if proxy not in self.failed_proxies:
                return proxy

            attempts += 1

        # All proxies failed, reset and try again
        self.failed_proxies.clear()
        return self.proxies[0] if self.proxies else None

    def mark_failed(self, proxy: str):
        """Mark a proxy as failed"""
        self.failed_proxies.add(proxy)
        print(f"⚠️  Proxy failed: {proxy}")

    def test_proxy(self, proxy: str, timeout: int = 5) -> bool:
        """Test if a proxy is working"""
        try:
            response = requests.get(
                'https://httpbin.org/ip',
                proxies={'http': proxy, 'https': proxy},
                timeout=timeout
            )
            return response.status_code == 200
        except:
            return False

    def get_working_proxy(self) -> Optional[str]:
        """Get a working proxy by testing them"""
        for proxy in self.proxies:
            if self.test_proxy(proxy):
                return proxy
        return None

def main():
    """Test the rotating proxy manager"""
    manager = RotatingProxyManager()

    print(f"📋 Loaded {len(manager.proxies)} proxies")
    print()

    # Test each proxy
    print("🔍 Testing proxies...")
    for i, proxy in enumerate(manager.proxies, 1):
        print(f"  {i}. {proxy}...", end=" ")
        if manager.test_proxy(proxy):
            print("✓ Working")
        else:
            print("✗ Failed")
            manager.mark_failed(proxy)

    print()

    # Demonstrate rotation
    print("🔄 Demonstrating proxy rotation:")
    for i in range(5):
        proxy = manager.get_proxy()
        if proxy:
            print(f"  Request {i+1}: Using {proxy}")
        else:
            print(f"  Request {i+1}: No proxy available")
        time.sleep(0.5)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Network Email Scraper with Kali Linux Tools
Scans network, extracts emails, validates, and sends without being banned
"""
import os
import sys
import re
import json
import time
import random
import sqlite3
import subprocess
import requests
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from python_engine.email_extractor import EmailValidator
from python_engine.database_manager import DatabaseManager
from send_test_emails import EmailSender, EmailTemplateManager

# Optional imports for enhanced features
try:
    from bs4 import BeautifulSoup
    HAS_BEAUTIFULSOUP = True
except ImportError:
    HAS_BEAUTIFULSOUP = False

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    HAS_GOOGLE_API = True
except ImportError:
    HAS_GOOGLE_API = False

class NetworkEmailScraper:
    """Scrape emails from network, validate, and send safely"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.getenv('DATABASE_PATH', './database/devnav.db')
        self.validator = EmailValidator(
            enable_virus_check=os.getenv('ENABLE_VIRUS_CHECK', 'true').lower() == 'true',
            enable_source_verification=os.getenv('ENABLE_SOURCE_VERIFICATION', 'true').lower() == 'true',
        )
        self.db_manager = DatabaseManager(self.db_path)
        self.email_sender = EmailSender()
        self.template_manager = EmailTemplateManager(self.db_path)

        # Rate limiting settings
        self.min_delay = int(os.getenv('EMAIL_MIN_DELAY', '5'))
        self.max_delay = int(os.getenv('EMAIL_MAX_DELAY', '15'))
        self.batch_size = int(os.getenv('EMAIL_BATCH_SIZE', '10'))
        self.batch_delay = int(os.getenv('EMAIL_BATCH_DELAY', '60'))

        # Proxy rotation
        self.proxies = self._load_proxies()
        self.current_proxy_index = 0

        # Email patterns
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

        # Data retention settings
        self.retention_days = int(os.getenv('DATA_RETENTION_DAYS', '365'))
        self.auto_cleanup = os.getenv('AUTO_CLEANUP', 'true').lower() == 'true'

        # Unsubscribe settings
        self.unsubscribe_base_url = os.getenv('UNSUBSCRIBE_BASE_URL', 'https://yoursite.com/unsubscribe')

    def _load_proxies(self) -> List[str]:
        """Load proxies for rotation"""
        proxies = []

        # Load from environment
        env_proxies = os.getenv('ROTATING_PROXIES', '')
        if env_proxies:
            proxies.extend([p.strip() for p in env_proxies.split(',') if p.strip()])

        # Load from file
        proxy_file = os.getenv('PROXY_FILE', 'proxies.txt')
        if os.path.exists(proxy_file):
            with open(proxy_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        proxies.append(line)

        return proxies

    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy in rotation"""
        if not self.proxies:
            return None

        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy

    # ==================== GMAIL EXPORT ====================

    def export_from_gmail(self, credentials_file: str = 'credentials.json',
                          token_file: str = 'token.json',
                          max_results: int = 100) -> List[str]:
        """
        Export emails from Gmail using Google API
        Requires: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
        """
        if not HAS_GOOGLE_API:
            print("❌ Google API libraries not installed")
            print("   Install with: pip install google-auth google-auth-oauthlib google-api-python-client")
            return []

        print(f"📧 Exporting emails from Gmail...")

        SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        creds = None

        # Load existing token
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        # Refresh or create new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_file):
                    print(f"❌ Credentials file not found: {credentials_file}")
                    print("   Download from Google Cloud Console:")
                    print("   https://console.cloud.google.com/apis/credentials")
                    return []

                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save token for future use
            with open(token_file, 'w') as token:
                token.write(creds.to_json())

        try:
            service = build('gmail', 'v1', credentials=creds)

            # Get messages
            results = service.users().messages().list(
                userId='me',
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            emails = set()

            print(f"  📬 Found {len(messages)} messages")

            for msg in messages:
                try:
                    message = service.users().messages().get(
                        userId='me',
                        id=msg['id']
                    ).execute()

                    # Extract email from headers
                    headers = message.get('payload', {}).get('headers', [])
                    for header in headers:
                        if header['name'].lower() in ['from', 'to', 'cc', 'bcc']:
                            found_emails = self.email_pattern.findall(header['value'])
                            emails.update(found_emails)

                    # Extract from body
                    payload = message.get('payload', {})
                    if 'parts' in payload:
                        for part in payload['parts']:
                            if part.get('mimeType') == 'text/plain':
                                body = part.get('body', {}).get('data', '')
                                if body:
                                    import base64
                                    decoded = base64.urlsafe_b64decode(body).decode('utf-8', errors='ignore')
                                    found_emails = self.email_pattern.findall(decoded)
                                    emails.update(found_emails)

                except Exception as e:
                    continue

            print(f"  ✓ Extracted {len(emails)} unique emails from Gmail")
            return list(emails)

        except Exception as e:
            print(f"❌ Gmail export error: {e}")
            return []

    # ==================== BEAUTIFUL SOUP SCRAPING ====================

    def scrape_with_beautifulsoup(self, url: str, depth: int = 2) -> List[str]:
        """
        Scrape emails using Beautiful Soup for better HTML parsing
        Requires: pip install beautifulsoup4 lxml
        """
        if not HAS_BEAUTIFULSOUP:
            print("⚠️  Beautiful Soup not installed, falling back to regex")
            return self.scrape_emails_from_url(url, depth)

        print(f"📧 Scraping emails from: {url} (Beautiful Soup)")

        emails = set()
        visited = set()

        def scrape_page(page_url: str, current_depth: int):
            if current_depth > depth or page_url in visited:
                return

            visited.add(page_url)

            try:
                # Use proxy if available
                proxy = self.get_next_proxy()
                proxies = {'http': proxy, 'https': proxy} if proxy else None

                response = requests.get(
                    page_url,
                    timeout=10,
                    proxies=proxies,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Method 1: Find mailto: links
                    mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
                    for link in mailto_links:
                        email = link['href'].replace('mailto:', '').split('?')[0]
                        if self.email_pattern.match(email):
                            emails.add(email.lower())

                    # Method 2: Find email patterns in text
                    text_emails = self.email_pattern.findall(soup.get_text())
                    emails.update([e.lower() for e in text_emails])

                    # Method 3: Find in meta tags
                    meta_tags = soup.find_all('meta', content=re.compile(r'@'))
                    for tag in meta_tags:
                        found_emails = self.email_pattern.findall(tag.get('content', ''))
                        emails.update([e.lower() for e in found_emails])

                    # Method 4: Find in script tags
                    script_tags = soup.find_all('script')
                    for script in script_tags:
                        if script.string:
                            found_emails = self.email_pattern.findall(script.string)
                            emails.update([e.lower() for e in found_emails])

                    # Follow links
                    if current_depth < depth:
                        links = soup.find_all('a', href=True)
                        base_domain = re.search(r'https?://([^/]+)', page_url)

                        if base_domain:
                            domain = base_domain.group(1)
                            for link in links[:10]:  # Limit to 10 links
                                href = link['href']
                                if href.startswith('http') and domain in href:
                                    time.sleep(random.uniform(1, 3))
                                    scrape_page(href, current_depth + 1)
                                elif href.startswith('/'):
                                    full_url = f"{page_url.rstrip('/')}{href}"
                                    time.sleep(random.uniform(1, 3))
                                    scrape_page(full_url, current_depth + 1)

            except Exception as e:
                print(f"  ⚠️  Error scraping {page_url}: {e}")

        scrape_page(url, 0)

        print(f"  ✓ Found {len(emails)} emails")
        return list(emails)

    # ==================== UNSUBSCRIBE LINKS ====================

    def generate_unsubscribe_link(self, email: str) -> str:
        """Generate unique unsubscribe link for email"""
        import hashlib
        token = hashlib.sha256(f"{email}{datetime.now().isoformat()}".encode()).hexdigest()[:32]
        return f"{self.unsubscribe_base_url}?email={email}&token={token}"

    def add_unsubscribe_to_body(self, body: str, email: str) -> str:
        """Add unsubscribe link to email body"""
        unsubscribe_link = self.generate_unsubscribe_link(email)

        unsubscribe_footer = f"""

---
📧 To unsubscribe from future emails, click here:
{unsubscribe_link}

This email was sent by DevNavigator.
If you believe this was sent in error, please contact us.
"""
        return body + unsubscribe_footer

    def add_unsubscribe_to_html(self, html_body: str, email: str) -> str:
        """Add unsubscribe link to HTML email body"""
        unsubscribe_link = self.generate_unsubscribe_link(email)

        unsubscribe_html = f"""
<br><br>
<hr style="border: 1px solid #e5e7eb; margin: 20px 0;">
<p style="font-size: 12px; color: #6b7280; text-align: center;">
    📧 To unsubscribe from future emails,
    <a href="{unsubscribe_link}" style="color: #2563eb; text-decoration: underline;">click here</a>
</p>
<p style="font-size: 10px; color: #9ca3af; text-align: center;">
    This email was sent by DevNavigator.<br>
    If you believe this was sent in error, please contact us.
</p>
"""
        return html_body + unsubscribe_html

    # ==================== CONSENT COLLECTION ====================

    def collect_consent(self, email: str, source: str = "web_form") -> bool:
        """Collect and record consent for email"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if contact exists
            cursor.execute("SELECT id, consent FROM contacts WHERE email = ?", (email,))
            result = cursor.fetchone()

            if result:
                contact_id, existing_consent = result
                if existing_consent:
                    print(f"  ✓ Consent already recorded for {email}")
                    return True

                # Update consent
                cursor.execute("""
                    UPDATE contacts
                    SET consent = 1, consent_date = ?, consent_source = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), source, contact_id))
            else:
                # Insert new contact with consent
                cursor.execute("""
                    INSERT INTO contacts (email, consent, consent_date, consent_source, created_at)
                    VALUES (?, 1, ?, ?, ?)
                """, (email, datetime.now().isoformat(), source, datetime.now().isoformat()))

            conn.commit()
            conn.close()

            print(f"  ✓ Consent recorded for {email}")
            return True

        except Exception as e:
            print(f"  ❌ Error recording consent: {e}")
            return False

    def verify_consent(self, email: str) -> bool:
        """Verify if email has valid consent"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT consent, consent_date, unsubscribed
                FROM contacts
                WHERE email = ?
            """, (email,))

            result = cursor.fetchone()
            conn.close()

            if not result:
                return False

            consent, consent_date, unsubscribed = result

            if unsubscribed:
                return False

            if not consent:
                return False

            # Check if consent is still valid (not expired)
            if consent_date:
                consent_dt = datetime.fromisoformat(consent_date)
                if datetime.now() - consent_dt > timedelta(days=self.retention_days):
                    print(f"  ⚠️  Consent expired for {email}")
                    return False

            return True

        except Exception as e:
            print(f"  ❌ Error verifying consent: {e}")
            return False

    # ==================== DATA RETENTION ====================

    def cleanup_expired_data(self) -> int:
        """Clean up expired data based on retention policy"""
        if not self.auto_cleanup:
            return 0

        print(f"🧹 Cleaning up data older than {self.retention_days} days...")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(days=self.retention_days)).isoformat()

            # Archive old contacts
            cursor.execute("""
                UPDATE contacts
                SET archived = 1, archived_at = ?
                WHERE created_at < ? AND archived = 0
            """, (datetime.now().isoformat(), cutoff_date))

            archived_count = cursor.rowcount

            # Delete old email logs
            cursor.execute("""
                DELETE FROM email_logs
                WHERE sent_at < ?
            """, (cutoff_date,))

            deleted_logs = cursor.rowcount

            # Delete old tracking data
            cursor.execute("""
                DELETE FROM email_tracking
                WHERE created_at < ?
            """, (cutoff_date,))

            deleted_tracking = cursor.rowcount

            conn.commit()
            conn.close()

            print(f"  ✓ Archived {archived_count} contacts")
            print(f"  ✓ Deleted {deleted_logs} email logs")
            print(f"  ✓ Deleted {deleted_tracking} tracking records")

            return archived_count

        except Exception as e:
            print(f"  ❌ Error during cleanup: {e}")
            return 0

    def get_data_retention_report(self) -> Dict:
        """Generate data retention report"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total contacts
            cursor.execute("SELECT COUNT(*) FROM contacts")
            total_contacts = cursor.fetchone()[0]

            # Active contacts
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE archived = 0")
            active_contacts = cursor.fetchone()[0]

            # Archived contacts
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE archived = 1")
            archived_contacts = cursor.fetchone()[0]

            # Contacts with consent
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE consent = 1")
            consented_contacts = cursor.fetchone()[0]

            # Unsubscribed contacts
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE unsubscribed = 1")
            unsubscribed_contacts = cursor.fetchone()[0]

            # Old contacts (beyond retention)
            cutoff_date = (datetime.now() - timedelta(days=self.retention_days)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE created_at < ?", (cutoff_date,))
            old_contacts = cursor.fetchone()[0]

            conn.close()

            return {
                'total_contacts': total_contacts,
                'active_contacts': active_contacts,
                'archived_contacts': archived_contacts,
                'consented_contacts': consented_contacts,
                'unsubscribed_contacts': unsubscribed_contacts,
                'old_contacts': old_contacts,
                'retention_days': self.retention_days
            }

        except Exception as e:
            print(f"  ❌ Error generating report: {e}")
            return {}

    # ==================== ENHANCED SCRAPING ====================

    def scan_network_nmap(self, target: str = "192.168.1.0/24", ports: str = "80,443,8080,8443") -> List[str]:
        """
        Scan network using nmap to find web services
        Returns list of URLs to scrape
        """
        print(f"🔍 Scanning network: {target}")
        print(f"   Ports: {ports}")

        urls = []

        try:
            # Run nmap scan
            cmd = [
                "nmap", "-p", ports,
                "--open",
                "-sV",
                "--script", "http-title,http-headers",
                "-oG", "-",  # Greppable output
                target
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                # Parse nmap output for hosts with web services
                for line in result.stdout.split('\n'):
                    if 'Ports:' in line:
                        # Extract host
                        host_match = re.search(r'Host:\s+(\d+\.\d+\.\d+\.\d+)', line)
                        if host_match:
                            host = host_match.group(1)

                            # Check for open ports
                            if '80/open' in line:
                                urls.append(f"http://{host}")
                            if '443/open' in line:
                                urls.append(f"https://{host}")
                            if '8080/open' in line:
                                urls.append(f"http://{host}:8080")
                            if '8443/open' in line:
                                urls.append(f"https://{host}:8443")

                print(f"✓ Found {len(urls)} web services")
            else:
                print(f"⚠️  Nmap scan returned error: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("⚠️  Nmap scan timed out")
        except FileNotFoundError:
            print("❌ Nmap not found. Install with: sudo apt install nmap")
        except Exception as e:
            print(f"❌ Nmap scan error: {e}")

        return urls

    def scan_network_netdiscover(self, interface: str = "eth0") -> List[str]:
        """
        Scan network using netdiscover to find active hosts
        Returns list of IP addresses
        """
        print(f"🔍 Running netdiscover on interface: {interface}")

        ips = []

        try:
            # Run netdiscover in passive mode for 30 seconds
            cmd = ["netdiscover", "-i", interface, "-P", "-N"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # Parse netdiscover output
                for line in result.stdout.split('\n'):
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if ip_match:
                        ips.append(ip_match.group(1))

                print(f"✓ Found {len(ips)} active hosts")
            else:
                print(f"⚠️  Netdiscover returned error: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("⚠️  Netdiscover timed out")
        except FileNotFoundError:
            print("❌ Netdiscover not found. Install with: sudo apt install netdiscover")
        except Exception as e:
            print(f"❌ Netdiscover error: {e}")

        return ips

    def scrape_emails_from_url(self, url: str, depth: int = 2) -> List[str]:
        """
        Scrape emails from a URL
        Follows links up to specified depth
        """
        # Use Beautiful Soup if available
        if HAS_BEAUTIFULSOUP:
            return self.scrape_with_beautifulsoup(url, depth)

        print(f"📧 Scraping emails from: {url}")

        emails = set()
        visited = set()

        def scrape_page(page_url: str, current_depth: int):
            if current_depth > depth or page_url in visited:
                return

            visited.add(page_url)

            try:
                # Use proxy if available
                proxy = self.get_next_proxy()
                proxies = {'http': proxy, 'https': proxy} if proxy else None

                response = requests.get(
                    page_url,
                    timeout=10,
                    proxies=proxies,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )

                if response.status_code == 200:
                    # Extract emails from page
                    found_emails = self.email_pattern.findall(response.text)
                    emails.update(found_emails)

                    # Find links to follow
                    if current_depth < depth:
                        link_pattern = re.compile(r'href=["\'](https?://[^"\']+)["\']', re.IGNORECASE)
                        links = link_pattern.findall(response.text)

                        # Only follow links on same domain
                        base_domain = re.search(r'https?://([^/]+)', page_url)
                        if base_domain:
                            domain = base_domain.group(1)
                            for link in links[:10]:  # Limit to 10 links per page
                                if domain in link:
                                    time.sleep(random.uniform(1, 3))  # Be polite
                                    scrape_page(link, current_depth + 1)

            except Exception as e:
                print(f"  ⚠️  Error scraping {page_url}: {e}")

        scrape_page(url, 0)

        print(f"  ✓ Found {len(emails)} emails")
        return list(emails)

    def scrape_emails_from_file(self, file_path: str) -> List[str]:
        """Extract emails from a file"""
        print(f"📧 Extracting emails from file: {file_path}")

        emails = set()

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                found_emails = self.email_pattern.findall(content)
                emails.update(found_emails)
        except Exception as e:
            print(f"  ❌ Error reading file: {e}")

        print(f"  ✓ Found {len(emails)} emails")
        return list(emails)

    def validate_emails(self, emails: List[str]) -> tuple:
        """Validate emails and return valid/invalid lists"""
        print(f"✅ Validating {len(emails)} emails...")

        valid_emails = []
        invalid_emails = []

        for email in emails:
            is_valid, reason = self.validator.is_valid_email(email.lower())
            if is_valid:
                valid_emails.append(email.lower())
            else:
                invalid_emails.append((email, reason))

        print(f"  ✓ Valid: {len(valid_emails)}")
        print(f"  ✗ Invalid: {len(invalid_emails)}")

        return valid_emails, invalid_emails

    def store_emails(self, emails: List[str], source: str = "network_scan") -> int:
        """Store validated emails in database"""
        print(f"💾 Storing {len(emails)} emails in database...")

        stored = 0
        for email in emails:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Check if email already exists
                cursor.execute("SELECT id FROM contacts WHERE email = ?", (email,))
                if cursor.fetchone():
                    continue

                # Insert new contact
                cursor.execute("""
                    INSERT INTO contacts (email, source, consent, created_at)
                    VALUES (?, ?, 1, ?)
                """, (email, source, datetime.now().isoformat()))

                conn.commit()
                conn.close()
                stored += 1

            except Exception as e:
                print(f"  ⚠️  Error storing {email}: {e}")

        print(f"  ✓ Stored {stored} new emails")
        return stored

    def send_emails_safely(self, template_name: str = None, limit: int = None) -> Dict:
        """
        Send emails with rate limiting and proxy rotation to avoid bans
        Includes unsubscribe links and consent verification
        """
        print(f"📤 Sending emails safely...")

        # Get contacts ready to send
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT id, email, name, company, country
            FROM contacts
            WHERE sent = 0 AND consent = 1 AND bounced = 0 AND unsubscribed = 0 AND archived = 0
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        contacts = cursor.fetchall()
        conn.close()

        if not contacts:
            print("  ℹ️  No contacts ready to send")
            return {"sent": 0, "failed": 0}

        print(f"  📋 Found {len(contacts)} contacts to send")

        # Get template
        template_manager = EmailTemplateManager(self.db_path)
        subject, body = template_manager.get_template(template_name)

        if not subject or not body:
            print(f"  ❌ Template '{template_name}' not found")
            return {"sent": 0, "failed": 0}

        # Send emails with rate limiting
        sent = 0
        failed = 0

        for i, contact in enumerate(contacts):
            contact_id, email, name, company, country = contact

            try:
                # Verify consent before sending
                if not self.verify_consent(email):
                    print(f"  ⚠️  [{i+1}/{len(contacts)}] No valid consent: {email}")
                    failed += 1
                    continue

                # Rate limiting
                if i > 0 and i % self.batch_size == 0:
                    print(f"  ⏸️  Batch delay: {self.batch_delay} seconds...")
                    time.sleep(self.batch_delay)
                else:
                    delay = random.uniform(self.min_delay, self.max_delay)
                    time.sleep(delay)

                # Rotate proxy
                proxy = self.get_next_proxy()
                if proxy:
                    os.environ['HTTP_PROXY'] = proxy
                    os.environ['HTTPS_PROXY'] = proxy

                # Add unsubscribe link to body
                body_with_unsubscribe = self.add_unsubscribe_to_body(body, email)

                # Send email
                success, message = self.email_sender.send_test_email(
                    to_email=email,
                    subject=subject,
                    body=body_with_unsubscribe,
                    template_name=template_name,
                    add_tracking=True,
                    log_status='sent',
                    mark_contact_sent=True
                )

                if success:
                    sent += 1
                    print(f"  ✓ [{i+1}/{len(contacts)}] Sent to {email}")
                else:
                    failed += 1
                    print(f"  ✗ [{i+1}/{len(contacts)}] Failed: {email} - {message}")

            except Exception as e:
                failed += 1
                print(f"  ✗ [{i+1}/{len(contacts)}] Error: {email} - {e}")

        print(f"\n📊 Send Summary:")
        print(f"  ✓ Sent: {sent}")
        print(f"  ✗ Failed: {failed}")

        return {"sent": sent, "failed": failed}

    def run_full_scan(self, targets: List[str] = None, template_name: str = None, send_limit: int = None):
        """
        Run complete workflow:
        1. Clean up expired data
        2. Scan network
        3. Extract emails
        4. Validate emails
        5. Store emails
        6. Send emails
        """
        print("=" * 80)
        print("🚀 NETWORK EMAIL SCRAPER - FULL SCAN")
        print("=" * 80)

        # Step 0: Clean up expired data
        print("\n🧹 Step 0: Cleaning up expired data...")
        self.cleanup_expired_data()

        all_emails = set()

        # Step 1: Scan network
        if targets:
            print("\n📡 Step 1: Scanning network...")
            for target in targets:
                if '/' in target:  # IP range
                    urls = self.scan_network_nmap(target)
                    for url in urls:
                        emails = self.scrape_emails_from_url(url)
                        all_emails.update(emails)
                else:  # Single URL
                    emails = self.scrape_emails_from_url(target)
                    all_emails.update(emails)

        # Step 2: Extract from files
        print("\n📂 Step 2: Extracting from files...")
        for file in Path('.').glob('*.txt'):
            emails = self.scrape_emails_from_file(str(file))
            all_emails.update(emails)

        for file in Path('.').glob('*.csv'):
            emails = self.scrape_emails_from_file(str(file))
            all_emails.update(emails)

        # Step 3: Validate emails
        print("\n✅ Step 3: Validating emails...")
        valid_emails, invalid_emails = self.validate_emails(list(all_emails))

        # Step 4: Store emails
        print("\n💾 Step 4: Storing emails...")
        stored = self.store_emails(valid_emails)

        # Step 5: Send emails
        if template_name and stored > 0:
            print("\n📤 Step 5: Sending emails...")
            result = self.send_emails_safely(template_name, send_limit)

        # Final summary
        print("\n" + "=" * 80)
        print("📊 FINAL SUMMARY")
        print("=" * 80)
        print(f"Total emails found: {len(all_emails)}")
        print(f"Valid emails: {len(valid_emails)}")
        print(f"Invalid emails: {len(invalid_emails)}")
        print(f"Stored in database: {stored}")

        if template_name:
            print(f"Emails sent: {result['sent']}")
            print(f"Emails failed: {result['failed']}")

        # Data retention report
        report = self.get_data_retention_report()
        if report:
            print(f"\n📋 Data Retention Report:")
            print(f"  Total contacts: {report.get('total_contacts', 0)}")
            print(f"  Active contacts: {report.get('active_contacts', 0)}")
            print(f"  Archived contacts: {report.get('archived_contacts', 0)}")
            print(f"  Consented contacts: {report.get('consented_contacts', 0)}")
            print(f"  Unsubscribed: {report.get('unsubscribed_contacts', 0)}")

        print("=" * 80)

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Network Email Scraper')
    parser.add_argument('--scan', nargs='+', help='Scan network targets (IP ranges or URLs)')
    parser.add_argument('--template', help='Email template to use for sending')
    parser.add_argument('--limit', type=int, help='Maximum emails to send')
    parser.add_argument('--send-only', action='store_true', help='Only send emails, skip scanning')
    parser.add_argument('--scan-only', action='store_true', help='Only scan, skip sending')
    parser.add_argument('--gmail-export', action='store_true', help='Export emails from Gmail')
    parser.add_argument('--cleanup', action='store_true', help='Clean up expired data')
    parser.add_argument('--report', action='store_true', help='Generate data retention report')

    args = parser.parse_args()

    scraper = NetworkEmailScraper()

    if args.gmail_export:
        # Export from Gmail
        emails = scraper.export_from_gmail()
        if emails:
            print(f"\n📧 Exported {len(emails)} emails from Gmail")
            stored = scraper.store_emails(emails, source="gmail_export")
            print(f"💾 Stored {stored} new emails")
    elif args.cleanup:
        # Clean up expired data
        scraper.cleanup_expired_data()
    elif args.report:
        # Generate report
        report = scraper.get_data_retention_report()
        print("\n📋 Data Retention Report:")
        for key, value in report.items():
            print(f"  {key}: {value}")
    elif args.send_only:
        # Only send emails
        scraper.send_emails_safely(args.template, args.limit)
    elif args.scan_only:
        # Only scan
        scraper.run_full_scan(args.scan, None, None)
    else:
        # Full workflow
        scraper.run_full_scan(args.scan, args.template, args.limit)

if __name__ == '__main__':
    main()

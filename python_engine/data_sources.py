"""
Data Source Integration Module
Integrates multiple email and IP databases for campaign sourcing
"""
import requests
import json
import sqlite3
import os
from typing import List, Dict, Set, Tuple
from enum import Enum
from datetime import datetime


class DataSource(Enum):
    """Available data sources"""
    HUNTER_IO = "hunter"
    CLEARBIT = "clearbit"
    APOLLO = "apollo"
    ROCKETREACH = "rocketreach"
    LINKSCRAPE = "linkscrape"
    MAXMIND_GEOIP = "maxmind"
    IPQUALITYSCORE = "ipqs"
    LEADIRO = "leadiro"
    CSV_UPLOAD = "csv"
    API_WEBHOOK = "webhook"


class EmailSourceManager:
    """Manages integration with email data sources"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', './database/devnav.db')
        self.db_path = db_path
        self.api_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment"""
        return {
            'hunter': os.getenv('HUNTER_API_KEY', os.getenv('HUNTER_IO_API_KEY', '')),
            'clearbit': os.getenv('CLEARBIT_API_KEY', ''),
            'apollo': os.getenv('APOLLO_API_KEY', ''),
            'rocketreach': os.getenv('ROCKETREACH_API_KEY', ''),
            'maxmind': os.getenv('MAXMIND_API_KEY', ''),
            'ipqs': os.getenv('IPQS_API_KEY', ''),
        }
    
    # ========================
    # HUNTER.IO Integration
    # ========================
    
    def search_hunter_io(self, domain: str, department: str = None) -> List[Dict]:
        """
        Search Hunter.io for emails at a domain
        Pricing: Free tier 10/month, Paid $99+/month
        
        Args:
            domain: Company domain (e.g., 'google.com')
            department: Optional department filter
        
        Returns list of {email, name, source_url}
        """
        if not self.api_keys['hunter']:
            print("❌ HUNTER_API_KEY not set")
            return []
        
        base_url = "https://api.hunter.io/v2/domain-search"
        params = {
            'domain': domain,
            'api_key': self.api_keys['hunter']
        }
        
        if department:
            params['department'] = department
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                emails = []
                for email_obj in data.get('data', {}).get('emails', []):
                    emails.append({
                        'email': email_obj['value'],
                        'name': email_obj.get('first_name', '') + ' ' + email_obj.get('last_name', ''),
                        'department': email_obj.get('department', ''),
                        'source': 'hunter.io',
                        'verified': email_obj.get('type') == 'personal'
                    })
                return emails
            else:
                print(f"❌ Hunter.io error: {response.status_code}")
                return []
        except requests.RequestException as e:
            print(f"❌ Hunter.io request failed: {e}")
            return []
    
    # ========================
    # CLEARBIT Integration
    # ========================
    
    def search_clearbit(self, domain: str) -> List[Dict]:
        """
        Get company info and employee emails from Clearbit
        Pricing: Free $0-100k rows, Paid from $500/month
        
        Args:
            domain: Company domain
        
        Returns list of company info with contact suggestions
        """
        if not self.api_keys['clearbit']:
            print("❌ CLEARBIT_API_KEY not set")
            return []
        
        base_url = f"https://api.clearbit.com/v2/companies/suggest"
        params = {'query': domain}
        headers = {'Authorization': f"Bearer {self.api_keys['clearbit']}"}
        
        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                companies = response.json()
                results = []
                for company in companies[:5]:  # Top 5 matches
                    results.append({
                        'domain': company.get('domain'),
                        'company': company.get('name'),
                        'employees': company.get('employeeCount'),
                        'industry': company.get('category', {}).get('industry'),
                        'country': company.get('geo', {}).get('countryCode'),
                        'source': 'clearbit'
                    })
                return results
        except requests.RequestException as e:
            print(f"❌ Clearbit request failed: {e}")
            return []
    
    # ========================
    # APOLLO Integration
    # ========================
    
    def search_apollo(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search Apollo for B2B people and enrich them with email addresses.
        Pricing: Free tier available, Paid plans unlock broader access.
        
        Args:
            query: Search query (person title or prospecting query)
            limit: Number of results
        
        Returns list of contacts with emails
        """
        if not self.api_keys['apollo']:
            print("❌ APOLLO_API_KEY not set")
            return []

        headers = {
            'x-api-key': self.api_keys['apollo'],
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
        }

        try:
            search_url = "https://api.apollo.io/api/v1/mixed_people/api_search"
            search_payload = {
                'person_titles': [query],
                'per_page': min(max(limit, 1), 100),
            }

            response = requests.post(search_url, headers=headers, json=search_payload, timeout=10)
            if response.status_code != 200:
                print(f"❌ Apollo search error: {response.status_code}")
                return []

            search_data = response.json()
            people = search_data.get('people', []) or []
            person_ids = [person.get('id') for person in people if person.get('id')]
            if not person_ids:
                return []

            contacts = []
            enrich_url = "https://api.apollo.io/api/v1/people/bulk_match"
            for start in range(0, min(len(person_ids), limit), 10):
                batch_ids = person_ids[start:start + 10]
                enrich_response = requests.post(
                    enrich_url,
                    params={'reveal_personal_emails': 'true', 'reveal_phone_number': 'false'},
                    headers=headers,
                    json={'details': [{'id': person_id} for person_id in batch_ids]},
                    timeout=10,
                )
                if enrich_response.status_code != 200:
                    print(f"❌ Apollo enrichment error: {enrich_response.status_code}")
                    continue

                enrich_data = enrich_response.json()
                for match in enrich_data.get('matches', []):
                    email = match.get('email')
                    if not email:
                        continue

                    organization = match.get('organization') or {}
                    contacts.append({
                        'email': email,
                        'name': match.get('name') or f"{match.get('first_name', '')} {match.get('last_name', '')}".strip(),
                        'title': match.get('title'),
                        'company': organization.get('name') or match.get('organization_name'),
                        'phone': match.get('phone_number'),
                        'country': match.get('country'),
                        'source': 'apollo',
                        'verified': match.get('email_status') == 'verified' or match.get('email_true_status') == 'Verified',
                    })

            return contacts
        except requests.RequestException as e:
            print(f"❌ Apollo request failed: {e}")
            return []
    
    # ========================
    # CSV/Bulk Upload
    # ========================
    
    def import_csv(self, file_path: str) -> Tuple[int, List[str]]:
        """
        Import emails from CSV file
        Expected format: email,name,company,department,country
        
        Args:
            file_path: Path to CSV file
        
        Returns (imported_count, errors)
        """
        import csv
        
        imported = 0
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                for row_num, row in enumerate(reader, start=2):
                    email = row.get('email', '').strip()
                    name = row.get('name', '').strip()
                    company = row.get('company', '').strip()
                    department = row.get('department', '').strip()
                    country = row.get('country', '').strip()
                    
                    if not email:
                        errors.append(f"Row {row_num}: Missing email")
                        continue
                    
                    try:
                        cursor.execute("""
                            INSERT INTO contacts (email, name, company, department, country, source)
                            VALUES (?, ?, ?, ?, ?, 'csv_upload')
                        """, (email, name, company, department, country))
                        imported += 1
                    except sqlite3.IntegrityError:
                        errors.append(f"Row {row_num}: Duplicate email {email}")
                
                conn.commit()
                conn.close()
        except Exception as e:
            errors.append(f"File error: {str(e)}")
        
        return imported, errors


class IPGeoTargeting:
    """IP address and geolocation targeting"""
    
    def __init__(self):
        self.api_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment"""
        return {
            'maxmind': os.getenv('MAXMIND_API_KEY', ''),
            'ipqs': os.getenv('IPQS_API_KEY', ''),
        }
    
    # ========================
    # MAXMIND GeoIP
    # ========================
    
    def get_geoip_maxmind(self, ip_address: str) -> Dict:
        """
        Get geolocation data from MaxMind GeoIP
        Pricing: Free GeoLite2, Paid from $120/year
        
        Args:
            ip_address: IP address to lookup
        
        Returns {country, city, latitude, longitude, timezone, isp}
        """
        if not self.api_keys['maxmind']:
            print("❌ MAXMIND_API_KEY not set")
            return {}
        
        base_url = f"https://geoip.maxmind.com/geoip/v2.1/city/{ip_address}"
        headers = {'Authorization': f"Basic {self.api_keys['maxmind']}"}
        
        try:
            response = requests.get(base_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'country': data['country']['iso_code'],
                    'country_name': data['country']['names']['en'],
                    'city': data.get('city', {}).get('names', {}).get('en', ''),
                    'latitude': data.get('location', {}).get('latitude'),
                    'longitude': data.get('location', {}).get('longitude'),
                    'timezone': data.get('location', {}).get('time_zone'),
                    'isp': data.get('traits', {}).get('isp'),
                    'source': 'maxmind'
                }
        except requests.RequestException as e:
            print(f"❌ MaxMind request failed: {e}")
            return {}
    
    # ========================
    # IP Quality Score
    # ========================
    
    def verify_ip_quality(self, ip_address: str) -> Dict:
        """
        Verify IP address quality and fraud risk
        Good for validating traffic sources
        Pricing: Free tier, Paid from $15/month
        
        Args:
            ip_address: IP to verify
        
        Returns {risk_score, is_vpn, is_proxy, country, threat_types}
        """
        if not self.api_keys['ipqs']:
            print("❌ IPQS_API_KEY not set")
            return {}
        
        base_url = "https://ipqualityscore.com/api/json/ip"
        params = {
            'ip': ip_address,
            'key': self.api_keys['ipqs'],
            'strictness': 1,
            'allow_public_access_points': True
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'fraud_score': data.get('fraud_score'),
                    'is_vpn': data.get('is_vpn'),
                    'is_proxy': data.get('is_proxy'),
                    'is_bot': data.get('is_bot'),
                    'country': data.get('country_code'),
                    'threat_types': data.get('threat_types', []),
                    'is_valid': data.get('is_valid'),
                    'source': 'ipqs'
                }
        except requests.RequestException as e:
            print(f"❌ IPQS request failed: {e}")
            return {}


class CampaignDataAnalytics:
    """Analytics for campaign data"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', './database/devnav.db')
        self.db_path = db_path
    
    def get_email_by_domain(self) -> List[Tuple]:
        """Get email distribution by company domain"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                SUBSTR(email, INSTR(email, '@') + 1) as domain,
                COUNT(*) as count
            FROM contacts
            GROUP BY domain
            ORDER BY count DESC
            LIMIT 20
        """)
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_email_by_country(self) -> List[Tuple]:
        """Get email distribution by country"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                country,
                COUNT(*) as count
            FROM contacts
            WHERE country IS NOT NULL
            GROUP BY country
            ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_source_quality(self) -> List[Dict]:
        """Analyze quality metrics by source"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                source,
                COUNT(*) as total,
                SUM(verified) as verified_count,
                ROUND(100.0 * SUM(verified) / COUNT(*), 2) as verification_rate
            FROM contacts
            GROUP BY source
            ORDER BY verification_rate DESC
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'source': row[0],
            'total': row[1],
            'verified': row[2],
            'verification_rate': row[3]
        } for row in results]


if __name__ == "__main__":
    print("Email Data Source Integrations Available:")
    print("\n1. Hunter.io - Domain-based email discovery")
    print("2. Clearbit - Company intelligence")
    print("3. Apollo - B2B contact database")
    print("4. CSV Upload - Bulk import")
    print("\n5. MaxMind GeoIP - Geolocation")
    print("6. IP Quality Score - Fraud detection")
    print("\nSet API keys in .env file to use services.")

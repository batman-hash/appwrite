#!/usr/bin/env python3
"""
Automated Email Extraction from Internet Sources
Searches specific requirements (IT jobs, remote, junior, etc) across free sources
"""
import os
import re
import json
import time
import requests
import sqlite3
from typing import List, Dict, Optional, Set, Tuple
from urllib.parse import urlencode, urlparse
from datetime import datetime
from dotenv import load_dotenv
from python_engine.email_extractor import EmailValidator

load_dotenv()

GLOBAL_COUNTRY_FILTERS = {"", "-", "all", "world", "global", "any", "anywhere", "worldwide", "*"}


def normalize_country_filter(country: Optional[str]) -> Optional[str]:
    """Normalize country inputs so global search aliases do not become hard filters."""
    if country is None:
        return None

    normalized = str(country).strip()
    if not normalized or normalized.lower() in GLOBAL_COUNTRY_FILTERS:
        return None

    return normalized


class AutoEmailExtractor:
    """Automatically extract emails from internet sources with specific criteria"""
    
    def __init__(self, db_path: str = None, proxy_url: Optional[str] = None):
        self.db_path = db_path or os.getenv('DATABASE_PATH', './database/devnav.db')
        self.session = requests.Session()
        self.session.timeout = 10
        self.session.trust_env = True
        self.proxies = self._configure_proxies(proxy_url)

    def _configure_proxies(self, proxy_url: Optional[str]) -> Dict[str, str]:
        """Configure optional explicit proxies for internet extraction."""
        proxies: Dict[str, str] = {}

        shared_proxy = proxy_url or os.getenv("EXTRACT_PROXY_URL")
        http_proxy = os.getenv("EXTRACT_HTTP_PROXY")
        https_proxy = os.getenv("EXTRACT_HTTPS_PROXY")
        no_proxy = os.getenv("EXTRACT_NO_PROXY")

        if shared_proxy:
            proxies["http"] = shared_proxy
            proxies["https"] = shared_proxy

        if http_proxy:
            proxies["http"] = http_proxy
        if https_proxy:
            proxies["https"] = https_proxy

        if proxies:
            self.session.proxies.update(proxies)

        if no_proxy:
            os.environ["NO_PROXY"] = no_proxy
            os.environ["no_proxy"] = no_proxy

        return proxies

    def proxy_summary(self) -> str:
        """Human-readable proxy summary for CLI output."""
        if not self.proxies:
            return "direct"

        http_proxy = self.proxies.get("http", "unset")
        https_proxy = self.proxies.get("https", "unset")
        return f"http={http_proxy}, https={https_proxy}"

    def proxy_configuration_error(self) -> Optional[str]:
        """Return a human-friendly proxy configuration error when obvious placeholders are used."""
        if not self.proxies:
            return None

        for scheme, proxy_value in self.proxies.items():
            parsed = urlparse(proxy_value)
            hostname = parsed.hostname

            if not parsed.scheme or not hostname:
                return (
                    f"Invalid {scheme.upper()} proxy URL: {proxy_value}. "
                    "Use a full URL like http://10.0.0.5:8080."
                )

            if hostname == "proxy-host":
                return (
                    "Your proxy is set to the placeholder host 'proxy-host'. "
                    "Replace it with your real proxy DNS name or IP, or unset EXTRACT_PROXY_URL to connect directly."
                )

        return None

    def _build_validator(self) -> EmailValidator:
        """Create the shared validator used by preview and storage flows."""
        return EmailValidator(
            enable_virus_check=os.getenv('ENABLE_VIRUS_CHECK', 'true').lower() == 'true',
            enable_source_verification=os.getenv('ENABLE_SOURCE_VERIFICATION', 'true').lower() == 'true',
        )

    def _validate_email_results(self, emails: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """Normalize and validate extracted email records before preview or storage."""
        validator = self._build_validator()
        valid_emails: List[Dict] = []
        failed: List[str] = []

        for email_data in emails:
            email = email_data.get('email', '').strip().lower()

            if not email:
                failed.append("missing-email: Missing email value")
                continue

            is_valid, reason = validator.is_valid_email(email)
            if not is_valid:
                failed.append(f"{email}: {reason}")
                continue

            normalized_email_data = dict(email_data)
            normalized_email_data['email'] = email
            valid_emails.append(normalized_email_data)

        return valid_emails, failed

    def _no_results_hints(self, criteria: Dict) -> List[str]:
        """Return practical guidance when internet extraction yields no validated emails."""
        hints: List[str] = []

        if not os.getenv('HUNTER_API_KEY') and not os.getenv('APOLLO_API_KEY'):
            hints.append(
                "Only free public-source search was available. GitHub public emails are rare, and the Kaggle step is informational only."
            )
            hints.append("Add HUNTER_API_KEY or APOLLO_API_KEY to search additional live sources.")

        if criteria.get('country'):
            hints.append("Try removing the country filter or using a broader region.")

        keywords = [keyword for keyword in criteria.get('keywords', []) if keyword]
        if len(keywords) > 1:
            hints.append("Try fewer keywords so the search is less restrictive.")

        hints.append("Use preview mode first, then enable INTERNET_SEARCH_STORE=1 only after you see validated results.")
        return hints
        
    def search_hunter_free(self, domain: str) -> List[Dict]:
        """
        Search Hunter.io free tier for emails
        Free tier: 10 searches/month (requires API key)
        """
        try:
            api_key = os.getenv('HUNTER_API_KEY')
            if not api_key:
                print("⚠️  Hunter API key not configured (HUNTER_API_KEY)")
                return []
            
            url = "https://api.hunter.io/v2/domain-search"
            params = {
                "domain": domain,
                "limit": 50,
                "offset": 0,
                "api_key": api_key
            }
            
            response = self.session.get(url, params=params)
            data = response.json()
            
            emails = []
            if data.get('data'):
                for email_data in data['data'].get('emails', []):
                    emails.append({
                        'email': email_data.get('value'),
                        'name': f"{email_data.get('first_name', '')} {email_data.get('last_name', '')}".strip(),
                        'title': email_data.get('position'),
                        'company': domain,
                        'country': 'Unknown',
                        'source': 'hunter.io'
                    })
            
            return emails
        except Exception as e:
            print(f"❌ Hunter.io error: {e}")
            return []

    def _build_hunter_discover_query(self, criteria: Dict) -> str:
        """Build a natural-language Hunter Discover query from the current search criteria."""
        title = str(criteria.get('title', '')).strip()
        keywords = [keyword.strip() for keyword in criteria.get('keywords', []) if keyword and keyword.strip()]
        country = normalize_country_filter(criteria.get('country')) or ''
        remote = bool(criteria.get('remote'))

        parts = []
        if title:
            parts.append(title)
        if keywords:
            parts.append(", ".join(keywords[:4]))
        if country:
            parts.append(country)
        if remote:
            parts.append("remote")

        if parts:
            return f"Companies related to {' '.join(parts)}"

        return "Software companies and developer tools"

    def _build_hunter_discover_queries(self, criteria: Dict, max_queries: int = 4) -> List[str]:
        """Build a small set of query variants so Discover can be looped safely."""
        title = str(criteria.get('title', '')).strip()
        keywords = [keyword.strip() for keyword in criteria.get('keywords', []) if keyword and keyword.strip()]
        country = normalize_country_filter(criteria.get('country'))
        remote = bool(criteria.get('remote'))

        keyword_phrase = " ".join(keywords[:4]).strip()
        query_variants: List[str] = []

        if title and keyword_phrase and country and remote:
            query_variants.append(f"{title} {keyword_phrase} {country} remote")
        if title and keyword_phrase and country:
            query_variants.append(f"{title} {keyword_phrase} {country}")
        if title and keyword_phrase and remote:
            query_variants.append(f"{title} {keyword_phrase} remote")
        if title and keyword_phrase:
            query_variants.append(f"{title} {keyword_phrase}")
        if title and country:
            query_variants.append(f"{title} {country}")
        if title and remote:
            query_variants.append(f"{title} remote")
        if title:
            query_variants.append(title)
        if keyword_phrase:
            query_variants.append(keyword_phrase)
        if country:
            query_variants.append(f"{country} companies")
        query_variants.append("Software companies and developer tools")

        deduped: List[str] = []
        seen: Set[str] = set()
        for query in query_variants:
            normalized = " ".join(query.split()).strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(normalized)
            if len(deduped) >= max_queries:
                break

        return deduped

    def search_hunter_discover(self, criteria: Dict, max_domains: int = 3) -> List[Dict]:
        """
        Use Hunter Discover to find relevant company domains, then expand each domain with Domain Search.
        """
        try:
            api_key = os.getenv('HUNTER_API_KEY')
            if not api_key:
                print("⚠️  Hunter API key not configured (HUNTER_API_KEY)")
                return []

            normalized_criteria = dict(criteria)
            normalized_criteria['country'] = normalize_country_filter(criteria.get('country'))

            queries = self._build_hunter_discover_queries(normalized_criteria)
            print(f"  🔍 Discovering companies with {len(queries)} query variant(s)")

            url = "https://api.hunter.io/v2/discover"
            discovered_domains: List[str] = []
            seen_domains: Set[str] = set()

            for index, query in enumerate(queries, start=1):
                print(f"    ↳ Discover pass {index}/{len(queries)}: {query}")
                try:
                    response = self.session.post(
                        url,
                        params={"api_key": api_key},
                        json={"query": query},
                        timeout=10,
                    )
                except Exception as exc:
                    print(f"❌ Hunter Discover error: {exc}")
                    continue

                if response.status_code != 200:
                    print(f"❌ Hunter Discover error: {response.status_code}")
                    continue

                data = response.json()
                companies = data.get("data", [])
                if isinstance(companies, dict):
                    companies = [companies]

                query_added = 0
                for company in companies:
                    domain = (company.get("domain") or "").strip()
                    if not domain or domain in seen_domains:
                        continue

                    seen_domains.add(domain)
                    discovered_domains.append(domain)
                    query_added += 1
                    if query_added >= max_domains:
                        break

                if query_added == 0:
                    print("      • No new domains from this pass")

                if index < len(queries):
                    pause_seconds = float(os.getenv("HUNTER_DISCOVER_QUERY_DELAY_SECONDS", "0.2"))
                    if pause_seconds > 0:
                        time.sleep(pause_seconds)

            if not discovered_domains:
                return []

            emails: List[Dict] = []
            for domain in discovered_domains:
                domain_emails = self.search_hunter_free(domain)
                emails.extend(domain_emails)

            return emails
        except Exception as e:
            print(f"❌ Hunter Discover error: {e}")
            return []
    
    def search_apollo_free(self, title: str, country: str = None) -> List[Dict]:
        """
        Search Apollo.io free tier using people search + enrichment.
        Free tier: limited searches (requires API key)
        """
        try:
            api_key = os.getenv('APOLLO_API_KEY')
            if not api_key:
                print("⚠️  Apollo API key not configured (APOLLO_API_KEY)")
                return []

            country = normalize_country_filter(country)

            headers = {
                "x-api-key": api_key,
                "accept": "application/json",
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
            }

            search_url = "https://api.apollo.io/api/v1/mixed_people/api_search"
            search_payload = {
                "person_titles": [title],
                "per_page": 25,
            }
            if country:
                search_payload["person_locations"] = [country]

            response = self.session.post(search_url, json=search_payload, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"❌ Apollo search error: {response.status_code}")
                return []

            data = response.json()
            people = data.get("people", []) or []
            person_ids = [person.get("id") for person in people if person.get("id")]
            if not person_ids:
                return []

            emails: List[Dict] = []
            enrich_url = "https://api.apollo.io/api/v1/people/bulk_match"
            for start in range(0, min(len(person_ids), 20), 10):
                batch_ids = person_ids[start:start + 10]
                enrich_response = self.session.post(
                    enrich_url,
                    params={"reveal_personal_emails": "true", "reveal_phone_number": "false"},
                    headers=headers,
                    json={"details": [{"id": person_id} for person_id in batch_ids]},
                    timeout=10,
                )

                if enrich_response.status_code != 200:
                    print(f"❌ Apollo enrichment error: {enrich_response.status_code}")
                    continue

                enrich_data = enrich_response.json()
                for match in enrich_data.get("matches", []):
                    email = match.get("email")
                    if not email:
                        continue

                    organization = match.get("organization") or {}
                    emails.append({
                        "email": email,
                        "name": match.get("name") or f"{match.get('first_name', '')} {match.get('last_name', '')}".strip(),
                        "title": match.get("title"),
                        "company": organization.get("name") or match.get("organization_name"),
                        "country": match.get("country"),
                        "source": "apollo.io",
                    })

            return emails
        except Exception as e:
            print(f"❌ Apollo.io error: {e}")
            return []
    
    def search_github_profiles(self, keywords: List[str], location: str = None, language: str = "javascript") -> List[Dict]:
        """
        Extract emails from GitHub public profiles
        No API key needed (public data)
        Searches for profiles matching keywords
        """
        try:
            location = normalize_country_filter(location)

            # Build search query
            query_parts = [f'"{kw}"' for kw in keywords]
            query = " ".join(query_parts)
            
            if location:
                query += f' location:{location}'
            
            # GitHub API doesn't directly return email, but we can scrape profiles
            # Alternative: use GitHub API to get public email from user bio
            print(f"  🔍 Searching GitHub for: {query}")
            
            url = "https://api.github.com/search/users"
            params = {
                "q": query,
                "sort": "repositories",
                "order": "desc",
                "per_page": 30
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            emails = []
            if data.get('items'):
                for user in data['items'][:20]:
                    try:
                        # Get individual user details
                        user_url = user.get('url')
                        user_response = self.session.get(user_url)
                        user_data = user_response.json()
                        
                        # Extract email if public
                        if user_data.get('email'):
                            emails.append({
                                'email': user_data['email'],
                                'name': user_data.get('name', user['login']),
                                'title': f"Developer ({', '.join(keywords)})",
                                'company': user_data.get('company', 'Self-Employed'),
                                'country': user_data.get('location', 'Unknown'),
                                'source': 'github.com'
                            })
                    except Exception as e:
                        continue
            
            return emails
        except Exception as e:
            print(f"❌ GitHub search error: {e}")
            return []
    
    def search_linkedinlike(self, title: str, country: str = None, remote: bool = False) -> List[Dict]:
        """
        Search similar to LinkedIn (using public data)
        This uses web scraping on public directories
        """
        try:
            print(f"  🔍 Searching professional profiles for: {title}")
            
            # Use Clearbit autocomplete as proxy (returns company employees)
            url = "https://autocomplete.clearbit.com/v1/companies"
            params = {"query": "software"}
            
            response = self.session.get(url, params=params, timeout=5)
            
            # Note: Clearbit API limited. For production, consider:
            # - LinkedIn scraping (with proper terms compliance)
            # - Email finder services
            # - Professional directory scraping
            
            return []
        except Exception as e:
            print(f"❌ LinkedIn search error: {e}")
            return []
    
    def search_kaggle_datasets(self) -> List[Dict]:
        """
        Get emails from public Kaggle datasets
        Searches for datasets with job/contact data
        """
        try:
            print("  🔍 Checking Kaggle datasets...")
            
            # Popular datasets:
            # - "Email addresses"
            # - "LinkedIn profiles"
            # - "Developer emails"
            # - "IT professionals"
            
            datasets = [
                {
                    'name': 'Email Addresses',
                    'description': 'Many tech professionals'
                },
                {
                    'name': 'Developer Profiles',
                    'description': 'GitHub, Stack Overflow exports'
                }
            ]
            
            print("  📊 Available Kaggle datasets:")
            for ds in datasets:
                print(f"      - {ds['name']}: {ds['description']}")
                print(f"        → Download from: https://www.kaggle.com/search?q={ds['name']}")
            
            return []
        except Exception as e:
            print(f"❌ Kaggle error: {e}")
            return []
    
    def search_all_sources(
        self,
        criteria: Dict,
        limit: int = 100,
        store_results: bool = False,
    ) -> Tuple[int, List[Dict]]:
        """
        Search all available sources based on criteria
        
        Criteria example:
        {
            'title': 'junior frontend developer',
            'keywords': ['react', 'javascript', 'remote'],
            'country': 'USA',
            'remote': True
        }
        """
        normalized_criteria = dict(criteria)
        normalized_criteria['country'] = normalize_country_filter(criteria.get('country'))

        all_emails = []
        
        display_criteria = dict(normalized_criteria)
        display_criteria['country'] = display_criteria.get('country') or 'Worldwide'

        print(f"\n🚀 Starting automated email extraction...")
        print(f"📋 Criteria: {display_criteria}")
        print("-" * 60)
        
        # 1. GitHub Search (Free, no key needed)
        print("\n1️⃣  GitHub Profiles")
        keywords = normalized_criteria.get('keywords', ['developer'])
        location = normalized_criteria.get('country')
        github_emails = self.search_github_profiles(
            keywords=keywords,
            location=location
        )
        all_emails.extend(github_emails)
        print(f"   ✓ Found {len(github_emails)} from GitHub")
        
        # 2. Hunter.io (Limited free tier)
        if os.getenv('HUNTER_API_KEY'):
            print("\n2️⃣  Hunter.io")
            hunter_emails = self.search_hunter_discover(normalized_criteria)
            if not hunter_emails:
                # Keep the older fallback path if Discover returns nothing.
                tech_domains = ['github.com', 'gitlab.com', 'stackoverflow.com']
                for domain in tech_domains[:2]:
                    hunter_emails.extend(self.search_hunter_free(domain))
            all_emails.extend(hunter_emails)
            print(f"   ✓ Found {len(hunter_emails)} from Hunter.io")
        
        # 3. Apollo.io (Limited free tier)
        if os.getenv('APOLLO_API_KEY'):
            print("\n3️⃣  Apollo.io")
            apollo_emails = self.search_apollo_free(
                title=normalized_criteria.get('title', 'developer'),
                country=normalized_criteria.get('country')
            )
            all_emails.extend(apollo_emails)
            print(f"   ✓ Found {len(apollo_emails)} from Apollo.io")
        
        # 4. Kaggle Datasets (Info only)
        print("\n4️⃣  Kaggle Datasets")
        self.search_kaggle_datasets()
        
        # Remove duplicates
        unique_emails = {}
        for email_data in all_emails:
            if email_data.get('email'):
                email = email_data['email'].lower()
                if email not in unique_emails:
                    unique_emails[email] = email_data
        
        unique_list = list(unique_emails.values())
        
        valid_list, validation_failures = self._validate_email_results(unique_list)

        print("\n" + "-" * 60)
        print(f"✓ Total unique emails found: {len(unique_list)}")
        print(f"✓ Validated emails ready: {len(valid_list)}")
        if validation_failures:
            print(f"✗ Rejected during validation: {len(validation_failures)}")
        if not valid_list:
            print("ℹ️  No validated emails were returned from the current live sources.")
            for hint in self._no_results_hints(normalized_criteria):
                print(f"   - {hint}")
        
        stored = 0
        if store_results:
            stored, failed = self._store_emails(valid_list, skip_validation=True)
            print(f"✓ Stored in database: {stored}")
            if failed:
                print(f"✗ Failed to store: {len(failed)}")
        else:
            print("✓ Local database writes: disabled for internet extraction")
        
        if limit is not None and limit > 0:
            return stored, valid_list[:limit]
        return stored, valid_list
    
    def _store_emails(self, emails: List[Dict], skip_validation: bool = False) -> Tuple[int, List[str]]:
        """Store extracted emails in database"""
        from python_engine.database_manager import DatabaseManager

        DatabaseManager(self.db_path).initialize_database()
        validator = None if skip_validation else self._build_validator()

        stored = 0
        failed = []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for email_data in emails:
            email = email_data.get('email', '').lower()
            
            if not email:
                continue

            if validator is not None:
                is_valid, reason = validator.is_valid_email(email)
                if not is_valid:
                    failed.append(f"{email}: {reason}")
                    continue
            
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO contacts 
                    (email, name, title, company, country, source, data_source, sent, consent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)
                """, (
                    email,
                    email_data.get('name', 'Unknown'),
                    email_data.get('title'),
                    email_data.get('company'),
                    email_data.get('country'),
                    email_data.get('source'),
                    email_data.get('source'),
                ))
                if cursor.rowcount > 0:
                    stored += 1
            except Exception as e:
                failed.append(f"{email}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return stored, failed
    
    def search_with_filters(self, criteria: Dict, store_results: bool = False) -> Tuple[int, List[Dict]]:
        """
        Search and automatically filter results by criteria
        Returns pre-filtered emails matching all criteria
        """
        from python_engine.contact_filters import ProfileMatcher
        
        # First search
        normalized_criteria = dict(criteria)
        normalized_criteria['country'] = normalize_country_filter(criteria.get('country'))

        _, emails = self.search_all_sources(normalized_criteria, store_results=False)
        
        # Then filter by requirements
        print(f"\n🔍 Applying filters...")
        matcher = ProfileMatcher()
        
        filtered = []
        for email_data in emails:
            scores = matcher.score_profile(email_data)
            
            # Check if matches criteria
            if scores.get('junior_developer', 0) >= 60:
                if scores.get('frontend_developer', 0) >= 50:
                    if criteria.get('remote') and scores.get('remote_capable', 0) >= 40:
                        filtered.append({**email_data, 'scores': scores})
                    elif not criteria.get('remote'):
                        filtered.append({**email_data, 'scores': scores})
        
        print(f"✓ Filtered to {len(filtered)} matching profiles")

        stored = 0
        if store_results:
            stored, failed = self._store_emails(filtered, skip_validation=True)
            print(f"✓ Stored filtered matches: {stored}")
            if failed:
                print(f"✗ Failed to store filtered matches: {len(failed)}")
        
        return stored, filtered


def search_emails_interactive():
    """Interactive email search based on user input"""
    print("\n🎯 What type of professionals are you looking for?")
    print("-" * 60)
    
    # Get criteria
    title = input("Job title (e.g., 'junior frontend developer'): ").strip()
    keywords_str = input("Keywords (comma-separated, e.g., 'react,javascript,remote'): ").strip()
    country = input("Country (optional, e.g., 'USA', 'Canada'): ").strip() or None
    remote = input("Remote jobs only? (y/n): ").strip().lower() == 'y'
    
    keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
    
    criteria = {
        'title': title,
        'keywords': keywords,
        'country': country,
        'remote': remote
    }
    
    # Extract
    extractor = AutoEmailExtractor()
    results = extractor.search_with_filters(criteria)
    
    # Show results
    print(f"\n📧 Found {len(results)} filtered results:")
    print("-" * 60)
    for i, email_data in enumerate(results[:10], 1):
        print(f"{i}. {email_data.get('name')} ({email_data.get('title')})")
        print(f"   Email: {email_data.get('email')}")
        print(f"   Company: {email_data.get('company')}")
        print()


if __name__ == '__main__':
    search_emails_interactive()

#!/usr/bin/env python3
"""
Automated Email Extraction from Internet Sources
Searches specific requirements (IT jobs, remote, junior, etc) across free sources
"""
import os
import re
import json
import requests
import sqlite3
from typing import List, Dict, Set, Tuple
from urllib.parse import urlencode
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class AutoEmailExtractor:
    """Automatically extract emails from internet sources with specific criteria"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.getenv('DATABASE_PATH', './database/devnav.db')
        self.session = requests.Session()
        self.session.timeout = 10
        
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
    
    def search_apollo_free(self, title: str, country: str = None) -> List[Dict]:
        """
        Search Apollo.io free tier
        Free tier: limited searches (requires API key)
        """
        try:
            api_key = os.getenv('APOLLO_API_KEY')
            if not api_key:
                print("⚠️  Apollo API key not configured (APOLLO_API_KEY)")
                return []
            
            url = "https://api.apollo.io/v1/mixed_companies"
            
            filters = {
                "title": title,
            }
            if country:
                filters["country_name"] = country
            
            headers = {"Content-Type": "application/json"}
            payload = {
                "filters": filters,
                "limit": 100,
                "api_key": api_key
            }
            
            response = self.session.post(url, json=payload, headers=headers)
            data = response.json()
            
            emails = []
            if data.get('contacts'):
                for contact in data['contacts'][:50]:
                    emails.append({
                        'email': contact.get('email'),
                        'name': f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
                        'title': contact.get('title'),
                        'company': contact.get('company_name'),
                        'country': contact.get('country'),
                        'source': 'apollo.io'
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
    
    def search_all_sources(self, criteria: Dict, limit: int = 100) -> Tuple[int, List[Dict]]:
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
        all_emails = []
        
        print(f"\n🚀 Starting automated email extraction...")
        print(f"📋 Criteria: {criteria}")
        print("-" * 60)
        
        # 1. GitHub Search (Free, no key needed)
        print("\n1️⃣  GitHub Profiles")
        keywords = criteria.get('keywords', ['developer'])
        location = criteria.get('country')
        github_emails = self.search_github_profiles(
            keywords=keywords,
            location=location
        )
        all_emails.extend(github_emails)
        print(f"   ✓ Found {len(github_emails)} from GitHub")
        
        # 2. Hunter.io (Limited free tier)
        if os.getenv('HUNTER_API_KEY'):
            print("\n2️⃣  Hunter.io")
            # Search common tech company domains
            tech_domains = ['github.com', 'gitlab.com', 'stackoverflow.com']
            for domain in tech_domains[:2]:
                hunter_emails = self.search_hunter_free(domain)
                all_emails.extend(hunter_emails)
            print(f"   ✓ Found {len(hunter_emails)} from Hunter.io")
        
        # 3. Apollo.io (Limited free tier)
        if os.getenv('APOLLO_API_KEY'):
            print("\n3️⃣  Apollo.io")
            apollo_emails = self.search_apollo_free(
                title=criteria.get('title', 'developer'),
                country=criteria.get('country')
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
        
        print("\n" + "-" * 60)
        print(f"✓ Total unique emails found: {len(unique_list)}")
        
        # Store in database
        stored, failed = self._store_emails(unique_list)
        
        print(f"✓ Stored in database: {stored}")
        if failed:
            print(f"✗ Failed to store: {len(failed)}")
        
        return stored, unique_list[:limit]
    
    def _store_emails(self, emails: List[Dict]) -> Tuple[int, List[str]]:
        """Store extracted emails in database"""
        stored = 0
        failed = []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for email_data in emails:
            email = email_data.get('email', '').lower()
            
            if not email or '@' not in email:
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
                stored += 1
            except Exception as e:
                failed.append(f"{email}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return stored, failed
    
    def search_with_filters(self, criteria: Dict) -> List[Dict]:
        """
        Search and automatically filter results by criteria
        Returns pre-filtered emails matching all criteria
        """
        from python_engine.contact_filters import ProfileMatcher
        
        # First search
        stored, emails = self.search_all_sources(criteria)
        
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
        
        return filtered


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

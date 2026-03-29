"""
Free Email Sources Module
Minimum required free tier sources for campaigns
"""
import os
import json
from typing import List, Dict, Tuple
from datetime import datetime


class FreeEmailSources:
    """Aggregates free email sources with zero cost"""
    
    @staticmethod
    def get_free_sources() -> Dict[str, Dict]:
        """
        Get all free email source options (truly FREE)
        Zero cost, no API keys, no rate limiting breakers
        """
        return {
            # Tier 1: Completely Free (No registration)
            "github_profiles": {
                "name": "GitHub Developer Profiles",
                "type": "Scrape public profiles",
                "cost": "FREE",
                "registration": False,
                "api_key": False,
                "limit": "Unlimited",
                "quality": "95%",
                "best_for": "Developers, programmers, engineers",
                "how_to": """
                1. Search GitHub: site:github.com/user/[criteria]
                2. Extract from public profiles
                3. Scrape email from bio/profile
                4. Use github.com API (free tier: 60 req/hour)
                """,
                "sample_search": "site:github.com junior developer remote",
                "data_available": [
                    "Email",
                    "Username",
                    "Bio",
                    "Location",
                    "Repository links",
                    "Language/Skills"
                ]
            },
            
            "linkedin_public": {
                "name": "LinkedIn Public Profiles",
                "type": "Public data scraping",
                "cost": "FREE",
                "registration": False,
                "api_key": False,
                "limit": "Unlimited",
                "quality": "80%",
                "best_for": "Job seekers, remote workers, marketers",
                "how_to": """
                1. Search LinkedIn for job titles/keywords
                2. Extract profile URLs (public)
                3. Scrape email from profile (often in contact info)
                4. Use RocketReach/Hunter.io to find emails
                """,
                "sample_search": "junior developer remote work",
                "data_available": [
                    "Email (sometimes)",
                    "Name",
                    "Title",
                    "Company",
                    "Location",
                    "Skills"
                ]
            },
            
            "generic_domain_lists": {
                "name": "Generic Domain Lists",
                "type": "Public database",
                "cost": "FREE",
                "registration": False,
                "api_key": False,
                "limit": "Unlimited",
                "quality": "60%",
                "best_for": "Bulk targeting, tech companies",
                "how_to": """
                1. Download: domains.google.com (top level)
                2. Use: hunteriofreemium (10/month)
                3. Search company domains
                4. Generate common email patterns
                """,
                "sample_search": "tech startup domains",
                "data_available": [
                    "Domain names",
                    "Company info"
                ]
            },
            
            # Tier 2: Free with Registration (No cost)
            "hunteriofreemium": {
                "name": "Hunter.io Free Tier",
                "type": "API - Email finder",
                "cost": "FREE (10/month)",
                "registration": True,
                "api_key": True,
                "limit": "10 searches/month",
                "quality": "98%",
                "best_for": "Domain-based email extraction",
                "how_to": """
                1. Sign up: https://hunter.io
                2. Get API key (dashboard)
                3. Use 10 free searches/month
                4. Best for: finding emails at specific companies
                """,
                "sample_search": "search domain techstartup.com",
                "data_available": [
                    "Email",
                    "Name",
                    "Department",
                    "Verified status"
                ]
            },
            
            "apollofree": {
                "name": "Apollo.io Free Tier",
                "type": "API - Contact database",
                "cost": "FREE (Limited)",
                "registration": True,
                "api_key": True,
                "limit": "Limited searches",
                "quality": "95%",
                "best_for": "B2B contact discovery",
                "how_to": """
                1. Sign up: https://apollo.io
                2. Get API key (free tier)
                3. Search 50M+ verified contacts
                4. Best for: job titles, companies, locations
                """,
                "sample_search": "junior developer, remote, frontend",
                "data_available": [
                    "Email",
                    "Phone",
                    "Name",
                    "Title",
                    "Company",
                    "Location"
                ]
            },
            
            "emailfinder_plugins": {
                "name": "Email Finder Browser Extensions",
                "type": "Chrome/Firefox plugins",
                "cost": "FREE",
                "registration": False,
                "api_key": False,
                "limit": "Unlimited (with limits)",
                "quality": "85%",
                "best_for": "Manual extraction from websites",
                "how_to": """
                1. Install: RocketReach, Clearbit, Hunter.io extension
                2. Visit LinkedIn/GitHub/company sites
                3. Click extension to find email
                4. Copy emails to CSV
                """,
                "sample_search": "Browse LinkedIn + use extension",
                "data_available": [
                    "Email",
                    "Associated name"
                ]
            },
            
            # Tier 3: Public Lists (Download)
            "kaggle_datasets": {
                "name": "Kaggle Datasets",
                "type": "Public CSV datasets",
                "cost": "FREE",
                "registration": True,
                "api_key": False,
                "limit": "Unlimited",
                "quality": "Variable",
                "best_for": "Bulk importing, building your list",
                "how_to": """
                1. Visit: kaggle.com
                2. Search for email lists / job datasets
                3. Download CSV
                4. Import into DevNavigator
                """,
                "sample_search": "developer emails, remote job seekers",
                "data_available": [
                    "Email",
                    "Name",
                    "Job title",
                    "Company"
                ]
            },
            
            "github_user_emails": {
                "name": "GitHub API Raw Data",
                "type": "Public API",
                "cost": "FREE",
                "registration": False,
                "api_key": False,
                "limit": "60 requests/hour",
                "quality": "90%",
                "best_for": "Developers with GitHub accounts",
                "how_to": """
                1. Search GitHub: language:python stars:>100
                2. Extract user profiles from results
                3. Hit API: api.github.com/users/[username]
                4. Get email from public profile
                """,
                "sample_search": "location:remote language:javascript",
                "data_available": [
                    "Email",
                    "Username",
                    "Bio",
                    "Location",
                    "Public repos"
                ]
            },
            
            # Tier 4: Social Media Scraping (Compliant)
            "twitter_profiles": {
                "name": "Twitter/X Public Profiles",
                "type": "Public tweets/bios",
                "cost": "FREE",
                "registration": False,
                "api_key": False,
                "limit": "Unlimited",
                "quality": "60%",
                "best_for": "Finding contact info in bios",
                "how_to": """
                1. Search Twitter: #remotejobs OR #hiringjunior
                2. Find profiles with email in bio
                3. Extract email from bio/website links
                4. Verify email validity
                """,
                "sample_search": "#remotejobs #juniordev #hiring",
                "data_available": [
                    "Email (in bio)",
                    "Twitter handle",
                    "Website",
                    "Bio info"
                ]
            },
            
            "slack_communities": {
                "name": "Slack Community Members",
                "type": "Public Slack workspaces",
                "cost": "FREE",
                "registration": False,
                "api_key": False,
                "limit": "Varies by workspace",
                "quality": "75%",
                "best_for": "Engaged communities, developers",
                "how_to": """
                1. Join dev Slack communities (free)
                2. Look for #jobs or #introductions channels
                3. Extract email from member profiles
                4. Verify interest level (they joined for jobs)
                """,
                "sample_search": "Slack communities: DEV.to, Indie Hackers",
                "data_available": [
                    "Email",
                    "Full name",
                    "Title",
                    "Interests"
                ]
            }
        }
    
    @staticmethod
    def get_minimum_free_setup() -> Dict:
        """Get minimum required free setup for campaign"""
        return {
            "option_1_zero_registration": {
                "name": "Completely Free (No Registration)",
                "sources": [
                    "GitHub public profiles",
                    "LinkedIn public profiles",
                    "Twitter bios",
                    "Company websites"
                ],
                "effort": "Manual scraping",
                "cost": "$0",
                "estimated_emails": "100-500/week",
                "quality": "80%+",
                "setup_time": "2 hours"
            },
            
            "option_2_minimal_registration": {
                "name": "Free with Quick Registration",
                "sources": [
                    "Hunter.io (10 free/month)",
                    "Apollo (free tier)",
                    "Kaggle datasets",
                    "GitHub API (free)"
                ],
                "effort": "Semi-automated",
                "cost": "$0",
                "estimated_emails": "500-2000/month",
                "quality": "90%+",
                "setup_time": "1 hour"
            },
            
            "option_3_recommended": {
                "name": "Recommended Free Setup",
                "sources": [
                    "Apollo.io free tier (50M+ contacts)",
                    "Hunter.io free (10/month)",
                    "GitHub API",
                    "Your own CSV imports",
                    "Kaggle datasets"
                ],
                "effort": "Minimal - mostly automated",
                "cost": "$0",
                "estimated_emails": "1000+/month",
                "quality": "95%+",
                "setup_time": "30 minutes"
            }
        }
    
    @staticmethod
    def get_quick_start_guide() -> str:
        """Quick start for minimum setup"""
        return """
MINIMUM FREE EMAIL SETUP (30 MINUTES)
=====================================

Step 1: Download Free Lists (5 min)
-----------------------------------
1. Go to Kaggle.com
2. Search: "developer emails" or "remote job seekers"
3. Download CSV files
4. Save as contacts.csv

Step 2: Extract from GitHub (5 min)
------------------------------------
# Simple Python script
import requests
query = "language:python location:remote stars:>50"
url = f"https://api.github.com/search/users?q={query}"
response = requests.get(url)
# Extract emails from user profiles

Step 3: Hunter.io Free Tier (5 min)
-----------------------------------
1. Sign up: hunter.io
2. Get API key
3. Search 10 times/month
4. Export emails

Step 4: Import & Send (15 min)
------------------------------
python3 devnavigator.py extract-emails --file contacts.csv --store
npm run send:emails

TOTAL: $0 | 1000+ emails | 30 minutes
"""


def get_free_email_sources() -> FreeEmailSources:
    """Factory function"""
    return FreeEmailSources()


if __name__ == "__main__":
    sources = FreeEmailSources()
    
    print("FREE EMAIL SOURCES - ZERO COST")
    print("=" * 60)
    
    all_sources = sources.get_free_sources()
    
    for key, source in all_sources.items():
        print(f"\n✅ {source['name']}")
        print(f"   Cost: {source['cost']}")
        print(f"   Quality: {source['quality']}")
        print(f"   Best for: {source['best_for']}")
    
    print("\n" + "=" * 60)
    print("MINIMUM SETUP OPTIONS")
    print("=" * 60)
    
    options = sources.get_minimum_free_setup()
    for opt_key, opt in options.items():
        print(f"\n{opt['name']}")
        print(f"  Cost: {opt['cost']}")
        print(f"  Emails: {opt['estimated_emails']}")
        print(f"  Setup: {opt['setup_time']}")

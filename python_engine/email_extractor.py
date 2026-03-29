"""
Email Extractor Module
Extracts emails from various sources and validates them
"""
import re
import sqlite3
import os
import hashlib
from typing import List, Set, Tuple
from urllib.parse import urlparse
import json


class EmailValidator:
    """Validates emails for authenticity and security"""
    
    def __init__(self, enable_virus_check: bool = True, enable_source_verification: bool = True):
        self.enable_virus_check = enable_virus_check
        self.enable_source_verification = enable_source_verification
        self.suspicious_domains = self._load_suspicious_domains()
        
    def _load_suspicious_domains(self) -> Set[str]:
        """Load list of suspicious domains to block"""
        return {
            'tempmail.com', 'throwaway.email', '10minutemail.com',
            'guerrillamail.com', 'mailinator.com', 'temp-mail.org'
        }
    
    def is_valid_email(self, email: str) -> Tuple[bool, str]:
        """
        Validate email format and check for suspicious patterns
        Returns: (is_valid, reason)
        """
        if not email or not isinstance(email, str):
            return False, "Invalid email type"
        
        email = email.strip().lower()
        
        # Basic RFC 5322 validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        # Check for suspicious domains
        domain = email.split('@')[1]
        if domain in self.suspicious_domains:
            return False, f"Suspicious domain: {domain}"
        
        # Check for common spam patterns
        if '+' in email.split('@')[0]:
            # Gmail alias - flag but allow if configured
            if not os.getenv('ALLOW_GMAIL_ALIASES', 'false').lower() == 'true':
                return False, "Gmail alias detected (potential spam)"
        
        if self.enable_source_verification:
            is_genuine, reason = self._verify_source_genuinely(email)
            if not is_genuine:
                return False, f"Source verification failed: {reason}"
        
        return True, "Valid"
    
    def _verify_source_genuinely(self, email: str) -> Tuple[bool, str]:
        """
        Attempt to verify if email source is genuine
        In production, this would check MX records, DNS verification, etc.
        """
        try:
            domain = email.split('@')[1]
            # Check if domain has MX records (simplified check)
            # In production, use dnspython library
            if domain.count('.') < 1:
                return False, "Invalid domain structure"
            return True, "Verified"
        except Exception as e:
            return False, str(e)


class EmailExtractor:
    """Extracts emails from various sources"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.validator = EmailValidator(
            enable_virus_check=os.getenv('ENABLE_VIRUS_CHECK', 'true').lower() == 'true',
            enable_source_verification=os.getenv('ENABLE_SOURCE_VERIFICATION', 'true').lower() == 'true'
        )
        
    def extract_from_text(self, text: str) -> Set[str]:
        """Extract all emails from text"""
        pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        emails = set(re.findall(pattern, text))
        return emails
    
    def extract_from_file(self, file_path: str) -> Set[str]:
        """Extract emails from a file (txt, csv, etc)"""
        emails = set()
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                emails = self.extract_from_text(content)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
        return emails
    
    def extract_from_json_list(self, json_data: str) -> Set[str]:
        """Extract emails from JSON data"""
        emails = set()
        try:
            data = json.loads(json_data)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'email' in item:
                        emails.add(item['email'])
                    elif isinstance(item, str):
                        extracted = self.extract_from_text(item)
                        emails.update(extracted)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
        return emails
    
    def validate_and_store(self, emails: Set[str], source: str = "manual") -> Tuple[int, List[str]]:
        """
        Validate emails and store in database
        Returns: (stored_count, failed_emails)
        """
        stored_count = 0
        failed_emails = []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for email in emails:
            is_valid, reason = self.validator.is_valid_email(email)
            
            if not is_valid:
                failed_emails.append(f"{email}: {reason}")
                continue
            
            try:
                # Check if email already in database
                cursor.execute("SELECT id FROM contacts WHERE email = ?", (email,))
                existing = cursor.fetchone()
                
                if not existing:
                    cursor.execute("""
                        INSERT INTO contacts (email, source, consent, sent)
                        VALUES (?, ?, 0, 0)
                    """, (email, source))
                    stored_count += 1
                    print(f"✓ Stored: {email}")
                else:
                    print(f"~ Already exists: {email}")
            except sqlite3.IntegrityError:
                failed_emails.append(f"{email}: Duplicate entry")
            except Exception as e:
                failed_emails.append(f"{email}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return stored_count, failed_emails


def get_email_extractor(db_path: str = None) -> EmailExtractor:
    """Factory function to get email extractor"""
    if db_path is None:
        db_path = os.getenv('DATABASE_PATH', './database/devnav.db')
    return EmailExtractor(db_path)

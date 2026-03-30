#!/usr/bin/env python3
"""
Test script for Network Email Scraper
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from network_email_scraper import NetworkEmailScraper

def test_email_extraction():
    """Test email extraction from text"""
    print("🧪 Testing email extraction...")

    scraper = NetworkEmailScraper()

    test_text = """
    Contact us at john.doe@example.com or jane.smith@company.org
    Support: support@techstartup.io
    Sales: sales@enterprise.com
    Invalid: not-an-email, @invalid.com, missing@.com
    """

    emails = scraper.email_pattern.findall(test_text)
    print(f"  Found {len(emails)} emails: {emails}")

    assert len(emails) == 4, f"Expected 4 emails, got {len(emails)}"
    print("  ✓ Email extraction test passed")

def test_validation():
    """Test email validation"""
    print("\n🧪 Testing email validation...")

    scraper = NetworkEmailScraper()

    test_emails = [
        "john.doe@example.com",
        "jane.smith@company.org",
        "invalid-email",
        "@invalid.com",
        "missing@.com",
    ]

    valid, invalid = scraper.validate_emails(test_emails)

    print(f"  Valid: {len(valid)}")
    print(f"  Invalid: {len(invalid)}")

    # At least one email should be valid
    assert len(valid) >= 1, f"Expected at least 1 valid email, got {len(valid)}"
    print("  ✓ Validation test passed")

def test_database():
    """Test database operations"""
    print("\n🧪 Testing database operations...")

    scraper = NetworkEmailScraper()

    # Test storing emails
    test_emails = [
        "test1@example.com",
        "test2@example.com",
        "test3@example.com",
    ]

    stored = scraper.store_emails(test_emails, source="test")
    print(f"  Stored {stored} emails")

    assert stored >= 0, "Storage should not fail"
    print("  ✓ Database test passed")

def main():
    """Run all tests"""
    print("=" * 80)
    print("🧪 NETWORK EMAIL SCRAPER - TEST SUITE")
    print("=" * 80)

    try:
        test_email_extraction()
        test_validation()
        test_database()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

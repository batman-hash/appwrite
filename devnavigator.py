#!/usr/bin/env python3
"""
DevNavigator Main CLI
Orchestrates email extraction, validation, and campaign sending
"""
import os
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from python_engine.email_extractor import get_email_extractor
from python_engine.database_manager import DatabaseManager
from python_engine.template_manager import TemplateManager
from dotenv import load_dotenv


def setup_environment():
    """Load environment variables"""
    load_dotenv()


def cmd_init_db(args):
    """Initialize database"""
    manager = DatabaseManager()
    manager.initialize_database()
    manager.insert_default_template()
    print(f"\n📊 Database Stats:")
    print(f"   Total contacts: {manager.get_contact_count()}")
    print(f"   Unsent emails: {manager.get_unsent_count()}")


def cmd_extract_emails(args):
    """Extract emails from file or text"""
    extractor = get_email_extractor()
    
    if args.file:
        print(f"📂 Extracting emails from: {args.file}")
        emails = extractor.extract_from_file(args.file)
    elif args.text:
        print(f"📝 Extracting emails from text...")
        emails = extractor.extract_from_text(args.text)
    else:
        print("❌ Please provide --file or --text")
        return
    
    print(f"📧 Found {len(emails)} email(s)")
    
    if emails and args.store:
        stored, failed = extractor.validate_and_store(emails, source=args.source)
        print(f"\n✓ Stored: {stored}")
        if failed:
            print(f"✗ Failed: {len(failed)}")
            for fail in failed[:5]:
                print(f"   - {fail}")


def cmd_list_templates(args):
    """List all email templates"""
    manager = TemplateManager()
    templates = manager.get_all_templates()
    
    print("\n📋 Email Templates:")
    print("-" * 60)
    for template in templates:
        marker = "⭐" if template['is_default'] else "  "
        print(f"{marker} [{template['id']}] {template['name']}")
        print(f"    Subject: {template['subject'][:50]}...")
    print("-" * 60)


def cmd_add_template(args):
    """Add a new email template"""
    manager = TemplateManager()
    
    print("📝 Creating new email template...")
    name = args.name or input("Template name: ")
    subject = args.subject or input("Subject: ")
    
    print("Body (press CTRL+D when done):")
    body = sys.stdin.read()
    
    manager.add_template(name, subject, body, is_default=args.default)


def cmd_stats(args):
    """Show campaign statistics"""
    manager = DatabaseManager()
    
    print("\n📊 Campaign Statistics:")
    print("-" * 40)
    print(f"Total contacts:    {manager.get_contact_count()}")
    print(f"Ready to send:      {manager.get_unsent_count()}")
    print("-" * 40)


def main():
    """Main CLI entry point"""
    setup_environment()
    
    parser = argparse.ArgumentParser(
        description='DevNavigator - Email Campaign Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize database
  python devnavigator.py init-db
  
  # Extract emails from file
  python devnavigator.py extract-emails --file emails.txt --store
  
  # List templates
  python devnavigator.py list-templates
  
  # Show statistics
  python devnavigator.py stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Init DB command
    subparsers.add_parser('init-db', help='Initialize database')
    
    # Extract emails command
    extract_parser = subparsers.add_parser('extract-emails', help='Extract emails from source')
    extract_parser.add_argument('--file', help='File to extract from')
    extract_parser.add_argument('--text', help='Text to extract from')
    extract_parser.add_argument('--store', action='store_true', help='Store in database')
    extract_parser.add_argument('--source', default='manual', help='Source name')
    
    # List templates command
    subparsers.add_parser('list-templates', help='List all templates')
    
    # Add template command
    add_template_parser = subparsers.add_parser('add-template', help='Add new template')
    add_template_parser.add_argument('--name', help='Template name')
    add_template_parser.add_argument('--subject', help='Email subject')
    add_template_parser.add_argument('--default', action='store_true', help='Set as default')
    
    # Stats command
    subparsers.add_parser('stats', help='Show campaign statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Route commands
    if args.command == 'init-db':
        cmd_init_db(args)
    elif args.command == 'extract-emails':
        cmd_extract_emails(args)
    elif args.command == 'list-templates':
        cmd_list_templates(args)
    elif args.command == 'add-template':
        cmd_add_template(args)
    elif args.command == 'stats':
        cmd_stats(args)


if __name__ == '__main__':
    main()

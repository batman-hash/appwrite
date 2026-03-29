#!/usr/bin/env python3
"""
DevNavigator Main CLI
Orchestrates email extraction, validation, and campaign sending
"""
import os
import sys
import argparse
import sqlite3
from pathlib import Path
from typing import List, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from python_engine.email_extractor import EmailValidator, get_email_extractor
from python_engine.database_manager import DatabaseManager
from python_engine.template_manager import TemplateManager
from python_engine.auto_email_extractor import AutoEmailExtractor
from send_test_emails import EMAIL_ALIASES, EmailSender, EmailTemplateManager
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
    summary = manager.get_queue_summary()
    
    print("\n📊 Campaign Statistics:")
    print("-" * 40)
    print(f"Total contacts:    {summary['total_contacts']}")
    print(f"Ready to send:     {summary['ready_to_send']}")
    print(f"Needs review:      {summary['needs_review']}")
    print(f"Recently imported: {summary['recent_imports']}")
    print(f"Sent:              {summary['sent_count']}")
    print(f"Bounced:           {summary['bounced_count']}")
    print(f"Unsubscribed:      {summary['unsubscribed_count']}")
    print(f"Archived:          {summary['archived_count']}")
    print("-" * 40)


def cmd_queue(args):
    """Show the current send queue with filters."""
    manager = DatabaseManager()
    summary = manager.get_queue_summary(recent_hours=args.recent_hours)
    contacts = manager.get_contacts(
        queue=args.queue,
        limit=args.limit,
        source=args.source,
        recent_hours=args.recent_hours,
    )

    print("\n📬 Send Queue Overview:")
    print("-" * 72)
    print(f"Total contacts:    {summary['total_contacts']}")
    print(f"Ready to send:     {summary['ready_to_send']}")
    print(f"Needs review:      {summary['needs_review']}")
    print(f"Recently imported: {summary['recent_imports']} (last {args.recent_hours}h)")
    print(f"Archived:          {summary['archived_count']}")
    print("-" * 72)

    if not contacts:
        print("No contacts matched this view.")
        return

    print(f"\nShowing {len(contacts)} contact(s) from queue='{args.queue}':\n")
    for contact in contacts:
        source = contact['source'] or 'manual'
        created = contact['created_at'] or 'N/A'
        print(f"- {contact['email']}")
        print(f"  Status: {contact['queue_status']} | Consent: {'Yes' if contact['consent'] else 'No'} | Source: {source}")
        print(f"  Company: {contact['company'] or 'N/A'} | Country: {contact['country'] or 'N/A'} | Added: {created}")


def cmd_archive_contacts(args):
    """Archive contacts so they disappear from active queue views."""
    manager = DatabaseManager()

    if args.sent:
        archived = manager.archive_contacts(sent_only=True)
        label = "sent contacts"
    elif args.all:
        archived = manager.archive_contacts(all_active=True)
        label = "active contacts"
    elif args.emails:
        emails = [email.strip() for email in args.emails.split(',') if email.strip()]
        archived = manager.archive_contacts(emails=emails)
        label = "selected contacts"
    else:
        print("❌ Choose one of: --sent, --all, or --emails")
        return

    summary = manager.get_queue_summary()
    print(f"\n🗄️ Archived {archived} {label}.")
    print(f"Active contacts: {summary['total_contacts']}")
    print(f"Archived:        {summary['archived_count']}")


def cmd_unarchive_contacts(args):
    """Restore archived contacts back into active queue views."""
    manager = DatabaseManager()

    if args.all:
        restored = manager.unarchive_contacts(all_archived=True)
        label = "archived contacts"
    elif args.emails:
        emails = [email.strip() for email in args.emails.split(',') if email.strip()]
        restored = manager.unarchive_contacts(emails=emails)
        label = "selected contacts"
    else:
        print("❌ Choose one of: --all or --emails")
        return

    summary = manager.get_queue_summary()
    print(f"\n📂 Restored {restored} {label}.")
    print(f"Active contacts: {summary['total_contacts']}")
    print(f"Archived:        {summary['archived_count']}")


def cmd_approve_recent_contacts(args):
    """Approve the newest review contacts so send-new can target them."""
    manager = DatabaseManager()
    approved = manager.approve_recent_contacts(limit=args.limit, recent_hours=args.recent_hours)
    summary = manager.get_queue_summary(recent_hours=args.recent_hours or 24)

    print(f"\n✅ Approved {approved} recent contact(s).")
    print(f"Ready to send: {summary['ready_to_send']}")
    print(f"Needs review:  {summary['needs_review']}")


def cmd_import_contacts(args):
    """Import a local leads file into the database."""
    manager = DatabaseManager()
    imported, duplicates, errors = manager.import_contacts_file(
        file_path=args.file,
        source=args.source,
        consent=1 if args.consent else 0,
    )

    print(f"\n📥 Import results for: {args.file}")
    print("-" * 40)
    print(f"Imported:   {imported}")
    print(f"Duplicates: {duplicates}")
    print(f"Consent:    {'approved/sendable' if args.consent else 'review required'}")
    if errors:
        print(f"Errors:     {len(errors)}")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")

    summary = manager.get_queue_summary()
    print("\nUpdated queue:")
    print(f"  Ready to send: {summary['ready_to_send']}")
    print(f"  Needs review:  {summary['needs_review']}")


def _collect_new_importable_emails(manager: DatabaseManager, file_path: str) -> Tuple[List[str], List[str]]:
    """Return valid emails from the file that are not already stored in the database."""
    path = Path(file_path)
    if not path.exists():
        return [], [f"File not found: {path}"]

    contacts = manager._load_contacts_from_file(path)
    if not contacts:
        return [], ["No valid contacts found in file"]

    validator = EmailValidator(
        enable_virus_check=os.getenv('ENABLE_VIRUS_CHECK', 'true').lower() == 'true',
        enable_source_verification=os.getenv('ENABLE_SOURCE_VERIFICATION', 'true').lower() == 'true',
    )

    candidate_emails: List[str] = []
    errors: List[str] = []
    seen = set()

    for contact in contacts:
        email = contact.get('email', '').strip().lower()
        if not email or email in seen:
            continue

        is_valid, reason = validator.is_valid_email(email)
        if not is_valid:
            errors.append(f"{email}: {reason}")
            continue

        candidate_emails.append(email)
        seen.add(email)

    if not candidate_emails:
        if not errors:
            errors.append("No valid contacts found in file")
        return [], errors

    conn = sqlite3.connect(manager.db_path)
    cursor = conn.cursor()
    placeholders = ','.join(['?' for _ in candidate_emails])
    cursor.execute(
        f"SELECT email FROM contacts WHERE email IN ({placeholders})",
        candidate_emails,
    )
    existing_emails = {row[0] for row in cursor.fetchall()}
    conn.close()

    importable_emails = [email for email in candidate_emails if email not in existing_emails]
    return importable_emails, errors


def cmd_import_send_approved(args):
    """Import approved contacts from a file and immediately send only those new contacts."""
    manager = DatabaseManager()
    importable_emails, preflight_errors = _collect_new_importable_emails(manager, args.file)

    imported, duplicates, errors = manager.import_contacts_file(
        file_path=args.file,
        source=args.source,
        consent=1,
    )

    print(f"\n📥 Import + Send results for: {args.file}")
    print("-" * 48)
    print(f"Imported new: {imported}")
    print(f"Duplicates:   {duplicates}")
    if errors:
        print(f"Import errors: {len(errors)}")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    elif preflight_errors:
        print(f"Preflight notes: {len(preflight_errors)}")
        for error in preflight_errors[:10]:
            print(f"  - {error}")
        if len(preflight_errors) > 10:
            print(f"  ... and {len(preflight_errors) - 10} more")

    send_emails = importable_emails[:args.limit] if args.limit else importable_emails
    if imported != len(importable_emails):
        send_emails = send_emails[:imported]

    if not send_emails:
        print("\nℹ️  No newly imported approved contacts were available to send.")
        print("    Only brand new emails from this file are included in this one-step send flow.")
        return

    template_manager = EmailTemplateManager()
    template_name = args.template or template_manager.get_default_template_name()
    if not template_name:
        print("\n❌ No default template is configured.")
        return

    subject, body = template_manager.get_template(template_name)
    if not subject or not body:
        print(f"\n❌ Template '{template_name}' was not found.")
        return

    preview = template_manager.preview_template(name=template_name, to_email=send_emails[0])
    from_name = EMAIL_ALIASES.get(template_name, 'DevNavigator Team')

    print(f"\n📧 Ready to send to {len(send_emails)} newly imported contact(s)")
    print(f"Template:      {template_name}")
    print(f"Sender name:   {from_name}")
    print(f"Register link: {preview['register_link'] or 'not set'}")
    print(f"Preview email: {send_emails[0]}")
    print("-" * 48)
    print(f"Subject: {preview['subject']}")
    print()
    print(preview['body'][:700])
    if len(preview['body']) > 700:
        print("\n... preview truncated ...")

    if not args.dry_run and not args.yes:
        confirm = input("\n⚠️  This will send REAL emails to the new imported contacts. Continue? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("✗ Cancelled")
            return

    sender = EmailSender()
    sent, failed = sender.send_batch(
        subject,
        body,
        limit=len(send_emails),
        dry_run=args.dry_run,
        from_name=from_name,
        emails=send_emails,
        template_name=template_name,
    )

    print("\n✅ Import + send complete!")
    print(f"   Sent:   {sent}")
    print(f"   Failed: {failed}")
    summary = manager.get_queue_summary()
    print(f"   Ready to send now: {summary['ready_to_send']}")
    print(f"   Sent total:        {summary['sent_count']}")


def cmd_search_auto(args):
    """Automatically search and extract emails from internet with specific criteria"""
    extractor = AutoEmailExtractor()
    
    title = args.title or input("Job title (e.g., 'junior frontend developer'): ")
    keywords_input = args.keywords or input("Keywords (comma-separated): ")
    keywords = [k.strip() for k in keywords_input.split(',')]
    country_input = args.country or input("Country (optional): ").strip()
    country = country_input if country_input else None
    
    criteria = {
        'title': title,
        'keywords': keywords,
        'country': country,
        'remote': args.remote
    }
    
    print(f"\n🚀 Starting automated search with criteria:")
    for key, val in criteria.items():
        print(f"   {key}: {val}")
    
    stored, results = extractor.search_all_sources(criteria, limit=100)
    
    print(f"\n✅ Extraction complete!")
    print(f"   Emails stored: {stored}")
    print(f"   Ready for campaign: {stored}")
    
    # Show preview
    print(f"\n📧 Preview (first 5):")
    from python_engine.database_manager import DatabaseManager
    manager = DatabaseManager()
    recent = manager.get_recent_contacts(5)
    if recent:
        for contact in recent:
            print(f"   {contact['email']} - {contact.get('title', 'Unknown')}")


def cmd_search_filtered(args):
    """Search with automatic filtering by profile criteria"""
    extractor = AutoEmailExtractor()
    
    criteria = {
        'title': args.title or 'junior frontend developer',
        'keywords': args.keywords.split(',') if args.keywords else ['react', 'javascript', 'remote'],
        'country': args.country or None,
        'remote': args.remote
    }
    
    print(f"\n🎯 Searching for: {criteria['title']}")
    print(f"   Keywords: {', '.join(criteria['keywords'])}")
    if criteria.get('country'):
        print(f"   Country: {criteria['country']}")
    if criteria['remote']:
        print(f"   Remote jobs only")
    
    results = extractor.search_with_filters(criteria)
    
    print(f"\n✅ Found {len(results)} matching profiles!")
    
    if results:
        print(f"\n📧 Top matches:")
        for i, contact in enumerate(results[:10], 1):
            print(f"\n{i}. {contact.get('name', 'Unknown')}")
            print(f"   Email: {contact['email']}")
            print(f"   Title: {contact.get('title', 'Unknown')}")
            print(f"   Company: {contact.get('company', 'Unknown')}")


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

    # Queue inspection command
    queue_parser = subparsers.add_parser('queue', help='Inspect the current send queue')
    queue_parser.add_argument('--queue', choices=['all', 'ready', 'review', 'recent', 'recent_ready', 'sent', 'archived'],
                              default='all', help='Queue view to show')
    queue_parser.add_argument('--limit', type=int, default=20, help='Maximum rows to display')
    queue_parser.add_argument('--source', help='Filter by exact source value')
    queue_parser.add_argument('--recent-hours', type=int, default=24, help='Window for recent queue filters')

    # Contact import command
    import_parser = subparsers.add_parser('import-contacts', help='Import contacts from a local CSV/text file')
    import_parser.add_argument('--file', required=True, help='Path to CSV or text file')
    import_parser.add_argument('--source', default='csv_upload', help='Source label stored in the database')
    import_parser.add_argument('--consent', action='store_true',
                               help='Mark imported contacts as approved/sendable')

    import_send_parser = subparsers.add_parser(
        'import-send-approved',
        help='Import approved contacts from a file and send only the newly imported ones',
    )
    import_send_parser.add_argument('--file', required=True, help='Path to CSV or text file')
    import_send_parser.add_argument('--source', default='approved_csv', help='Source label stored in the database')
    import_send_parser.add_argument('--template', help='Template to send after import')
    import_send_parser.add_argument('--limit', type=int, help='Maximum number of newly imported contacts to send')
    import_send_parser.add_argument('--dry-run', action='store_true', help='Preview the send without emailing')
    import_send_parser.add_argument('--yes', action='store_true', help='Skip confirmation before sending')

    archive_parser = subparsers.add_parser('archive-contacts', help='Archive contacts from active queue views')
    archive_parser.add_argument('--sent', action='store_true', help='Archive all sent contacts')
    archive_parser.add_argument('--all', action='store_true', help='Archive all active contacts')
    archive_parser.add_argument('--emails', help='Comma-separated emails to archive')

    unarchive_parser = subparsers.add_parser('unarchive-contacts', help='Restore archived contacts')
    unarchive_parser.add_argument('--all', action='store_true', help='Restore all archived contacts')
    unarchive_parser.add_argument('--emails', help='Comma-separated emails to restore')

    approve_parser = subparsers.add_parser('approve-recent-contacts', help='Approve newest review contacts')
    approve_parser.add_argument('--limit', type=int, default=20, help='Number of recent contacts to approve')
    approve_parser.add_argument('--recent-hours', type=int, help='Only approve contacts added within this many hours')
    
    # Search auto command
    search_auto_parser = subparsers.add_parser('search-auto', help='Search and extract emails with criteria')
    search_auto_parser.add_argument('--title', help='Job title to search for')
    search_auto_parser.add_argument('--keywords', help='Keywords (comma-separated)')
    search_auto_parser.add_argument('--country', help='Country to target')
    search_auto_parser.add_argument('--remote', action='store_true', help='Remote jobs only')
    
    # Search filtered command
    search_filtered_parser = subparsers.add_parser('search-filtered', help='Search with automatic filtering')
    search_filtered_parser.add_argument('--title', help='Job title')
    search_filtered_parser.add_argument('--keywords', help='Keywords (comma-separated)')
    search_filtered_parser.add_argument('--country', help='Country')
    search_filtered_parser.add_argument('--remote', action='store_true', help='Remote only')
    
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
    elif args.command == 'queue':
        cmd_queue(args)
    elif args.command == 'import-contacts':
        cmd_import_contacts(args)
    elif args.command == 'import-send-approved':
        cmd_import_send_approved(args)
    elif args.command == 'archive-contacts':
        cmd_archive_contacts(args)
    elif args.command == 'unarchive-contacts':
        cmd_unarchive_contacts(args)
    elif args.command == 'approve-recent-contacts':
        cmd_approve_recent_contacts(args)
    elif args.command == 'search-auto':
        cmd_search_auto(args)
    elif args.command == 'search-filtered':
        cmd_search_filtered(args)


if __name__ == '__main__':
    main()

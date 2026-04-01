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

# Add the appwrite project root to path so direct execution can import kernel.bridge.*
APPWRITE_ROOT = Path(__file__).resolve().parents[2]
if str(APPWRITE_ROOT) not in sys.path:
    sys.path.insert(0, str(APPWRITE_ROOT))

from kernel.bridge.python_engine.email_extractor import EmailValidator, get_email_extractor
from kernel.bridge.python_engine.email_verification import (
    DEFAULT_VERIFICATION_TEMPLATE,
    EmailVerificationService,
)
from kernel.bridge.python_engine.database_manager import DatabaseManager
from kernel.bridge.python_engine.template_manager import TemplateManager
from kernel.bridge.python_engine.auto_email_extractor import AutoEmailExtractor
from kernel.bridge.send_test_emails import EMAIL_ALIASES, EmailSender, EmailTemplateManager
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


def cmd_validate_email(args):
    """Validate a single email address and show the reason."""
    validator = EmailValidator(
        enable_virus_check=os.getenv('ENABLE_VIRUS_CHECK', 'true').lower() == 'true',
        enable_source_verification=not args.skip_dns,
    )
    normalized = args.email.strip().lower()
    is_valid, reason = validator.is_valid_email(normalized)

    print("\n📧 Email Validation")
    print("-" * 40)
    print(f"Email: {normalized}")
    print(f"Valid: {'yes' if is_valid else 'no'}")
    print(f"Reason: {reason}")


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


def cmd_send_verification_email(args):
    """Create and optionally send an email verification request."""
    template_name = args.template or DEFAULT_VERIFICATION_TEMPLATE
    template_manager = EmailTemplateManager()
    subject, body = template_manager.get_template(template_name)
    if not subject or not body:
        print(f"\n❌ Template '{template_name}' was not found.")
        return

    verification_service = EmailVerificationService()
    payload = verification_service.prepare_verification(
        args.email,
        recipient_name=args.name or '',
        source=args.source,
        template_name=template_name,
        expiry_hours=args.expiry_hours,
        persist=not args.dry_run,
    )
    preview = template_manager.preview_template(
        name=template_name,
        to_email=args.email,
        recipient_name=args.name or 'there',
        extra_context=payload.to_template_context(),
    )
    from_name = EMAIL_ALIASES.get(template_name, 'DevNavigator Verification')

    print(f"\n✉️ Verification email prepared for {payload.email}")
    print("-" * 56)
    print(f"Template:    {template_name}")
    print(f"Sender name: {from_name}")
    print(f"Code:        {payload.verification_code}")
    print(f"Expires:     {payload.expires_at}")
    print(f"Link:        {payload.verification_link}")
    print("-" * 56)
    print(f"Subject: {preview['subject']}")
    print()
    print(preview['body'][:900])
    if len(preview['body']) > 900:
        print("\n... preview truncated ...")

    if args.dry_run:
        print("\nℹ️  Dry run only. No verification request was stored or emailed.")
        return

    sender = EmailSender()
    success, message = sender.send_verification_email(
        payload.email,
        subject,
        body,
        from_name=from_name,
        extra_context=payload.to_template_context(),
    )
    if success:
        verification_service.mark_sent(payload.request_id)
    else:
        verification_service.mark_failed(payload.request_id)

    print()
    if success:
        print(f"✅ Verification email sent to {payload.email}")
    else:
        print(f"❌ Verification email failed for {payload.email}")
    print(f"Status: {message}")


def cmd_confirm_verification(args):
    """Confirm a stored verification request."""
    if not args.token and not (args.email and args.code):
        print("❌ Provide either --token or both --email and --code")
        return

    verification_service = EmailVerificationService()
    success, message, details = verification_service.confirm(
        token=args.token,
        email=args.email,
        verification_code=args.code,
    )

    print("\n🔐 Verification Result")
    print("-" * 40)
    print(f"Success: {'yes' if success else 'no'}")
    print(f"Message: {message}")
    if details:
        print(f"Email:   {details['email']}")
        print(f"Request: {details['request_id']}")


def cmd_verification_status(args):
    """Show the current verification status for a contact."""
    verification_service = EmailVerificationService()
    status = verification_service.get_status(args.email)
    if not status:
        print(f"❌ No verification record found for {args.email}")
        return

    print("\n📋 Verification Status")
    print("-" * 48)
    print(f"Email:               {status['email']}")
    print(f"Verified:            {'yes' if status['verified'] else 'no'}")
    print(f"Contact status:      {status['verification_status']}")
    print(f"Verification sent:   {status['verification_sent_at'] or 'not sent'}")
    print(f"Verified at:         {status['verified_at'] or 'not verified'}")

    latest_request = status.get('latest_request')
    if latest_request:
        print(f"Latest request:      {latest_request['status']}")
        print(f"Requested at:        {latest_request['requested_at']}")
        print(f"Request expires at:  {latest_request['expires_at']}")
        print(f"Template:            {latest_request['template_name']}")


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
    
    matched, results = extractor.search_all_sources(criteria, limit=100)
    
    print(f"\n✅ Extraction complete!")
    print(f"   Matches found: {matched}")
    print(f"   Ready for campaign: {len(results)}")
    
    # Show preview
    print(f"\n📧 Preview (first 5):")
    from kernel.bridge.python_engine.database_manager import DatabaseManager
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


def cmd_list_search_emails(args):
    """List emails stored in a SQLite search database."""
    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"\n❌ Database not found: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]

    chosen_table = None
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        if 'email' in columns:
            chosen_table = table
            break

    if not chosen_table:
        conn.close()
        print(f"\n❌ No table with an email column was found in {db_path}")
        return

    cursor.execute(
        f"""
        SELECT DISTINCT email
        FROM {chosen_table}
        WHERE email IS NOT NULL AND TRIM(email) != ''
        ORDER BY email COLLATE NOCASE
        """
    )
    rows = [row[0] for row in cursor.fetchall()]
    conn.close()

    print(f"\n📧 Stored search emails from {db_path}:")
    print("-" * 60)
    print(f"Table: {chosen_table}")
    print(f"Emails found: {len(rows)}")
    print("-" * 60)

    if args.emails_only:
        for email in rows:
            print(email)
        return

    for email in rows[:100]:
        print(f"- {email}")
    if len(rows) > 100:
        print(f"... and {len(rows) - 100} more")


def main():
    """Main CLI entry point"""
    setup_environment()
    
    parser = argparse.ArgumentParser(
        description='DevNavigator - Email Campaign Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize database
  python3 devnavigator.py init-db
  
  # Extract emails from file
  python3 devnavigator.py extract-emails --file emails.txt --store
  
  # List templates
  python3 devnavigator.py list-templates
  
  # Show statistics
  python3 devnavigator.py stats
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

    validate_parser = subparsers.add_parser('validate-email', help='Validate a single email address')
    validate_parser.add_argument('--email', required=True, help='Email address to validate')
    validate_parser.add_argument('--skip-dns', action='store_true',
                                 help='Only validate syntax/domain pattern without DNS lookups')
    
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

    verification_send_parser = subparsers.add_parser(
        'send-verification-email',
        help='Create and send a verification email to a contact',
    )
    verification_send_parser.add_argument('--email', required=True, help='Email address to verify')
    verification_send_parser.add_argument('--name', help='Recipient name for the template')
    verification_send_parser.add_argument('--source', default='verification_request',
                                          help='Source label used when creating the contact')
    verification_send_parser.add_argument('--template', default=DEFAULT_VERIFICATION_TEMPLATE,
                                          help='Template used for the verification email')
    verification_send_parser.add_argument('--expiry-hours', type=int,
                                          help='Override verification request expiry time')
    verification_send_parser.add_argument('--dry-run', action='store_true',
                                          help='Preview the verification email without storing or sending')

    confirm_verification_parser = subparsers.add_parser(
        'confirm-verification',
        help='Confirm an email verification request',
    )
    confirm_verification_parser.add_argument('--token', help='Verification token from a verification link')
    confirm_verification_parser.add_argument('--email', help='Email address to confirm with a code')
    confirm_verification_parser.add_argument('--code', help='Verification code for the email address')

    verification_status_parser = subparsers.add_parser(
        'verification-status',
        help='Show the latest verification status for an email address',
    )
    verification_status_parser.add_argument('--email', required=True, help='Email address to inspect')

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

    list_search_emails_parser = subparsers.add_parser(
        'list-search-emails',
        help='List emails stored in a SQLite search database',
    )
    list_search_emails_parser.add_argument(
        '--db-path',
        default='./database/internet_search.db',
        help='Path to the SQLite database that stores search results',
    )
    list_search_emails_parser.add_argument(
        '--emails-only',
        action='store_true',
        help='Print only email addresses, one per line',
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Route commands
    if args.command == 'init-db':
        cmd_init_db(args)
    elif args.command == 'extract-emails':
        cmd_extract_emails(args)
    elif args.command == 'validate-email':
        cmd_validate_email(args)
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
    elif args.command == 'send-verification-email':
        cmd_send_verification_email(args)
    elif args.command == 'confirm-verification':
        cmd_confirm_verification(args)
    elif args.command == 'verification-status':
        cmd_verification_status(args)
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
    elif args.command == 'list-search-emails':
        cmd_list_search_emails(args)


if __name__ == '__main__':
    main()

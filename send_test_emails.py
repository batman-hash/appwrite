#!/usr/bin/env python3
"""
Email Template Setup & Test Send
Create templates and send test emails to extracted contacts
"""
import os
import sys
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


# Email aliases for different campaign types (same email, different display names)
EMAIL_ALIASES = {
    'junior_dev_recruitment': 'DevNavigator Jobs 🚀',
    'freelance_opportunities': 'DevNavigator Projects 💼',
    'marketing_partnership': 'DevNavigator Partnerships 🤝',
    'learning_program': 'DevNavigator Academy 🎓',
}


class EmailTemplateManager:
    """Create and manage email templates"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or os.getenv('DATABASE_PATH', './database/devnav.db')
    
    def add_template(self, name, subject, body, is_default=False):
        """Add email template to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO email_templates (name, subject, body, is_default)
                VALUES (?, ?, ?, ?)
            """, (name, subject, body, is_default))
            conn.commit()
            print(f"✓ Template '{name}' created")
            return True
        except Exception as e:
            print(f"✗ Error creating template: {e}")
            return False
        finally:
            conn.close()
    
    def get_template(self, name):
        """Get template by name"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT subject, body FROM email_templates WHERE name = ?", (name,))
        result = cursor.fetchone()
        conn.close()
        return result if result else (None, None)


class EmailSender:
    """Send test emails"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_URL', 'smtp.gmail.com:587').split('://')[-1]
        self.port = 587
        self.username = os.getenv('SMTP_USERNAME', '')
        self.password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('SMTP_FROM', self.username)
        self.use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        self.db_path = os.getenv('DATABASE_PATH', './database/devnav.db')
    
    def send_test_email(self, to_email, subject, body, template_name=None, from_name=None):
        """
        Send single test email
        Args:
            from_name: Display name for sender (e.g., "DevNavigator Jobs")
        Returns: (success: bool, message: str)
        """
        try:
            # Replace variables
            body = body.replace('$email', to_email)
            body = body.replace('$date', datetime.now().strftime('%Y-%m-%d'))
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            
            # Set From with display name (email alias effect)
            if from_name:
                msg['From'] = f"{from_name} <{self.from_email}>"
            else:
                msg['From'] = self.from_email
            
            msg['To'] = to_email
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Send
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            # Log to database
            self._log_send(to_email, subject, 'sent', template_name)
            
            return True, "Sent"
        
        except Exception as e:
            self._log_send(to_email, subject, 'failed', template_name, str(e))
            return False, f"Failed: {str(e)}"
    
    def _log_send(self, email, subject, status, template_name=None, error=None):
        """Log email send to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get contact ID
            cursor.execute("SELECT id FROM contacts WHERE email = ?", (email,))
            contact = cursor.fetchone()
            
            if contact:
                contact_id = contact[0]
                cursor.execute("""
                    INSERT INTO email_logs (contact_id, sent_at, status, error_message)
                    VALUES (?, ?, ?, ?)
                """, (contact_id, datetime.now(), status, error))
                
                # Update contact sent status
                if status == 'sent':
                    cursor.execute("UPDATE contacts SET sent = 1 WHERE id = ?", (contact_id,))
                
                conn.commit()
        except Exception as e:
            print(f"  Warning: Could not log send: {e}")
        finally:
            conn.close()
    
    def send_batch(self, subject, body, limit=None, dry_run=False, from_name=None):
        """
        Send emails to all stored contacts with optional display name
        Args:
            from_name: Display name (e.g., "DevNavigator Jobs")
        Returns: (sent_count, failed_count)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get unsent contacts
            query = "SELECT email FROM contacts WHERE sent = 0"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            contacts = cursor.fetchall()
            conn.close()
            
            sent = 0
            failed = 0
            
            print(f"\n📧 Sending to {len(contacts)} contacts...")
            if from_name:
                print(f"📛 Sender name: {from_name}")
            print("=" * 60)
            
            for i, (email,) in enumerate(contacts, 1):
                if dry_run:
                    sender_display = f" (from: {from_name})" if from_name else ""
                    print(f"{i}. [DRY RUN] Would send to: {email}{sender_display}")
                    sent += 1
                else:
                    success, msg = self.send_test_email(email, subject, body, from_name=from_name)
                    status = "✓" if success else "✗"
                    print(f"{i}. {status} {email}: {msg}")
                    
                    if success:
                        sent += 1
                    else:
                        failed += 1
            
            print("=" * 60)
            print(f"✓ Sent: {sent}, ✗ Failed: {failed}")
            
            return sent, failed
        
        except Exception as e:
            print(f"Error during batch send: {e}")
            return 0, len(contacts)


def setup_templates():
    """Create default email templates"""
    
    manager = EmailTemplateManager()
    
    # Template 1: Junior Developer Recruitment
    template1 = {
        'name': 'junior_dev_recruitment',
        'subject': 'Exciting Opportunity: Join Our Development Team! 🚀',
        'body': '''Hi there!

We came across your profile and were impressed by your skills and enthusiasm for web development.

We're looking for talented junior developers to join our growing team. We offer:

✓ Mentorship from experienced developers
✓ Work on real-world projects
✓ Flexible remote work options
✓ Competitive compensation and benefits

Would you be interested in learning more? We'd love to chat!

Feel free to reply to this email or check out our careers page.

Best regards,
DevNavigator Team
https://devnavigator.io

---
This is a test email. Your email: $email
Sent: $date
''',
        'is_default': True
    }
    manager.add_template(**template1)
    
    # Template 2: Freelance Opportunities
    template2 = {
        'name': 'freelance_opportunities',
        'subject': 'Freelance Project Opportunity - We Want You! 💼',
        'body': '''Hello!

We have an exciting freelance project coming up that could be perfect for you.

Project Details:
- Duration: 4-6 weeks
- Rate: Competitive hourly rate
- Remote: 100% work from home
- Tech Stack: React, Node.js, PostgreSQL

Your expertise in $category makes you a great fit!

Interested? Let's discuss the details!

Reply to this email or visit: https://projects.devnavigator.io

Cheers,
DevNavigator Crew

---
Test Email | $email | $date
''',
        'is_default': False
    }
    manager.add_template(**template2)
    
    # Template 3: Marketing Collaboration
    template3 = {
        'name': 'marketing_partnership',
        'subject': 'Let\'s Collaborate on Something Great 🤝',
        'body': '''Hi!

We've been following your work in the marketing space and love your approach.

We're starting a new growth initiative and think partnering with someone like you could be mutually beneficial.

Would you be open to a quick chat? We can discuss potential collaboration opportunities.

Looking forward to connecting!

DevNavigator Partnership Team
hello@devnavigator.io

---
Test Campaign | $email | $date
''',
        'is_default': False
    }
    manager.add_template(**template3)
    
    # Template 4: Learning & Mentorship
    template4 = {
        'name': 'learning_program',
        'subject': 'Free Web Development Bootcamp - Limited Spots! 🎓',
        'body': '''Hi $email,

We're running an intensive web development bootcamp this spring and we're inviting top candidates.

Program Highlights:
✓ 12 weeks of hands-on training
✓ 1-on-1 mentorship
✓ Build 5+ real projects
✓ 100% remote
✓ Job placement assistance

Early applicants get 50% discount!

Learn more: https://bootcamp.devnavigator.io

Enroll now!

DevNavigator Academy
$date
''',
        'is_default': False
    }
    manager.add_template(**template4)
    
    print("\n✅ All templates created successfully!\n")


def show_templates():
    """Display all available templates"""
    try:
        conn = sqlite3.connect(os.getenv('DATABASE_PATH', './database/devnav.db'))
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, subject, is_default FROM email_templates")
        templates = cursor.fetchall()
        conn.close()
        
        print("\n📋 Available Email Templates:")
        print("=" * 70)
        
        for name, subject, is_default in templates:
            marker = "⭐" if is_default else "  "
            print(f"{marker} [{name}]")
            print(f"    Subject: {subject[:55]}...")
            print()
    
    except Exception as e:
        print(f"Error: {e}")


def test_send_email(template_name=None, limit=3, dry_run=False):
    """Send test emails to extracted contacts with email alias"""
    
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║           📧 TEST EMAIL SENDING                           ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    if not template_name:
        template_name = 'junior_dev_recruitment'
    
    manager = EmailTemplateManager()
    subject, body = manager.get_template(template_name)
    
    if not subject or not body:
        print(f"✗ Template '{template_name}' not found!")
        show_templates()
        return
    
    # Get email alias for this template
    from_name = EMAIL_ALIASES.get(template_name, 'DevNavigator Team')
    
    print(f"\n📧 Using template: {template_name}")
    print(f"   Subject: {subject}")
    print(f"   📛 Sender name: {from_name}")
    print(f"   Limit: {limit} emails")
    print(f"   Dry run: {'Yes (no emails sent)' if dry_run else 'No (emails will be sent)'}")
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - Showing what would be sent:\n")
    else:
        confirm = input("\n⚠️  This will send REAL emails. Continue? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("✗ Cancelled")
            return
        print()
    
    sender = EmailSender()
    sent, failed = sender.send_batch(subject, body, limit=limit, dry_run=dry_run, from_name=from_name)
    
    print(f"\n✅ Complete!")
    if not dry_run:
        print(f"   Sent: {sent}")
        print(f"   Failed: {failed}")
        print(f"   Status saved to database")


def main():
    """Main CLI"""
    if len(sys.argv) < 2:
        print("""
📧 Email Template & Test Send Tool (with Email Aliases)

Usage:
  python3 send_test_emails.py setup              # Create templates
  python3 send_test_emails.py list               # Show templates
  python3 send_test_emails.py send [--dry-run]   # Send test emails
  python3 send_test_emails.py send [--limit 5]   # Send to N contacts

📛 EMAIL ALIASES (Different sender names, same email):
  - junior_dev_recruitment  → "DevNavigator Jobs 🚀"
  - freelance_opportunities → "DevNavigator Projects 💼"
  - marketing_partnership   → "DevNavigator Partnerships 🤝"
  - learning_program        → "DevNavigator Academy 🎓"

Examples:
  # Create templates with aliases
  python3 send_test_emails.py setup
  
  # Show available templates
  python3 send_test_emails.py list
  
  # Preview emails (dry run, shows email alias)
  python3 send_test_emails.py send --dry-run
  
  # Send to first 3 contacts with automatic alias
  python3 send_test_emails.py send --limit 3
  
  # Send using specific template (with matching alias)
  python3 send_test_emails.py send --template freelance_opportunities --limit 5

💡 How it works:
  - Same email: matteopennacchia43@gmail.com
  - Recipients see different sender names
  - Great for A/B testing different campaign angles
  - Perfect for advertising without multiple accounts
        """)
        return
    
    command = sys.argv[1]
    
    if command == 'setup':
        setup_templates()
    
    elif command == 'list':
        show_templates()
    
    elif command == 'send':
        limit = 3
        template = None
        dry_run = False
        
        # Parse arguments
        for i, arg in enumerate(sys.argv[2:]):
            if arg == '--dry-run':
                dry_run = True
            elif arg == '--limit' and i + 3 < len(sys.argv):
                limit = int(sys.argv[i + 3])
            elif arg == '--template' and i + 3 < len(sys.argv):
                template = sys.argv[i + 3]
        
        test_send_email(template_name=template, limit=limit, dry_run=dry_run)
    
    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()

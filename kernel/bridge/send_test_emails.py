#!/usr/bin/env python3
"""
Email Template Setup & Test Send
Create templates and send test emails to extracted contacts
"""
import os
import sys
import sqlite3
import smtplib
import html
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from dotenv import load_dotenv
from datetime import datetime
from string import Template
from pathlib import Path
from urllib.parse import urlparse

APPWRITE_ROOT = Path(__file__).resolve().parents[2]
if str(APPWRITE_ROOT) not in sys.path:
    sys.path.insert(0, str(APPWRITE_ROOT))

load_dotenv()

from kernel.bridge.python_engine.database_manager import DatabaseManager

# Import tracking system
try:
    from tracking import EmailTracker
    HAS_TRACKING = True
except:
    HAS_TRACKING = False


# Email aliases for different campaign types (same email, different display names)
EMAIL_ALIASES = {
    'default_campaign': 'DevNavigator Team',
    'junior_dev_recruitment': 'DevNavigator Jobs 🚀',
    'freelance_opportunities': 'DevNavigator Projects 💼',
    'marketing_partnership': 'DevNavigator Partnerships 🤝',
    'learning_program': 'DevNavigator Academy 🎓',
    'earning_opportunity': 'Earning Opportunity Network 💰',
    'email_verification': 'DevNavigator Verification',
}

SENDABLE_WHERE = "archived = 0 AND sent = 0 AND consent = 1 AND bounced = 0 AND unsubscribed = 0"

CAMPAIGN_LINK_ENV_VARS = {
    'default_campaign': 'DEFAULT_CAMPAIGN_REGISTER_LINK',
    'junior_dev_recruitment': 'JUNIOR_DEV_RECRUITMENT_REGISTER_LINK',
    'freelance_opportunities': 'FREELANCE_OPPORTUNITIES_REGISTER_LINK',
    'marketing_partnership': 'MARKETING_PARTNERSHIP_REGISTER_LINK',
    'learning_program': 'LEARNING_PROGRAM_REGISTER_LINK',
    'earning_opportunity': 'EARNING_OPPORTUNITY_REGISTER_LINK',
}

CAMPAIGN_LINK_DEFAULTS = {
    'default_campaign': 'https://devnavigator.io',
    'junior_dev_recruitment': 'https://devnavigator.io',
    'freelance_opportunities': 'https://projects.devnavigator.io',
    'marketing_partnership': '',
    'learning_program': 'https://bootcamp.devnavigator.io',
    'earning_opportunity': 'https://www.freelancer.com/u/matteo272?frm=matteo272&sb=t',
}

CAMPAIGN_IMAGE_DIRS = {
    'earning_opportunity': Path('Work_From_Home_Campaign/Images_Visuals'),
}

PREFERRED_IMAGE_FILES = [
    'hero_work_setup',
    'money_bag',
    'beach_lifestyle',
]


def get_campaign_register_link(template_name=None):
    """Resolve the campaign-specific registration link from environment."""
    if template_name:
        env_var = CAMPAIGN_LINK_ENV_VARS.get(template_name)
        if env_var:
            value = os.getenv(env_var, '').strip()
            if value:
                return value
        fallback = CAMPAIGN_LINK_DEFAULTS.get(template_name, '').strip()
        if fallback:
            return fallback
    return os.getenv('DEFAULT_REGISTER_LINK', '').strip()


def should_use_public_tracking(tracking_server_url):
    """Only use tracking when the server URL is publicly reachable."""
    if not tracking_server_url:
        return False

    try:
        parsed = urlparse(tracking_server_url)
    except Exception:
        return False

    hostname = (parsed.hostname or '').lower()
    if not hostname:
        return False

    local_hosts = {'localhost', '127.0.0.1', '::1'}
    if hostname in local_hosts or hostname.endswith('.local'):
        return False

    return True


def get_campaign_visuals(template_name=None):
    """Return local campaign image files to embed in HTML emails."""
    image_dir = CAMPAIGN_IMAGE_DIRS.get(template_name)
    if not image_dir:
        return []

    if not image_dir.exists():
        return []

    allowed_suffixes = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
    files = [path for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() in allowed_suffixes]
    if not files:
        return []

    preferred = []
    seen = set()
    for stem in PREFERRED_IMAGE_FILES:
        for path in files:
            if path.stem.lower() == stem and path not in seen:
                preferred.append(path)
                seen.add(path)
                break

    for path in sorted(files):
        if path not in seen:
            preferred.append(path)
            seen.add(path)

    return preferred[:3]


def format_text_as_html_paragraphs(rendered_body):
    """Convert plain text email content into simple HTML paragraphs."""
    sections = []
    for paragraph in rendered_body.split('\n\n'):
        escaped = html.escape(paragraph).replace('\n', '<br>')
        if escaped.strip():
            sections.append(
                f'<p style="margin:0 0 16px 0;font-size:16px;line-height:1.7;color:#1f2937;">{escaped}</p>'
            )
    return ''.join(sections)


def build_html_email(rendered_body, image_count=0, template_name=None, register_link='', verification_link=''):
    """Convert the rendered message into email-safe HTML."""
    image_blocks = [
        (
            f'<img src="cid:campaign_image_{index}" '
            f'style="display:block;width:100%;height:auto;border:0;border-radius:16px;" '
            f'alt="Campaign visual {index + 1}">'
        )
        for index in range(image_count)
    ]
    body_html = format_text_as_html_paragraphs(rendered_body)

    if template_name == 'email_verification':
        cta_html = ''
        if verification_link and verification_link != '[SET EMAIL_VERIFICATION_BASE_URL]':
            safe_link = html.escape(verification_link, quote=True)
            cta_html = (
                '<div style="margin:28px 0 20px 0;text-align:center;">'
                f'<a href="{safe_link}" '
                'style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;'
                'font-size:16px;font-weight:600;padding:14px 28px;border-radius:999px;">'
                'Verify Email'
                '</a>'
                '</div>'
            )

        return (
            '<html><body style="margin:0;padding:0;background:#f4f7fb;font-family:Arial,sans-serif;">'
            '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" '
            'style="background:#f4f7fb;padding:24px 0;">'
            '<tr><td align="center">'
            '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" '
            'style="max-width:640px;background:#ffffff;border-radius:20px;overflow:hidden;">'
            '<tr><td style="background:#111827;padding:32px;text-align:center;">'
            '<div style="font-size:28px;line-height:1.2;font-weight:700;color:#ffffff;">'
            'Confirm Your Email'
            '</div>'
            '<div style="margin-top:10px;font-size:16px;line-height:1.5;color:#d1d5db;">'
            'One quick step to verify your address for DevNavigator.'
            '</div>'
            f'{cta_html}'
            '</td></tr>'
            '<tr><td style="padding:32px;">'
            f'{body_html}'
            '</td></tr>'
            '</table>'
            '</td></tr></table>'
            '</body></html>'
        )

    if template_name == 'earning_opportunity':
        hero_image = image_blocks[0] if image_blocks else ''
        extra_images = image_blocks[1:]

        extra_image_rows = ''
        if extra_images:
            cells = []
            for image_html in extra_images:
                cells.append(
                    '<td style="padding:8px;vertical-align:top;">'
                    f'{image_html}'
                    '</td>'
                )
            if len(cells) == 1:
                cells.append('<td style="padding:8px;vertical-align:top;"></td>')
            extra_image_rows = (
                '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" '
                'style="margin-top:8px;border-collapse:collapse;"><tr>'
                + ''.join(cells[:2]) +
                '</tr></table>'
            )

        cta_html = ''
        if register_link:
            safe_link = html.escape(register_link, quote=True)
            cta_html = (
                '<div style="margin:24px 0 18px 0;text-align:center;">'
                f'<a href="{safe_link}" '
                'style="display:inline-block;background:#00c853;color:#ffffff;text-decoration:none;'
                'font-size:16px;font-weight:bold;padding:14px 28px;border-radius:999px;">'
                'Get Started'
                '</a>'
                '</div>'
            )

        return (
            '<html><body style="margin:0;padding:0;background:#eef2f7;font-family:Arial,sans-serif;">'
            '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" '
            'style="background:#eef2f7;padding:24px 0;">'
            '<tr><td align="center">'
            '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" '
            'style="max-width:680px;background:#ffffff;border-radius:24px;overflow:hidden;">'
            '<tr><td style="background:#0f172a;padding:40px 32px 28px 32px;text-align:center;">'
            '<div style="font-size:34px;line-height:1.15;font-weight:bold;color:#ffffff;">'
            'Start Earning From Home'
            '</div>'
            '<div style="margin-top:12px;font-size:18px;line-height:1.5;color:#cbd5e1;">'
            '100% Free Opportunity'
            '</div>'
            f'{cta_html}'
            '</td></tr>'
            + (
                '<tr><td style="padding:24px 24px 8px 24px;">'
                f'{hero_image}'
                '</td></tr>'
                if hero_image else ''
            ) +
            '<tr><td style="padding:24px 32px 32px 32px;">'
            f'{body_html}'
            f'{extra_image_rows}'
            '</td></tr>'
            '</table>'
            '</td></tr></table>'
            '</body></html>'
        )

    image_html = ''.join(
        f'<div style="margin:16px 0;">{block}</div>'
        for block in image_blocks
    )

    return (
        '<html><body style="font-family:Arial,sans-serif;line-height:1.6;color:#1f2937;">'
        f'{body_html}'
        f'{image_html}'
        '</body></html>'
    )


def render_email_content(to_email, subject, body, template_name=None, recipient_name=None,
                         add_tracking=True, extra_context=None):
    """Render a message with variables and optional tracked registration link."""
    register_link = get_campaign_register_link(template_name)
    context = {
        'name': recipient_name or 'there',
        'email': to_email,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'register_link': register_link or '[SET REGISTER LINK]',
    }
    if extra_context:
        context.update({key: str(value) for key, value in extra_context.items() if value is not None})

    rendered_subject = Template(subject).safe_substitute(context)
    rendered_body = Template(body).safe_substitute(context)

    # Backward-compatible replacements for older templates using {var} syntax.
    for key, value in context.items():
        rendered_subject = rendered_subject.replace(f'{{{key}}}', value)
        rendered_body = rendered_body.replace(f'{{{key}}}', value)

    if add_tracking and HAS_TRACKING and register_link:
        tracker = EmailTracker()
        if should_use_public_tracking(tracker.tracking_server_url):
            tracked_link = tracker.get_tracking_link(
                register_link,
                to_email,
                f"{template_name or 'campaign'}_register",
            )
            rendered_body = rendered_body.replace(register_link, tracked_link)
            tracking_pixel = tracker.get_tracking_pixel(to_email)
            rendered_body = rendered_body + f"\n\n{tracking_pixel}"

    return rendered_subject, rendered_body


class EmailTemplateManager:
    """Create and manage email templates"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or os.getenv('DATABASE_PATH', './database/devnav.db')
        DatabaseManager(self.db_path)
    
    def add_template(self, name, subject, body, is_default=False):
        """Add email template to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if is_default:
                cursor.execute("UPDATE email_templates SET is_default = 0")
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
    
    def get_template(self, name=None):
        """Get template by name, or return the default template when omitted."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if name:
            cursor.execute("SELECT subject, body FROM email_templates WHERE name = ?", (name,))
        else:
            cursor.execute("""
                SELECT subject, body
                FROM email_templates
                WHERE is_default = 1
                ORDER BY id ASC
                LIMIT 1
            """)
        result = cursor.fetchone()
        conn.close()
        return result if result else (None, None)

    def get_default_template_name(self):
        """Return the current default template name."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name
            FROM email_templates
            WHERE is_default = 1
            ORDER BY id ASC
            LIMIT 1
        """)
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def preview_template(self, name=None, to_email='preview@example.com', recipient_name='there',
                         extra_context=None):
        """Return a rendered preview of a template."""
        template_name = name or self.get_default_template_name()
        subject, body = self.get_template(template_name)
        if not subject or not body:
            return None
        visuals = get_campaign_visuals(template_name)
        rendered_subject, rendered_body = render_email_content(
            to_email=to_email,
            subject=subject,
            body=body,
            template_name=template_name,
            recipient_name=recipient_name,
            add_tracking=False,
            extra_context=extra_context,
        )
        return {
            'name': template_name,
            'subject': rendered_subject,
            'body': rendered_body,
            'register_link': get_campaign_register_link(template_name),
            'verification_link': (extra_context or {}).get('verification_link', ''),
            'visuals': [str(path) for path in visuals],
        }


class EmailSender:
    """Send test emails"""
    
    def __init__(self):
        # Parse SMTP URL: smtp://server:port or just server:port
        smtp_url = os.getenv('SMTP_URL', 'smtp.gmail.com:587')
        if '://' in smtp_url:
            smtp_url = smtp_url.split('://')[-1]
        
        # Split server and port
        if ':' in smtp_url:
            self.smtp_server, port_str = smtp_url.rsplit(':', 1)
            try:
                self.port = int(port_str)
            except:
                self.smtp_server = smtp_url
                self.port = 587
        else:
            self.smtp_server = smtp_url
            self.port = 587
        
        self.username = os.getenv('SMTP_USERNAME', '')
        self.password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('SMTP_FROM', self.username)
        self.use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        self.db_path = os.getenv('DATABASE_PATH', './database/devnav.db')
        DatabaseManager(self.db_path)
    
    def send_test_email(self, to_email, subject, body, template_name=None, from_name=None,
                        add_tracking=True, extra_context=None, log_status='sent',
                        mark_contact_sent=True):
        """
        Send single test email with optional tracking
        Args:
            from_name: Display name for sender (e.g., "DevNavigator Jobs")
        Returns: (success: bool, message: str)
        """
        try:
            subject, body = render_email_content(
                to_email=to_email,
                subject=subject,
                body=body,
                template_name=template_name,
                add_tracking=add_tracking,
                extra_context=extra_context,
            )
            visuals = get_campaign_visuals(template_name)
            html_body = build_html_email(
                body,
                image_count=len(visuals),
                template_name=template_name,
                register_link=get_campaign_register_link(template_name),
                verification_link=(extra_context or {}).get('verification_link', ''),
            )
            
            # Create message
            msg = MIMEMultipart('related')
            alternative = MIMEMultipart('alternative')
            msg['Subject'] = subject
            
            # Set From with display name (email alias effect)
            if from_name:
                msg['From'] = f"{from_name} <{self.from_email}>"
            else:
                msg['From'] = self.from_email
            
            msg['To'] = to_email
            
            alternative.attach(MIMEText(body, 'plain'))
            alternative.attach(MIMEText(html_body, 'html'))
            msg.attach(alternative)

            for index, image_path in enumerate(visuals):
                mime_type, _ = mimetypes.guess_type(str(image_path))
                if not mime_type or not mime_type.startswith('image/'):
                    continue

                with open(image_path, 'rb') as handle:
                    image_part = MIMEImage(handle.read())
                image_part.add_header('Content-ID', f'<campaign_image_{index}>')
                image_part.add_header('Content-Disposition', 'inline', filename=image_path.name)
                msg.attach(image_part)
            
            # Send
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            # Log to database
            self._log_send(
                to_email,
                subject,
                log_status,
                template_name,
                mark_contact_sent=mark_contact_sent,
            )

            return True, "Sent"

        except Exception as e:
            failure_status = 'verification_failed' if log_status == 'verification_sent' else 'failed'
            self._log_send(
                to_email,
                subject,
                failure_status,
                template_name,
                str(e),
                mark_contact_sent=False,
            )
            return False, f"Failed: {str(e)}"

    def send_verification_email(self, to_email, subject, body, from_name=None, extra_context=None):
        """Send a verification email without changing campaign delivery state."""
        return self.send_test_email(
            to_email,
            subject,
            body,
            template_name='email_verification',
            from_name=from_name,
            add_tracking=False,
            extra_context=extra_context,
            log_status='verification_sent',
            mark_contact_sent=False,
        )

    def _log_send(self, email, subject, status, template_name=None, error=None,
                  mark_contact_sent=True):
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
                if status == 'sent' and mark_contact_sent:
                    cursor.execute("UPDATE contacts SET sent = 1 WHERE id = ?", (contact_id,))
                
                conn.commit()
        except Exception as e:
            print(f"  Warning: Could not log send: {e}")
        finally:
            conn.close()
    
    def send_batch(self, subject, body, limit=None, dry_run=False, from_name=None,
                   emails=None, country=None, exclude_emails=None, template_name=None,
                   recent_hours=None):
        """
        Send emails to selected contacts with optional filtering
        Args:
            from_name: Display name (e.g., "DevNavigator Jobs")
            emails: List of specific emails to send to
            country: Filter by country code (e.g., 'IN', 'US')
            exclude_emails: List of emails to exclude
        Returns: (sent_count, failed_count)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            conditions = [SENDABLE_WHERE]
            params = []

            if emails:
                placeholders = ','.join(['?' for _ in emails])
                conditions.append(f"email IN ({placeholders})")
                params.extend(emails)

            if country:
                conditions.append("country = ?")
                params.append(country)

            if recent_hours is not None:
                conditions.append("datetime(created_at) > datetime('now', '-' || ? || ' hours')")
                params.append(recent_hours)

            query = f"""
                SELECT email
                FROM contacts
                WHERE {' AND '.join(conditions)}
                ORDER BY datetime(created_at) DESC, email ASC
            """
            cursor.execute(query, params)
            
            contacts = list(cursor.fetchall())
            
            # Exclude specific emails if provided
            if exclude_emails:
                contacts = [c for c in contacts if c[0] not in exclude_emails]
            
            if limit:
                contacts = contacts[:limit]
            
            conn.close()
            
            sent = 0
            failed = 0
            
            print(f"\n📧 Sending to {len(contacts)} contacts...")
            if from_name:
                print(f"📛 Sender name: {from_name}")
            if emails:
                print(f"🎯 Specific emails selected")
            if country:
                print(f"🌍 Country filter: {country}")
            if recent_hours is not None:
                print(f"🕒 New contacts only: last {recent_hours} hour(s)")
            if exclude_emails:
                print(f"🚫 Excluding: {len(exclude_emails)} emails")
            if not contacts:
                print("ℹ️  No contacts matched the approved send queue.")
                print("    Only contacts with consent=1 and without sent/bounced/unsubscribed flags are eligible.")
            print("=" * 60)
            
            for i, (email,) in enumerate(contacts, 1):
                if dry_run:
                    sender_display = f" (from: {from_name})" if from_name else ""
                    print(f"{i}. [DRY RUN] Would send to: {email}{sender_display}")
                    sent += 1
                else:
                    success, msg = self.send_test_email(
                        email,
                        subject,
                        body,
                        template_name=template_name,
                        from_name=from_name,
                    )
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
        'is_default': False
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

Reply to this email or register here: $register_link

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

Learn more and register: $register_link

Enroll now!

DevNavigator Academy
$date
''',
        'is_default': False
    }
    manager.add_template(**template4)
    
    # Template 5: Earning Opportunity Network
    template5 = {
        'name': 'earning_opportunity',
        'subject': 'Free Registration: Flexible Online Earning Opportunity 💰',
        'body': '''Hi,

I wanted to share a simple way to get started with our current earning opportunity campaign.

This is focused on people who want flexible online work they can manage from home and explore at their own pace.

If you want to register and see the details, use this link:
$register_link

What happens next:
- you create your account
- you review the available opportunity
- you decide if it is a good fit for you

There is no pressure to continue if it is not right for you.

If you want more information before registering, just reply to this email and I will help.

Best regards,
Matteo
Earning Opportunity Network

---
Email: $email | Date: $date
''',
        'is_default': True
    }
    manager.add_template(**template5)
    
    print("\n✅ All templates created successfully!\n")


def show_templates():
    """Display all available templates"""
    try:
        conn = sqlite3.connect(os.getenv('DATABASE_PATH', './database/devnav.db'))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, subject, is_default
            FROM email_templates
            ORDER BY is_default DESC, name ASC
        """)
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


def test_send_email(template_name=None, limit=3, dry_run=False, emails=None, country=None,
                    exclude_emails=None, recent_hours=None):
    """Send test emails to selected contacts with optional filtering"""
    
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║           📧 TEST EMAIL SENDING                           ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    manager = EmailTemplateManager()
    if not template_name:
        template_name = manager.get_default_template_name()

    if not template_name:
        print("✗ No default template is configured.")
        return

    subject, body = manager.get_template(template_name)
    
    if not subject or not body:
        print(f"✗ Template '{template_name}' not found!")
        show_templates()
        return
    
    # Get email alias for this template
    from_name = EMAIL_ALIASES.get(template_name, 'DevNavigator Team')
    
    preview = manager.preview_template(
        name=template_name,
        to_email=(emails[0] if emails else 'preview@example.com'),
    )

    print(f"\n📧 Using template: {template_name}")
    print(f"   Subject: {subject}")
    print(f"   📛 Sender name: {from_name}")
    print(f"   🔗 Register link: {preview['register_link'] or 'not set'}")
    print(f"   🖼️  Visuals attached: {len(preview['visuals'])}")
    if recent_hours is not None:
        print(f"   🕒 New contacts only: last {recent_hours} hour(s)")
    print(f"   Limit: {limit} emails")
    print(f"   Dry run: {'Yes (no emails sent)' if dry_run else 'No (emails will be sent)'}")

    print("\n📝 Rendered preview:")
    print("-" * 60)
    print(f"Subject: {preview['subject']}")
    print()
    print(preview['body'][:900])
    if len(preview['body']) > 900:
        print("\n... preview truncated ...")
    print("-" * 60)
    if preview['visuals']:
        print("Visual files:")
        for image_path in preview['visuals']:
            print(f"  - {image_path}")
        print("-" * 60)

    if dry_run:
        print("\n⚠️  DRY RUN MODE - Showing what would be sent:\n")
    else:
        confirm = input("\n⚠️  This will send REAL emails. Continue? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("✗ Cancelled")
            return
        print()
    
    sender = EmailSender()
    sent, failed = sender.send_batch(subject, body, limit=limit, dry_run=dry_run,
                                     from_name=from_name, emails=emails,
                                     country=country, exclude_emails=exclude_emails,
                                     template_name=template_name, recent_hours=recent_hours)
    
    print(f"\n✅ Complete!")
    if not dry_run:
        print(f"   Sent: {sent}")
        print(f"   Failed: {failed}")
        print(f"   Status saved to database")


def preview_template(template_name=None, to_email='preview@example.com'):
    """Print the rendered template without sending."""
    manager = EmailTemplateManager()
    template = manager.preview_template(name=template_name, to_email=to_email)

    if not template:
        requested = template_name or 'default template'
        print(f"✗ Could not load {requested}")
        return

    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║                📝 TEMPLATE PREVIEW                        ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"\nTemplate: {template['name']}")
    print(f"Register link: {template['register_link'] or 'not set'}")
    print(f"Visuals attached: {len(template['visuals'])}")
    print("-" * 60)
    print(f"Subject: {template['subject']}")
    print()
    print(template['body'])
    if template['visuals']:
        print("\nVisual files:")
        for image_path in template['visuals']:
            print(f"  - {image_path}")
    print("-" * 60)


def main():
    """Main CLI"""
    if len(sys.argv) < 2:
        print("""
📧 Email Template & Test Send Tool (with Email Aliases & Filtering)

Usage:
  python3 appwrite/kernel/bridge/send_test_emails.py setup              # Create templates
  python3 appwrite/kernel/bridge/send_test_emails.py list               # Show templates
  python3 appwrite/kernel/bridge/send_test_emails.py preview [OPTIONS]  # Preview rendered template
  python3 appwrite/kernel/bridge/send_test_emails.py send [OPTIONS]     # Send test emails
  python3 appwrite/kernel/bridge/send_test_emails.py send-new [OPTIONS] # Send only recent approved contacts

🎯 FILTERING OPTIONS:
  --limit N                    # Send to N contacts max
  --country CODE              # Filter by country (e.g., US, IN, GB)
  --emails email1,email2,...  # Send to specific emails only
  --exclude email1,email2,... # Exclude specific emails
  --dry-run                   # Preview without sending
  --template NAME             # Use specific template
  --email ADDRESS             # Preview template using a sample recipient
  --recent-hours N            # Only use approved contacts added in last N hours

📛 EMAIL ALIASES (Different sender names, same email):
  - junior_dev_recruitment  → "DevNavigator Jobs 🚀"
  - freelance_opportunities → "DevNavigator Projects 💼"
  - marketing_partnership   → "DevNavigator Partnerships 🤝"
  - learning_program        → "DevNavigator Academy 🎓"
  - earning_opportunity     → "Earning Opportunity Network 💰"

EXAMPLES:
  # Send to all using the current default template
  python3 appwrite/kernel/bridge/send_test_emails.py send --limit 10
  
  # Send to specific emails only
  python3 appwrite/kernel/bridge/send_test_emails.py send --emails alex.kumar@startuptech.in,jane.smith@webagency.com
  
  # Send to India contacts only
  python3 appwrite/kernel/bridge/send_test_emails.py send --country IN --dry-run
  
  # Send to all except certain people
  python3 appwrite/kernel/bridge/send_test_emails.py send --exclude alex.kumar@startuptech.in,john.doe@reactdev.io
  
  # Preview first 3 (no emails sent)
  python3 appwrite/kernel/bridge/send_test_emails.py send --dry-run --limit 3
  
  # Send earning opportunity to US contacts only
  python3 appwrite/kernel/bridge/send_test_emails.py send --template earning_opportunity --country US

  # Preview the actual email before sending
  python3 appwrite/kernel/bridge/send_test_emails.py preview --template earning_opportunity --email demo@example.com

  # Auto-send only approved new contacts from the last 24 hours
  python3 appwrite/kernel/bridge/send_test_emails.py send-new --dry-run
  
  # Test with 2 specific people before mass send
  python3 appwrite/kernel/bridge/send_test_emails.py send --template earning_opportunity \\
    --emails alex.kumar@startuptech.in,priya.patel@techcorp.com --dry-run

💡 WORKFLOW:
  1. Preview with --dry-run to see who will get it
  2. Refine with filters (--country, --emails, --exclude)
  3. Remove --dry-run to actually send
  4. Check stats: python3 devnavigator.py stats
        """)
        return
    
    command = sys.argv[1]
    
    if command == 'setup':
        setup_templates()
    
    elif command == 'list':
        show_templates()

    elif command == 'preview':
        template = None
        to_email = 'preview@example.com'

        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]

            if arg == '--template' and i + 1 < len(sys.argv):
                template = sys.argv[i + 1]
                i += 1
            elif arg == '--email' and i + 1 < len(sys.argv):
                to_email = sys.argv[i + 1]
                i += 1

            i += 1

        preview_template(template_name=template, to_email=to_email)

    elif command in ('send', 'send-new'):
        limit = None
        template = None
        dry_run = False
        emails = None
        country = None
        exclude_emails = None
        recent_hours = 24 if command == 'send-new' else None
        
        # Parse arguments
        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            
            if arg == '--dry-run':
                dry_run = True
            elif arg == '--limit' and i + 1 < len(sys.argv):
                limit = int(sys.argv[i + 1])
                i += 1
            elif arg == '--template' and i + 1 < len(sys.argv):
                template = sys.argv[i + 1]
                i += 1
            elif arg == '--emails' and i + 1 < len(sys.argv):
                emails = [e.strip() for e in sys.argv[i + 1].split(',')]
                i += 1
            elif arg == '--country' and i + 1 < len(sys.argv):
                country = sys.argv[i + 1].upper()
                i += 1
            elif arg == '--exclude' and i + 1 < len(sys.argv):
                exclude_emails = [e.strip() for e in sys.argv[i + 1].split(',')]
                i += 1
            elif arg == '--recent-hours' and i + 1 < len(sys.argv):
                recent_hours = int(sys.argv[i + 1])
                i += 1
            
            i += 1
        
        test_send_email(template_name=template, limit=limit, dry_run=dry_run,
                       emails=emails, country=country, exclude_emails=exclude_emails,
                       recent_hours=recent_hours)
    
    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()

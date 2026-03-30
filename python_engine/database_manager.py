"""
Database Initialization and Management
Sets up SQLite database with proper schema for email campaigns
"""
import csv
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from python_engine.email_extractor import EmailValidator


class DatabaseManager:
    """Manages SQLite database for campaign management"""

    ACTIVE_WHERE = "archived = 0"
    ARCHIVED_WHERE = "archived = 1"
    SENDABLE_WHERE = "archived = 0 AND sent = 0 AND consent = 1 AND bounced = 0 AND unsubscribed = 0"
    REVIEW_WHERE = "archived = 0 AND sent = 0 AND (consent = 0 OR consent IS NULL) AND bounced = 0 AND unsubscribed = 0"
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', './database/devnav.db')
        self.db_path = db_path
        self._ensure_directory()
        self._ensure_contact_archive_columns()
        self._ensure_contact_verification_columns()
        self._ensure_email_verification_table()
    
    def _ensure_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _ensure_contact_archive_columns(self):
        """Ensure archive-related columns exist on older databases."""
        if not os.path.exists(self.db_path):
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'contacts'
        """)
        if not cursor.fetchone():
            conn.close()
            return

        cursor.execute("PRAGMA table_info(contacts)")
        columns = {row[1] for row in cursor.fetchall()}

        if 'archived' not in columns:
            cursor.execute("ALTER TABLE contacts ADD COLUMN archived INTEGER DEFAULT 0")
        if 'archived_at' not in columns:
            cursor.execute("ALTER TABLE contacts ADD COLUMN archived_at TIMESTAMP")

        conn.commit()
        conn.close()

    def _ensure_contact_verification_columns(self):
        """Ensure verification-related columns exist on older databases."""
        if not os.path.exists(self.db_path):
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'contacts'
        """)
        if not cursor.fetchone():
            conn.close()
            return

        cursor.execute("PRAGMA table_info(contacts)")
        columns = {row[1] for row in cursor.fetchall()}

        if 'verification_status' not in columns:
            cursor.execute("ALTER TABLE contacts ADD COLUMN verification_status TEXT DEFAULT 'not_requested'")
        if 'verification_sent_at' not in columns:
            cursor.execute("ALTER TABLE contacts ADD COLUMN verification_sent_at TIMESTAMP")
        if 'verified_at' not in columns:
            cursor.execute("ALTER TABLE contacts ADD COLUMN verified_at TIMESTAMP")

        conn.commit()
        conn.close()

    def _ensure_email_verification_table(self):
        """Ensure the verification request table exists for email confirmation flows."""
        if not os.path.exists(self.db_path):
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_verification_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                email TEXT NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                verification_code TEXT NOT NULL,
                template_name TEXT DEFAULT 'email_verification',
                status TEXT DEFAULT 'pending',
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                verified_at TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email_verification_email
            ON email_verification_requests(email)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email_verification_status
            ON email_verification_requests(status)
        """)
        conn.commit()
        conn.close()
    
    def initialize_database(self):
        """Create all necessary tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Contacts table (enriched with data source fields)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                company TEXT,
                department TEXT,
                title TEXT,
                phone TEXT,
                country TEXT,
                city TEXT,
                source TEXT,
                verified INTEGER DEFAULT 0,
                verification_status TEXT DEFAULT 'not_requested',
                verification_sent_at TIMESTAMP,
                verified_at TIMESTAMP,
                consent INTEGER DEFAULT 0,
                sent INTEGER DEFAULT 0,
                opened INTEGER DEFAULT 0,
                bounced INTEGER DEFAULT 0,
                unsubscribed INTEGER DEFAULT 0,
                archived INTEGER DEFAULT 0,
                archived_at TIMESTAMP,
                data_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._ensure_contact_archive_columns()
        self._ensure_contact_verification_columns()

        # Email templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Campaign tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                template_id INTEGER NOT NULL,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                total_emails INTEGER,
                sent_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (template_id) REFERENCES email_templates(id)
            )
        """)
        
        # Email send logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                campaign_id INTEGER,
                template_id INTEGER,
                sent_at TIMESTAMP,
                status TEXT,
                error_message TEXT,
                FOREIGN KEY (contact_id) REFERENCES contacts(id),
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
                FOREIGN KEY (template_id) REFERENCES email_templates(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_verification_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                email TEXT NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                verification_code TEXT NOT NULL,
                template_name TEXT DEFAULT 'email_verification',
                status TEXT DEFAULT 'pending',
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                verified_at TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            )
        """)
        
        # IP Tracking and Geo-targeting table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT UNIQUE NOT NULL,
                country TEXT,
                city TEXT,
                latitude REAL,
                longitude REAL,
                timezone TEXT,
                isp TEXT,
                fraud_score INTEGER,
                is_vpn INTEGER DEFAULT 0,
                is_proxy INTEGER DEFAULT 0,
                is_bot INTEGER DEFAULT 0,
                threat_types TEXT,
                data_source TEXT,
                last_verified TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_contacts_sent ON contacts(sent)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_contacts_consent ON contacts(consent)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_contacts_country ON contacts(country)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_contacts_archived ON contacts(archived)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_contacts_verification_status ON contacts(verification_status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email_logs_contact ON email_logs(contact_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email_verification_email
            ON email_verification_requests(email)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email_verification_status
            ON email_verification_requests(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ip_tracking_address ON ip_tracking(ip_address)
        """)
        
        conn.commit()
        conn.close()
        print(f"✓ Database initialized at {self.db_path}")
    
    def insert_default_template(self):
        """Insert default email template"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        default_template = {
            'name': 'default_campaign',
            'subject': "We're launching a new children's learning app! 🚀",
            'body': """Hi {name},

We are launching a commercial app project for children and wanted to share it with you.

The app is designed to help children learn through a blog-style experience with educational content about information, culture, stories, religion, and interactive pop-up features.

Key Features:
- Educational content for children
- Interactive learning experiences
- Safe and secure environment
- Engaging blog-style interface

If you would like to hear more about the project, reply to this email and we will follow up with details.

Best regards,
DevNavigator Team
matteopennacchia43@gmail.com
""".strip()
        }
        verification_template = {
            'name': 'email_verification',
            'subject': "Confirm your email address for DevNavigator",
            'body': """Hi {name},

Please confirm that {email} is the right address for DevNavigator updates.

Verify your email: $verification_link
Verification code: $verification_code
Expires at: $verification_expires_at

If you did not request this, you can safely ignore this email.

Best regards,
DevNavigator Team
""".strip()
        }

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO email_templates (name, subject, body, is_default)
                VALUES (?, ?, ?, 1)
            """, (default_template['name'], default_template['subject'], default_template['body']))
            cursor.execute("""
                INSERT OR IGNORE INTO email_templates (name, subject, body, is_default)
                VALUES (?, ?, ?, 0)
            """, (
                verification_template['name'],
                verification_template['subject'],
                verification_template['body'],
            ))

            conn.commit()
            print("✓ Default templates inserted")
        except sqlite3.IntegrityError:
            print("~ Default templates already exist")
        finally:
            conn.close()
    
    def get_contact_count(self, include_archived: bool = False) -> int:
        """Get total contact count."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if include_archived:
            cursor.execute("SELECT COUNT(*) FROM contacts")
        else:
            cursor.execute(f"SELECT COUNT(*) FROM contacts WHERE {self.ACTIVE_WHERE}")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_unsent_count(self) -> int:
        """Get count of unsent emails"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM contacts WHERE {self.SENDABLE_WHERE}")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_recent_contacts(self, limit: int = 10) -> list:
        """Get recently added contacts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, name, title, company, country, created_at
            FROM contacts 
            WHERE archived = 0
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        contacts = []
        for row in cursor.fetchall():
            contacts.append({
                'id': row[0],
                'email': row[1],
                'name': row[2],
                'title': row[3],
                'company': row[4],
                'country': row[5],
                'created_at': row[6]
            })
        
        conn.close()
        return contacts

    def get_queue_summary(self, recent_hours: int = 24) -> Dict[str, int]:
        """Return high-level queue counts for the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN archived = 0 THEN 1 ELSE 0 END), 0) AS total_contacts,
                COALESCE(SUM(CASE WHEN archived = 0 AND sent = 0 AND consent = 1 AND bounced = 0 AND unsubscribed = 0 THEN 1 ELSE 0 END), 0) AS ready_to_send,
                COALESCE(SUM(CASE WHEN archived = 0 AND sent = 0 AND (consent = 0 OR consent IS NULL) AND bounced = 0 AND unsubscribed = 0 THEN 1 ELSE 0 END), 0) AS needs_review,
                COALESCE(SUM(CASE WHEN archived = 0 AND sent = 1 THEN 1 ELSE 0 END), 0) AS sent_count,
                COALESCE(SUM(CASE WHEN archived = 0 AND bounced = 1 THEN 1 ELSE 0 END), 0) AS bounced_count,
                COALESCE(SUM(CASE WHEN archived = 0 AND unsubscribed = 1 THEN 1 ELSE 0 END), 0) AS unsubscribed_count,
                COALESCE(SUM(CASE WHEN archived = 0 AND sent = 0 AND bounced = 0 AND unsubscribed = 0 AND datetime(created_at) > datetime('now', '-' || ? || ' hours') THEN 1 ELSE 0 END), 0) AS recent_imports,
                COALESCE(SUM(CASE WHEN archived = 1 THEN 1 ELSE 0 END), 0) AS archived_count
            FROM contacts
            """,
            (recent_hours,),
        )

        row = cursor.fetchone()
        conn.close()

        return {
            'total_contacts': row[0],
            'ready_to_send': row[1],
            'needs_review': row[2],
            'sent_count': row[3],
            'bounced_count': row[4],
            'unsubscribed_count': row[5],
            'recent_imports': row[6],
            'archived_count': row[7],
        }

    def get_contacts(
        self,
        queue: str = 'all',
        limit: Optional[int] = None,
        source: Optional[str] = None,
        recent_hours: int = 24,
    ) -> List[Dict[str, object]]:
        """Fetch contacts with a computed queue status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        conditions = []
        params: List[object] = []

        if queue == 'ready':
            conditions.append(self.SENDABLE_WHERE)
        elif queue == 'review':
            conditions.append(self.REVIEW_WHERE)
        elif queue == 'sent':
            conditions.append(self.ACTIVE_WHERE)
            conditions.append("sent = 1")
        elif queue == 'archived':
            conditions.append(self.ARCHIVED_WHERE)
        elif queue == 'recent':
            conditions.append(self.ACTIVE_WHERE)
            conditions.append("sent = 0")
            conditions.append("bounced = 0")
            conditions.append("unsubscribed = 0")
            conditions.append("datetime(created_at) > datetime('now', '-' || ? || ' hours')")
            params.append(recent_hours)
        elif queue == 'recent_ready':
            conditions.append(self.SENDABLE_WHERE)
            conditions.append("datetime(created_at) > datetime('now', '-' || ? || ' hours')")
            params.append(recent_hours)
        else:
            conditions.append(self.ACTIVE_WHERE)

        if source:
            conditions.append("source = ?")
            params.append(source)

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        limit_sql = " LIMIT ?" if limit is not None else ""
        if limit is not None:
            params.append(limit)

        cursor.execute(
            f"""
            SELECT
                email,
                name,
                company,
                country,
                source,
                consent,
                sent,
                opened,
                bounced,
                unsubscribed,
                archived,
                datetime(created_at, 'localtime') AS created_local,
                CASE
                    WHEN archived = 1 THEN 'Archived'
                    WHEN bounced = 1 THEN 'Bounced'
                    WHEN unsubscribed = 1 THEN 'Unsubscribed'
                    WHEN sent = 1 THEN 'Sent'
                    WHEN consent = 1 AND sent = 0 THEN 'Ready to send'
                    ELSE 'Needs review'
                END AS queue_status
            FROM contacts
            {where_sql}
            ORDER BY created_at DESC, email ASC
            {limit_sql}
            """,
            params,
        )

        contacts = []
        for row in cursor.fetchall():
            contacts.append({
                'email': row[0],
                'name': row[1],
                'company': row[2],
                'country': row[3],
                'source': row[4],
                'consent': row[5],
                'sent': row[6],
                'opened': row[7],
                'bounced': row[8],
                'unsubscribed': row[9],
                'archived': row[10],
                'created_at': row[11],
                'queue_status': row[12],
            })

        conn.close()
        return contacts

    def export_contacts(
        self,
        output_path: str,
        queue: str = 'all',
        limit: Optional[int] = None,
        source: Optional[str] = None,
        recent_hours: int = 24,
    ) -> int:
        """Export contacts from a queue view to CSV."""
        contacts = self.get_contacts(
            queue=queue,
            limit=limit,
            source=source,
            recent_hours=recent_hours,
        )

        path = Path(output_path)
        if path.parent:
            path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            'email',
            'name',
            'company',
            'country',
            'source',
            'queue_status',
            'consent',
            'sent',
            'opened',
            'bounced',
            'unsubscribed',
            'archived',
            'created_at',
        ]

        with path.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for contact in contacts:
                writer.writerow({field: contact.get(field, '') for field in fieldnames})

        return len(contacts)

    def get_send_status(self, limit: int = 20) -> Dict[str, object]:
        """Return a summary of send activity and recent contact delivery states."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_attempts,
                COALESCE(SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END), 0) AS successful,
                COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) AS failed,
                COALESCE(SUM(CASE WHEN status = 'verification_sent' THEN 1 ELSE 0 END), 0) AS verification_sent
            FROM email_logs
            """
        )
        totals = cursor.fetchone()

        cursor.execute(
            """
            SELECT
                email,
                sent,
                opened,
                bounced,
                unsubscribed,
                source,
                datetime(updated_at, 'localtime') AS updated_local
            FROM contacts
            WHERE archived = 0
            ORDER BY sent DESC, datetime(updated_at) DESC, email ASC
            LIMIT ?
            """,
            (limit,),
        )

        contacts = []
        for row in cursor.fetchall():
            contacts.append({
                'email': row[0],
                'sent': bool(row[1]),
                'opened': bool(row[2]),
                'bounced': bool(row[3]),
                'unsubscribed': bool(row[4]),
                'source': row[5],
                'updated_at': row[6],
            })

        conn.close()
        return {
            'total_attempts': totals[0] or 0,
            'successful': totals[1] or 0,
            'failed': totals[2] or 0,
            'verification_sent': totals[3] or 0,
            'contacts': contacts,
        }

    def import_contacts_file(
        self,
        file_path: str,
        source: str = 'csv_upload',
        consent: int = 0,
    ) -> Tuple[int, int, List[str]]:
        """Import contacts from a CSV or text file into the database."""
        path = Path(file_path)
        if not path.exists():
            return 0, 0, [f"File not found: {path}"]

        validator = EmailValidator(
            enable_virus_check=os.getenv('ENABLE_VIRUS_CHECK', 'true').lower() == 'true',
            enable_source_verification=os.getenv('ENABLE_SOURCE_VERIFICATION', 'true').lower() == 'true'
        )
        contacts = self._load_contacts_from_file(path)

        if not contacts:
            return 0, 0, ["No valid contacts found in file"]

        imported = 0
        duplicates = 0
        errors: List[str] = []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for contact in contacts:
            email = contact['email'].strip().lower()
            is_valid, reason = validator.is_valid_email(email)
            if not is_valid:
                errors.append(f"{email}: {reason}")
                continue

            try:
                cursor.execute(
                    """
                    INSERT INTO contacts (
                        email, name, company, department, country, source, consent, sent
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                    (
                        email,
                        contact.get('name', '').strip(),
                        contact.get('company', '').strip(),
                        contact.get('department', '').strip(),
                        contact.get('country', '').strip(),
                        source,
                        1 if consent else 0,
                    ),
                )
                imported += 1
            except sqlite3.IntegrityError:
                duplicates += 1

        conn.commit()
        conn.close()

        return imported, duplicates, errors

    def archive_contacts(
        self,
        emails: Optional[List[str]] = None,
        sent_only: bool = False,
        all_active: bool = False,
    ) -> int:
        """Archive selected active contacts without deleting them."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if emails:
            placeholders = ','.join(['?' for _ in emails])
            cursor.execute(
                f"""
                UPDATE contacts
                SET archived = 1, archived_at = CURRENT_TIMESTAMP
                WHERE archived = 0 AND email IN ({placeholders})
                """,
                emails,
            )
        elif sent_only:
            cursor.execute("""
                UPDATE contacts
                SET archived = 1, archived_at = CURRENT_TIMESTAMP
                WHERE archived = 0 AND sent = 1
            """)
        elif all_active:
            cursor.execute("""
                UPDATE contacts
                SET archived = 1, archived_at = CURRENT_TIMESTAMP
                WHERE archived = 0
            """)
        else:
            conn.close()
            return 0

        archived_count = cursor.rowcount
        conn.commit()
        conn.close()
        return archived_count

    def unarchive_contacts(
        self,
        emails: Optional[List[str]] = None,
        all_archived: bool = False,
    ) -> int:
        """Restore archived contacts back into the active queue."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if emails:
            placeholders = ','.join(['?' for _ in emails])
            cursor.execute(
                f"""
                UPDATE contacts
                SET archived = 0, archived_at = NULL
                WHERE archived = 1 AND email IN ({placeholders})
                """,
                emails,
            )
        elif all_archived:
            cursor.execute("""
                UPDATE contacts
                SET archived = 0, archived_at = NULL
                WHERE archived = 1
            """)
        else:
            conn.close()
            return 0

        restored_count = cursor.rowcount
        conn.commit()
        conn.close()
        return restored_count

    def approve_recent_contacts(self, limit: int = 20, recent_hours: Optional[int] = None) -> int:
        """Mark the newest review contacts as approved/sendable."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        conditions = [self.REVIEW_WHERE]
        params: List[object] = []

        if recent_hours is not None:
            conditions.append("datetime(created_at) > datetime('now', '-' || ? || ' hours')")
            params.append(recent_hours)

        where_sql = " AND ".join(conditions)
        params.append(limit)

        cursor.execute(
            f"""
            UPDATE contacts
            SET consent = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id IN (
                SELECT id
                FROM contacts
                WHERE {where_sql}
                ORDER BY datetime(created_at) DESC, email ASC
                LIMIT ?
            )
            """,
            params,
        )

        approved_count = cursor.rowcount
        conn.commit()
        conn.close()
        return approved_count

    def approve_contacts(self, emails: List[str]) -> int:
        """Mark the provided contacts as approved/sendable."""
        normalized_emails = [email.strip().lower() for email in emails if email and email.strip()]
        if not normalized_emails:
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        placeholders = ','.join(['?' for _ in normalized_emails])
        cursor.execute(
            f"""
            UPDATE contacts
            SET consent = 1, updated_at = CURRENT_TIMESTAMP
            WHERE archived = 0
              AND sent = 0
              AND bounced = 0
              AND unsubscribed = 0
              AND email IN ({placeholders})
            """,
            normalized_emails,
        )

        approved_count = cursor.rowcount
        conn.commit()
        conn.close()
        return approved_count

    def upsert_contact_for_verification(
        self,
        email: str,
        name: str = '',
        source: str = 'verification_request',
    ) -> int:
        """Ensure a contact row exists before creating a verification request."""
        normalized_email = email.strip().lower()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, source FROM contacts WHERE email = ?", (normalized_email,))
        row = cursor.fetchone()

        if row:
            contact_id, existing_name, existing_source = row
            cursor.execute(
                """
                UPDATE contacts
                SET
                    name = CASE
                        WHEN COALESCE(name, '') = '' AND ? != '' THEN ?
                        ELSE name
                    END,
                    source = CASE
                        WHEN COALESCE(source, '') = '' AND ? != '' THEN ?
                        ELSE source
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (name.strip(), name.strip(), source.strip(), source.strip(), contact_id),
            )
            conn.commit()
            conn.close()
            return contact_id

        cursor.execute(
            """
            INSERT INTO contacts (
                email, name, source, verified, verification_status, consent, sent
            ) VALUES (?, ?, ?, 0, 'not_requested', 0, 0)
            """,
            (normalized_email, name.strip(), source.strip()),
        )
        contact_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return contact_id

    def create_verification_request(
        self,
        contact_id: int,
        email: str,
        token_hash: str,
        verification_code: str,
        expires_at: str,
        template_name: str = 'email_verification',
    ) -> int:
        """Store a new verification request and supersede older pending ones."""
        normalized_email = email.strip().lower()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE email_verification_requests
            SET status = 'superseded'
            WHERE email = ? AND status IN ('pending', 'sent')
            """,
            (normalized_email,),
        )
        cursor.execute(
            """
            INSERT INTO email_verification_requests (
                contact_id, email, token_hash, verification_code, template_name, status, expires_at
            ) VALUES (?, ?, ?, ?, ?, 'pending', ?)
            """,
            (contact_id, normalized_email, token_hash, verification_code, template_name, expires_at),
        )
        request_id = cursor.lastrowid
        cursor.execute(
            """
            UPDATE contacts
            SET verification_status = 'pending', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (contact_id,),
        )

        conn.commit()
        conn.close()
        return request_id

    def set_verification_request_status(self, request_id: int, status: str) -> bool:
        """Update a verification request and keep the contact's latest status in sync."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT contact_id
            FROM email_verification_requests
            WHERE id = ?
            """,
            (request_id,),
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False

        contact_id = row[0]
        cursor.execute(
            """
            UPDATE email_verification_requests
            SET status = ?
            WHERE id = ?
            """,
            (status, request_id),
        )

        if status == 'sent':
            cursor.execute(
                """
                UPDATE contacts
                SET verification_status = 'sent',
                    verification_sent_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (contact_id,),
            )
        elif status in {'failed', 'expired'}:
            cursor.execute(
                """
                UPDATE contacts
                SET verification_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, contact_id),
            )

        conn.commit()
        conn.close()
        return True

    def confirm_verification(
        self,
        *,
        token_hash: Optional[str] = None,
        email: Optional[str] = None,
        verification_code: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[Dict[str, object]]]:
        """Confirm a verification request by token hash or email + code."""
        if not token_hash and not (email and verification_code):
            return False, "Provide a token or an email + verification code", None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if token_hash:
            cursor.execute(
                """
                SELECT id, contact_id, email, status, expires_at,
                       CASE WHEN datetime(expires_at) <= datetime('now') THEN 1 ELSE 0 END AS is_expired
                FROM email_verification_requests
                WHERE token_hash = ?
                ORDER BY requested_at DESC
                LIMIT 1
                """,
                (token_hash,),
            )
        else:
            cursor.execute(
                """
                SELECT id, contact_id, email, status, expires_at,
                       CASE WHEN datetime(expires_at) <= datetime('now') THEN 1 ELSE 0 END AS is_expired
                FROM email_verification_requests
                WHERE email = ? AND verification_code = ?
                ORDER BY requested_at DESC
                LIMIT 1
                """,
                (email.strip().lower(), verification_code.strip()),
            )

        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Verification request not found", None

        request_id, contact_id, matched_email, status, expires_at, is_expired = row

        if status == 'verified':
            conn.close()
            return True, "Email already verified", {
                'request_id': request_id,
                'contact_id': contact_id,
                'email': matched_email,
                'expires_at': expires_at,
            }

        if is_expired:
            cursor.execute(
                """
                UPDATE email_verification_requests
                SET status = 'expired'
                WHERE id = ?
                """,
                (request_id,),
            )
            cursor.execute(
                """
                UPDATE contacts
                SET verification_status = 'expired', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (contact_id,),
            )
            conn.commit()
            conn.close()
            return False, "Verification request has expired", None

        if status not in {'pending', 'sent'}:
            conn.close()
            return False, f"Verification request is {status}", None

        cursor.execute(
            """
            UPDATE email_verification_requests
            SET status = 'verified', verified_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (request_id,),
        )
        cursor.execute(
            """
            UPDATE email_verification_requests
            SET status = 'superseded'
            WHERE email = ? AND id != ? AND status IN ('pending', 'sent')
            """,
            (matched_email, request_id),
        )
        cursor.execute(
            """
            UPDATE contacts
            SET verified = 1,
                verification_status = 'verified',
                verified_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (contact_id,),
        )

        conn.commit()
        conn.close()
        return True, "Email verified successfully", {
            'request_id': request_id,
            'contact_id': contact_id,
            'email': matched_email,
            'expires_at': expires_at,
        }

    def get_verification_status(self, email: str) -> Optional[Dict[str, object]]:
        """Return the latest verification state for a contact email."""
        normalized_email = email.strip().lower()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, email, verified, verification_status, verification_sent_at, verified_at
            FROM contacts
            WHERE email = ?
            """,
            (normalized_email,),
        )
        contact_row = cursor.fetchone()
        if not contact_row:
            conn.close()
            return None

        cursor.execute(
            """
            SELECT id, status, template_name, requested_at, expires_at, verified_at
            FROM email_verification_requests
            WHERE email = ?
            ORDER BY requested_at DESC, id DESC
            LIMIT 1
            """,
            (normalized_email,),
        )
        request_row = cursor.fetchone()
        conn.close()

        latest_request = None
        if request_row:
            latest_request = {
                'request_id': request_row[0],
                'status': request_row[1],
                'template_name': request_row[2],
                'requested_at': request_row[3],
                'expires_at': request_row[4],
                'verified_at': request_row[5],
            }

        return {
            'contact_id': contact_row[0],
            'email': contact_row[1],
            'verified': bool(contact_row[2]),
            'verification_status': contact_row[3],
            'verification_sent_at': contact_row[4],
            'verified_at': contact_row[5],
            'latest_request': latest_request,
        }

    def _load_contacts_from_file(self, path: Path) -> List[Dict[str, str]]:
        """Load contacts from CSV when possible, otherwise fall back to raw email extraction."""
        if path.suffix.lower() == '.csv':
            csv_contacts = self._load_contacts_from_csv(path)
            if csv_contacts is not None:
                return csv_contacts

        raw_contacts: List[Dict[str, str]] = []
        content = path.read_text(encoding='utf-8', errors='ignore')
        seen = set()
        validator = EmailValidator(
            enable_virus_check=False,
            enable_source_verification=False,
        )

        for token in content.replace('\n', ' ').split():
            candidate = token.strip(" \t\r\n,;<>[](){}\"'")
            if '@' not in candidate:
                continue
            is_valid, _ = validator.is_valid_email(candidate)
            if is_valid and candidate.lower() not in seen:
                raw_contacts.append({'email': candidate.lower()})
                seen.add(candidate.lower())

        return raw_contacts

    def _load_contacts_from_csv(self, path: Path) -> Optional[List[Dict[str, str]]]:
        """Read a CSV file with an email column if present."""
        with path.open('r', encoding='utf-8', errors='ignore', newline='') as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                return None

            field_map = {field.lower().strip(): field for field in reader.fieldnames if field}
            if 'email' not in field_map:
                return None

            contacts = []
            seen = set()
            for row in reader:
                email = (row.get(field_map['email']) or '').strip().lower()
                if not email or email in seen:
                    continue
                contacts.append({
                    'email': email,
                    'name': (row.get(field_map.get('name', ''), '') or '').strip(),
                    'company': (row.get(field_map.get('company', ''), '') or '').strip(),
                    'department': (row.get(field_map.get('department', ''), '') or '').strip(),
                    'country': (row.get(field_map.get('country', ''), '') or '').strip(),
                })
                seen.add(email)

        return contacts


def initialize_db():
    """CLI function to initialize database"""
    manager = DatabaseManager()
    manager.initialize_database()
    manager.insert_default_template()
    print(f"\nDatabase Stats:")
    print(f"  Total contacts: {manager.get_contact_count()}")
    print(f"  Unsent emails: {manager.get_unsent_count()}")


if __name__ == "__main__":
    initialize_db()

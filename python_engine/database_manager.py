"""
Database Initialization and Management
Sets up SQLite database with proper schema for email campaigns
"""
import sqlite3
import os
from datetime import datetime
from pathlib import Path


class DatabaseManager:
    """Manages SQLite database for campaign management"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', './database/devnav.db')
        self.db_path = db_path
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
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
                consent INTEGER DEFAULT 0,
                sent INTEGER DEFAULT 0,
                opened INTEGER DEFAULT 0,
                bounced INTEGER DEFAULT 0,
                unsubscribed INTEGER DEFAULT 0,
                data_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
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
            CREATE INDEX IF NOT EXISTS idx_email_logs_contact ON email_logs(contact_id)
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
        
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO email_templates (name, subject, body, is_default)
                VALUES (?, ?, ?, 1)
            """, (default_template['name'], default_template['subject'], default_template['body']))
            
            conn.commit()
            print("✓ Default template inserted")
        except sqlite3.IntegrityError:
            print("~ Default template already exists")
        finally:
            conn.close()
    
    def get_contact_count(self) -> int:
        """Get total contact count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM contacts")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_unsent_count(self) -> int:
        """Get count of unsent emails"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE sent = 0 AND consent = 1")
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

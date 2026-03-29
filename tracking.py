#!/usr/bin/env python3
"""
Email Tracking System
Track opens and clicks from sent emails
"""
import os
import sqlite3
import hashlib
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class EmailTracker:
    """Generate tracking pixels and manage tracking data"""
    
    def __init__(self, db_path=None, tracking_server_url=None):
        self.db_path = db_path or os.getenv('DATABASE_PATH', './database/devnav.db')
        self.tracking_server_url = tracking_server_url or os.getenv('TRACKING_SERVER_URL', 'http://localhost:8888')
        self.tracking_pixel_endpoint = f"{self.tracking_server_url}/track/pixel"
        self.tracking_click_endpoint = f"{self.tracking_server_url}/track/click"
    
    def generate_tracking_id(self, email, campaign_id=None):
        """Generate unique tracking ID for email"""
        data = f"{email}:{datetime.now().isoformat()}:{uuid.uuid4()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def get_tracking_pixel(self, email, campaign_id=None):
        """Get invisible tracking pixel URL for email opens"""
        tracking_id = self.generate_tracking_id(email, campaign_id)
        pixel_url = f"{self.tracking_pixel_endpoint}?id={tracking_id}&email={email}"
        
        # Store tracking ID in database
        self._store_tracking(email, tracking_id, 'pixel')
        
        # Return HTML pixel
        return f'<img src="{pixel_url}" width="1" height="1" alt="" />'
    
    def get_tracking_link(self, url, email, link_name="click"):
        """Wrap URL for click tracking"""
        tracking_id = self.generate_tracking_id(email)
        tracked_url = f"{self.tracking_click_endpoint}?id={tracking_id}&email={email}&link={link_name}&redirect={url}"
        
        self._store_tracking(email, tracking_id, 'link', link_name)
        
        return tracked_url
    
    def _store_tracking(self, email, tracking_id, tracking_type, link_name=None):
        """Store tracking ID in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if tracking table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    tracking_id TEXT UNIQUE NOT NULL,
                    tracking_type TEXT,
                    link_name TEXT,
                    opened INTEGER DEFAULT 0,
                    clicked INTEGER DEFAULT 0,
                    open_time TIMESTAMP,
                    click_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                INSERT OR IGNORE INTO email_tracking 
                (email, tracking_id, tracking_type, link_name) 
                VALUES (?, ?, ?, ?)
            """, (email, tracking_id, tracking_type, link_name))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not store tracking: {e}")
    
    def record_open(self, tracking_id):
        """Record email open"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE email_tracking 
                SET opened = 1, open_time = CURRENT_TIMESTAMP 
                WHERE tracking_id = ? AND opened = 0
            """, (tracking_id,))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error recording open: {e}")
            return False
    
    def record_click(self, tracking_id):
        """Record link click"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE email_tracking 
                SET clicked = 1, click_time = CURRENT_TIMESTAMP 
                WHERE tracking_id = ?
            """, (tracking_id,))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error recording click: {e}")
            return False
    
    def get_tracking_stats(self, email=None):
        """Get tracking statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if email:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(opened) as opened,
                        SUM(clicked) as clicked
                    FROM email_tracking 
                    WHERE email = ?
                """, (email,))
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(opened) as opened,
                        SUM(clicked) as clicked
                    FROM email_tracking
                """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                total, opened, clicked = result
                return {
                    'total_sent': total or 0,
                    'opens': opened or 0,
                    'clicks': clicked or 0,
                    'open_rate': f"{(opened / total * 100):.1f}%" if total else "0%",
                    'click_rate': f"{(clicked / total * 100):.1f}%" if total else "0%"
                }
            return None
        except Exception as e:
            print(f"Error fetching stats: {e}")
            return None
    
    def get_detailed_tracking(self):
        """Get detailed tracking info per email"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    email,
                    COUNT(*) as total,
                    SUM(opened) as opens,
                    SUM(clicked) as clicks,
                    MAX(open_time) as last_open,
                    MAX(click_time) as last_click
                FROM email_tracking 
                GROUP BY email
                ORDER BY email
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            return results
        except Exception as e:
            print(f"Error fetching detailed tracking: {e}")
            return []


def show_stats():
    """Display tracking statistics"""
    tracker = EmailTracker()
    stats = tracker.get_tracking_stats()
    
    if stats:
        print("\n╔════════════════════════════════════════════════════════════╗")
        print("║              📊 EMAIL TRACKING STATISTICS                ║")
        print("╚════════════════════════════════════════════════════════════╝\n")
        
        print(f"📧 Total Sent:    {stats['total_sent']}")
        print(f"👁️  Opened:       {stats['opens']} ({stats['open_rate']})")
        print(f"🔗 Clicked:       {stats['clicks']} ({stats['click_rate']})\n")
        
        # Detailed per-email
        print("📋 Detailed Tracking by Email:")
        print("=" * 70)
        
        detailed = tracker.get_detailed_tracking()
        if detailed:
            for email, total, opens, clicks, last_open, last_click in detailed:
                print(f"\n📧 {email}")
                print(f"   Opens:  {opens or 0}/{total} | Last: {last_open or 'Never'}")
                print(f"   Clicks: {clicks or 0}/{total} | Last: {last_click or 'Never'}")
        else:
            print("  No tracking data yet")
    else:
        print("❌ No tracking data available")


def show_help():
    """Show help message"""
    print("""
📊 Email Tracking System

Usage:
  python3 tracking.py stats          # Show tracking statistics
  python3 tracking.py setup-server   # Start tracking server (for opens/clicks)

Requirements to enable full tracking:
  1. Run tracking server:
     python3 tracking.py setup-server
  
  2. Update .env with:
     TRACKING_SERVER_URL=http://your-server:8888

How Tracking Works:
  
  📨 OPEN TRACKING
    - Invisible 1x1 pixel embedded in HTML emails
    - Loads from tracking server when recipient opens email
    - Recorded in database
  
  🔗 CLICK TRACKING
    - Links wrapped with tracking URL
    - Redirects to original link after recording
    - User doesn't see tracking
  
  💾 DATABASE
    - All tracking stored in sqlite3
    - email_tracking table auto-created
    - Timestamps recorded for each action

Examples:
  # Check overall stats
  python3 tracking.py stats
  
  # Start tracking server on port 8888
  python3 tracking.py setup-server
  
  # With custom port
  python3 tracking.py setup-server --port 9000

Privacy Notes:
  ✓ Compliant with CAN-SPAM (with unsubscribe links)
  ✓ Does NOT collect location/device info
  ✓ Only tracks open/click events
  ✓ No third-party sharing
    """)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        show_help()
    else:
        command = sys.argv[1]
        
        if command == 'stats':
            show_stats()
        
        elif command == 'setup-server':
            # Start tracking server
            try:
                from http.server import HTTPServer, BaseHTTPRequestHandler
                import json
                import urllib.parse
                
                class TrackingHandler(BaseHTTPRequestHandler):
                    """Handle tracking requests"""
                    
                    def do_GET(self):
                        """Handle GET requests for tracking"""
                        parsed_path = urllib.parse.urlparse(self.path)
                        query_params = urllib.parse.parse_qs(parsed_path.query)
                        
                        if parsed_path.path == '/track/pixel':
                            # Pixel tracking (email opens)
                            tracking_id = query_params.get('id', [None])[0]
                            email = query_params.get('email', [None])[0]
                            
                            if tracking_id:
                                tracker = EmailTracker()
                                tracker.record_open(tracking_id)
                                print(f"✓ OPEN TRACKED: {email} ({tracking_id})")
                            
                            # Return 1x1 transparent GIF
                            self.send_response(200)
                            self.send_header('Content-type', 'image/gif')
                            self.end_headers()
                            self.wfile.write(b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b')
                        
                        elif parsed_path.path == '/track/click':
                            # Click tracking
                            tracking_id = query_params.get('id', [None])[0]
                            email = query_params.get('email', [None])[0]
                            link_name = query_params.get('link', ['unknown'])[0]
                            redirect_url = query_params.get('redirect', [''])[0]
                            
                            if tracking_id:
                                tracker = EmailTracker()
                                tracker.record_click(tracking_id)
                                print(f"✓ CLICK TRACKED: {email} - {link_name} ({tracking_id})")
                            
                            # Redirect to original link
                            if redirect_url:
                                self.send_response(302)
                                self.send_header('Location', redirect_url)
                                self.end_headers()
                            else:
                                self.send_response(200)
                                self.send_header('Content-type', 'text/html')
                                self.end_headers()
                                self.wfile.write(b'<html><body>Thank you!</body></html>')
                        
                        else:
                            self.send_response(404)
                            self.end_headers()
                    
                    def log_message(self, format, *args):
                        """Suppress default logging"""
                        pass
                
                port = 8888
                if '--port' in sys.argv:
                    idx = sys.argv.index('--port')
                    if idx + 1 < len(sys.argv):
                        port = int(sys.argv[idx + 1])
                
                server = HTTPServer(('0.0.0.0', port), TrackingHandler)
                
                print(f"""
╔════════════════════════════════════════════════════════════╗
║          📊 EMAIL TRACKING SERVER RUNNING                 ║
╚════════════════════════════════════════════════════════════╝

🚀 Server: http://localhost:{port}
📍 Tracking Endpoints:
   - Pixel:  http://localhost:{port}/track/pixel
   - Click:  http://localhost:{port}/track/click

⚙️  Configuration:
   - Update .env with: TRACKING_SERVER_URL=http://your-ip:{port}
   - Tracking pixels embedded in HTML emails
   - Links wrapped for click tracking
   - All events logged to SQLite database

📝 Tracking logs will appear below:
════════════════════════════════════════════════════════════
                """)
                
                server.serve_forever()
            
            except Exception as e:
                print(f"❌ Error starting tracking server: {e}")
                print("\nMake sure port 8888 is available")
                print("Use --port XXXX to change port")
        
        elif command == 'help':
            show_help()
        
        else:
            print(f"Unknown command: {command}")
            show_help()

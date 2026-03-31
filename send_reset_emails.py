"""
Password Reset Email Sender
This script checks for users who requested password reset and sends them emails via SMTP.
"""

import sqlite3
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "my-express-app", "user.db")

# Email configuration - Uses environment variables for security
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", SMTP_USERNAME)
FROM_NAME = "CYBERGHOST Admin"

def send_reset_email(to_email, user_id):
    """
    Send a password reset email to the user.
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("❌ Email not configured. Set SMTP_USERNAME and SMTP_PASSWORD environment variables.")
        return False
    
    subject = "CYBERGHOST - Password Reset Approved"
    
    # Email body
    body = f"""
    Hello,
    
    Your password reset request has been approved by the admin.
    
    Please contact the admin to get your new password or reset it through the website if available.
    
    If you didn't request this, please ignore this email.
    
    - CYBERGHOST Team
    """
    
    msg = MIMEMultipart()
    msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        return False

def process_reset_requests():
    """
    Check database for users who requested password reset and send them emails.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all users who requested reset
    cursor.execute("""
        SELECT id, email, reset_requested_at 
        FROM users 
        WHERE reset_requested = 1 AND role != 'admin'
    """)
    
    users = cursor.fetchall()
    
    if not users:
        print("No pending password reset requests.")
        conn.close()
        return
    
    print(f"Found {len(users)} user(s) waiting for password reset:\n")
    
    for user_id, email, requested_at in users:
        print(f"Processing user ID {user_id}: {email}")
        print(f"  Requested at: {requested_at}")
        
        # Send email
        success = send_reset_email(email, user_id)
        
        if success:
            print(f"  ✓ Email sent to {email}")
        else:
            print(f"  ✗ Failed to send email to {email}")
    
    conn.close()
    print("\nDone processing reset requests.")

def approve_reset(user_id):
    """
    Manually approve a reset request for a specific user and send email.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        print(f"User ID {user_id} not found.")
        conn.close()
        return
    
    email = row[0]
    
    # Send email
    success = send_reset_email(email, user_id)
    
    if success:
        print(f"✅ Reset email sent to {email} (User ID: {user_id})")
    else:
        print(f"❌ Failed to send email to {email}")
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    print("CYBERGHOST Password Reset Email Sender")
    print("=" * 40)
    
    # Check if email is configured
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("\n⚠️  Email not configured!")
        print("Set environment variables before running:")
        print("  Windows PowerShell:")
        print('    $env:SMTP_USERNAME="matteopennacchia43@gmail.com"')
        print('    $env:SMTP_PASSWORD="Mygmailaccount89"')
        print("\n  Or run in same terminal:")
        print('    set SMTP_USERNAME=matteopennacchia43@gmail.com')
        print('    set SMTP_PASSWORD=Mygmailaccount89')
        print("\n  Then run: python send_reset_emails.py")
        sys.exit(1)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--approve":
        # Approve specific user: python send_reset_emails.py --approve 5
        user_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
        if user_id:
            approve_reset(user_id)
        else:
            print("Usage: python send_reset_emails.py --approve <user_id>")
    else:
        # Process all pending requests
        process_reset_requests()

#!/usr/bin/env python3
"""
Email Notification Popup System
Monitors Gmail for new emails and shows popup notifications with sound alerts.
Also sends a copy of all outgoing emails to the administrator.
"""
import os
import sys
import imaplib
import email
from email.header import decode_header
import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configuration
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'matteopennacchia43@gmail.com')
CHECK_INTERVAL = 30  # Check for new emails every 30 seconds
NOTIFICATION_SOUND_ENABLED = True
POPUP_DURATION = 10  # Show popup for 10 seconds


class EmailNotifier:
    """Monitors Gmail and shows popup notifications for new emails."""

    def __init__(self):
        self.imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        self.imap_port = int(os.getenv('IMAP_PORT', '993'))
        self.email_address = os.getenv('EMAIL_ADDRESS', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.running = False
        self.last_check = None
        self.seen_emails = set()

    def connect(self):
        """Connect to Gmail IMAP server."""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mail.login(self.email_address, self.email_password)
            print(f"✓ Connected to {self.imap_server}")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect from IMAP server."""
        try:
            self.mail.close()
            self.mail.logout()
        except:
            pass

    def decode_subject(self, subject):
        """Decode email subject."""
        if subject is None:
            return "(No Subject)"

        decoded_parts = decode_header(subject)
        subject_parts = []

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    subject_parts.append(part.decode(encoding))
                else:
                    subject_parts.append(part.decode('utf-8', errors='ignore'))
            else:
                subject_parts.append(part)

        return ' '.join(subject_parts)

    def get_email_body(self, msg):
        """Extract email body from message."""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode()
                        break
                    except:
                        pass
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode()
                    except:
                        pass
        else:
            content_type = msg.get_content_type()
            if content_type == "text/plain":
                try:
                    body = msg.get_payload(decode=True).decode()
                except:
                    pass
            elif content_type == "text/html":
                try:
                    body = msg.get_payload(decode=True).decode()
                except:
                    pass

        return body[:500]  # Limit to 500 characters

    def check_new_emails(self):
        """Check for new emails in inbox."""
        try:
            self.mail.select('INBOX')
            status, messages = self.mail.search(None, 'UNSEEN')

            if status != 'OK':
                return []

            email_ids = messages[0].split()
            new_emails = []

            for email_id in email_ids:
                if email_id in self.seen_emails:
                    continue

                status, msg_data = self.mail.fetch(email_id, '(RFC822)')

                if status != 'OK':
                    continue

                msg = email.message_from_bytes(msg_data[0][1])

                subject = self.decode_subject(msg['Subject'])
                from_addr = msg['From']
                date = msg['Date']
                body = self.get_email_body(msg)

                new_emails.append({
                    'id': email_id,
                    'subject': subject,
                    'from': from_addr,
                    'date': date,
                    'body': body
                })

                self.seen_emails.add(email_id)

            return new_emails
        except Exception as e:
            print(f"✗ Error checking emails: {e}")
            return []

    def play_notification_sound(self):
        """Play a bleep notification sound."""
        if not NOTIFICATION_SOUND_ENABLED:
            return

        try:
            # Try to use system bell
            print('\a', end='', flush=True)

            # Also try pygame if available
            try:
                import pygame
                pygame.mixer.init()
                # Generate a simple beep sound
                import numpy as np
                sample_rate = 44100
                duration = 0.3
                frequency = 880
                t = np.linspace(0, duration, int(sample_rate * duration))
                wave = np.sin(2 * np.pi * frequency * t)
                wave = (wave * 32767).astype(np.int16)
                pygame.mixer.Sound(wave).play()
            except ImportError:
                pass
        except:
            pass

    def show_popup(self, email_data):
        """Show a tkinter popup notification for a new email."""
        def create_popup():
            root = tk.Tk()
            root.title("📧 New Email Notification")
            root.geometry("500x400")
            root.configure(bg='#2b2b2b')

            # Make window stay on top
            root.attributes('-topmost', True)

            # Header
            header_frame = tk.Frame(root, bg='#1e1e1e', pady=10)
            header_frame.pack(fill=tk.X)

            tk.Label(
                header_frame,
                text="📧 New Email Received",
                font=('Arial', 16, 'bold'),
                fg='#00ff00',
                bg='#1e1e1e'
            ).pack()

            # Email details
            details_frame = tk.Frame(root, bg='#2b2b2b', pady=10)
            details_frame.pack(fill=tk.X, padx=10)

            tk.Label(
                details_frame,
                text=f"From: {email_data['from']}",
                font=('Arial', 10),
                fg='#ffffff',
                bg='#2b2b2b',
                anchor='w'
            ).pack(fill=tk.X)

            tk.Label(
                details_frame,
                text=f"Subject: {email_data['subject']}",
                font=('Arial', 10, 'bold'),
                fg='#ffff00',
                bg='#2b2b2b',
                anchor='w'
            ).pack(fill=tk.X)

            tk.Label(
                details_frame,
                text=f"Date: {email_data['date']}",
                font=('Arial', 9),
                fg='#888888',
                bg='#2b2b2b',
                anchor='w'
            ).pack(fill=tk.X)

            # Email body
            body_frame = tk.Frame(root, bg='#2b2b2b', pady=10)
            body_frame.pack(fill=tk.BOTH, expand=True, padx=10)

            tk.Label(
                body_frame,
                text="Content:",
                font=('Arial', 10, 'bold'),
                fg='#ffffff',
                bg='#2b2b2b',
                anchor='w'
            ).pack(fill=tk.X)

            body_text = scrolledtext.ScrolledText(
                body_frame,
                wrap=tk.WORD,
                font=('Arial', 9),
                fg='#ffffff',
                bg='#1e1e1e',
                height=10
            )
            body_text.pack(fill=tk.BOTH, expand=True)
            body_text.insert(tk.END, email_data['body'])
            body_text.config(state=tk.DISABLED)

            # Close button
            button_frame = tk.Frame(root, bg='#2b2b2b', pady=10)
            button_frame.pack(fill=tk.X)

            tk.Button(
                button_frame,
                text="Close",
                command=root.destroy,
                font=('Arial', 10),
                bg='#ff4444',
                fg='#ffffff',
                padx=20
            ).pack()

            # Play sound
            self.play_notification_sound()

            # Auto-close after POPUP_DURATION seconds
            root.after(POPUP_DURATION * 1000, root.destroy)

            root.mainloop()

        # Run popup in a separate thread
        popup_thread = threading.Thread(target=create_popup, daemon=True)
        popup_thread.start()

    def start_monitoring(self):
        """Start monitoring for new emails."""
        if not self.connect():
            return

        self.running = True
        print(f"✓ Started monitoring {self.email_address}")
        print(f"  Checking every {CHECK_INTERVAL} seconds")
        print(f"  Admin email: {ADMIN_EMAIL}")
        print(f"  Press Ctrl+C to stop\n")

        try:
            while self.running:
                new_emails = self.check_new_emails()

                for email_data in new_emails:
                    print(f"\n📧 New email from: {email_data['from']}")
                    print(f"   Subject: {email_data['subject']}")
                    print(f"   Date: {email_data['date']}")

                    # Show popup notification
                    self.show_popup(email_data)

                if new_emails:
                    print(f"\n✓ Found {len(new_emails)} new email(s)")

                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n\n✓ Stopping email monitor...")
        finally:
            self.disconnect()
            self.running = False


def send_notification_email(subject, body, recipient=ADMIN_EMAIL):
    """Send a notification email to the administrator."""
    from send_test_emails import EmailSender

    sender = EmailSender()

    notification_subject = f"[DevNavigator Notification] {subject}"
    notification_body = f"""
📧 EMAIL NOTIFICATION
{'=' * 60}

This is an automated notification from DevNavigator.

{body}

{'=' * 60}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    success, message = sender.send_test_email(
        to_email=recipient,
        subject=notification_subject,
        body=notification_body,
        from_name="DevNavigator Notifier"
    )

    if success:
        print(f"✓ Notification sent to {recipient}")
    else:
        print(f"✗ Failed to send notification: {message}")

    return success


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Email Notification System')
    parser.add_argument('--monitor', action='store_true', help='Start monitoring for new emails')
    parser.add_argument('--test', action='store_true', help='Send a test notification')
    parser.add_argument('--check-once', action='store_true', help='Check for new emails once and exit')

    args = parser.parse_args()

    if args.test:
        print("📧 Sending test notification...")
        send_notification_email(
            subject="Test Notification",
            body="This is a test notification from DevNavigator Email Notifier.\n\nIf you receive this, the notification system is working correctly!"
        )
    elif args.check_once:
        notifier = EmailNotifier()
        if notifier.connect():
            new_emails = notifier.check_new_emails()
            print(f"✓ Found {len(new_emails)} new email(s)")
            for email_data in new_emails:
                print(f"\n📧 From: {email_data['from']}")
                print(f"   Subject: {email_data['subject']}")
            notifier.disconnect()
    elif args.monitor:
        notifier = EmailNotifier()
        notifier.start_monitoring()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

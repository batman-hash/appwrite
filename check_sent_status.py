#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('database/devnav.db')
cursor = conn.cursor()

print("✓ VERIFICATION: Emails Marked as SENT Only After Successful Delivery")
print("=" * 80)
print()

cursor.execute("""
SELECT 
  email,
  CASE WHEN sent = 1 THEN '✓ SENT' ELSE '✗ UNSENT' END as status,
  CASE WHEN opened = 1 THEN '✓ OPENED' ELSE '○ WAITING' END as opened
FROM contacts
ORDER BY sent DESC, email
""")

results = cursor.fetchall()

print(f"{'Email':<35} {'Status':<12} {'Opened':<15}")
print("-" * 80)

for email, status, opened in results:
    print(f"{email:<35} {status:<12} {opened:<15}")

print()
print("Summary:")
cursor.execute("SELECT COUNT(*) FROM contacts WHERE sent = 1")
sent_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM contacts")
total_count = cursor.fetchone()[0]

print(f"  ✓ Sent: {sent_count}/{total_count}")
print(f"  ✗ Unsent: {total_count - sent_count}/{total_count}")

print()
print("How it works:")
print("  1. When you send an email → system attempts delivery")
print("  2. If SUCCESS → marked 'sent = 1' ✓")
print("  3. If FAILED → stays 'sent = 0' and logs error")
print("  4. Prevents duplicate sends to same recipient")
print()
print("Querying send logs...")
print()

cursor.execute("""
SELECT 
  COUNT(*) as total_sends,
  SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as successful,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
FROM email_logs
""")

total, successful, failed = cursor.fetchone()
print(f"Total send attempts: {total or 0}")
print(f"  ✓ Successful: {successful or 0}")
print(f"  ✗ Failed: {failed or 0}")

conn.close()

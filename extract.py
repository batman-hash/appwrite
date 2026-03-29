#!/usr/bin/env python3
"""
Automated Email Extraction Tool
Extract maximum emails from multiple sources
"""
import subprocess
import sys
import sqlite3

def run_command(cmd):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def get_email_count():
    """Get current email count from database"""
    try:
        conn = sqlite3.connect('database/devnav.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM contacts")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def extraction_menu():
    """Interactive extraction menu"""
    while True:
        count = get_email_count()
        
        print("\n" + "="*80)
        print(f"📧 EXTRACTION TOOL - Current: {count} emails")
        print("="*80)
        print()
        print("QUICK EXTRACTIONS:")
        print("  1. 🔍 GitHub Search - Junior Developers")
        print("  2. 🔍 GitHub Search - Freelancers")
        print("  3. 🔍 GitHub Search - Remote Workers")
        print("  4. 🔍 GitHub Search - Money-Motivated")
        print("  5. 🔍 GitHub Search - Custom Query")
        print()
        print("ADVANCED:")
        print("  6. 📊 Filtered Search - Junior + Frontend + Remote")
        print("  7. 📊 Filtered Search - Job Seekers")
        print("  8. 📊 Filtered Search - Money Motivated")
        print("  9. 📁 Import from CSV file")
        print()
        print("RESULTS:")
        print("  10. 📋 View all emails")
        print("  11. 📊 Show statistics")
        print("  12. 💾 Export to CSV")
        print()
        print("  0. ❌ Exit")
        print()
        
        choice = input("Select option (0-12): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            print("\n🔍 Searching GitHub for junior developers...")
            extract_github("junior developer remote")
        elif choice == "2":
            print("\n🔍 Searching GitHub for freelancers...")
            extract_github("freelance javascript")
        elif choice == "3":
            print("\n🔍 Searching GitHub for remote workers...")
            extract_github("remote developer available")
        elif choice == "4":
            print("\n🔍 Searching GitHub for money-motivated...")
            extract_github("developer available for hire")
        elif choice == "5":
            query = input("Enter search query: ").strip()
            if query:
                print(f"\n🔍 Searching GitHub for: {query}")
                extract_github(query)
        elif choice == "6":
            print("\n📊 Filtered search: Junior + Frontend + Remote")
            extract_filtered("--junior 70 --frontend 60 --remote 50")
        elif choice == "7":
            print("\n📊 Filtered search: Job Seekers")
            extract_filtered("--job_seeker 80")
        elif choice == "8":
            print("\n📊 Filtered search: Money Motivated")
            extract_filtered("--money_motivated 75 --remote 60")
        elif choice == "9":
            file = input("Enter CSV filename: ").strip()
            if file:
                print(f"\n📁 Importing from {file}...")
                extract_file(file)
        elif choice == "10":
            view_emails()
        elif choice == "11":
            show_stats()
        elif choice == "12":
            export_csv()

def extract_github(query):
    """Extract from GitHub"""
    before = get_email_count()
    success, output = run_command(f'python3 devnavigator.py search-auto --query "{query}"')
    after = get_email_count()
    
    if success:
        print(f"✓ Added {after - before} new emails")
        print(f"  Total now: {after} emails")
    else:
        print(f"✗ Search failed")

def extract_filtered(filters):
    """Extract with filters"""
    before = get_email_count()
    success, output = run_command(f'python3 devnavigator.py search-filtered {filters}')
    after = get_email_count()
    
    if success:
        print(f"✓ Added {after - before} filtered emails")
        print(f"  Total now: {after} emails")
    else:
        print(f"✗ Filtered search failed")

def extract_file(filename):
    """Extract from file"""
    before = get_email_count()
    success, output = run_command(f'python3 devnavigator.py extract-emails --file {filename} --store')
    after = get_email_count()
    
    if success:
        print(f"✓ Added {after - before} emails from file")
        print(f"  Total now: {after} emails")
    else:
        print(f"✗ File import failed")

def view_emails():
    """View emails in database"""
    try:
        conn = sqlite3.connect('database/devnav.db')
        cursor = conn.cursor()
        cursor.execute("SELECT email, country FROM contacts ORDER BY email LIMIT 50")
        
        emails = cursor.fetchall()
        print(f"\n📋 First 50 emails (of {get_email_count()} total):")
        print("-" * 60)
        
        for email, country in emails:
            country_str = f"({country})" if country else ""
            print(f"  • {email} {country_str}")
        
        if len(emails) == 50:
            print(f"  ... and {get_email_count() - 50} more")
        
        conn.close()
    except:
        print("✗ Error reading emails")

def show_stats():
    """Show extraction statistics"""
    try:
        conn = sqlite3.connect('database/devnav.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM contacts")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE sent = 1")
        sent = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE opened = 1")
        opened = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT country) FROM contacts WHERE country IS NOT NULL")
        countries = cursor.fetchone()[0]
        
        print(f"\n📊 Statistics:")
        print(f"  Total emails: {total}")
        print(f"  Sent: {sent}")
        print(f"  Opened: {opened}")
        print(f"  Countries represented: {countries}")
        
        conn.close()
    except:
        print("✗ Error reading stats")

def export_csv():
    """Export emails to CSV"""
    try:
        filename = "extracted_emails_export.csv"
        conn = sqlite3.connect('database/devnav.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT email, name, company, country FROM contacts ORDER BY email")
        emails = cursor.fetchall()
        
        with open(filename, 'w') as f:
            f.write("email,name,company,country\n")
            for email, name, company, country in emails:
                name = name or ""
                company = company or ""
                country = country or ""
                f.write(f'{email},"{name}","{company}",{country}\n')
        
        print(f"✓ Exported {len(emails)} emails to {filename}")
        conn.close()
    except:
        print("✗ Export failed")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Command line mode
        cmd = sys.argv[1]
        
        if cmd == "github":
            query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "junior developer remote"
            extract_github(query)
        
        elif cmd == "filter":
            filters = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "--junior 70 --remote 60"
            extract_filtered(filters)
        
        elif cmd == "import":
            file = sys.argv[2] if len(sys.argv) > 2 else "emails.csv"
            extract_file(file)
        
        elif cmd == "stats":
            show_stats()
        
        elif cmd == "view":
            view_emails()
        
        elif cmd == "export":
            export_csv()
        
        else:
            print(f"Unknown command: {cmd}")
            print("\nUsage:")
            print("  python3 extract.py github [QUERY]")
            print("  python3 extract.py filter [FILTERS]")
            print("  python3 extract.py import [FILE]")
            print("  python3 extract.py stats")
            print("  python3 extract.py view")
            print("  python3 extract.py export")
    else:
        # Interactive menu
        extraction_menu()

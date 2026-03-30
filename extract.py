#!/usr/bin/env python3
"""
Legacy extraction helper.

This wrapper keeps older shortcuts working while routing everything through
the main devnavigator CLI so the project has one shared extraction workflow.
"""
import subprocess
import sys
from pathlib import Path


DEFAULT_DB_PATH = Path("database/devnav.db")

FILTER_PRESETS = {
    "junior_frontend_remote": [
        "--title", "junior frontend developer",
        "--keywords", "junior,frontend,react,javascript,remote",
        "--remote",
    ],
    "job_seekers": [
        "--title", "developer seeking opportunities",
        "--keywords", "open to work,job seeker,available,opportunities",
    ],
    "money_motivated": [
        "--title", "freelance developer",
        "--keywords", "freelance,contract,for hire,remote",
        "--remote",
    ],
}


def run_command(args):
    """Run a command and return True when it succeeds."""
    try:
        completed = subprocess.run(args, check=False)
        return completed.returncode == 0
    except Exception as exc:
        print(f"✗ Command failed: {exc}")
        return False


def get_email_count():
    """Read the active contact count from SQLite."""
    if not DEFAULT_DB_PATH.exists():
        return 0

    try:
        completed = subprocess.run(
            [
                "sqlite3",
                str(DEFAULT_DB_PATH),
                "SELECT COUNT(*) FROM contacts WHERE archived = 0;",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            return 0
        return int((completed.stdout or "0").strip() or "0")
    except Exception:
        return 0


def extraction_menu():
    """Interactive extraction menu."""
    while True:
        count = get_email_count()

        print("\n" + "=" * 80)
        print(f"📧 EXTRACTION TOOL - Current: {count} active contacts")
        print("=" * 80)
        print()
        print("QUICK EXTRACTIONS:")
        print("  1. 🔍 GitHub Search - Junior Developers")
        print("  2. 🔍 GitHub Search - Freelancers")
        print("  3. 🔍 GitHub Search - Remote Workers")
        print("  4. 🔍 GitHub Search - Money-Motivated")
        print("  5. 🔍 GitHub Search - Custom Query")
        print()
        print("FILTERED PRESETS:")
        print("  6. 📊 Junior + Frontend + Remote")
        print("  7. 📊 Job Seekers")
        print("  8. 📊 Money Motivated")
        print("  9. 📁 Import from file")
        print()
        print("RESULTS:")
        print("  10. 📋 View contacts")
        print("  11. 📊 Show statistics")
        print("  12. 💾 Export to CSV")
        print()
        print("  0. ❌ Exit")
        print()

        choice = input("Select option (0-12): ").strip()

        if choice == "0":
            break
        if choice == "1":
            extract_github("junior developer remote")
        elif choice == "2":
            extract_github("freelance javascript developer")
        elif choice == "3":
            extract_github("remote developer available")
        elif choice == "4":
            extract_github("developer available for hire")
        elif choice == "5":
            query = input("Enter search query: ").strip()
            if query:
                extract_github(query)
        elif choice == "6":
            extract_filtered("junior_frontend_remote")
        elif choice == "7":
            extract_filtered("job_seekers")
        elif choice == "8":
            extract_filtered("money_motivated")
        elif choice == "9":
            file_name = input("Enter filename: ").strip()
            if file_name:
                extract_file(file_name)
        elif choice == "10":
            view_emails()
        elif choice == "11":
            show_stats()
        elif choice == "12":
            export_csv()


def extract_github(query):
    """Search live sources and store validated results in the main database."""
    before = get_email_count()
    success = run_command([
        "python3", "devnavigator.py", "search-auto",
        "--query", query,
        "--store",
        "--show-limit", "10",
    ])
    after = get_email_count()

    if success:
        print(f"✓ Added {after - before} new contact(s)")
        print(f"  Total now: {after}")
    else:
        print("✗ Search failed")


def extract_filtered(preset_or_args):
    """Run a filtered preset or pass through raw search-filtered args."""
    before = get_email_count()

    if isinstance(preset_or_args, str) and preset_or_args in FILTER_PRESETS:
        cli_args = FILTER_PRESETS[preset_or_args]
    elif isinstance(preset_or_args, list):
        cli_args = preset_or_args
    else:
        cli_args = [str(preset_or_args)]

    command = ["python3", "devnavigator.py", "search-filtered", "--store", *cli_args]
    success = run_command(command)
    after = get_email_count()

    if success:
        print(f"✓ Added {after - before} filtered contact(s)")
        print(f"  Total now: {after}")
    else:
        print("✗ Filtered search failed")


def extract_file(filename):
    """Import contacts from a local file."""
    before = get_email_count()
    success = run_command([
        "python3", "devnavigator.py", "extract-emails",
        "--file", filename,
        "--store",
        "--show-limit", "10",
    ])
    after = get_email_count()

    if success:
        print(f"✓ Added {after - before} contact(s) from file")
        print(f"  Total now: {after}")
    else:
        print("✗ File import failed")


def view_emails():
    """Show the shared queue view."""
    run_command(["python3", "devnavigator.py", "queue", "--queue", "all", "--limit", "50"])


def show_stats():
    """Show shared campaign statistics."""
    run_command(["python3", "devnavigator.py", "stats"])


def export_csv(output_path="extracted_emails_export.csv"):
    """Export contacts to CSV through the main CLI."""
    success = run_command([
        "python3", "devnavigator.py", "export-contacts",
        "--output", output_path,
        "--queue", "all",
    ])
    if success:
        print(f"✓ Exported contacts to {output_path}")
    else:
        print("✗ Export failed")


def show_usage():
    """Show CLI usage."""
    print("Usage:")
    print("  python3 extract.py github [QUERY]")
    print("  python3 extract.py filter [PRESET|SEARCH-FILTERED-ARGS]")
    print("  python3 extract.py import [FILE]")
    print("  python3 extract.py stats")
    print("  python3 extract.py view")
    print("  python3 extract.py export [OUTPUT]")
    print()
    print("Filter presets:")
    for preset in sorted(FILTER_PRESETS):
        print(f"  - {preset}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "github":
            query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "junior developer remote"
            extract_github(query)
        elif command == "filter":
            if len(sys.argv) > 2 and sys.argv[2] in FILTER_PRESETS:
                extract_filtered(sys.argv[2])
            elif len(sys.argv) > 2:
                extract_filtered(sys.argv[2:])
            else:
                extract_filtered("junior_frontend_remote")
        elif command == "import":
            file_name = sys.argv[2] if len(sys.argv) > 2 else "emails.csv"
            extract_file(file_name)
        elif command == "stats":
            show_stats()
        elif command == "view":
            view_emails()
        elif command == "export":
            output = sys.argv[2] if len(sys.argv) > 2 else "extracted_emails_export.csv"
            export_csv(output)
        else:
            print(f"Unknown command: {command}")
            print()
            show_usage()
    else:
        extraction_menu()

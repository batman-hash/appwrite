import sqlite3
from datetime import datetime, timedelta, timezone

from python_engine.database_manager import DatabaseManager


def test_queue_summary_and_filters(tmp_path):
    db_path = tmp_path / "devnav.db"
    manager = DatabaseManager(str(db_path))
    manager.initialize_database()
    now = datetime.now(timezone.utc)
    recent_a = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    recent_b = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    recent_c = (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
    recent_d = (now - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")
    recent_e = (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")
    old_time = (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT INTO contacts (
            email, source, consent, sent, bounced, unsubscribed, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("ready@example.com", "manual", 1, 0, 0, 0, recent_a),
            ("review@example.com", "manual", 0, 0, 0, 0, recent_b),
            ("sent@example.com", "manual", 1, 1, 0, 0, recent_c),
            ("bounced@example.com", "manual", 1, 0, 1, 0, recent_d),
            ("unsub@example.com", "manual", 1, 0, 0, 1, recent_e),
            ("old-review@example.com", "manual", 0, 0, 0, 0, old_time),
        ],
    )
    conn.commit()
    conn.close()

    summary = manager.get_queue_summary(recent_hours=24)

    assert summary["total_contacts"] == 6
    assert summary["ready_to_send"] == 1
    assert summary["needs_review"] == 2
    assert summary["sent_count"] == 1
    assert summary["bounced_count"] == 1
    assert summary["unsubscribed_count"] == 1
    assert summary["recent_imports"] == 2
    assert summary["archived_count"] == 0

    ready_contacts = manager.get_contacts(queue="ready")
    review_contacts = manager.get_contacts(queue="review")

    assert [contact["email"] for contact in ready_contacts] == ["ready@example.com"]
    assert {contact["email"] for contact in review_contacts} == {
        "review@example.com",
        "old-review@example.com",
    }


def test_import_contacts_file_from_csv(tmp_path):
    db_path = tmp_path / "devnav.db"
    csv_path = tmp_path / "emails.csv"

    csv_path.write_text(
        "email,name,company,country\n"
        "alice@example.com,Alice,Acme,US\n"
        "bob@example.com,Bob,BuildCo,GB\n"
        "invalid-email,Nope,Nowhere,US\n"
        "existing@example.com,Existing,OldCo,IT\n",
        encoding="utf-8",
    )

    manager = DatabaseManager(str(db_path))
    manager.initialize_database()

    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO contacts (email, source, consent, sent) VALUES (?, ?, 0, 0)",
        ("existing@example.com", "seed"),
    )
    conn.commit()
    conn.close()

    imported, duplicates, errors = manager.import_contacts_file(
        str(csv_path),
        source="work_from_home_campaign",
    )

    assert imported == 2
    assert duplicates == 1
    assert len(errors) == 1
    assert "invalid-email" in errors[0]

    contacts = manager.get_contacts(queue="review", source="work_from_home_campaign")
    assert {contact["email"] for contact in contacts} == {"alice@example.com", "bob@example.com"}
    assert all(contact["queue_status"] == "Needs review" for contact in contacts)


def test_archive_and_unarchive_contacts(tmp_path):
    db_path = tmp_path / "devnav.db"
    manager = DatabaseManager(str(db_path))
    manager.initialize_database()

    conn = sqlite3.connect(str(db_path))
    conn.executemany(
        "INSERT INTO contacts (email, source, consent, sent) VALUES (?, ?, ?, ?)",
        [
            ("sent-one@example.com", "manual", 1, 1),
            ("sent-two@example.com", "manual", 1, 1),
            ("active@example.com", "manual", 1, 0),
        ],
    )
    conn.commit()
    conn.close()

    archived = manager.archive_contacts(sent_only=True)
    assert archived == 2

    summary = manager.get_queue_summary()
    assert summary["total_contacts"] == 1
    assert summary["archived_count"] == 2

    archived_contacts = manager.get_contacts(queue="archived")
    assert {contact["email"] for contact in archived_contacts} == {
        "sent-one@example.com",
        "sent-two@example.com",
    }
    assert all(contact["queue_status"] == "Archived" for contact in archived_contacts)

    restored = manager.unarchive_contacts(emails=["sent-one@example.com"])
    assert restored == 1

    summary = manager.get_queue_summary()
    assert summary["total_contacts"] == 2
    assert summary["archived_count"] == 1


def test_approve_recent_contacts_only_updates_newest_review_rows(tmp_path):
    db_path = tmp_path / "devnav.db"
    manager = DatabaseManager(str(db_path))
    manager.initialize_database()

    now = datetime.now(timezone.utc)
    newest = (now - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    newer = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    older = (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(str(db_path))
    conn.executemany(
        """
        INSERT INTO contacts (email, source, consent, sent, archived, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            ("newest-review@example.com", "manual", 0, 0, 0, newest),
            ("newer-review@example.com", "manual", 0, 0, 0, newer),
            ("older-review@example.com", "manual", 0, 0, 0, older),
            ("already-approved@example.com", "manual", 1, 0, 0, newest),
        ],
    )
    conn.commit()
    conn.close()

    approved = manager.approve_recent_contacts(limit=2, recent_hours=24)
    assert approved == 2

    ready_contacts = manager.get_contacts(queue="ready")
    review_contacts = manager.get_contacts(queue="review")

    assert {contact["email"] for contact in ready_contacts} == {
        "newest-review@example.com",
        "newer-review@example.com",
        "already-approved@example.com",
    }
    assert {contact["email"] for contact in review_contacts} == {"older-review@example.com"}

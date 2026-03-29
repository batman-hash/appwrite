from types import SimpleNamespace

import devnavigator
from python_engine.database_manager import DatabaseManager
from send_test_emails import EmailTemplateManager


def test_import_send_approved_sends_only_new_imported_contacts(tmp_path, monkeypatch):
    db_path = tmp_path / "devnav.db"
    csv_path = tmp_path / "approved.csv"
    csv_path.write_text(
        "email,name\n"
        "alice@example.com,Alice\n"
        "bob@example.com,Bob\n"
        "existing@example.com,Existing\n",
        encoding="utf-8",
    )

    manager = DatabaseManager(str(db_path))
    manager.initialize_database()
    conn = __import__("sqlite3").connect(str(db_path))
    conn.execute(
        "INSERT INTO contacts (email, source, consent, sent) VALUES (?, ?, ?, ?)",
        ("existing@example.com", "seed", 1, 0),
    )
    conn.commit()
    conn.close()

    template_manager = EmailTemplateManager(str(db_path))
    template_manager.add_template(
        "earning_opportunity",
        "Hello",
        "Register here: $register_link",
        is_default=True,
    )

    monkeypatch.setenv("DATABASE_PATH", str(db_path))

    captured = {}

    class FakeSender:
        def send_batch(self, subject, body, limit=None, dry_run=False, from_name=None,
                       emails=None, country=None, exclude_emails=None, template_name=None,
                       recent_hours=None):
            captured["subject"] = subject
            captured["body"] = body
            captured["limit"] = limit
            captured["dry_run"] = dry_run
            captured["from_name"] = from_name
            captured["emails"] = emails
            captured["template_name"] = template_name
            return len(emails or []), 0

    monkeypatch.setattr(devnavigator, "EmailSender", FakeSender)

    args = SimpleNamespace(
        file=str(csv_path),
        source="approved_csv",
        template="earning_opportunity",
        limit=None,
        dry_run=True,
        yes=False,
    )

    devnavigator.cmd_import_send_approved(args)

    assert captured["emails"] == ["alice@example.com", "bob@example.com"]
    assert captured["limit"] == 2
    assert captured["dry_run"] is True
    assert captured["template_name"] == "earning_opportunity"
    assert captured["from_name"] == "Earning Opportunity Network 💰"

    ready_contacts = manager.get_contacts(queue="ready")
    assert {contact["email"] for contact in ready_contacts} == {
        "alice@example.com",
        "bob@example.com",
        "existing@example.com",
    }


def test_import_send_approved_skips_send_when_nothing_new(tmp_path, monkeypatch):
    db_path = tmp_path / "devnav.db"
    csv_path = tmp_path / "approved.csv"
    csv_path.write_text(
        "email\n"
        "existing@example.com\n",
        encoding="utf-8",
    )

    manager = DatabaseManager(str(db_path))
    manager.initialize_database()
    conn = __import__("sqlite3").connect(str(db_path))
    conn.execute(
        "INSERT INTO contacts (email, source, consent, sent) VALUES (?, ?, ?, ?)",
        ("existing@example.com", "seed", 1, 0),
    )
    conn.commit()
    conn.close()

    template_manager = EmailTemplateManager(str(db_path))
    template_manager.add_template(
        "earning_opportunity",
        "Hello",
        "Register here: $register_link",
        is_default=True,
    )

    monkeypatch.setenv("DATABASE_PATH", str(db_path))

    called = {"value": False}

    class FakeSender:
        def send_batch(self, *args, **kwargs):
            called["value"] = True
            return 0, 0

    monkeypatch.setattr(devnavigator, "EmailSender", FakeSender)

    args = SimpleNamespace(
        file=str(csv_path),
        source="approved_csv",
        template="earning_opportunity",
        limit=None,
        dry_run=True,
        yes=False,
    )

    devnavigator.cmd_import_send_approved(args)

    assert called["value"] is False
    assert manager.get_contact_count() == 1


def test_send_verification_email_tracks_request_without_marking_contact_sent(tmp_path, monkeypatch):
    db_path = tmp_path / "devnav.db"
    manager = DatabaseManager(str(db_path))
    manager.initialize_database()
    manager.insert_default_template()

    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("EMAIL_VERIFICATION_BASE_URL", "https://example.com/verify")

    captured = {}

    class FakeSender:
        def send_verification_email(self, to_email, subject, body, from_name=None, extra_context=None):
            captured["to_email"] = to_email
            captured["subject"] = subject
            captured["body"] = body
            captured["from_name"] = from_name
            captured["extra_context"] = extra_context
            return True, "Sent"

    monkeypatch.setattr(devnavigator, "EmailSender", FakeSender)

    args = SimpleNamespace(
        email="verify@example.com",
        name="Alice",
        source="manual",
        template="email_verification",
        expiry_hours=24,
        dry_run=False,
    )

    devnavigator.cmd_send_verification_email(args)

    assert captured["to_email"] == "verify@example.com"
    assert captured["from_name"] == "DevNavigator Verification"
    assert captured["extra_context"]["verification_link"].startswith("https://example.com/verify?token=")
    assert len(captured["extra_context"]["verification_code"]) == 6

    status = manager.get_verification_status("verify@example.com")
    assert status["verified"] is False
    assert status["verification_status"] == "sent"
    assert status["latest_request"]["status"] == "sent"

    conn = __import__("sqlite3").connect(str(db_path))
    sent_flag = conn.execute(
        "SELECT sent FROM contacts WHERE email = ?",
        ("verify@example.com",),
    ).fetchone()[0]
    conn.close()

    assert sent_flag == 0

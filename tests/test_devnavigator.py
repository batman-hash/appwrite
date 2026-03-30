import csv
import sqlite3
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


def test_extract_emails_show_limit_lists_recent_contacts(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "devnav.db"
    manager = DatabaseManager(str(db_path))
    manager.initialize_database()

    input_file = tmp_path / "emails.txt"
    input_file.write_text(
        "alice@example.com\n"
        "bob@example.com\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("ENABLE_SOURCE_VERIFICATION", "false")

    args = SimpleNamespace(
        file=str(input_file),
        text=None,
        store=True,
        source="manual",
        show_limit=10,
    )

    devnavigator.cmd_extract_emails(args)

    output = capsys.readouterr().out
    assert "📋 Newest 2 contact(s):" in output
    assert "alice@example.com" in output
    assert "bob@example.com" in output


def test_search_auto_show_limit_lists_results(monkeypatch, capsys):
    class FakeExtractor:
        def __init__(self, db_path=None, proxy_url=None):
            self.db_path = db_path
            self._proxy_url = proxy_url

        def proxy_configuration_error(self):
            return None

        def proxy_summary(self):
            return self._proxy_url or "direct"

        def search_all_sources(self, criteria, limit=100, store_results=False):
            assert store_results is False
            return 0, [
                {
                    "email": f"user{i}@example.com",
                    "title": "Frontend Developer",
                    "company": "Example Co",
                    "source": "github.com",
                }
                for i in range(12)
            ]

    monkeypatch.setattr(devnavigator, "AutoEmailExtractor", FakeExtractor)

    args = SimpleNamespace(
        title="frontend developer",
        keywords="react,javascript",
        country="USA",
        remote=True,
        show_limit=10,
        store=False,
        db_path=None,
        proxy_url="http://proxy.internal:8080",
    )

    devnavigator.cmd_search_auto(args)

    output = capsys.readouterr().out
    assert "Validated results ready: 12" in output
    assert "Emails stored: 0 (preview-only mode)" in output
    assert "📧 Preview (first 10 validated result(s)):" in output
    assert "local_db_writes: disabled" in output
    assert "proxy: http://proxy.internal:8080" in output
    assert "user0@example.com" in output
    assert "user9@example.com" in output


def test_search_auto_respects_max_results(monkeypatch):
    captured = {}

    class FakeExtractor:
        def __init__(self, db_path=None, proxy_url=None):
            self.db_path = db_path
            self._proxy_url = proxy_url

        def proxy_configuration_error(self):
            return None

        def proxy_summary(self):
            return self._proxy_url or "direct"

        def search_all_sources(self, criteria, limit=100, store_results=False):
            captured["limit"] = limit
            return 0, []

    monkeypatch.setattr(devnavigator, "AutoEmailExtractor", FakeExtractor)

    args = SimpleNamespace(
        title="frontend developer",
        keywords="react,javascript",
        country="all",
        remote=True,
        show_limit=0,
        max_results=1000,
        store=False,
        db_path=None,
        proxy_url=None,
    )

    devnavigator.cmd_search_auto(args)

    assert captured["limit"] == 1000


def test_search_auto_show_limit_zero_lists_all_results(monkeypatch, capsys):
    class FakeExtractor:
        def __init__(self, db_path=None, proxy_url=None):
            self.db_path = db_path
            self._proxy_url = proxy_url

        def proxy_configuration_error(self):
            return None

        def proxy_summary(self):
            return self._proxy_url or "direct"

        def search_all_sources(self, criteria, limit=100, store_results=False):
            assert store_results is False
            return 0, [
                {
                    "email": "user1@example.com",
                    "title": "Frontend Developer",
                    "company": "Example Co",
                    "source": "github.com",
                },
                {
                    "email": "user2@example.com",
                    "title": "Frontend Developer",
                    "company": "Example Co",
                    "source": "hunter.io",
                },
            ]

    monkeypatch.setattr(devnavigator, "AutoEmailExtractor", FakeExtractor)

    args = SimpleNamespace(
        title="frontend developer",
        keywords="react,javascript",
        country="USA",
        remote=True,
        show_limit=0,
        store=False,
        db_path=None,
        proxy_url="http://proxy.internal:8080",
    )

    devnavigator.cmd_search_auto(args)

    output = capsys.readouterr().out
    assert "Preview (all validated result(s)):" in output
    assert "user1@example.com" in output
    assert "user2@example.com" in output


def test_crawl_emails_alias_delegates_to_search_auto(monkeypatch):
    captured = {}

    def fake_cmd_search_auto(args):
        captured["args"] = args
        return 0

    monkeypatch.setattr(devnavigator, "cmd_search_auto", fake_cmd_search_auto)

    args = SimpleNamespace(title="frontend developer")

    result = devnavigator.cmd_crawl_emails(args)

    assert result == 0
    assert captured["args"] is args


def test_search_auto_query_infers_title_and_keywords(monkeypatch):
    captured = {}

    class FakeExtractor:
        def __init__(self, db_path=None, proxy_url=None):
            self.db_path = db_path

        def proxy_configuration_error(self):
            return None

        def proxy_summary(self):
            return "direct"

        def search_all_sources(self, criteria, limit=100, store_results=False):
            captured["criteria"] = criteria
            captured["store_results"] = store_results
            return 0, []

    monkeypatch.setattr(devnavigator, "AutoEmailExtractor", FakeExtractor)

    args = SimpleNamespace(
        query="frontend developer remote",
        title=None,
        keywords=None,
        country="USA",
        remote=True,
        show_limit=0,
        store=False,
        db_path=None,
        proxy_url=None,
    )

    devnavigator.cmd_search_auto(args)

    assert captured["criteria"]["title"] == "frontend developer remote"
    assert captured["criteria"]["keywords"] == ["frontend", "developer", "remote"]
    assert captured["criteria"]["country"] == "USA"
    assert captured["store_results"] is False


def test_search_auto_treats_all_country_as_worldwide(monkeypatch, capsys):
    captured = {}

    class FakeExtractor:
        def __init__(self, db_path=None, proxy_url=None):
            self.db_path = db_path

        def proxy_configuration_error(self):
            return None

        def proxy_summary(self):
            return "direct"

        def search_all_sources(self, criteria, limit=100, store_results=False):
            captured["criteria"] = criteria
            return 0, []

    monkeypatch.setattr(devnavigator, "AutoEmailExtractor", FakeExtractor)

    args = SimpleNamespace(
        query=None,
        title="frontend developer",
        keywords="react,javascript",
        country="all",
        remote=True,
        show_limit=0,
        store=False,
        db_path=None,
        proxy_url=None,
    )

    devnavigator.cmd_search_auto(args)

    output = capsys.readouterr().out
    assert captured["criteria"]["country"] is None
    assert "country: Worldwide" in output


def test_search_filtered_can_store_results(monkeypatch, capsys):
    captured = {}

    class FakeExtractor:
        def __init__(self, db_path=None, proxy_url=None):
            self.db_path = db_path

        def proxy_configuration_error(self):
            return None

        def proxy_summary(self):
            return "direct"

        def search_with_filters(self, criteria, store_results=False):
            captured["criteria"] = criteria
            captured["store_results"] = store_results
            return 2, [{"email": "valid@example.com", "title": "Frontend Developer", "company": "Example Co"}]

    monkeypatch.setattr(devnavigator, "AutoEmailExtractor", FakeExtractor)

    args = SimpleNamespace(
        query="junior frontend remote",
        title=None,
        keywords=None,
        country=None,
        remote=True,
        store=True,
        db_path="/tmp/internet_search.db",
        proxy_url=None,
    )

    devnavigator.cmd_search_filtered(args)

    output = capsys.readouterr().out
    assert captured["criteria"]["title"] == "junior frontend remote"
    assert captured["criteria"]["keywords"] == ["junior", "frontend", "remote"]
    assert captured["store_results"] is True
    assert "Stored filtered matches: 2" in output


def test_search_auto_can_export_preview_results(monkeypatch, tmp_path, capsys):
    export_path = tmp_path / "internet_results.csv"

    class FakeExtractor:
        def __init__(self, db_path=None, proxy_url=None):
            self.db_path = db_path
            self._proxy_url = proxy_url

        def proxy_configuration_error(self):
            return None

        def proxy_summary(self):
            return self._proxy_url or "direct"

        def search_all_sources(self, criteria, limit=100, store_results=False):
            return 0, [
                {
                    "email": "user@example.com",
                    "name": "User",
                    "title": "Frontend Developer",
                    "company": "Example Co",
                    "country": "USA",
                    "source": "github.com",
                }
            ]

    monkeypatch.setattr(devnavigator, "AutoEmailExtractor", FakeExtractor)

    args = SimpleNamespace(
        query=None,
        title="frontend developer",
        keywords="react,javascript",
        country="USA",
        remote=True,
        show_limit=0,
        store=False,
        db_path=None,
        export_path=str(export_path),
        proxy_url=None,
    )

    devnavigator.cmd_search_auto(args)

    output = capsys.readouterr().out
    assert "Exported results: 1" in output
    assert export_path.exists()

    with export_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows == [{
        "email": "user@example.com",
        "name": "User",
        "title": "Frontend Developer",
        "company": "Example Co",
        "country": "USA",
        "source": "github.com",
    }]


def test_search_deliver_stores_batch_without_sending(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "internet_search.db"
    manager = DatabaseManager(str(db_path))
    manager.initialize_database()

    class FakeExtractor:
        def __init__(self, db_path=None, proxy_url=None):
            self.db_path = db_path
            self._proxy_url = proxy_url

        def proxy_configuration_error(self):
            return None

        def proxy_summary(self):
            return self._proxy_url or "direct"

        def search_all_sources(self, criteria, limit=0, store_results=False):
            assert store_results is True
            conn = sqlite3.connect(self.db_path)
            conn.executemany(
                """
                INSERT INTO contacts (email, name, title, company, country, source, consent, sent)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0)
                """,
                [
                    ("alpha@example.com", "Alpha", "Frontend Developer", "Example Co", "US", "github.com"),
                    ("beta@example.com", "Beta", "Frontend Developer", "Example Co", "US", "hunter.io"),
                ],
            )
            conn.commit()
            conn.close()
            return 2, [
                {
                    "email": "alpha@example.com",
                    "name": "Alpha",
                    "title": "Frontend Developer",
                    "company": "Example Co",
                    "country": "US",
                    "source": "github.com",
                },
                {
                    "email": "beta@example.com",
                    "name": "Beta",
                    "title": "Frontend Developer",
                    "company": "Example Co",
                    "country": "US",
                    "source": "hunter.io",
                },
            ]

    monkeypatch.setattr(devnavigator, "AutoEmailExtractor", FakeExtractor)

    send_called = {"value": False}

    class FailSender:
        def __init__(self):
            send_called["value"] = True

    monkeypatch.setattr(devnavigator, "EmailSender", FailSender)

    args = SimpleNamespace(
        query=None,
        title="frontend developer",
        keywords="react,javascript",
        country="US",
        remote=True,
        show_limit=10,
        db_path=str(db_path),
        export_path=None,
        proxy_url=None,
        template=None,
        send=False,
        dry_run=False,
        yes=False,
        send_limit=None,
    )

    devnavigator.cmd_search_deliver(args)

    output = capsys.readouterr().out
    assert "Search results stored for validation review only." in output
    assert send_called["value"] is False
    summary = manager.get_queue_summary()
    assert summary["needs_review"] == 2


def test_search_deliver_can_approve_and_send_validated_batch(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "internet_search.db"
    manager = DatabaseManager(str(db_path))
    manager.initialize_database()
    manager.insert_default_template()

    class FakeExtractor:
        def __init__(self, db_path=None, proxy_url=None):
            self.db_path = db_path
            self._proxy_url = proxy_url

        def proxy_configuration_error(self):
            return None

        def proxy_summary(self):
            return self._proxy_url or "direct"

        def search_all_sources(self, criteria, limit=0, store_results=False):
            assert store_results is True
            conn = sqlite3.connect(self.db_path)
            conn.executemany(
                """
                INSERT INTO contacts (email, name, title, company, country, source, consent, sent)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0)
                """,
                [
                    ("alpha@example.com", "Alpha", "Frontend Developer", "Example Co", "US", "github.com"),
                    ("beta@example.com", "Beta", "Frontend Developer", "Example Co", "US", "hunter.io"),
                ],
            )
            conn.commit()
            conn.close()
            return 2, [
                {
                    "email": "alpha@example.com",
                    "name": "Alpha",
                    "title": "Frontend Developer",
                    "company": "Example Co",
                    "country": "US",
                    "source": "github.com",
                },
                {
                    "email": "beta@example.com",
                    "name": "Beta",
                    "title": "Frontend Developer",
                    "company": "Example Co",
                    "country": "US",
                    "source": "hunter.io",
                },
            ]

    monkeypatch.setattr(devnavigator, "AutoEmailExtractor", FakeExtractor)

    captured = {}

    class FakeSender:
        def __init__(self):
            pass

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
        query=None,
        title="frontend developer",
        keywords="react,javascript",
        country="US",
        remote=True,
        show_limit=10,
        db_path=str(db_path),
        export_path=None,
        proxy_url=None,
        template=None,
        send=True,
        dry_run=True,
        yes=False,
        send_limit=None,
    )

    devnavigator.cmd_search_deliver(args)

    output = capsys.readouterr().out
    assert "Approved 2 validated contact(s) for sending." in output
    assert captured["emails"] == ["alpha@example.com", "beta@example.com"]
    assert captured["dry_run"] is True
    assert captured["template_name"] == "default_campaign"
    assert captured["from_name"] == "DevNavigator Team"

    ready_contacts = manager.get_contacts(queue="ready")
    assert {contact["email"] for contact in ready_contacts} == {
        "alpha@example.com",
        "beta@example.com",
    }


def test_queue_can_list_all_contacts_from_specific_database(tmp_path, capsys):
    db_path = tmp_path / "internet_search.db"
    manager = DatabaseManager(str(db_path))
    manager.initialize_database()

    conn = sqlite3.connect(str(db_path))
    conn.executemany(
        "INSERT INTO contacts (email, name, title, company, country, source, consent, sent) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("alpha@example.com", "Alpha", "Frontend Developer", "Example Co", "US", "github.com", 0, 0),
            ("beta@example.com", "Beta", "Frontend Developer", "Example Co", "US", "hunter.io", 1, 0),
            ("gamma@example.com", "Gamma", "Frontend Developer", "Example Co", "US", "apollo.io", 1, 1),
        ],
    )
    conn.commit()
    conn.close()

    args = SimpleNamespace(
        queue="all",
        limit=0,
        source=None,
        recent_hours=24,
        db_path=str(db_path),
    )

    devnavigator.cmd_queue(args)

    output = capsys.readouterr().out
    assert "Showing 3 contact(s) from queue='all':" in output
    assert "alpha@example.com" in output
    assert "beta@example.com" in output
    assert "gamma@example.com" in output


def test_list_search_emails_includes_archived_contacts_from_specific_database(tmp_path, capsys):
    db_path = tmp_path / "internet_search.db"
    manager = DatabaseManager(str(db_path))
    manager.initialize_database()

    conn = sqlite3.connect(str(db_path))
    conn.executemany(
        "INSERT INTO contacts (email, name, title, company, country, source, consent, sent, archived) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("alpha@example.com", "Alpha", "Frontend Developer", "Example Co", "US", "github.com", 0, 0, 0),
            ("beta@example.com", "Beta", "Frontend Developer", "Example Co", "US", "hunter.io", 1, 0, 0),
            ("gamma@example.com", "Gamma", "Frontend Developer", "Example Co", "US", "apollo.io", 1, 1, 1),
        ],
    )
    conn.commit()
    conn.close()

    args = SimpleNamespace(
        db_path=str(db_path),
        source=None,
        recent_hours=24,
        limit=0,
        emails_only=False,
    )

    devnavigator.cmd_list_search_emails(args)

    output = capsys.readouterr().out
    assert "Showing 3 email(s):" in output
    assert "alpha@example.com" in output
    assert "beta@example.com" in output
    assert "gamma@example.com" in output
    assert "Status: Archived" in output


def test_search_auto_returns_error_for_placeholder_proxy(monkeypatch, capsys):
    class FakeExtractor:
        def __init__(self, db_path=None, proxy_url=None):
            self.db_path = db_path
            self._proxy_url = proxy_url

        def proxy_configuration_error(self):
            return "placeholder proxy"

    monkeypatch.setattr(devnavigator, "AutoEmailExtractor", FakeExtractor)

    args = SimpleNamespace(
        title="frontend developer",
        keywords="react,javascript",
        country="USA",
        remote=True,
        show_limit=10,
        store=False,
        db_path=None,
        proxy_url="http://proxy-host:8080",
    )

    exit_code = devnavigator.cmd_search_auto(args)

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "placeholder proxy" in output

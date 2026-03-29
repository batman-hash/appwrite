import sqlite3
from datetime import datetime, timedelta, timezone

from python_engine.database_manager import DatabaseManager
from send_test_emails import (
    EmailTemplateManager,
    EmailSender,
    build_html_email,
    get_campaign_visuals,
    get_campaign_register_link,
    render_email_content,
    should_use_public_tracking,
)


def test_default_template_switches_with_latest_default(tmp_path):
    db_path = tmp_path / "templates.db"
    DatabaseManager(str(db_path)).initialize_database()
    manager = EmailTemplateManager(str(db_path))

    manager.add_template("first_template", "First", "Hello", is_default=True)
    manager.add_template("second_template", "Second", "Hi", is_default=True)

    assert manager.get_default_template_name() == "second_template"
    assert manager.get_template() == ("Second", "Hi")


def test_render_email_uses_campaign_specific_register_link(monkeypatch):
    monkeypatch.setenv("EARNING_OPPORTUNITY_REGISTER_LINK", "https://example.com/register")

    assert get_campaign_register_link("earning_opportunity") == "https://example.com/register"

    subject, body = render_email_content(
        to_email="person@example.com",
        subject="Welcome",
        body="Register here: $register_link\nEmail: $email",
        template_name="earning_opportunity",
        add_tracking=False,
    )

    assert subject == "Welcome"
    assert "https://example.com/register" in body
    assert "person@example.com" in body


def test_render_email_skips_localhost_tracking(monkeypatch):
    monkeypatch.setenv("TRACKING_SERVER_URL", "http://localhost:8888")
    monkeypatch.setenv("EARNING_OPPORTUNITY_REGISTER_LINK", "https://example.com/register")

    assert not should_use_public_tracking("http://localhost:8888")

    _, body = render_email_content(
        to_email="person@example.com",
        subject="Welcome",
        body="Register here: $register_link",
        template_name="earning_opportunity",
        add_tracking=True,
    )

    assert "https://example.com/register" in body
    assert "localhost:8888" not in body
    assert "<img" not in body


def test_render_email_supports_verification_context():
    subject, body = render_email_content(
        to_email="person@example.com",
        subject="Verify $email",
        body="Use $verification_code or click $verification_link before $verification_expires_at",
        template_name="email_verification",
        add_tracking=False,
        extra_context={
            "verification_code": "123456",
            "verification_link": "https://example.com/verify?token=abc",
            "verification_expires_at": "2026-04-01 10:00:00 UTC",
        },
    )

    assert subject == "Verify person@example.com"
    assert "123456" in body
    assert "https://example.com/verify?token=abc" in body
    assert "2026-04-01 10:00:00 UTC" in body


def test_get_campaign_visuals_prefers_named_files(tmp_path, monkeypatch):
    image_dir = tmp_path / "visuals"
    image_dir.mkdir()
    for name in ["other.png", "money_bag.png", "beach_lifestyle.jpg", "hero_work_setup.webp"]:
        (image_dir / name).write_bytes(b"fake")

    monkeypatch.setitem(__import__("send_test_emails").CAMPAIGN_IMAGE_DIRS, "earning_opportunity", image_dir)

    visuals = get_campaign_visuals("earning_opportunity")

    assert [path.name for path in visuals] == [
        "hero_work_setup.webp",
        "money_bag.png",
        "beach_lifestyle.jpg",
    ]


def test_build_html_email_embeds_expected_cids():
    html = build_html_email("Hello\n\nWorld", image_count=2)

    assert "Hello" in html
    assert "World" in html
    assert "cid:campaign_image_0" in html
    assert "cid:campaign_image_1" in html


def test_earning_opportunity_html_has_cta_and_hero():
    html = build_html_email(
        "Register here",
        image_count=3,
        template_name="earning_opportunity",
        register_link="https://example.com/register",
    )

    assert "Start Earning From Home" in html
    assert "100% Free Opportunity" in html
    assert "https://example.com/register" in html
    assert "Get Started" in html
    assert "cid:campaign_image_0" in html
    assert "cid:campaign_image_1" in html
    assert "cid:campaign_image_2" in html


def test_email_verification_html_has_verify_cta():
    html = build_html_email(
        "Confirm your email",
        template_name="email_verification",
        verification_link="https://example.com/verify?token=abc",
    )

    assert "Confirm Your Email" in html
    assert "Verify Email" in html
    assert "https://example.com/verify?token=abc" in html


def test_send_batch_recent_hours_only_targets_new_approved_contacts(tmp_path, monkeypatch):
    db_path = tmp_path / "send.db"
    DatabaseManager(str(db_path)).initialize_database()

    now = datetime.now(timezone.utc)
    recent_time = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    old_time = (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(str(db_path))
    conn.executemany(
        """
        INSERT INTO contacts (email, source, consent, sent, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("recent-approved@example.com", "manual", 1, 0, recent_time),
            ("old-approved@example.com", "manual", 1, 0, old_time),
            ("recent-review@example.com", "manual", 0, 0, recent_time),
        ],
    )
    conn.commit()
    conn.close()

    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    sender = EmailSender()
    sent, failed = sender.send_batch(
        "Subject",
        "Body",
        dry_run=True,
        recent_hours=24,
        template_name="earning_opportunity",
    )

    assert sent == 1
    assert failed == 0

from python_engine.database_manager import DatabaseManager
from python_engine.email_verification import EmailVerificationService


def test_email_verification_service_tracks_request_and_confirmation(tmp_path, monkeypatch):
    db_path = tmp_path / "verification.db"
    monkeypatch.setenv("EMAIL_VERIFICATION_BASE_URL", "https://example.com/verify")

    manager = DatabaseManager(str(db_path))
    manager.initialize_database()

    service = EmailVerificationService(str(db_path))
    payload = service.prepare_verification(
        "verify@example.com",
        recipient_name="Alice",
        source="manual",
    )

    assert payload.request_id is not None
    assert payload.contact_id is not None
    assert payload.verification_link.startswith("https://example.com/verify?token=")

    pending_status = service.get_status("verify@example.com")
    assert pending_status["verified"] is False
    assert pending_status["verification_status"] == "pending"
    assert pending_status["latest_request"]["status"] == "pending"

    assert service.mark_sent(payload.request_id) is True

    sent_status = service.get_status("verify@example.com")
    assert sent_status["verification_status"] == "sent"
    assert sent_status["latest_request"]["status"] == "sent"

    success, message, details = service.confirm(token=payload.token)

    assert success is True
    assert message == "Email verified successfully"
    assert details["email"] == "verify@example.com"

    verified_status = service.get_status("verify@example.com")
    assert verified_status["verified"] is True
    assert verified_status["verification_status"] == "verified"
    assert verified_status["latest_request"]["status"] == "verified"

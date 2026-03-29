import dns.resolver

from python_engine.email_extractor import EmailValidator


class _FakeMXRecord:
    def __init__(self, exchange):
        self.exchange = exchange


def test_email_validator_accepts_domains_with_mx_records(monkeypatch):
    def fake_resolve(domain, record_type, lifetime=None):
        assert domain == "example.com"
        assert record_type == "MX"
        return [_FakeMXRecord("mail.example.com.")]

    monkeypatch.setattr(dns.resolver, "resolve", fake_resolve)

    validator = EmailValidator(enable_source_verification=True)
    is_valid, reason = validator.is_valid_email("person@example.com")

    assert is_valid is True
    assert reason == "Valid"


def test_email_validator_rejects_nonexistent_domains(monkeypatch):
    def fake_resolve(domain, record_type, lifetime=None):
        raise dns.resolver.NXDOMAIN

    monkeypatch.setattr(dns.resolver, "resolve", fake_resolve)

    validator = EmailValidator(enable_source_verification=True)
    is_valid, reason = validator.is_valid_email("person@missing.example")

    assert is_valid is False
    assert "Domain does not exist" in reason

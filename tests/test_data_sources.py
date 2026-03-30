from python_engine.data_sources import EmailSourceManager


def test_email_source_manager_prefers_hunter_api_key(monkeypatch):
    monkeypatch.setenv("HUNTER_API_KEY", "hunter-primary")
    monkeypatch.setenv("HUNTER_IO_API_KEY", "hunter-legacy")

    manager = EmailSourceManager()

    assert manager.api_keys["hunter"] == "hunter-primary"


def test_email_source_manager_search_apollo_enriches_people(monkeypatch):
    monkeypatch.setenv("APOLLO_API_KEY", "apollo-test-key")

    class FakeResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

    def fake_post(url, headers=None, json=None, params=None, timeout=None):
        if url.endswith("/mixed_people/api_search"):
            return FakeResponse({"people": [{"id": "person-1"}]})
        if url.endswith("/people/bulk_match"):
            return FakeResponse(
                {
                    "matches": [
                        {
                            "email": "alice@example.com",
                            "first_name": "Alice",
                            "last_name": "Smith",
                            "title": "Frontend Developer",
                            "organization": {"name": "Example Co"},
                            "country": "US",
                            "email_status": "verified",
                        }
                    ]
                }
            )
        raise AssertionError(f"Unexpected Apollo URL: {url}")

    monkeypatch.setattr("python_engine.data_sources.requests.post", fake_post)

    manager = EmailSourceManager()
    contacts = manager.search_apollo("Frontend Developer", limit=10)

    assert contacts == [
        {
            "email": "alice@example.com",
            "name": "Alice Smith",
            "title": "Frontend Developer",
            "company": "Example Co",
            "phone": None,
            "country": "US",
            "source": "apollo",
            "verified": True,
        }
    ]

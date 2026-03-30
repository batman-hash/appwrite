from python_engine.auto_email_extractor import AutoEmailExtractor
from python_engine.database_manager import DatabaseManager


def test_auto_email_extractor_uses_explicit_proxy_url(monkeypatch):
    monkeypatch.delenv("EXTRACT_PROXY_URL", raising=False)
    monkeypatch.delenv("EXTRACT_HTTP_PROXY", raising=False)
    monkeypatch.delenv("EXTRACT_HTTPS_PROXY", raising=False)

    extractor = AutoEmailExtractor(proxy_url="http://proxy.local:8080")

    assert extractor.session.proxies["http"] == "http://proxy.local:8080"
    assert extractor.session.proxies["https"] == "http://proxy.local:8080"
    assert "proxy.local:8080" in extractor.proxy_summary()


def test_auto_email_extractor_prefers_protocol_specific_proxy_env(monkeypatch):
    monkeypatch.setenv("EXTRACT_PROXY_URL", "http://shared.proxy:9000")
    monkeypatch.setenv("EXTRACT_HTTP_PROXY", "http://http.proxy:8080")
    monkeypatch.setenv("EXTRACT_HTTPS_PROXY", "http://https.proxy:8443")

    extractor = AutoEmailExtractor()

    assert extractor.session.proxies["http"] == "http://http.proxy:8080"
    assert extractor.session.proxies["https"] == "http://https.proxy:8443"


def test_auto_email_extractor_rejects_placeholder_proxy_host():
    extractor = AutoEmailExtractor(proxy_url="http://proxy-host:8080")

    assert "placeholder host 'proxy-host'" in extractor.proxy_configuration_error()


def test_auto_email_extractor_validates_before_store(tmp_path, monkeypatch):
    db_path = tmp_path / "internet_search.db"
    DatabaseManager(str(db_path)).initialize_database()

    def fake_is_valid_email(self, email):
        if email == "valid@example.com":
            return True, "Valid"
        return False, "Invalid email format"

    monkeypatch.setattr("python_engine.auto_email_extractor.EmailValidator.is_valid_email", fake_is_valid_email)

    extractor = AutoEmailExtractor(db_path=str(db_path))
    stored, failed = extractor._store_emails([
        {"email": "valid@example.com", "source": "github.com"},
        {"email": "broken.example.com", "source": "github.com"},
    ])

    assert stored == 1
    assert failed == ["broken.example.com: Invalid email format"]


def test_auto_email_extractor_preview_returns_only_validated_results(tmp_path, monkeypatch):
    db_path = tmp_path / "internet_search.db"
    DatabaseManager(str(db_path)).initialize_database()

    def fake_is_valid_email(self, email):
        if email == "valid@example.com":
            return True, "Valid"
        return False, "Invalid email format"

    monkeypatch.setattr("python_engine.auto_email_extractor.EmailValidator.is_valid_email", fake_is_valid_email)

    extractor = AutoEmailExtractor(db_path=str(db_path))
    monkeypatch.setattr(
        extractor,
        "search_github_profiles",
        lambda keywords, location: [
            {"email": "valid@example.com", "source": "github.com"},
            {"email": "broken.example.com", "source": "github.com"},
        ],
    )
    monkeypatch.setattr(extractor, "search_hunter_discover", lambda criteria, max_domains=3: [])
    monkeypatch.setattr(extractor, "search_apollo_free", lambda title, country=None: [])
    monkeypatch.setattr(extractor, "search_kaggle_datasets", lambda: [])

    stored, results = extractor.search_all_sources(
        {"title": "frontend developer", "keywords": ["react"], "country": "USA", "remote": True},
        store_results=False,
    )

    assert stored == 0
    assert results == [{"email": "valid@example.com", "source": "github.com"}]


def test_auto_email_extractor_treats_all_country_as_global_search(tmp_path, monkeypatch):
    db_path = tmp_path / "internet_search.db"
    DatabaseManager(str(db_path)).initialize_database()

    captured = {}

    extractor = AutoEmailExtractor(db_path=str(db_path))
    monkeypatch.setattr(extractor, "search_github_profiles", lambda keywords, location: captured.setdefault("github_location", location) or [])
    monkeypatch.setattr(extractor, "search_hunter_discover", lambda criteria, max_domains=3: captured.setdefault("hunter_country", criteria.get("country")) or [])
    monkeypatch.setattr(extractor, "search_apollo_free", lambda title, country=None: captured.setdefault("apollo_country", country) or [])
    monkeypatch.setattr(extractor, "search_kaggle_datasets", lambda: None)

    stored, results = extractor.search_all_sources(
        {"title": "frontend developer", "keywords": ["react"], "country": "all", "remote": True},
        store_results=False,
    )

    assert stored == 0
    assert results == []
    assert captured["github_location"] is None
    assert captured["hunter_country"] is None
    assert captured["apollo_country"] is None


def test_auto_email_extractor_prints_no_results_hints(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "internet_search.db"
    DatabaseManager(str(db_path)).initialize_database()

    monkeypatch.delenv("HUNTER_API_KEY", raising=False)
    monkeypatch.delenv("APOLLO_API_KEY", raising=False)

    extractor = AutoEmailExtractor(db_path=str(db_path))
    monkeypatch.setattr(extractor, "search_github_profiles", lambda keywords, location: [])
    monkeypatch.setattr(extractor, "search_hunter_discover", lambda criteria, max_domains=3: [])
    monkeypatch.setattr(extractor, "search_apollo_free", lambda title, country=None: [])
    monkeypatch.setattr(extractor, "search_kaggle_datasets", lambda: [])

    stored, results = extractor.search_all_sources(
        {"title": "frontend developer", "keywords": ["react", "javascript"], "country": "USA", "remote": True},
        store_results=False,
    )

    output = capsys.readouterr().out
    assert stored == 0
    assert results == []
    assert "No validated emails were returned from the current live sources." in output
    assert "GitHub public emails are rare" in output
    assert "Try removing the country filter or using a broader region." in output
    assert "Try fewer keywords so the search is less restrictive." in output


def test_auto_email_extractor_hunter_discover_expands_domains(tmp_path, monkeypatch):
    db_path = tmp_path / "internet_search.db"
    DatabaseManager(str(db_path)).initialize_database()

    def fake_is_valid_email(self, email):
        return True, "Valid"

    class FakeResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

    monkeypatch.setattr("python_engine.auto_email_extractor.EmailValidator.is_valid_email", fake_is_valid_email)
    monkeypatch.setenv("HUNTER_API_KEY", "hunter-test-key")

    extractor = AutoEmailExtractor(db_path=str(db_path))
    monkeypatch.setattr(extractor, "search_github_profiles", lambda keywords, location: [])
    monkeypatch.setattr(extractor, "search_apollo_free", lambda title, country=None: [])
    monkeypatch.setattr(extractor, "search_kaggle_datasets", lambda: [])

    def fake_post(url, params=None, json=None, timeout=None):
        if url.endswith("/discover"):
            return FakeResponse(
                {
                    "data": [
                        {"domain": "example.com", "organization": "Example Co", "emails_count": {"personal": 2}},
                        {"domain": "second.example", "organization": "Second Co", "emails_count": {"personal": 1}},
                    ]
                }
            )
        raise AssertionError(f"Unexpected POST url: {url}")

    def fake_get(url, params=None, timeout=None):
        if "domain-search" in url:
            return FakeResponse(
                {
                    "data": {
                        "emails": [
                            {
                                "value": "alice@example.com",
                                "first_name": "Alice",
                                "last_name": "Smith",
                                "position": "Developer",
                            }
                        ]
                    }
                }
            )
        raise AssertionError(f"Unexpected GET url: {url}")

    monkeypatch.setattr(extractor.session, "post", fake_post)
    monkeypatch.setattr(extractor.session, "get", fake_get)

    stored, results = extractor.search_all_sources(
        {"title": "frontend developer", "keywords": ["react"], "country": "USA", "remote": True},
        store_results=False,
    )

    assert stored == 0
    assert [contact["email"] for contact in results] == ["alice@example.com"]


def test_auto_email_extractor_hunter_discover_loops_query_variants(tmp_path, monkeypatch):
    db_path = tmp_path / "internet_search.db"
    DatabaseManager(str(db_path)).initialize_database()

    class FakeResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return self._payload

    queries = []

    monkeypatch.setattr("python_engine.auto_email_extractor.EmailValidator.is_valid_email", lambda self, email: (True, "Valid"))
    monkeypatch.setenv("HUNTER_API_KEY", "hunter-test-key")
    monkeypatch.setattr("python_engine.auto_email_extractor.time.sleep", lambda seconds: None)

    extractor = AutoEmailExtractor(db_path=str(db_path))
    monkeypatch.setattr(extractor, "search_github_profiles", lambda keywords, location: [])
    monkeypatch.setattr(extractor, "search_apollo_free", lambda title, country=None: [])
    monkeypatch.setattr(extractor, "search_kaggle_datasets", lambda: None)
    monkeypatch.setattr(extractor, "search_hunter_free", lambda domain: [{"email": f"contact@{domain}", "source": "hunter.io"}])

    def fake_post(url, params=None, json=None, timeout=None):
        if url.endswith("/discover"):
            queries.append(json["query"])
            return FakeResponse({"data": [{"domain": "example.com"}, {"domain": "second.example"}]})
        raise AssertionError(f"Unexpected POST url: {url}")

    monkeypatch.setattr(extractor.session, "post", fake_post)

    results = extractor.search_hunter_discover(
        {"title": "frontend developer", "keywords": ["react", "javascript"], "country": "all", "remote": True},
        max_domains=2,
    )

    assert len(queries) >= 2
    assert queries[0] != queries[1]
    assert [contact["email"] for contact in results] == [
        "contact@example.com",
        "contact@second.example",
    ]

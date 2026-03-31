from __future__ import annotations

import unittest

from backend.app import create_app


class AuthApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_me_requires_login(self):
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_login_requires_fields(self):
        response = self.client.post("/api/auth/login", json={})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()


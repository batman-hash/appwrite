from __future__ import annotations

import unittest

from backend.app import create_app


class UsersApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_users_me_requires_login(self):
        response = self.client.get("/api/users/me")
        self.assertEqual(response.status_code, 401)

    def test_users_listing_requires_login(self):
        response = self.client.get("/api/users")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()


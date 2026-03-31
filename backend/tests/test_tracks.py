from __future__ import annotations

import unittest

from backend.app import create_app


class TracksApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_tracks_library_returns_items(self):
        response = self.client.get("/api/tracks/library")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertIsInstance(payload["items"], list)


if __name__ == "__main__":
    unittest.main()


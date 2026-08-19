import os
import sys
import unittest

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_dharma.db")

from backend.main import app
from backend.models import Base, engine


class BackendTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_register_user(self):
        response = self.client.post(
            "/auth/register",
            json={"username": "alice", "password": "secret123"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["username"], "alice")
        self.assertIn("id", body)
        self.assertIn("access_token", body)

    def test_login_user(self):
        self.client.post(
            "/auth/register",
            json={"username": "bob", "password": "strongpass123"},
        )
        response = self.client.post(
            "/auth/login",
            json={"username": "bob", "password": "strongpass123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "bob")
        self.assertIn("access_token", response.json())

    def test_duplicate_registration_is_rejected(self):
        self.client.post(
            "/auth/register",
            json={"username": "carol", "password": "strongpass123"},
        )
        response = self.client.post(
            "/auth/register",
            json={"username": "carol", "password": "anotherpassword"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("already exists", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()

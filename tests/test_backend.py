import os
import sys
import unittest

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_dharma.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

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

    def test_chat_requires_authentication(self):
        response = self.client.post(
            "/chat",
            json={"message": "hello", "assistant_response": "hi", "mode": "Calm"},
        )
        self.assertEqual(response.status_code, 401)

    def test_chat_is_saved_for_authenticated_user(self):
        registration = self.client.post(
            "/auth/register",
            json={"username": "dharma_user", "password": "strongpass123"},
        )
        token = registration.json()["access_token"]
        response = self.client.post(
            "/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "How should I handle stress?",
                "assistant_response": "Take one manageable step.",
                "mode": "Calm",
            },
        )
        self.assertEqual(response.status_code, 200)

        history = self.client.get(
            "/chat/history",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(history.status_code, 200)
        messages = history.json()[0]["messages"]
        self.assertEqual(messages[0]["content"], "How should I handle stress?")
        self.assertEqual(messages[1]["content"], "Take one manageable step.")


if __name__ == "__main__":
    unittest.main()

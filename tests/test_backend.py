import os
import sys
import unittest
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_dharma.db")

from auth import login, signup
from backend.main import app
from backend.models import Base, engine
from dharma_ai import generate_response


class BackendTests(unittest.TestCase):
    def setUp(self):
        engine.dispose()
        if os.path.exists("test_dharma.db"):
            os.remove("test_dharma.db")
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        engine.dispose()

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

    def test_signup_and_login_fallback_work_without_backend(self):
        username = f"uiuser-{uuid.uuid4().hex[:8]}"
        password = "secret123"

        success, message = signup(username, password)
        self.assertTrue(success, message)

        success, message = login(username, password)
        self.assertTrue(success, message)

    def test_generate_response_uses_quick_local_answer_without_external_services(self):
        with patch("dharma_ai.load_chroma", side_effect=AssertionError("should not load Chroma")), \
             patch("dharma_ai.load_groq", side_effect=AssertionError("should not load Groq")):
            response = generate_response("I feel lost and need guidance", "Calm")

        self.assertTrue(response)
        self.assertIn("pause", response.lower())


if __name__ == "__main__":
    unittest.main()

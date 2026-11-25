import os
import sys
import unittest
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_dharma.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

from backend.main import app, clear_tts_audio_cache, generate_tts_audio_bytes
from backend.models import Base, engine


class BackendTests(unittest.TestCase):
    def setUp(self):
        clear_tts_audio_cache()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_voice_transcription_cors_preflight_allows_local_frontend_origin(self):
        response = self.client.options(
            "/voice/transcribe?language=en",
            headers={
                "Origin": "http://127.0.0.1:8501",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://127.0.0.1:8501",
        )

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

    def test_voice_transcription_requires_authentication(self):
        response = self.client.post(
            "/voice/transcribe",
            headers={"Content-Type": "audio/webm"},
            content=b"audio-data",
        )
        self.assertEqual(response.status_code, 401)

    def test_voice_transcription_uses_authenticated_user_language_and_audio_type(self):
        registration = self.client.post(
            "/auth/register",
            json={"username": "voice_user", "password": "strongpass123"},
        )
        token = registration.json()["access_token"]
        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}), patch(
            "backend.main.transcribe_audio_bytes",
            return_value="A spoken message.",
        ) as transcribe:
            response = self.client.post(
                "/voice/transcribe?language=hi",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "audio/webm;codecs=opus",
                },
                content=b"audio-data",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"transcript": "A spoken message."})
        transcribe.assert_called_once_with(b"audio-data", "hi", "audio/webm")

    def test_voice_transcription_rejects_unsupported_audio_type(self):
        registration = self.client.post(
            "/auth/register",
            json={"username": "voice_format_user", "password": "strongpass123"},
        )
        token = registration.json()["access_token"]
        response = self.client.post(
            "/voice/transcribe",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            content=b"audio-data",
        )
        self.assertEqual(response.status_code, 415)

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
        session_id = response.json()["session_id"]

        follow_up = self.client.post(
            "/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "What is one small step?",
                "assistant_response": "Start with a five-minute walk.",
                "mode": "Calm",
                "chat_id": session_id,
            },
        )
        self.assertEqual(follow_up.status_code, 200)
        self.assertEqual(follow_up.json()["session_id"], session_id)

        new_chat = self.client.post(
            "/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": "How can I focus?",
                "assistant_response": "Remove one distraction.",
                "mode": "Logical",
            },
        )
        self.assertEqual(new_chat.status_code, 200)
        self.assertNotEqual(new_chat.json()["session_id"], session_id)

        history = self.client.get(
            "/chat/history",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(history.status_code, 200)
        chats = history.json()
        self.assertEqual(len(chats), 2)
        original_chat = next(chat for chat in chats if chat["id"] == session_id)
        messages = original_chat["messages"]
        self.assertEqual(
            messages,
            [
                {"role": "user", "content": "How should I handle stress?"},
                {"role": "assistant", "content": "Take one manageable step."},
                {"role": "user", "content": "What is one small step?"},
                {"role": "assistant", "content": "Start with a five-minute walk."},
            ],
        )
        new_chat = next(chat for chat in chats if chat["id"] != session_id)
        self.assertEqual(
            new_chat["messages"],
            [
                {"role": "user", "content": "How can I focus?"},
                {"role": "assistant", "content": "Remove one distraction."},
            ],
        )

    def test_regenerated_chat_replaces_latest_assistant_response(self):
        registration = self.client.post(
            "/auth/register",
            json={"username": "regenerate_user", "password": "strongpass123"},
        )
        token = registration.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        original = self.client.post(
            "/chat",
            headers=headers,
            json={
                "message": "How should I handle stress?",
                "assistant_response": "Take a long walk.",
                "mode": "Calm",
            },
        )
        session_id = original.json()["session_id"]

        regenerated = self.client.post(
            "/chat",
            headers=headers,
            json={
                "message": "How should I handle stress?",
                "assistant_response": "Start with one manageable task.",
                "mode": "Calm",
                "chat_id": session_id,
                "replace_last_response": True,
            },
        )

        self.assertEqual(regenerated.status_code, 200)
        self.assertEqual(regenerated.json()["session_id"], session_id)
        history = self.client.get("/chat/history", headers=headers)
        messages = history.json()[0]["messages"]
        self.assertEqual(
            messages,
            [
                {"role": "user", "content": "How should I handle stress?"},
                {"role": "assistant", "content": "Start with one manageable task."},
            ],
        )

    def test_language_preference_and_profile(self):
        registration = self.client.post(
            "/auth/register",
            json={"username": "lang_user", "password": "strongpass123", "language_preference": "hi"},
        )
        self.assertEqual(registration.status_code, 200)
        self.assertEqual(registration.json()["language_preference"], "hi")
        token = registration.json()["access_token"]

        profile = self.client.get(
            "/user/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.json()["language_preference"], "hi")

        update = self.client.put(
            "/user/language",
            headers={"Authorization": f"Bearer {token}"},
            json={"language": "en"},
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.json()["language_preference"], "en")

    def test_chat_delete_and_clear_history(self):
        registration = self.client.post(
            "/auth/register",
            json={"username": "delete_user", "password": "strongpass123"},
        )
        token = registration.json()["access_token"]
        chat1 = self.client.post(
            "/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "Chat 1", "assistant_response": "Reply 1"},
        )
        chat2 = self.client.post(
            "/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "Chat 2", "assistant_response": "Reply 2"},
        )
        s1 = chat1.json()["session_id"]
        s2 = chat2.json()["session_id"]

        del_res = self.client.delete(
            f"/chat/{s1}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(del_res.status_code, 200)

        history = self.client.get("/chat/history", headers={"Authorization": f"Bearer {token}"}).json()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["id"], s2)

        clear_res = self.client.delete(
            "/chat/history",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(clear_res.status_code, 200)

        history_empty = self.client.get("/chat/history", headers={"Authorization": f"Bearer {token}"}).json()
        self.assertEqual(len(history_empty), 0)


    def test_voice_tts_endpoint_returns_audio_stream(self):
        with patch("backend.main.generate_tts_audio_bytes", return_value=b"fake-mp3-stream"):
            response = self.client.get(
                "/voice/tts?text=%E0%A4%A8%E0%A4%AE%E0%A4%B8%E0%A5%8D%E0%A4%A4%E0%A5%87&lang=hi",
                headers={"Origin": "http://127.0.0.1:8501"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers.get("content-type"), "audio/mpeg")
            self.assertEqual(response.headers.get("cache-control"), "no-store")
            self.assertEqual(response.headers.get("x-tts-voice"), "hi-IN-SwaraNeural")
            self.assertEqual(response.headers.get("x-tts-language"), "hi")
            self.assertEqual(
                response.headers.get("access-control-expose-headers"),
                "X-TTS-Voice, X-TTS-Language",
            )
            self.assertEqual(response.content, b"fake-mp3-stream")

    def test_hindi_tts_uses_original_text_and_fixed_edge_voice(self):
        text = "नमस्ते, आपका दिन शुभ हो।"
        with patch("backend.main.generate_tts_audio_bytes", return_value=b"mp3") as generate:
            response = self.client.get("/voice/tts", params={"text": text, "lang": "hi"})

        self.assertEqual(response.status_code, 200)
        generate.assert_called_once_with(text, "hi")

    def test_english_tts_uses_english_edge_voice(self):
        text = "Hello, have a nice day."
        with patch("backend.main.generate_tts_audio_bytes", return_value=b"mp3") as generate:
            response = self.client.get("/voice/tts", params={"text": text, "lang": "en"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("x-tts-voice"), "en-US-AriaNeural")
        generate.assert_called_once_with(text, "en")

    def test_voice_tts_post_accepts_text_in_json_body(self):
        text = "Hello, have a nice day."
        with patch("backend.main.generate_tts_audio_bytes", return_value=b"mp3") as generate:
            response = self.client.post(
                "/voice/tts",
                json={"text": text, "lang": "en"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("x-tts-voice"), "en-US-AriaNeural")
        self.assertEqual(response.content, b"mp3")
        generate.assert_called_once_with(text, "en")

    def test_voice_tts_reports_edge_tts_failure(self):
        with patch(
            "backend.main.generate_tts_audio_bytes",
            side_effect=RuntimeError("Edge TTS unavailable"),
        ):
            response = self.client.get(
                "/voice/tts",
                params={"text": "नमस्ते", "lang": "hi"},
            )

        self.assertEqual(response.status_code, 502)
        self.assertIn("hi-IN-SwaraNeural", response.json()["detail"])
        self.assertIn("Edge TTS unavailable", response.json()["detail"])

    def test_voice_tts_rejects_text_that_would_be_truncated(self):
        response = self.client.get(
            "/voice/tts",
            params={"text": "न" * 3001, "lang": "hi"},
        )

        self.assertEqual(response.status_code, 413)

    def test_voice_tts_rejects_empty_text(self):
        response = self.client.get("/voice/tts?text=%20&lang=hi")
        self.assertEqual(response.status_code, 400)

    def test_tts_cache_coalesces_concurrent_requests(self):
        synthesis_started = Event()
        allow_synthesis_to_finish = Event()

        def synthesize(text, voice):
            synthesis_started.set()
            if not allow_synthesis_to_finish.wait(timeout=3):
                raise TimeoutError("Test synthesis was not released")
            return b"shared-mp3"

        with patch("backend.main._synthesize_edge_tts", side_effect=synthesize) as synthesis:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(
                        generate_tts_audio_bytes,
                        "नमस्ते",
                        "hi",
                    )
                    for _ in range(4)
                ]
                self.assertTrue(synthesis_started.wait(timeout=2))
                time.sleep(0.1)
                allow_synthesis_to_finish.set()
                results = [future.result(timeout=3) for future in futures]

        self.assertEqual(results, [b"shared-mp3"] * 4)
        synthesis.assert_called_once_with("नमस्ते", "hi-IN-SwaraNeural")
        self.assertEqual(generate_tts_audio_bytes("नमस्ते", "hi"), b"shared-mp3")
        synthesis.assert_called_once()

    def test_tts_cache_key_includes_language_and_failures_are_not_cached(self):
        with patch(
            "backend.main._synthesize_edge_tts",
            side_effect=[b"hindi-mp3", RuntimeError("temporary failure"), b"english-mp3"],
        ) as synthesis:
            self.assertEqual(
                generate_tts_audio_bytes("Hello", "hi"),
                b"hindi-mp3",
            )
            with self.assertRaisesRegex(RuntimeError, "temporary failure"):
                generate_tts_audio_bytes("Hello", "en")
            self.assertEqual(
                generate_tts_audio_bytes("Hello", "en"),
                b"english-mp3",
            )

        self.assertEqual(
            [call.args for call in synthesis.call_args_list],
            [
                ("Hello", "hi-IN-SwaraNeural"),
                ("Hello", "en-US-AriaNeural"),
                ("Hello", "en-US-AriaNeural"),
            ],
        )

    def test_api_translate_endpoint(self):
        with patch("dharma_ai.translate_text", return_value="??????"):
            response = self.client.post(
                "/api/translate",
                json={"text": "Hello", "target_language": "hi"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"translated": "??????"})


if __name__ == "__main__":
    unittest.main()

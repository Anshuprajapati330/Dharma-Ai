import hashlib
import os
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def signup(username, password):
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json={"username": username, "password": password},
            timeout=10,
        )
        if response.status_code == 200:
            return True, "Signup successful", response.json().get("access_token")
        return False, response.json().get("detail", "Signup failed"), None
    except requests.RequestException:
        return False, "Backend unavailable. Start the API server first.", None


def login(username, password):
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if response.status_code == 200:
            return True, "Login successful", response.json().get("access_token")
        return False, response.json().get("detail", "Login failed"), None
    except requests.RequestException:
        return False, "Backend unavailable. Start the API server first.", None


def save_chat(token, message, assistant_response, mode):
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": message,
                "assistant_response": assistant_response,
                "mode": mode,
            },
            timeout=10,
        )
        if response.status_code == 200:
            return True, "Chat saved"
        return False, response.json().get("detail", "Chat could not be saved")
    except requests.RequestException:
        return False, "Chat could not be saved because the backend is unavailable."


def get_chat_history(token):
    try:
        response = requests.get(
            f"{API_BASE_URL}/chat/history",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if response.status_code == 200:
            return True, response.json()
        return False, response.json().get("detail", "Chat history could not be loaded")
    except requests.RequestException:
        return False, "Chat history could not be loaded because the backend is unavailable."
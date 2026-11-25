import os
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def signup(username, password, language_preference="en"):
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json={
                "username": username,
                "password": password,
                "language_preference": language_preference,
            },
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return True, "Signup successful", data.get("access_token"), data
        return False, response.json().get("detail", "Signup failed"), None, None
    except requests.RequestException:
        return False, "Backend unavailable. Start the API server first.", None, None


def login(username, password):
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return True, "Login successful", data.get("access_token"), data
        detail = response.json().get("detail", "Login failed")
        if response.status_code == 401 and detail == "Invalid password":
            detail = "Incorrect password"
        elif response.status_code == 422:
            detail = "Password must be at least 8 characters"
        return False, detail, None, None
    except requests.RequestException:
        return False, "Backend unavailable. Start the API server first.", None, None


def get_user_profile(token):
    try:
        response = requests.get(
            f"{API_BASE_URL}/user/profile",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if response.status_code == 200:
            return True, response.json()
        return False, None
    except requests.RequestException:
        return False, None


def update_user_language(token, language):
    try:
        response = requests.put(
            f"{API_BASE_URL}/user/language",
            headers={"Authorization": f"Bearer {token}"},
            json={"language": language},
            timeout=10,
        )
        if response.status_code == 200:
            return True, response.json().get("language_preference", language)
        return False, language
    except requests.RequestException:
        return False, language


def save_chat(token, message, assistant_response, mode, chat_id=None, replace_last_response=False):
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "message": message,
                "assistant_response": assistant_response,
                "mode": mode,
                "chat_id": chat_id,
                "replace_last_response": replace_last_response,
            },
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return True, "Chat saved", data.get("session_id"), data.get("title")
        return False, response.json().get("detail", "Chat could not be saved"), None, None
    except requests.RequestException:
        return False, "Chat could not be saved because the backend is unavailable.", None, None


def delete_chat(token, chat_id):
    try:
        response = requests.delete(
            f"{API_BASE_URL}/chat/{chat_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if response.status_code == 200:
            return True, "Chat deleted"
        return False, response.json().get("detail", "Could not delete chat")
    except requests.RequestException:
        return False, "Backend is unavailable."


def clear_chat_history(token):
    try:
        response = requests.delete(
            f"{API_BASE_URL}/chat/history",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if response.status_code == 200:
            return True, "History cleared"
        return False, response.json().get("detail", "Could not clear history")
    except requests.RequestException:
        return False, "Backend is unavailable."


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
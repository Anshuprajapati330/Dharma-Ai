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
            return True, "Signup successful"
        return False, response.json().get("detail", "Signup failed")
    except requests.RequestException:
        return False, "Backend unavailable. Start the API server first."


def login(username, password):
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if response.status_code == 200:
            return True, "Login successful"
        return False, response.json().get("detail", "Login failed")
    except requests.RequestException:
        return False, "Backend unavailable. Start the API server first."
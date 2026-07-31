import os
import requests

from sqlalchemy.orm import sessionmaker

from backend.auth import hash_password, verify_password
from backend.models import User, engine

Session = sessionmaker(bind=engine)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def _ensure_local_user_store():
    from backend.models import Base

    Base.metadata.create_all(engine)


def signup(username, password):
    username = (username or "").strip()
    password = (password or "").strip()
    if not username or not password:
        return False, "Username and password are required."

    _ensure_local_user_store()
    session_factory = Session()
    try:
        existing = session_factory.query(User).filter(User.username == username).first()
        if existing:
            return False, "User already exists"

        user = User(username=username, password_hash=hash_password(password))
        session_factory.add(user)
        session_factory.commit()
        return True, "Signup successful"
    finally:
        session_factory.close()


def login(username, password):
    username = (username or "").strip()
    password = (password or "").strip()
    if not username or not password:
        return False, "Username and password are required."

    _ensure_local_user_store()
    session_factory = Session()
    try:
        user = session_factory.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            return False, "Invalid credentials"
        return True, "Login successful"
    finally:
        session_factory.close()


def signup_via_backend(username, password):
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
        return None, None


def login_via_backend(username, password):
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
        return None, None
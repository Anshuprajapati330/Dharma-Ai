import json
import os
import hashlib

FILE = "users.json"

def load_users():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(FILE, "w") as f:
        json.dump(users, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup(username, password):
    users = load_users()

    if username in users:
        return False, "User already exists"

    users[username] = hash_password(password)
    save_users(users)

    return True, "Signup successful"

def login(username, password):
    users = load_users()

    if username not in users:
        return False, "User not found"

    if users[username] != hash_password(password):
        return False, "Incorrect password"

    return True, "Login successful"
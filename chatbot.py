import os
import subprocess
import sys
import time
from pathlib import Path

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
APP_DIR = Path(__file__).resolve().parent

# Configure the page before starting the local API or rendering widgets.
st.set_page_config(page_title="Dharma-AI", page_icon="🧠", layout="wide")


def ensure_backend():
    """Reuse a running local API or start one for the Streamlit session."""
    try:
        if requests.get(f"{API_BASE_URL}/health", timeout=0.75).ok:
            return True
    except requests.RequestException:
        pass

    if not API_BASE_URL.startswith(("http://127.0.0.1", "http://localhost")):
        return False

    backend_process = st.session_state.get("backend_process")
    if backend_process is None or backend_process.poll() is not None:
        try:
            backend_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
                cwd=str(APP_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            return False
        st.session_state.backend_process = backend_process

    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if backend_process.poll() is not None:
            return False
        try:
            if requests.get(f"{API_BASE_URL}/health", timeout=0.25).ok:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.2)

    return False


if "backend_available" not in st.session_state:
    st.session_state.backend_available = ensure_backend()


def get_auth_functions():
    from auth import login, signup, get_chat_history, save_chat
    return login, signup, get_chat_history, save_chat


def get_response_function():
    from dharma_ai import generate_response
    return generate_response


def get_voice_function():
    from voice_input import speech_to_text
    return speech_to_text

# ----------------------
# SESSION STATE
# ----------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "messages" not in st.session_state:
    st.session_state.messages = []

if "mode" not in st.session_state:
    st.session_state.mode = "Calm 🧘"

if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""

if "draft_input" not in st.session_state:
    st.session_state.draft_input = ""

if "last_auth_error" not in st.session_state:
    st.session_state.last_auth_error = ""

if "access_token" not in st.session_state:
    st.session_state.access_token = None

def show_auth_error(message):
    """Show the same authentication error only once until it changes."""
    if message != st.session_state.last_auth_error:
        st.error(message)
        st.session_state.last_auth_error = message

# ----------------------
# 🔐 LOGIN / SIGNUP UI
# ----------------------
if not st.session_state.authenticated:

    st.title("🔐 Dharma-AI Login")

    tab1, tab2 = st.tabs(["Login", "Signup"])

    # LOGIN
    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            st.session_state.backend_available = ensure_backend()
            if st.session_state.backend_available:
                login, signup, get_chat_history, save_chat = get_auth_functions()
                success, msg, token = login(username, password)
                if success:
                    st.session_state.last_auth_error = ""
                    st.session_state.authenticated = True
                    st.session_state.user = username
                    st.session_state.access_token = token
                    history_ok, history = get_chat_history(token)
                    if history_ok:
                        st.session_state.messages = [
                            message
                            for chat in history
                            for message in chat["messages"]
                        ]
                    st.success("Login successful")
                    st.rerun()
                else:
                    show_auth_error(msg)
            else:
                show_auth_error("Backend is temporarily unavailable. Please try again.")

    # SIGNUP
    with tab2:
        new_user = st.text_input("New Username", key="signup_user")
        new_pass = st.text_input("New Password", type="password", key="signup_pass")

        if st.button("Signup"):
            st.session_state.backend_available = ensure_backend()
            if st.session_state.backend_available:
                login, signup, get_chat_history, save_chat = get_auth_functions()
                success, msg, _ = signup(new_user, new_pass)
                if success:
                    st.session_state.last_auth_error = ""
                    st.success("Signup successful, now login")
                else:
                    show_auth_error(msg)
            else:
                show_auth_error("Backend is temporarily unavailable. Please try again.")

# ----------------------
# 🤖 CHATBOT UI
# ----------------------
else:

    # ----------------------
    # SIDEBAR
    # ----------------------
    with st.sidebar:
        st.write(f"👤 {st.session_state.user}")

        st.session_state.mode = st.selectbox(
            "Select Mode",
            ["Calm 🧘", "Logical 🧠", "Ethical ⚖️", "Motivational 🚀", "Direct 🎯"]
        )

        if st.button("🧹 Clear Chat"):
            st.session_state.messages = []
            st.rerun()

        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.access_token = None
            st.session_state.messages = []
            st.rerun()

    # ----------------------
    # TITLE
    # ----------------------
    st.title("🧠 Dharma-AI")
    st.caption("Ethical • Intelligent • Voice-enabled AI")

    # ----------------------
    # TIPS
    # ----------------------
    st.markdown("### 💡 Tips")
    st.info("Ask about life, ethics, decisions, or motivation.")

    # ----------------------
    # CHAT HISTORY
    # ----------------------
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**Dharma-AI:** {msg['content']}  \n`{msg.get('mode','')}`")

    # ----------------------
    # INPUT AREA
    # ----------------------
    col1, col2, col3 = st.columns([5, 1, 1])

    with col1:
        user_input = st.text_input("Type your message...", key="chat_input")

    with col2:
        send_button = st.button("Send")

    with col3:
        mic_button = st.button("🎤 Speak")

    # ----------------------
    # TEXT INPUT
    # ----------------------
    if send_button:
        cleaned_input = user_input.strip()
        last_message = st.session_state.messages[-1] if st.session_state.messages else None
        if not cleaned_input or (last_message and last_message["role"] == "user" and last_message["content"] == cleaned_input):
            st.stop()

        st.session_state.messages.append({"role": "user", "content": cleaned_input})

        with st.spinner("🧠 Thinking..."):
            generate_response = get_response_function()
            response = generate_response(cleaned_input, st.session_state.mode.split()[0])

        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "mode": st.session_state.mode
        })

        _, _, _, save_chat = get_auth_functions()
        save_chat(st.session_state.access_token, cleaned_input, response, st.session_state.mode)

        st.session_state.draft_input = ""
        st.rerun()

    # ----------------------
    # VOICE INPUT
    # ----------------------
    if mic_button:
        st.info("🎤 Listening... Speak now")

        speech_to_text = get_voice_function()
        voice_text = speech_to_text()

        if voice_text:
            st.session_state.messages.append({
                "role": "user",
                "content": voice_text
            })

            with st.spinner("🧠 Thinking..."):
                generate_response = get_response_function()
                response = generate_response(voice_text, st.session_state.mode.split()[0])

            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "mode": st.session_state.mode
            })

            _, _, _, save_chat = get_auth_functions()
            save_chat(st.session_state.access_token, voice_text, response, st.session_state.mode)

            st.rerun()
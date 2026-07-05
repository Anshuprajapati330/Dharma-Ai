import streamlit as st
from auth import login, signup
from dharma_ai import generate_response
from daily_wisdom import get_daily_wisdom
from voice_input import speech_to_text

# ----------------------
# PAGE CONFIG
# ----------------------
st.set_page_config(page_title="Dharma-AI", page_icon="🧠", layout="wide")

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
            success, msg = login(username, password)
            if success:
                st.session_state.authenticated = True
                st.session_state.user = username
                st.success("Login successful")
                st.rerun()
            else:
                st.error(msg)

    # SIGNUP
    with tab2:
        new_user = st.text_input("New Username", key="signup_user")
        new_pass = st.text_input("New Password", type="password", key="signup_pass")

        if st.button("Signup"):
            success, msg = signup(new_user, new_pass)
            if success:
                st.success("Signup successful, now login")
            else:
                st.error(msg)

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
    if send_button and user_input:
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        with st.spinner("🧠 Thinking..."):
            response = generate_response(user_input, st.session_state.mode.split()[0])

        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "mode": st.session_state.mode
        })

        st.session_state.chat_input = ""
        st.rerun()

    # ----------------------
    # VOICE INPUT
    # ----------------------
    if mic_button:
        st.info("🎤 Listening... Speak now")

        voice_text = speech_to_text()

        if voice_text:
            st.session_state.messages.append({
                "role": "user",
                "content": voice_text
            })

            with st.spinner("🧠 Thinking..."):
                response = generate_response(voice_text, st.session_state.mode.split()[0])

            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "mode": st.session_state.mode
            })

            st.rerun()
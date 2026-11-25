import os
import logging
import subprocess
import sys
import threading
import time
from datetime import date, datetime, timezone
from pathlib import Path
from html import escape
import json
import re

import requests
import streamlit as st
from daily_wisdom import get_daily_wisdom
from response_formatting import format_ai_content

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Dharma-AI | Wisdom & Ethics Assistant",
    page_icon="🪷",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
APP_DIR = Path(__file__).resolve().parent

# ============================================================
# BILINGUAL UI DICTIONARY
# ============================================================
UI_TEXT = {
    "en": {
        "app_title": "Dharma-AI",
        "app_tagline": "Ancient Wisdom × Modern Ethics × AI",
        "online": "Online",
        "new_chat": "⊕  New Chat",
        "chat_history": "◷  Chat History",
        "clear_chat": "🗑  Clear Chat",
        "clear_all": "🗑  Clear All History",
        "daily_wisdom": "☼  Daily Wisdom",
        "settings": "⚙  Settings",
        "logout": "⇥  Logout",
        "language_label": "Language: 🇬🇧 English",
        "switch_lang": "Switch to हिन्दी",
        "recent_conversations": "Recent Conversations",
        "no_conversations": "No saved conversations yet.",
        "modes_title": "CHAT MODES",
        "composer_placeholder": "Ask Dharma-AI anything about your decisions, ethics, life...",
        "composer_hint": "Dharma-AI provides ethical clarity and wisdom, but all decisions remain yours.",
        "reflecting": "🪷 Dharma-AI is reflecting...",
        "generating_response": "Generating the response...",
        "ai_error": "Dharma-AI could not reach the configured AI model. Check provider connectivity or quota and try again.",
        "chat_save_warning": "Your response was generated, but it could not be saved to chat history.",
        "retry_history": "Retry loading history",
        "starting_ai": "🪷 Dharma-AI is preparing the knowledge base...",
        "empty_title": "What is on your mind?",
        "empty_desc": "Explore timeless wisdom from the Bhagavad Gita, Ramayana, Mahabharata and Western ethics, powered by AI.",
        "empty_prompt_label": "Or choose a starting reflection:",
        "listen": "🔊 Listen",
        "listen_hi": "🔊 Listen in Hindi",
        "listen_en": "🔊 Listen in English",
        "pause": "⏸ Pause",
        "resume": "▶ Play",
        "stop": "⏹ Stop",
        "copy": "📋 Copy",
        "copied": "✓ Copied!",
        "translate_to": "🌐 Translate to Hindi",
        "original_text": "Original text",
        "regenerate": "↻ Regenerate",
        "mic_title": "Voice input",
        "send_title": "Send message",
        "listening": "🔴 Listening... Speak now (Tap 🎙 again to stop)",
        "transcribing": "⏳ Transcribing speech...",
        "mic_unavailable": "Microphone access is unavailable. You can continue using text input.",
        "type_first": "Please enter a message first.",
        "calm": "Calm",
        "calm_desc": "Peaceful & mindful",
        "logical": "Logical",
        "logical_desc": "Reasoned & balanced",
        "ethical": "Ethical",
        "ethical_desc": "Duty & principles",
        "motivational": "Motivational",
        "motivational_desc": "Inspire & uplift",
        "direct": "Direct",
        "direct_desc": "Clear & practical",
        "suggestions": [
            "I am confused about an important career decision.",
            "How can I deal with fear of failure and anxiety?",
            "What does the Bhagavad Gita teach about attachment and duty?",
            "How do I resolve a painful conflict with someone close to me?",
        ],
    },
    "hi": {
        "app_title": "Dharma-AI (धर्म-AI)",
        "app_tagline": "सनातन विवेक × आधुनिक नीतिशास्त्र × AI",
        "online": "सक्रिय (Online)",
        "new_chat": "⊕  नई बातचीत",
        "chat_history": "◷  चैट इतिहास",
        "clear_chat": "🗑  चैट साफ़ करें",
        "clear_all": "🗑  समस्त इतिहास साफ़ करें",
        "daily_wisdom": "☼  दैनिक विवेक (Daily Wisdom)",
        "settings": "⚙  सेटिंग्स",
        "logout": "⇥  लॉग आउट",
        "language_label": "भाषा: 🇮🇳 हिन्दी",
        "switch_lang": "Switch to English",
        "recent_conversations": "हालिया बातचीत",
        "no_conversations": "अभी कोई सहेजी गई बातचीत नहीं है।",
        "modes_title": "संवाद शैली (MODES)",
        "composer_placeholder": "Dharma-AI से जीवन, कर्तव्य, निर्णय या दुविधा पर पूछें...",
        "composer_hint": "Dharma-AI विवेकपूर्ण दृष्टि प्रदान करता है, अंतिम निर्णय सदैव आपका अपना है।",
        "reflecting": "🪷 Dharma-AI विचार कर रहा है...",
        "generating_response": "उत्तर तैयार किया जा रहा है...",
        "ai_error": "Dharma-AI चुने हुए AI मॉडल से उत्तर नहीं पा सका। कनेक्शन या कोटा जाँचकर पुनः प्रयास करें।",
        "chat_save_warning": "उत्तर तैयार हुआ, लेकिन चैट इतिहास में सहेजा नहीं जा सका।",
        "retry_history": "इतिहास फिर से लोड करें",
        "starting_ai": "🪷 Dharma-AI ज्ञानकोश तैयार कर रहा है...",
        "empty_title": "आपके मन में क्या विचार या दुविधा है?",
        "empty_desc": "गीता, रामायण, महाभारत और पाश्चात्य नीतिशास्त्र के आलोक में अपने निर्णयों को स्पष्ट दिशा दें।",
        "empty_prompt_label": "या किसी विचार से शुरुआत करें:",
        "listen": "🔊 सुनें",
        "listen_hi": "🔊 हिन्दी में सुनें",
        "listen_en": "🔊 English में सुनें",
        "pause": "⏸ रोकें",
        "resume": "▶ फिर चलाएँ",
        "stop": "⏹ रोकें",
        "copy": "📋 कॉपी करें",
        "copied": "✓ कॉपी किया गया!",
        "translate_to": "🌐 Translate to English",
        "original_text": "मूल संदेश",
        "regenerate": "↻ पुनः उत्तर दें",
        "mic_title": "ध्वनि इनपुट (बोलकर पूछें)",
        "send_title": "संदेश भेजें",
        "listening": "🔴 सुन रहे हैं... बोलिए (रोकने के लिए 🎙 दबाएं)",
        "transcribing": "⏳ वाणी का रूपांतरण हो रहा है...",
        "mic_unavailable": "माइक्रोफ़ोन उपलब्ध नहीं है। आप सामान्य रूप से लिखकर पूछ सकते हैं।",
        "type_first": "कृपया पहले एक संदेश लिखें।",
        "calm": "Calm (शांत)",
        "calm_desc": "शांत व संवेदनशील",
        "logical": "Logical (तर्कसंगत)",
        "logical_desc": "तर्कसंगत व संतुलित",
        "ethical": "Ethical (नैतिक)",
        "ethical_desc": "कर्तव्य व मूल्य",
        "motivational": "Motivational (प्रेरक)",
        "motivational_desc": "प्रेरक व सकारात्मक",
        "direct": "Direct (प्रत्यक्ष)",
        "direct_desc": "संक्षिप्त व व्यावहारिक",
        "suggestions": [
            "मैं करियर से जुड़े एक बड़े निर्णय को लेकर असमंजस में हूँ।",
            "असफलता के भय और मानसिक तनाव से कैसे निपटें?",
            "श्रीमद्भगवद्गीता में निष्काम कर्म और आसक्ति के बारे में क्या कहा गया है?",
            "क्रोध और आवेग पर नियंत्रण पाने के व्यावहारिक उपाय क्या हैं?",
        ],
    },
}

# ============================================================
# BACKEND AUTO-START HELPER
# ============================================================
_backend_start_lock = threading.Lock()
_backend_process = None


def ensure_backend():
    """Ensure the FastAPI backend is running locally."""
    global _backend_process
    try:
        if requests.get(f"{API_BASE_URL}/health", timeout=0.75).ok:
            return True
    except requests.RequestException:
        pass

    if not API_BASE_URL.startswith(("http://127.0.0.1", "http://localhost")):
        return False

    with _backend_start_lock:
        try:
            if requests.get(f"{API_BASE_URL}/health", timeout=0.75).ok:
                return True
        except requests.RequestException:
            pass

        if _backend_process is None or _backend_process.poll() is not None:
            try:
                _backend_process = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
                    cwd=str(APP_DIR),
                )
            except OSError:
                logging.exception("Could not start the Dharma-AI backend")
                return False
        backend_process = _backend_process

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

# ============================================================
# INITIALIZE SESSION STATE
# ============================================================
if "backend_available" not in st.session_state:
    st.session_state.backend_available = False

if "ai_warmup_complete" not in st.session_state:
    st.session_state.ai_warmup_complete = threading.Event()

if "ai_warmup_started" not in st.session_state:
    st.session_state.ai_warmup_started = False


def start_ai_warmup():
    if st.session_state.ai_warmup_started:
        return

    st.session_state.ai_warmup_started = True
    warmup_complete = st.session_state.ai_warmup_complete

    def _warm_ai():
        try:
            from dharma_ai import warm_up
            if not warm_up():
                logging.warning("AI warm-up did not complete successfully")
        except Exception:
            logging.exception("AI warm-up failed")
        finally:
            warmup_complete.set()

    threading.Thread(target=_warm_ai, daemon=True).start()


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = ""

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "language" not in st.session_state:
    st.session_state.language = "en"

if "mode" not in st.session_state:
    st.session_state.mode = "Calm"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "recent_chats" not in st.session_state:
    st.session_state.recent_chats = []

if "chat_history_loaded" not in st.session_state:
    st.session_state.chat_history_loaded = False

if "chat_history_load_error" not in st.session_state:
    st.session_state.chat_history_load_error = ""

if "show_history" not in st.session_state:
    st.session_state.show_history = False

if "daily_wisdom" not in st.session_state:
    st.session_state.daily_wisdom = get_daily_wisdom()

if "chat_input_version" not in st.session_state:
    st.session_state.chat_input_version = 0

if "last_auth_error" not in st.session_state:
    st.session_state.last_auth_error = ""

if "translations" not in st.session_state:
    st.session_state.translations = {}

if "show_translation_for" not in st.session_state:
    st.session_state.show_translation_for = set()

if "staged_prompt" not in st.session_state:
    st.session_state.staged_prompt = ""

if "regenerating_response" not in st.session_state:
    st.session_state.regenerating_response = False

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_auth_functions():
    from auth import login, signup, get_chat_history, save_chat, update_user_language, get_user_profile, delete_chat, clear_chat_history
    return login, signup, get_chat_history, save_chat, update_user_language, get_user_profile, delete_chat, clear_chat_history

def get_response_function():
    from dharma_ai import generate_response
    return generate_response

def get_translation_function():
    from dharma_ai import translate_text
    return translate_text

def t(key):
    """Retrieve localized string based on active language."""
    lang = st.session_state.get("language", "en")
    lang_dict = UI_TEXT.get(lang, UI_TEXT["en"])
    return lang_dict.get(key, UI_TEXT["en"].get(key, ""))

def format_chat_time(timestamp):
    if not timestamp:
        return ""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%b %d, %I:%M %p")
    except Exception:
        return ""

# ============================================================
# UNIFIED CSS DESIGN (DHAMIC LOTUS AESTHETIC)
# ============================================================
st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,500;0,600;1,400&family=Noto+Sans+Devanagari:wght@400;500;600&display=swap');

:root {
    --bg-primary: #1a273a;
    --bg-secondary: #23344d;
    --bg-card: rgba(28, 42, 63, 0.85);
    --bg-composer: rgba(22, 34, 52, 0.95);
    --accent-lotus: #f09cb0;
    --accent-gold: #e5b869;
    --accent-teal: #4ecdc4;
    --text-primary: #f0f4fa;
    --text-secondary: #a9b9d4;
    --border-color: rgba(255, 255, 255, 0.09);
    --border-highlight: rgba(240, 156, 176, 0.35);
}

html, body {
    font-family: 'Inter', 'Noto Sans Devanagari', -apple-system, sans-serif;
    color: var(--text-primary);
    background-color: var(--bg-primary);
}

/* Restrict main container from overflowing outside the viewport */
[data-testid="stApp"] header[data-testid="stHeader"] {
    display: flex !important;
    position: fixed !important;
    inset: 0 0 auto !important;
    height: 2.75rem !important;
    z-index: 1000 !important;
    background: transparent !important;
    box-shadow: none !important;
    pointer-events: none !important;
}

[data-testid="stHeader"] [data-testid="stToolbar"] {
    pointer-events: none !important;
}

[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"] {
    visibility: visible !important;
    pointer-events: auto !important;
}

[data-testid="stAppDeployButton"],
[data-testid="stMainMenu"] {
    display: none !important;
}

[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at 75% 20%, rgba(112, 145, 185, 0.12), transparent 35%),
                linear-gradient(135deg, #182536 0%, #22344c 50%, #152232 100%);
    height: 100vh;
    overflow: hidden !important;
}

[data-testid="stAppViewContainer"] > .main {
    height: 100vh;
    overflow: hidden !important;
}

.block-container {
    max-width: 1140px !important;
    padding: 0.8rem 1.4rem 0.5rem !important;
    height: 100vh !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
    position: relative !important;
}

[data-testid="stMain"] .block-container > [data-testid="stVerticalBlock"] {
    flex: 1 1 0% !important;
    min-height: 0 !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
    padding-bottom: 120px !important;
    box-sizing: border-box !important;
}

[data-testid="stElementContainer"]:has(#dharma-chat-scroll) {
    display: flex !important;
    flex: 1 1 0% !important;
    min-height: 0 !important;
    overflow: hidden !important;
}

[data-testid="stElementContainer"]:has(#dharma-chat-scroll) > [data-testid="stHtml"] {
    display: flex !important;
    flex: 1 1 0% !important;
    min-height: 0 !important;
    overflow: hidden !important;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #172436 0%, #1c2c42 100%) !important;
    border-right: 1px solid var(--border-color) !important;
}

[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem !important;
    height: auto !important;
    overflow-y: auto !important;
}

.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 12px 16px;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 14px;
}

.sidebar-logo {
    font-size: 32px;
    line-height: 1;
    filter: drop-shadow(0 2px 8px rgba(240, 156, 176, 0.4));
}

.sidebar-title {
    font-family: 'Playfair Display', serif;
    font-size: 22px;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: 0.5px;
}

.sidebar-tagline {
    font-size: 10px;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 2px;
}

.sidebar-user-card {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 12px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    margin-bottom: 14px;
}

.sidebar-avatar {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: linear-gradient(135deg, #f09cb0, #e5b869);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 13px;
    color: #172436;
}

.sidebar-section-title {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.2px;
    color: #8397b8;
    text-transform: uppercase;
    margin: 14px 4px 6px;
}

/* Stable Header */
.dharma-header {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 18px;
    background: var(--bg-card);
    backdrop-filter: blur(14px);
    border: 1px solid var(--border-color);
    border-radius: 14px;
    margin-bottom: 10px;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.15);
}

.dharma-header-brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.dharma-header-logo {
    font-size: 26px;
    line-height: 1;
}

.dharma-header-text h2 {
    margin: 0;
    font-family: 'Playfair Display', serif;
    font-size: 19px;
    color: #ffffff;
    font-weight: 600;
}

.dharma-header-text p {
    margin: 0;
    font-size: 11px;
    color: var(--text-secondary);
}

.dharma-header-pills {
    display: flex;
    align-items: center;
    gap: 8px;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    background: rgba(78, 205, 196, 0.12);
    border: 1px solid rgba(78, 205, 196, 0.3);
    border-radius: 20px;
    font-size: 11px;
    color: #8be5dc;
    font-weight: 500;
}

.status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #4ecdc4;
    box-shadow: 0 0 6px #4ecdc4;
}

.mode-badge {
    padding: 4px 11px;
    background: rgba(229, 184, 105, 0.14);
    border: 1px solid rgba(229, 184, 105, 0.35);
    border-radius: 20px;
    font-size: 11px;
    color: #f7d28e;
    font-weight: 500;
}

.lang-badge {
    padding: 4px 11px;
    background: rgba(240, 156, 176, 0.14);
    border: 1px solid rgba(240, 156, 176, 0.35);
    border-radius: 20px;
    font-size: 11px;
    color: #f7bccc;
    font-weight: 500;
}

/* Chat Scroll Container */
#dharma-chat-scroll {
    flex: 1 1 0%;
    height: 100% !important;
    max-height: 100% !important;
    min-height: 0 !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    scroll-behavior: auto;
    padding: 10px 14px 24px 6px;
    margin-bottom: 8px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    box-sizing: border-box !important;
    overscroll-behavior: contain;
}

#dharma-chat-scroll::-webkit-scrollbar {
    width: 8px;
}

#dharma-chat-scroll::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.12);
    border-radius: 10px;
}

#dharma-chat-scroll::-webkit-scrollbar-thumb {
    background: rgba(240, 156, 176, 0.35);
    border-radius: 10px;
}

#dharma-chat-scroll::-webkit-scrollbar-thumb:hover {
    background: rgba(240, 156, 176, 0.6);
}

/* Message Cards */
.msg-row-user {
    display: flex;
    justify-content: flex-end;
    margin: 4px 0;
}

.msg-bubble-user {
    max-width: 78%;
    background: linear-gradient(135deg, #2b4568 0%, #35537d 100%);
    border: 1px solid rgba(138, 178, 235, 0.28);
    border-radius: 18px 18px 4px 18px;
    padding: 13px 18px;
    color: #ffffff;
    font-size: 14.5px;
    line-height: 1.55;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
    word-break: break-word;
}

.msg-row-ai {
    display: flex;
    gap: 12px;
    margin: 6px 0;
    align-items: flex-start;
}

.msg-avatar-ai {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(240, 156, 176, 0.25), rgba(229, 184, 105, 0.25));
    border: 1px solid var(--border-highlight);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 19px;
    flex-shrink: 0;
    margin-top: 4px;
}

.msg-card-ai {
    flex: 1;
    max-width: 92%;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 4px 18px 18px 18px;
    padding: 16px 20px;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.18);
}

.msg-card-ai-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.msg-card-ai-title {
    font-weight: 600;
    font-size: 13.5px;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 8px;
}

.msg-card-ai-content {
    font-size: 14.5px;
    line-height: 1.7;
    color: #e4edf8;
    word-break: break-word;
}

.msg-card-ai-content p {
    margin: 0 0 10px 0;
}

.msg-card-ai-content h3,
.msg-card-ai-content h4 {
    color: #ffffff;
    line-height: 1.45;
    margin: 14px 0 7px;
}

.msg-card-ai-content h3 {
    font-size: 16px;
}

.msg-card-ai-content h4 {
    font-size: 14px;
}

.msg-card-ai-content ul {
    margin: 6px 0 12px 20px;
    padding: 0;
}

.msg-card-ai-content li {
    margin-bottom: 5px;
}

.msg-card-ai-content strong {
    color: #ffffff;
    font-weight: 600;
}

/* Shloka highlight box */
.shloka-card {
    background: linear-gradient(135deg, rgba(229, 184, 105, 0.1) 0%, rgba(240, 156, 176, 0.07) 100%);
    border-left: 3px solid var(--accent-gold);
    border-radius: 8px;
    padding: 12px 16px;
    margin: 12px 0;
}

.shloka-label {
    font-size: 11px;
    font-weight: 700;
    color: var(--accent-gold);
    letter-spacing: 0.8px;
    text-transform: uppercase;
    margin-bottom: 6px;
}

.shloka-text {
    font-family: 'Noto Sans Devanagari', 'Playfair Display', serif;
    font-size: 15.5px;
    color: #fff6e5;
    font-weight: 500;
    line-height: 1.6;
}

/* Message Actions Bar */
.msg-actions-bar {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 14px;
    padding-top: 10px;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
}

[class*="st-key-message-actions-handler"] {
    display: none !important;
}

.action-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11.5px;
    font-family: inherit;
    color: var(--text-secondary);
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 3px 10px;
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
    line-height: inherit;
}

.action-chip:hover {
    color: #ffffff;
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.2);
}

.translation-box {
    margin-top: 12px;
    padding: 12px 16px;
    background: rgba(20, 32, 48, 0.9);
    border: 1px dashed rgba(240, 156, 176, 0.4);
    border-radius: 10px;
    font-size: 13.5px;
    line-height: 1.6;
    color: #f7d2dc;
}

/* Empty State */
.empty-hero {
    margin: auto;
    text-align: center;
    max-width: 640px;
    padding: 24px 16px;
}

.empty-lotus {
    font-size: 48px;
    line-height: 1;
    margin-bottom: 12px;
    filter: drop-shadow(0 4px 12px rgba(240, 156, 176, 0.4));
}

.empty-hero h1 {
    font-family: 'Playfair Display', serif;
    font-size: 28px;
    color: #ffffff;
    margin: 0 0 8px;
}

.empty-hero p {
    font-size: 14px;
    color: var(--text-secondary);
    line-height: 1.6;
    margin: 0 0 20px;
}

.suggestion-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    text-align: left;
    margin-top: 12px;
}

.suggestion-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 12px 14px;
    font-size: 13px;
    color: #dde7f5;
    transition: all 0.2s ease;
    cursor: pointer;
}

.suggestion-card:hover {
    border-color: var(--border-highlight);
    background: rgba(38, 56, 82, 0.85);
    transform: translateY(-1px);
}

/* Fixed Bottom Composer */
.dharma-composer-shell,
[class*="st-key-dharma-composer-shell"] {
    position: absolute !important;
    left: 1.4rem;
    right: 1.4rem;
    bottom: 0.5rem;
    z-index: 20;
    width: calc(100% - 2.8rem) !important;
    background: var(--bg-composer);
    backdrop-filter: blur(18px);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 10px 14px;
    box-shadow: 0 -4px 22px rgba(0, 0, 0, 0.35);
    box-sizing: border-box;
}

.composer-hint-text {
    font-size: 10.5px;
    color: #7d90af;
    text-align: center;
    margin-top: 6px;
}

/* Voice active banner */
.voice-banner {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.35);
    border-radius: 8px;
    padding: 6px 12px;
    margin-bottom: 8px;
    font-size: 12px;
    color: #fca5a5;
    animation: pulse 1.6s infinite;
}

@keyframes pulse {
    0% { opacity: 0.8; }
    50% { opacity: 1; }
    100% { opacity: 0.8; }
}

/* Login Page Original Preservation */
.login-page {
    height: calc(100vh - 125px);
    min-height: 0;
    margin: -10px -18px -25px;
    padding: 44px 50px 34px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: radial-gradient(circle at 18% 22%, rgba(240, 156, 176, 0.14), transparent 30%),
                radial-gradient(circle at 82% 80%, rgba(229, 184, 105, 0.12), transparent 32%),
                linear-gradient(135deg, #182536 0%, #20314a 55%, #131f2e 100%);
    border-radius: 20px;
    border: 1px solid var(--border-color);
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.3);
}

.login-logo {
    font-size: 44px;
    line-height: 1;
    margin-bottom: 4px;
    filter: drop-shadow(0 4px 12px rgba(240, 156, 176, 0.45));
}

.login-title {
    font-family: 'Playfair Display', serif;
    font-size: 32px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.5px;
}

.login-subtitle {
    font-size: 12px;
    color: var(--accent-lotus);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 3px;
    font-weight: 600;
}

.login-hero-copy h1 {
    font-family: 'Playfair Display', serif;
    font-size: 38px;
    line-height: 1.15;
    color: #ffffff;
    margin: 18px 0 10px;
}

.login-hero-copy h1 span {
    color: var(--accent-gold);
    font-style: italic;
}

.login-hero-description {
    font-size: 14px;
    line-height: 1.65;
    color: var(--text-secondary);
    max-width: 580px;
    margin-bottom: 22px;
}

.login-features {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
    flex-wrap: wrap;
}

.login-feature {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 10px 14px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 12.5px;
}

.login-feature-icon {
    font-size: 18px;
    color: var(--accent-gold);
}

.login-feature strong {
    color: #ffffff;
}

.login-feature small {
    display: block;
    font-size: 10.5px;
    color: var(--text-secondary);
    margin-top: 2px;
}

.login-quote {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    color: #c9d6eb;
    font-size: 13.5px;
    padding-left: 14px;
    border-left: 2px solid var(--accent-lotus);
}

/* Tabs & Auth Form Styling */
[data-testid="stTabs"] h3 {
    color: #ffffff !important;
    font-family: 'Playfair Display', serif;
    font-weight: 600;
}

[data-testid="stTabs"] p, [data-testid="stTabs"] .stCaption, [data-testid="stTabs"] label {
    color: #c0d0e6 !important;
}

button[data-baseweb="tab"] {
    color: #a9b9d4 !important;
    font-weight: 500;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #f09cb0 !important;
    border-bottom-color: #f09cb0 !important;
}

@media (max-width: 768px) {
    .block-container {
        padding: 0.4rem 0.6rem !important;
    }
    .suggestion-grid {
        grid-template-columns: 1fr;
    }
    .msg-bubble-user {
        max-width: 90%;
    }
    .msg-card-ai {
        max-width: 95%;
    }
    .dharma-header-text p {
        display: none;
    }
}
</style>
""")

# ============================================================
# JAVASCRIPT CLIENT FOR SCROLLING, VOICE INPUT & AUDIO TTS
# ============================================================
st.html(r"""
<script>
(function () {
// Auto-scroll the chat container to the newest message
function dharmaScrollChatToBottom() {
    const chat = document.getElementById('dharma-chat-scroll');
    if (!chat) return;
    chat.scrollTop = chat.scrollHeight;
}

function initDharmaScrollWatcher() {
    const chat = document.getElementById('dharma-chat-scroll');
    if (!chat) return;

    // Keep the latest response and its action buttons visible after each render.
    dharmaScrollChatToBottom(false);
    requestAnimationFrame(() => dharmaScrollChatToBottom(false));
    setTimeout(() => dharmaScrollChatToBottom(false), 100);
    setTimeout(() => dharmaScrollChatToBottom(false), 300);

    if (chat.dataset.scrollWatcherAttached) return;
    chat.dataset.scrollWatcherAttached = 'true';

    let userScrolledUp = false;
    chat.addEventListener('scroll', () => {
        const dist = chat.scrollHeight - chat.scrollTop - chat.clientHeight;
        userScrolledUp = dist > 90;
    }, { passive: true });

    const observer = new MutationObserver(() => {
        if (!userScrolledUp) {
            dharmaScrollChatToBottom(false);
        }
    });

    observer.observe(chat, {
        childList: true,
        subtree: true,
        characterData: true
    });
}

if (window.dharmaGlobalObserver) {
    window.dharmaGlobalObserver.disconnect();
}
window.dharmaGlobalObserver = new MutationObserver(() => {
    initDharmaScrollWatcher();
});
window.dharmaGlobalObserver.observe(document.body, { childList: true, subtree: true });
initDharmaScrollWatcher();

// Copy text helper
async function dharmaCopyText(text, btnElement) {
    try {
        if (navigator.clipboard?.writeText) {
            await navigator.clipboard.writeText(text);
        } else {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.setAttribute('readonly', '');
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            const copied = document.execCommand('copy');
            textarea.remove();
            if (!copied) throw new Error('Clipboard access is unavailable.');
        }
        showVoiceStatus('Message copied to clipboard.', 2000);
        const original = btnElement.textContent;
        btnElement.textContent = '✓ Copied!';
        setTimeout(() => { btnElement.textContent = original; }, 1800);
    } catch (error) {
        console.error('Could not copy message:', error);
        showVoiceStatus('Could not copy to clipboard. Check browser clipboard permissions.', 5000);
    }
}

// Both selected languages use the configured backend voices.
let currentSpeechCancelled = false;
let currentSpeechPaused = false;
let currentActiveAudio = null;
let currentAudioAbortController = null;
let currentAudioObjectUrl = null;
let speechRequestId = 0;

function dharmaStopSpeech() {
    speechRequestId++;
    currentSpeechCancelled = true;
    currentSpeechPaused = false;
    if (currentAudioAbortController) {
        currentAudioAbortController.abort();
        currentAudioAbortController = null;
    }
    if (currentActiveAudio) {
        const audio = currentActiveAudio;
        currentActiveAudio = null;
        audio.onplay = null;
        audio.onended = null;
        audio.onerror = null;
        audio.pause();
        audio.removeAttribute('src');
        audio.load();
    }
    if (currentAudioObjectUrl) {
        URL.revokeObjectURL(currentAudioObjectUrl);
        currentAudioObjectUrl = null;
    }
    showVoiceStatus('Audio stopped.', 2000);
}

function dharmaPauseSpeech() {
    if (currentActiveAudio && !currentActiveAudio.paused) {
        currentActiveAudio.pause();
        currentSpeechPaused = true;
        showVoiceStatus('Audio paused. Press Play to resume from this point.');
        return;
    }

    if (currentAudioAbortController) {
        currentSpeechPaused = true;
        showVoiceStatus('Audio is preparing. Press Play to resume when it is ready.');
        return;
    }

    showVoiceStatus('Audio is not currently playing.', 3000);
}

async function dharmaResumeSpeech() {
    if (currentSpeechPaused && currentActiveAudio) {
        try {
            await currentActiveAudio.play();
        } catch (error) {
            console.error('Could not resume audio playback:', error);
            showVoiceStatus('Could not resume audio. Please try again.', 5000);
        }
        return;
    }

    if (currentSpeechPaused && currentAudioAbortController) {
        currentSpeechPaused = false;
        showVoiceStatus('Preparing audio...');
        return;
    }

    showVoiceStatus('Audio is not paused.', 3000);
}

function cleanSpeechText(text) {
    return String(text || '')
        .replace(/<[^>]+>/g, ' ')
        .replace(/```[\s\S]*?```/g, ' ')
        .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        .replace(/[*#_~`>]/g, '')
        .replace(/^\s*[-•]\s*/gm, '')
        .replace(/\s+/g, ' ')
        .trim();
}

function getSpeechScriptRatios(text) {
    const letters = [...String(text || '')].filter(character => /\p{L}/u.test(character));
    if (!letters.length) return { devanagari: 0, latin: 0 };
    return {
        devanagari: letters.filter(character => /\p{Script=Devanagari}/u.test(character)).length / letters.length,
        latin: letters.filter(character => /\p{Script=Latin}/u.test(character)).length / letters.length
    };
}

async function dharmaPlayServerAudio(text, lang, requestId) {
    if (requestId !== speechRequestId || currentSpeechCancelled) return;
    const banner = document.getElementById('voice-status-banner');
    const apiBaseUrl = (banner?.dataset.apiBaseUrl || window.location.origin).replace(/\/+$/, '');
    const controller = new AbortController();
    currentAudioAbortController = controller;
    showVoiceStatus(lang === 'hi' ? '🪷 Preparing Hindi audio...' : '🔊 Preparing English audio...');
    const requestStartedAt = performance.now();
    let audio = null;

    try {
        const response = await fetch(`${apiBaseUrl}/voice/tts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, lang }),
            signal: controller.signal,
            cache: 'no-store'
        });
        if (requestId !== speechRequestId || currentSpeechCancelled) return;
        if (!response.ok) {
            const contentType = response.headers.get('content-type') || '';
            let detail = '';
            if (contentType.includes('application/json')) {
                const body = await response.json().catch(() => ({}));
                detail = body.detail || '';
            } else {
                detail = (await response.text()).trim();
            }
            throw new Error(detail || `Speech service failed (${response.status}).`);
        }

        const expectedVoice = lang === 'hi' ? 'hi-IN-SwaraNeural' : 'en-US-AriaNeural';
        const returnedVoice = response.headers.get('X-TTS-Voice');
        if (returnedVoice !== expectedVoice) {
            throw new Error(`Expected ${expectedVoice}, but the speech service returned ${returnedVoice || 'an unknown voice'}.`);
        }

        const audioBlob = await response.blob();
        if (!audioBlob.size) {
            throw new Error('Speech service returned an empty audio file.');
        }
        if (requestId !== speechRequestId || currentSpeechCancelled) return;

        currentAudioObjectUrl = URL.createObjectURL(audioBlob);
        audio = new Audio(currentAudioObjectUrl);
        currentActiveAudio = audio;
        currentAudioAbortController = null;
        const audioReadyAt = performance.now();
        const audioPreparationMs = Math.round(audioReadyAt - requestStartedAt);
        console.info('[Dharma-AI] TTS audio ready', {
            language: lang,
            voice: returnedVoice,
            preparationMs: audioPreparationMs,
            audioBytes: audioBlob.size
        });

        const releaseAudio = () => {
            if (currentActiveAudio === audio) currentActiveAudio = null;
            if (currentAudioObjectUrl) {
                URL.revokeObjectURL(currentAudioObjectUrl);
                currentAudioObjectUrl = null;
            }
        };
        audio.onplay = () => {
            if (requestId !== speechRequestId || currentActiveAudio !== audio) return;
            currentSpeechPaused = false;
            console.info('[Dharma-AI] TTS playback started', {
                language: lang,
                voice: returnedVoice,
                playbackStartMs: Math.round(performance.now() - audioReadyAt)
            });
            showVoiceStatus(
                `${lang === 'hi' ? '🔊 Playing Hindi audio' : '🔊 Playing English audio'} (ready in ${(audioPreparationMs / 1000).toFixed(1)}s).`,
                15000
            );
        };
        audio.onpause = () => {
            if (requestId !== speechRequestId || currentActiveAudio !== audio || audio.ended) return;
            currentSpeechPaused = true;
            showVoiceStatus('Audio paused. Press Play to resume from this point.');
        };
        audio.onended = () => {
            if (requestId !== speechRequestId || currentActiveAudio !== audio) return;
            currentSpeechPaused = false;
            releaseAudio();
            showVoiceStatus('Playback completed.', 2000);
        };
        audio.onerror = () => {
            if (requestId !== speechRequestId || currentActiveAudio !== audio) return;
            currentSpeechPaused = false;
            releaseAudio();
            console.error('Audio playback failed for the synthesized response.');
            showVoiceStatus('The speech service returned audio that could not be played.', 5000);
        };
        if (currentSpeechPaused) {
            audio.pause();
            showVoiceStatus('Audio paused. Press Play to resume from this point.');
            return;
        }
        await audio.play();
        if (requestId !== speechRequestId || currentSpeechCancelled) {
            audio.pause();
            return;
        }
    } catch (err) {
        if (requestId !== speechRequestId || currentSpeechCancelled) return;
        if (err.name === 'AbortError') return;
        if (err.name === 'NotAllowedError' && audio && currentActiveAudio === audio) {
            currentSpeechPaused = true;
            showVoiceStatus('Audio is ready. Press Play to start playback.');
            return;
        }
        console.error('Backend speech request or playback failed:', err);
        showVoiceStatus(err.message || 'Backend speech request failed.', 6000);
        if (currentActiveAudio === audio) {
            currentActiveAudio = null;
        }
        if (currentAudioObjectUrl) {
            URL.revokeObjectURL(currentAudioObjectUrl);
            currentAudioObjectUrl = null;
        }
        currentSpeechPaused = false;
    } finally {
        if (currentAudioAbortController === controller) {
            currentAudioAbortController = null;
        }
    }
}

async function dharmaSpeak(text, targetLang) {
    dharmaStopSpeech();
    const requestId = speechRequestId;
    currentSpeechCancelled = false;
    targetLang = targetLang === 'hi' ? 'hi' : 'en';

    let cleanText = cleanSpeechText(text);
    if (!cleanText) {
        showVoiceStatus('There is no text available to speak.', 5000);
        return;
    }

    const { devanagari: devanagariRatio, latin: latinRatio } = getSpeechScriptRatios(cleanText);
    const needsTranslation = targetLang === 'hi'
        ? devanagariRatio < 0.35
        : latinRatio < 0.6;

    if (needsTranslation) {
        showVoiceStatus(targetLang === 'hi' ? 'Translating to Hindi for speech...' : 'Translating to English for speech...');
        try {
            const banner = document.getElementById('voice-status-banner');
            const apiBaseUrl = (banner?.dataset.apiBaseUrl || window.location.origin).replace(/\/+$/, '');
            const resp = await fetch(`${apiBaseUrl}/api/translate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: cleanText, target_language: targetLang })
            });
            if (!resp.ok) {
                const error = await resp.json().catch(() => ({}));
                throw new Error(error.detail || `Translation failed (${resp.status}).`);
            }
            const data = await resp.json();
            const translatedText = cleanSpeechText(data.translated);
            if (!translatedText) {
                throw new Error('The translation service returned empty text.');
            }
            const translatedRatios = getSpeechScriptRatios(translatedText);
            const translatedRatio = targetLang === 'hi'
                ? translatedRatios.devanagari
                : translatedRatios.latin;
            if (translatedRatio < (targetLang === 'hi' ? 0.2 : 0.6)) {
                throw new Error(`The translation service did not return ${targetLang === 'hi' ? 'Hindi' : 'English'} text.`);
            }
            cleanText = translatedText;
        } catch (error) {
            if (requestId !== speechRequestId) return;
            console.error('Speech translation failed:', error);
            showVoiceStatus(`Could not translate for ${targetLang === 'hi' ? 'Hindi' : 'English'} audio: ${error.message}`, 6000);
            return;
        }
    }
    if (requestId !== speechRequestId) return;

    return dharmaPlayServerAudio(cleanText, targetLang, requestId);
}

if (!window.dharmaChatActionHandlerInstalled) {
    document.addEventListener('click', function(event) {
        const button = event.target.closest('[data-chat-action]');
        if (!button) return;

        const message = button.closest('.msg-card-ai');
        const action = button.dataset.chatAction;
        const text = message?.dataset.messageText;
        if (!message || !text) {
            showVoiceStatus('Could not load this message action. Please refresh and try again.', 5000);
            return;
        }

        if (action === 'listen-hi') {
            dharmaSpeak(text, 'hi');
        } else if (action === 'listen-en') {
            dharmaSpeak(text, 'en');
        } else if (action === 'listen') {
            dharmaSpeak(text, message.dataset.language || 'en');
        } else if (action === 'stop') {
            dharmaStopSpeech();
        } else if (action === 'pause') {
            dharmaPauseSpeech();
        } else if (action === 'resume') {
            dharmaResumeSpeech();
        } else if (action === 'copy') {
            dharmaCopyText(text, button);
        } else if (action === 'translate' || action === 'regenerate') {
            const handler = document.querySelector('[class*="st-key-message-actions-handler"]');
            const handlerButtons = handler?.querySelectorAll('button');
            const targetButton = handlerButtons?.[action === 'translate' ? 0 : 1];
            if (targetButton) {
                targetButton.click();
            } else {
                showVoiceStatus('This action is unavailable. Please refresh and try again.', 5000);
            }
        }
    });
    window.dharmaChatActionHandlerInstalled = true;
}

// Populate prompt in chat input
function dharmaPopulatePrompt(text) {
    const inputs = document.querySelectorAll('input[type="text"], textarea');
    for (let input of inputs) {
        if (input.placeholder && (input.placeholder.includes('Dharma') || input.placeholder.includes('Ask') || input.placeholder.includes('जीवन') || input.placeholder.includes('दुविधा'))) {
            const inputPrototype = input instanceof window.HTMLTextAreaElement
                ? window.HTMLTextAreaElement.prototype
                : window.HTMLInputElement.prototype;
            const valueSetter = Object.getOwnPropertyDescriptor(
                inputPrototype,
                'value'
            )?.set;
            if (!valueSetter) continue;
            valueSetter.call(input, text);
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.focus();
            return true;
        }
    }
    return false;
}


// Record audio locally and transcribe it through the authenticated API.
let voiceRecorder = null;
let voiceStream = null;
let voiceChunks = [];
let voiceState = 'idle';
let voiceRecordingId = 0;
let voiceStatusTimeout = null;

function toggleDharmaVoice(lang) {
    if (voiceState === 'recording') {
        if (voiceRecorder && voiceRecorder.state === 'recording') {
            voiceState = 'transcribing';
            voiceRecorder.stop();
            showVoiceStatus('Recording stopped. Transcribing...');
        } else {
            voiceRecordingId += 1;
            voiceState = 'idle';
            showVoiceStatus('Voice recording cancelled.', 2500);
        }
        return;
    }
    if (voiceState === 'transcribing') {
        showVoiceStatus('Transcription is still processing...');
        return;
    }

    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
        showVoiceStatus('Audio recording is not supported in this browser. Please type your message.', 5000);
        return;
    }

    const requestId = ++voiceRecordingId;
    voiceState = 'recording';
    showVoiceStatus('Requesting microphone access...');
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream) {
        if (requestId !== voiceRecordingId) {
            stream.getTracks().forEach(track => track.stop());
            return;
        }

        voiceStream = stream;
        voiceChunks = [];
        const mimeType = typeof MediaRecorder.isTypeSupported === 'function'
            ? ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4']
                .find(type => MediaRecorder.isTypeSupported(type))
            : null;
        const recorder = mimeType
            ? new MediaRecorder(stream, { mimeType })
            : new MediaRecorder(stream);
        voiceRecorder = recorder;
        let recordingFailed = false;

        recorder.ondataavailable = function(event) {
            if (event.data.size) voiceChunks.push(event.data);
        };
        recorder.onerror = function() {
            recordingFailed = true;
            showVoiceStatus('Microphone recording failed. Check your microphone and try again.', 5000);
            finishVoiceRecording();
            voiceState = 'idle';
        };
        recorder.onstop = function() {
            if (recordingFailed) return;
            const recording = new Blob(voiceChunks, {
                type: recorder.mimeType || 'audio/webm'
            });
            const audioLanguage = lang === 'hi' ? 'hi' : 'en';
            finishVoiceRecording();
            if (!recording.size) {
                voiceState = 'idle';
                showVoiceStatus('No audio was recorded. Tap the microphone to try again.', 5000);
                return;
            }
            transcribeVoiceRecording(recording, audioLanguage, requestId);
        };

        voiceRecorder.start();
        showVoiceStatus('Listening... Speak now, then tap the microphone to stop.');
    }).catch(function(error) {
        if (requestId !== voiceRecordingId) return;
        console.warn('Microphone access failed:', error);
        finishVoiceRecording();
        voiceState = 'idle';
        const message = error.name === 'NotAllowedError'
            ? 'Microphone access was denied. Allow microphone access in your browser settings.'
            : 'Could not access a microphone. Check its connection and browser permissions.';
        showVoiceStatus(message, 5000);
    });
}

function finishVoiceRecording() {
    if (voiceStream) {
        voiceStream.getTracks().forEach(track => track.stop());
        voiceStream = null;
    }
    voiceRecorder = null;
}

async function transcribeVoiceRecording(recording, language, requestId) {
    voiceState = 'transcribing';
    showVoiceStatus('Transcribing your recording...');
    const banner = document.getElementById('voice-status-banner');
    const apiBaseUrl = banner?.dataset.apiBaseUrl;
    const accessToken = banner?.dataset.accessToken;

    try {
        const response = await fetch(
            `${apiBaseUrl}/voice/transcribe?language=${encodeURIComponent(language)}`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': recording.type || 'audio/webm'
                },
                body: recording
            }
        );
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.detail || 'Voice transcription failed.');
        }
        if (requestId !== voiceRecordingId) return;
        if (!dharmaPopulatePrompt(result.transcript)) {
            throw new Error('Message field not found. Please try again.');
        }
        showVoiceStatus('Speech added to your message.', 2500);
    } catch (error) {
        console.error('Voice transcription failed:', error);
        if (requestId === voiceRecordingId) {
            showVoiceStatus(error.message || 'Voice transcription failed. Please try again.', 6000);
        }
    } finally {
        if (requestId === voiceRecordingId) voiceState = 'idle';
    }
}

function showVoiceStatus(message, duration = 0) {
    const banner = document.getElementById('voice-status-banner');
    if (!banner) return;
    clearTimeout(voiceStatusTimeout);
    voiceStatusTimeout = null;
    banner.textContent = message;
    banner.style.display = 'flex';
    if (duration) {
        voiceStatusTimeout = setTimeout(hideVoiceStatus, duration);
    }
}

function hideVoiceStatus() {
    const banner = document.getElementById('voice-status-banner');
    if (!banner) return;
    clearTimeout(voiceStatusTimeout);
    voiceStatusTimeout = null;
    banner.style.display = 'none';
}

if (!window.dharmaVoiceClickHandlerInstalled) {
    document.addEventListener('click', function(event) {
        const micButton = event.target.closest(
            '[data-testid="stElementContainer"][class*="st-key-btn_mic_"] button'
        );
        if (!micButton) return;

        event.preventDefault();
        event.stopImmediatePropagation();
        const language = document.getElementById('voice-status-banner')?.dataset.language || 'en';
        toggleDharmaVoice(language);
    }, true);
    window.dharmaVoiceClickHandlerInstalled = true;
}
})();
</script>
""", unsafe_allow_javascript=True)

# ============================================================
# LOGIN / SIGNUP VIEW (Preserved & Enhanced)
# ============================================================
start_ai_warmup()

wisdom = st.session_state.daily_wisdom
wisdom_text = wisdom["hindi"] if st.session_state.language == "hi" else wisdom["english"]
st.html(f"""
    <div style="background:rgba(229,184,105,0.12);border:1px solid rgba(229,184,105,0.3);border-radius:12px;padding:12px 18px;margin-bottom:10px;font-size:13.5px;color:#fdf0d5;">
        <strong style="color:#e5b869;">{escape(t("daily_wisdom"))}</strong><br>
        “{escape(wisdom_text)}” — <em>{escape(wisdom["reference"])}</em>
    </div>
""")

if not st.session_state.authenticated:
    render_col1, render_col2 = st.columns([1.1, 0.9], gap="large")

    with render_col1:
        st.html("""
            <div class="login-page">
                <div>
                    <div class="login-logo">🪷</div>
                    <div class="login-title">Dharma-AI</div>
                    <div class="login-subtitle">Ancient Wisdom × Modern Ethics × AI</div>
                    
                    <div class="login-hero-copy">
                        <h1>Guidance for<br><span>Better Decisions</span></h1>
                        <p class="login-hero-description">
                            Explore timeless wisdom from the Bhagavad Gita, Ramayana, Mahabharata and Western ethics, powered by AI. Find clarity, balance and the righteous path for your choices.
                        </p>
                        
                        <div class="login-features">
                            <div class="login-feature">
                                <span class="login-feature-icon">▣</span>
                                <div><strong>Ancient Wisdom</strong><small>Gita · Ramayana · Mahabharata</small></div>
                            </div>
                            <div class="login-feature">
                                <span class="login-feature-icon">⚖</span>
                                <div><strong>Modern Ethics</strong><small>Duty · Consequences · Virtue</small></div>
                            </div>
                            <div class="login-feature">
                                <span class="login-feature-icon">✦</span>
                                <div><strong>Dual Language</strong><small>English & हिन्दी with Voice</small></div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="login-quote">
                    “कर्मण्येवाधिकारस्ते मा फलेषु कदाचन” — You have a right to your duty, but not to the fruits thereof.<br>
                    <span style="font-size:11px;color:#a9b8cf;">— Bhagavad Gita 2.47</span>
                </div>
            </div>
        """)

    with render_col2:
        st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
        login_tab, signup_tab = st.tabs(["🔐 Login", "✨ Create Account"])

        login, signup, get_chat_history, save_chat, update_user_language, get_user_profile, _, _ = get_auth_functions()

        with login_tab:
            st.markdown("### Welcome Back")
            st.caption("Sign in to access your Dharma-AI conversations.")
            login_user = st.text_input("Username", key="login_username", placeholder="Enter your username")
            login_pass = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")

            if st.button("Login to Dharma-AI", key="btn_login", use_container_width=True):
                if not login_user.strip() or not login_pass.strip():
                    st.warning("Please provide both username and password.")
                else:
                    st.session_state.backend_available = ensure_backend()
                    if st.session_state.backend_available:
                        success, msg, token, user_data = login(login_user.strip(), login_pass.strip())
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.user = login_user.strip()
                            st.session_state.access_token = token
                            if user_data and user_data.get("language_preference"):
                                st.session_state.language = user_data.get("language_preference")
                            st.session_state.last_auth_error = ""
                            
                            # Load previous chat history
                            h_ok, chats = get_chat_history(token)
                            if h_ok and isinstance(chats, list):
                                st.session_state.recent_chats = chats
                                st.session_state.chat_history_load_error = ""
                            else:
                                st.session_state.chat_history_load_error = str(chats)
                            st.session_state.chat_history_loaded = True
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("Backend API is currently unavailable. Please start the backend.")

        with signup_tab:
            st.markdown("### Create New Account")
            st.caption("Begin your journey of ethical clarity.")
            signup_user = st.text_input("Choose Username", key="signup_username", placeholder="3 to 50 characters")
            signup_pass = st.text_input("Choose Password", type="password", key="signup_password", placeholder="At least 8 characters")
            signup_lang = st.selectbox("Preferred Language", options=["en", "hi"], format_func=lambda x: "🇬🇧 English" if x == "en" else "🇮🇳 हिन्दी", key="signup_lang")

            if st.button("Create Account", key="btn_signup", use_container_width=True):
                if not signup_user.strip() or not signup_pass.strip():
                    st.warning("Please provide a username and password.")
                else:
                    st.session_state.backend_available = ensure_backend()
                    if st.session_state.backend_available:
                        success, msg, token, user_data = signup(signup_user.strip(), signup_pass.strip(), signup_lang)
                        if success:
                            st.success("Account created successfully! You can now log in.")
                        else:
                            st.error(msg)
                    else:
                        st.error("Backend API is currently unavailable.")

# ============================================================
# MAIN AUTHENTICATED CHAT VIEW
# ============================================================
else:
    login, signup, get_chat_history, save_chat, update_user_language, get_user_profile, delete_chat, clear_chat_history = get_auth_functions()

    # Load history once per login; an empty history is still a successful load.
    if not st.session_state.chat_history_loaded and st.session_state.access_token:
        try:
            h_ok, chats = get_chat_history(st.session_state.access_token)
            if h_ok and isinstance(chats, list):
                st.session_state.recent_chats = chats
                st.session_state.chat_history_load_error = ""
            else:
                st.session_state.chat_history_load_error = str(chats)
        except Exception:
            st.session_state.chat_history_load_error = (
                "Chat history could not be loaded. Check backend connectivity."
            )
            logging.exception("Could not load chat history")
        finally:
            st.session_state.chat_history_loaded = True

    # ========================================================
    # SIDEBAR
    # ========================================================
    with st.sidebar:
        username = escape(str(st.session_state.user or "User"))
        user_initials = escape(username[:2].upper())

        st.html(f"""
            <div class="sidebar-brand">
                <div class="sidebar-logo">🪷</div>
                <div>
                    <div class="sidebar-title">Dharma-AI</div>
                    <div class="sidebar-tagline">{t('app_tagline')}</div>
                </div>
            </div>
            <div class="sidebar-user-card">
                <div class="sidebar-avatar">{user_initials}</div>
                <div style="flex:1;">
                    <div style="font-weight:600;font-size:13.5px;color:#ffffff;">{username}</div>
                    <div style="font-size:10.5px;color:#a9b9d4;">{t('language_label')}</div>
                </div>
            </div>
        """)

        # Language Switcher in Sidebar
        lang_col1, lang_col2 = st.columns(2)
        with lang_col1:
            if st.button("🇬🇧 English", key="btn_lang_en", use_container_width=True, type="primary" if st.session_state.language == "en" else "secondary"):
                if st.session_state.language != "en":
                    st.session_state.language = "en"
                    if st.session_state.access_token:
                        update_user_language(st.session_state.access_token, "en")
                    st.rerun()
        with lang_col2:
            if st.button("🇮🇳 हिन्दी", key="btn_lang_hi", use_container_width=True, type="primary" if st.session_state.language == "hi" else "secondary"):
                if st.session_state.language != "hi":
                    st.session_state.language = "hi"
                    if st.session_state.access_token:
                        update_user_language(st.session_state.access_token, "hi")
                    st.rerun()

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # New Chat Button
        if st.button(t("new_chat"), key="sidebar_new_chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.current_chat_id = None
            st.session_state.chat_input_version += 1
            st.rerun()

        # Chat History Toggle
        if st.button(t("chat_history"), key="sidebar_toggle_history", use_container_width=True):
            st.session_state.show_history = not st.session_state.show_history
            st.rerun()

        if st.session_state.chat_history_load_error:
            st.warning(st.session_state.chat_history_load_error)
            if st.button(t("retry_history"), key="retry_chat_history", use_container_width=True):
                st.session_state.chat_history_loaded = False
                st.session_state.chat_history_load_error = ""
                st.rerun()

        # Render Chat History if open
        if st.session_state.show_history:
            st.html(f'<div class="sidebar-section-title">{t("recent_conversations")}</div>')
            chats = st.session_state.recent_chats or []
            if not chats:
                st.caption(t("no_conversations"))
            else:
                for chat in chats[:10]:
                    chat_id = chat.get("id")
                    title = escape(str(chat.get("title") or "Conversation"))
                    if len(title) > 30:
                        title = title[:28] + "…"
                    
                    hist_col, del_col = st.columns([8.2, 1.8])
                    with hist_col:
                        if st.button(f"▸ {title}", key=f"hist_chat_{chat_id}", use_container_width=True):
                            st.session_state.messages = list(chat.get("messages", []))
                            st.session_state.current_chat_id = chat_id
                            st.session_state.show_history = False
                            st.session_state.chat_input_version += 1
                            st.rerun()
                    with del_col:
                        if st.button("✕", key=f"del_chat_{chat_id}", help="Delete this chat"):
                            delete_chat(st.session_state.access_token, chat_id)
                            st.session_state.recent_chats = [c for c in st.session_state.recent_chats if c.get("id") != chat_id]
                            if st.session_state.current_chat_id == chat_id:
                                st.session_state.messages = []
                                st.session_state.current_chat_id = None
                            st.rerun()

                if st.button(t("clear_all"), key="btn_clear_all_history", use_container_width=True):
                    clear_chat_history(st.session_state.access_token)
                    st.session_state.recent_chats = []
                    st.session_state.chat_history_loaded = True
                    st.session_state.chat_history_load_error = ""
                    st.session_state.messages = []
                    st.session_state.current_chat_id = None
                    st.rerun()

        st.html(f'<div class="sidebar-section-title">{t("modes_title")}</div>')
        modes = [
            ("🍃", "Calm", t("calm_desc")),
            ("🧠", "Logical", t("logical_desc")),
            ("⚖️", "Ethical", t("ethical_desc")),
            ("🔥", "Motivational", t("motivational_desc")),
            ("🎯", "Direct", t("direct_desc")),
        ]

        for icon, mode_key, mode_desc in modes:
            is_active = st.session_state.mode == mode_key
            label = f"{icon}  {mode_key} {'●' if is_active else ''}"
            if st.button(label, key=f"btn_mode_{mode_key}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.mode = mode_key
                st.rerun()
            st.html(f'<div style="padding:0 24px 6px;color:#8ba2c4;font-size:10.5px;">{escape(mode_desc)}</div>')

        # Daily Wisdom
        if st.button(t("daily_wisdom"), key="btn_daily_wisdom", use_container_width=True):
            st.session_state.daily_wisdom = get_daily_wisdom(st.session_state.daily_wisdom)
            st.rerun()

        # Clear active conversation
        if st.session_state.messages:
            if st.button(t("clear_chat"), key="btn_clear_current_chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.current_chat_id = None
                st.session_state.chat_input_version += 1
                st.rerun()

        # Logout
        if st.button(t("logout"), key="btn_logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = ""
            st.session_state.access_token = None
            st.session_state.messages = []
            st.session_state.current_chat_id = None
            st.session_state.recent_chats = []
            st.session_state.chat_history_loaded = False
            st.session_state.chat_history_load_error = ""
            st.rerun()

        st.html("""
            <div style="text-align:center;padding:16px 8px;color:#7c8da8;font-family:'Playfair Display',serif;font-size:12px;">
                <div style="font-size:24px;margin-bottom:4px;">🪷</div>
                “Dharma protects those who protect Dharma.”<br>
                <span style="font-size:10px;">— धर्मो रक्षति रक्षितः</span>
            </div>
        """)

    # ========================================================
    # MAIN AREA: HEADER
    # ========================================================
    active_mode = st.session_state.mode
    curr_lang = st.session_state.language
    lang_name = "English" if curr_lang == "en" else "हिन्दी"

    hdr_col_left, hdr_col_right = st.columns([8.2, 1.8])
    with hdr_col_left:
        st.html(f"""
            <div class="dharma-header">
                <div class="dharma-header-brand">
                    <div class="dharma-header-logo">🪷</div>
                    <div class="dharma-header-text">
                        <h2>{t('app_title')}</h2>
                        <p>{t('app_tagline')}</p>
                    </div>
                </div>
                <div class="dharma-header-pills">
                    <span class="mode-badge">{active_mode}</span>
                    <span class="lang-badge">{lang_name}</span>
                    <span class="status-pill"><span class="status-dot"></span> {t('online')}</span>
                </div>
            </div>
        """)
    with hdr_col_right:
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        if st.button("🇮🇳 हिन्दी" if curr_lang == "en" else "🇬🇧 English", key="btn_hdr_quick_lang", use_container_width=True, help=t("switch_lang")):
            new_l = "hi" if curr_lang == "en" else "en"
            st.session_state.language = new_l
            if st.session_state.access_token:
                update_user_language(st.session_state.access_token, new_l)
            st.rerun()

    # ========================================================
    # MAIN AREA: CONVERSATION CONTAINER (ONLY SCROLLS HERE)
    # ========================================================
    message_elements = []

    if not st.session_state.messages:
        with st.container():
            # Beautiful Empty State Header
            st.html(f"""
                <div class="empty-hero">
                    <div class="empty-lotus">🪷</div>
                    <h1>{t('empty_title')}</h1>
                    <p>{t('empty_desc')}</p>
                    <div style="font-size:12px;font-weight:600;color:#9eb3d2;letter-spacing:0.5px;margin-bottom:10px;">{t('empty_prompt_label')}</div>
                </div>
            """)
            suggestions = t("suggestions")
            sug_col1, sug_col2 = st.columns(2)
            with sug_col1:
                if st.button(f"💭 {suggestions[0]}", key="sug_btn_0", use_container_width=True):
                    st.session_state.pending_submission = suggestions[0]
                    st.rerun()
                if st.button(f"💭 {suggestions[1]}", key="sug_btn_1", use_container_width=True):
                    st.session_state.pending_submission = suggestions[1]
                    st.rerun()
            with sug_col2:
                if st.button(f"💭 {suggestions[2]}", key="sug_btn_2", use_container_width=True):
                    st.session_state.pending_submission = suggestions[2]
                    st.rerun()
                if st.button(f"💭 {suggestions[3]}", key="sug_btn_3", use_container_width=True):
                    st.session_state.pending_submission = suggestions[3]
                    st.rerun()
    else:
        for idx, msg in enumerate(st.session_state.messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                message_elements.append(f"""
                    <div class="msg-row-user">
                        <div class="msg-bubble-user">
                            {escape(content).replace(chr(10), '<br>')}
                        </div>
                    </div>
                """)
            else:
                formatted_html = format_ai_content(content)
                mode_str = escape(msg.get("mode", st.session_state.mode))
                message_text = escape(content, quote=True)
                # Check if translated version exists in session state
                translation_html = ""
                if idx in st.session_state.translations:
                    trans_text = format_ai_content(st.session_state.translations[idx])
                    translation_html = f"""
                        <div class="translation-box">
                            <strong>🌐 Translation ({'हिन्दी' if curr_lang == 'en' else 'English'}):</strong><br>
                            {trans_text}
                        </div>
                    """

                message_elements.append(f"""
                    <div class="msg-row-ai">
                        <div class="msg-avatar-ai">🪷</div>
                        <div class="msg-card-ai" data-message-text="{message_text}" data-language="{escape(curr_lang, quote=True)}">
                            <div class="msg-card-ai-head">
                                <span class="msg-card-ai-title">
                                    Dharma-AI
                                    <span class="mode-badge" style="font-size:9.5px;padding:2px 7px;">{mode_str}</span>
                                </span>
                            </div>
                            <div class="msg-card-ai-content">
                                {formatted_html}
                            </div>
                            {translation_html}
                            <div class="msg-actions-bar">
                                <button type="button" class="action-chip" data-chat-action="listen-hi">{t('listen_hi')}</button>
                                <button type="button" class="action-chip" data-chat-action="listen-en">{t('listen_en')}</button>
                                <button type="button" class="action-chip" data-chat-action="pause">{t('pause')}</button>
                                <button type="button" class="action-chip" data-chat-action="resume">{t('resume')}</button>
                                <button type="button" class="action-chip" data-chat-action="stop">{t('stop')}</button>
                                <button type="button" class="action-chip" data-chat-action="copy">{t('copy')}</button>
                                {f'<button type="button" class="action-chip" data-chat-action="translate">{t("translate_to")}</button>' if idx == len(st.session_state.messages) - 1 and msg.get("role") == "assistant" else ''}
                                {f'<button type="button" class="action-chip" data-chat-action="regenerate">{t("regenerate")}</button>' if idx == len(st.session_state.messages) - 1 and msg.get("role") == "assistant" else ''}
                            </div>
                        </div>
                    </div>
                """)

        conversation_html = f"""
            <div id="dharma-chat-scroll">
                {''.join(message_elements)}
            </div>
            <script>
                (function() {{
                    function scrollToBottom() {{
                        const el = document.getElementById('dharma-chat-scroll');
                        if (el) {{
                            el.scrollTop = el.scrollHeight;
                        }}
                    }}
                    scrollToBottom();
                    requestAnimationFrame(scrollToBottom);
                    setTimeout(scrollToBottom, 60);
                    setTimeout(scrollToBottom, 200);
                    setTimeout(scrollToBottom, 500);
                }})();
            </script>
        """
        st.html(conversation_html)

        # Keep native Streamlit actions as hidden handlers for the message action chips.
        if st.session_state.messages and st.session_state.messages[-1].get("role") == "assistant":
            last_idx = len(st.session_state.messages) - 1
            last_content = st.session_state.messages[-1].get("content", "")
            target_lang = "hi" if curr_lang == "en" else "en"

            with st.container(key="message-actions-handler"):
                translate_clicked = st.button(t("translate_to"), key=f"btn_translate_{last_idx}", use_container_width=True)
                regenerate_clicked = st.button(t("regenerate"), key=f"btn_regen_{last_idx}", use_container_width=True)

            if translate_clicked:
                with st.spinner("Translating..."):
                    try:
                        trans_fn = get_translation_function()
                        translated = trans_fn(last_content, target_language=target_lang)
                        if not translated.strip() or translated.strip() == last_content.strip():
                            raise RuntimeError("The translation service returned the original text.")
                        st.session_state.translations[last_idx] = translated
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Translation failed: {exc}")

            if regenerate_clicked:
                last_user_query = None
                for m in reversed(st.session_state.messages[:-1]):
                    if m.get("role") == "user":
                        last_user_query = m.get("content")
                        break
                if last_user_query:
                    st.session_state.messages.pop()
                    st.session_state.pending_submission = last_user_query
                    st.session_state.regenerating_response = True
                    st.rerun()


    # Empty placeholder for streaming response if generating
    response_placeholder = st.empty()

    # ========================================================
    # MAIN AREA: FIXED BOTTOM COMPOSER
    # ========================================================
    st.html(f"""
        <div id="voice-status-banner" class="voice-banner"
             data-language="{escape(st.session_state.language)}"
             data-api-base-url="{escape(API_BASE_URL)}"
             data-access-token="{escape(st.session_state.access_token or '')}"
             role="status" aria-live="polite" style="display:none;"></div>
    """)

    with st.container(key="dharma-composer-shell"):
        comp_mic_col, comp_form_col = st.columns([0.8, 9.2], gap="small")

        with comp_mic_col:
            st.button("🎙", key=f"btn_mic_{st.session_state.chat_input_version}", help=t("mic_title"), use_container_width=True)

        with comp_form_col:
            with st.form(key=f"chat_composer_form_{st.session_state.chat_input_version}", clear_on_submit=False, border=False):
                form_in_col, form_btn_col = st.columns([8.8, 1.2], gap="small")
                with form_in_col:
                    initial_val = st.session_state.staged_prompt if st.session_state.staged_prompt else ""
                    user_text = st.text_input(
                        "Message",
                        value=initial_val,
                        placeholder=t("composer_placeholder"),
                        key=f"user_msg_input_{st.session_state.chat_input_version}",
                        label_visibility="collapsed",
                    )
                    if st.session_state.staged_prompt:
                        st.session_state.staged_prompt = ""

                with form_btn_col:
                    send_clicked = st.form_submit_button("➤", help=t("send_title"), use_container_width=True)

        st.html(f"<div class='composer-hint-text'>{t('composer_hint')}</div>")


    active_submission = None
    regenerating_response = False
    if send_clicked:
        if not user_text.strip():
            st.toast(t("type_first"), icon="💬")
            st.stop()
        active_submission = user_text.strip()
    elif st.session_state.get("pending_submission"):
        active_submission = st.session_state.pop("pending_submission", "").strip()
        regenerating_response = st.session_state.pop("regenerating_response", False)

    if active_submission:
        cleaned_msg = active_submission

        # Prevent duplicate submissions
        if (
            not regenerating_response
            and st.session_state.messages
            and st.session_state.messages[-1].get("role") == "user"
            and st.session_state.messages[-1].get("content") == cleaned_msg
        ):
            st.stop()

        # Conversational memory window (last 8 messages)
        conversation_history = list(st.session_state.messages)
        if regenerating_response and conversation_history and conversation_history[-1].get("role") == "user":
            conversation_history.pop()
        else:
            st.session_state.messages.append({"role": "user", "content": cleaned_msg})

        streamed_chunks = []
        last_stream_render = [0.0]
        stream_render_seconds = [0.0]
        first_stream_render_ms = [None]
        stream_started_at = time.perf_counter()
        user_message_html = (
            '<div class="msg-row-user"><div class="msg-bubble-user">'
            f'{escape(cleaned_msg).replace(chr(10), "<br>")}'
            '</div></div>'
        )

        response_placeholder.markdown(
            f"""
            {user_message_html}
            <div class="msg-row-ai">
                <div class="msg-avatar-ai">🪷</div>
                <div class="msg-card-ai">
                    <div class="msg-card-ai-head">
                        <span class="msg-card-ai-title">Dharma-AI</span>
                    </div>
                    <div class="msg-card-ai-content">{escape(t("generating_response"))}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        def on_stream_token(chunk):
            streamed_chunks.append(chunk)
            now = time.monotonic()
            if len(streamed_chunks) > 1 and now - last_stream_render[0] < 0.12:
                return
            last_stream_render[0] = now
            formatted = format_ai_content("".join(streamed_chunks))
            render_started = time.perf_counter()
            response_placeholder.markdown(
                f"""
                {user_message_html}
                <div class="msg-row-ai">
                    <div class="msg-avatar-ai">🪷</div>
                    <div class="msg-card-ai">
                        <div class="msg-card-ai-head">
                            <span class="msg-card-ai-title">Dharma-AI <span class="mode-badge" style="font-size:9.5px;">{escape(t("generating_response"))}</span></span>
                        </div>
                        <div class="msg-card-ai-content">{formatted}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_finished = time.perf_counter()
            stream_render_seconds[0] += render_finished - render_started
            if first_stream_render_ms[0] is None:
                first_stream_render_ms[0] = round(
                    (render_finished - stream_started_at) * 1000
                )

        with st.spinner(t("generating_response")):
            try:
                if not st.session_state.ai_warmup_complete.is_set():
                    st.info(t("starting_ai"))
                if not st.session_state.ai_warmup_complete.wait(timeout=300):
                    raise TimeoutError("AI startup did not finish within 300 seconds.")
                final_render_started = time.perf_counter()
                response_placeholder.markdown(
                    f"""
                    {user_message_html}
                    <div class="msg-row-ai">
                        <div class="msg-avatar-ai">🪷</div>
                        <div class="msg-card-ai">
                            <div class="msg-card-ai-head">
                                <span class="msg-card-ai-title">Dharma-AI</span>
                            </div>
                            <div class="msg-card-ai-content">{escape(t("generating_response"))}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                stream_render_seconds[0] += time.perf_counter() - final_render_started
                logging.info(
                    "Dharma-AI frontend timing stage=stream_render first_render_ms=%s render_submit_ms=%d input_chars=%d",
                    first_stream_render_ms[0] if first_stream_render_ms[0] is not None else "unavailable",
                    round(stream_render_seconds[0] * 1000),
                    len(cleaned_msg),
                )
                generate_fn = get_response_function()
                ai_reply = generate_fn(
                    cleaned_msg,
                    mode=st.session_state.mode,
                    conversation_history=conversation_history,
                    language=st.session_state.language,
                    on_token=on_stream_token,
                )
            except Exception:
                logging.exception("Chat response generation failed")
                ai_reply = t("ai_error")

        response_placeholder.markdown(
            f"""
            {user_message_html}
            <div class="msg-row-ai">
                <div class="msg-avatar-ai">🪷</div>
                <div class="msg-card-ai">
                    <div class="msg-card-ai-head">
                        <span class="msg-card-ai-title">Dharma-AI</span>
                    </div>
                    <div class="msg-card-ai-content">{format_ai_content(ai_reply)}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.session_state.messages.append({
            "role": "assistant",
            "content": ai_reply,
            "mode": st.session_state.mode,
        })

        # Save to database
        if st.session_state.access_token:
            try:
                _, _, _, save_chat, _, _, _, _ = get_auth_functions()
                ok, save_message, saved_session_id, saved_title = save_chat(
                    st.session_state.access_token,
                    cleaned_msg,
                    ai_reply,
                    st.session_state.mode,
                    st.session_state.current_chat_id,
                    replace_last_response=regenerating_response,
                )
                if ok and saved_session_id is not None:
                    st.session_state.current_chat_id = saved_session_id
                    saved_chat = {
                        "id": saved_session_id,
                        "title": saved_title or "Conversation",
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "messages": list(st.session_state.messages),
                    }
                    st.session_state.recent_chats = [
                        saved_chat,
                        *(
                            chat
                            for chat in st.session_state.recent_chats
                            if chat.get("id") != saved_session_id
                        ),
                    ]
                elif not ok:
                    logging.warning("Chat history save failed: %s", save_message)
                    st.warning(save_message or t("chat_save_warning"))
            except Exception:
                logging.exception("The generated response could not be saved to chat history")
                st.warning(t("chat_save_warning"))

        st.session_state.chat_input_version += 1
        st.rerun()

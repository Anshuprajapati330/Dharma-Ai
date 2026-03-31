import streamlit as st
from dharma_ai import generate_response
from datetime import datetime

# Page Config
st.set_page_config(
    page_title="Dharma-AI Chatbot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better chat interface
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1a1f35 100%);
        color: white;
    }
    
    .title {
        font-size: 42px;
        font-weight: bold;
        text-align: center;
        color: #5a9fc7;
        margin-bottom: 10px;
    }
    
    .subtitle {
        text-align: center;
        font-size: 16px;
        color: #cbd5e1;
        margin-bottom: 30px;
    }
    
    .chat-container {
        background-color: #1e293b;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0px 0px 20px rgba(0,0,0,0.5);
    }
    
    .message-container {
        display: flex;
        margin-bottom: 15px;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message {
        background-color: #5a9fc7;
        padding: 12px 16px;
        border-radius: 12px;
        max-width: 70%;
        margin-left: auto;
        margin-right: 0;
        word-wrap: break-word;
    }
    
    .bot-message {
        background-color: #334155;
        padding: 12px 16px;
        border-radius: 12px;
        max-width: 70%;
        margin-right: auto;
        margin-left: 0;
        word-wrap: break-word;
    }
    
    .mode-badge {
        display: inline-block;
        background-color: #475569;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        color: #e2e8f0;
        margin-top: 5px;
    }
    
    .sidebar-box {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        box-shadow: 0px 0px 15px rgba(0,0,0,0.4);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for chat history and mode
if "messages" not in st.session_state:
    st.session_state.messages = []

if "mode" not in st.session_state:
    st.session_state.mode = "Calm 🧘"

if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = False

# Sidebar Configuration
with st.sidebar:
    st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
    st.markdown("### ⚙️ Configuration")
    
    st.session_state.mode = st.selectbox(
        "Select Guidance Mode:",
        [
            "Calm 🧘",
            "Logical 🧠",
            "Ethical ⚖️",
            "Motivational 🚀",
            "Direct 🎯"
        ],
        index=0
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Tips Section
    st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
    st.markdown("### 💡 Tips")
    st.markdown("""
    • Ask clear, specific questions
    • Choose the mode that fits your need
    • Explore different perspectives
    • Be open to the guidance
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Chat History Controls
    st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
    st.markdown("### 🗂️ Chat History")
    if st.button("🔄 Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_started = False
        st.rerun()
    
    if len(st.session_state.messages) > 0:
        st.markdown(f"**Messages:** {len(st.session_state.messages)}")
    st.markdown("</div>", unsafe_allow_html=True)

# Main Chat Area
st.markdown('<div class="title">🧠 Dharma-AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ethical • Intelligent • Context-Aware Guidance</div>', unsafe_allow_html=True)

st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Display chat history
if st.session_state.messages:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
                <div class="message-container">
                    <div class="user-message">
                        <strong>You:</strong> {message['content']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="message-container">
                    <div class="bot-message">
                        <strong>Dharma-AI:</strong><br>{message['content']}<br>
                        <span class="mode-badge">{message['mode']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div style='text-align: center; color: #cbd5e1; padding: 40px;'>
            <h3>👋 Welcome to Dharma-AI Chatbot</h3>
            <p>Ask me anything and receive ethical, intelligent guidance.</p>
            <p>Start by typing your question below...</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Chat Input Area
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

col1, col2 = st.columns([4, 1])

with col1:
    user_input = st.text_input(
        "💬 Type your question here...",
        placeholder="Ask me anything...",
        label_visibility="collapsed"
    )

with col2:
    send_button = st.button("Send ➤", use_container_width=True)

if send_button and user_input:
    st.session_state.conversation_started = True
    
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Get clean mode
    clean_mode = st.session_state.mode.split()[0]
    
    # Generate response
    with st.spinner("🧠 Dharma-AI is thinking deeply..."):
        try:
            response = generate_response(user_input, clean_mode)
            
            # Add bot response to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "mode": st.session_state.mode
            })
            
            st.rerun()
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<center>🙏 Built with ❤️ using Dharma-AI | Ethical Guidance, Powered by Wisdom</center>", unsafe_allow_html=True)

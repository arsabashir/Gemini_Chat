"""
Google Gemini-Pro Chat Application
A Streamlit web app for conversational chat with Google's Gemini-Pro model.
"""

import os
import streamlit as st
import google.generativeai as genai

# --------------------------------------------------------------------------
# Page configuration
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Gemini Chat",
    page_icon="✨",
    layout="centered",
)

# --------------------------------------------------------------------------
# Custom styling
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        /* Hide default Streamlit chrome for a cleaner look */
        #MainMenu, footer { visibility: hidden; }

        /* Page background */
        .stApp {
            background: linear-gradient(180deg, #fafbff 0%, #f5f3ff 100%);
        }

        /* Header */
        .app-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.5rem 0 0.25rem 0;
        }
        .app-header .icon {
            font-size: 2.2rem;
            filter: drop-shadow(0 2px 6px rgba(124, 92, 255, 0.35));
        }
        .app-header h1 {
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
            background: linear-gradient(90deg, #6D5BFF 0%, #A855F7 60%, #EC4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .app-subtitle {
            color: #6b7280;
            font-size: 0.95rem;
            margin: 0 0 1.25rem 0.05rem;
        }

        /* Chat bubbles */
        [data-testid="stChatMessage"] {
            border-radius: 16px;
            padding: 0.9rem 1.1rem;
            margin-bottom: 0.6rem;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
            border: 1px solid rgba(15, 23, 42, 0.05);
        }

        /* Chat input */
        [data-testid="stChatInput"] textarea {
            border-radius: 14px !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid rgba(15, 23, 42, 0.06);
        }
        [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            font-weight: 700;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 10px;
            font-weight: 500;
        }
    </style>
    <div class="app-header">
        <span class="icon">✨</span>
        <h1>Gemini Chat</h1>
    </div>
    <div class="app-subtitle">Conversational AI powered by Google Gemini &amp; Streamlit</div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# API key handling
# --------------------------------------------------------------------------
# Priority: Streamlit secrets -> environment variable -> sidebar input
try:
    default_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    default_key = ""
default_key = default_key or os.environ.get("GOOGLE_API_KEY", "")

with st.sidebar:
    st.markdown("### ⚙️ Settings")

    api_key = st.text_input(
    "Google API Key",
    value=default_key,
    type="password",
    help="Get a key from https://aistudio.google.com/app/apikey",
)
    

    st.markdown("&nbsp;", unsafe_allow_html=True)
    st.markdown("**Model**")
    model_name = st.selectbox(
        "Model",
        options=["gemini-3-flash-preview", "gemini-3.1-flash-lite", "gemini-3.1-pro-preview"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("**Temperature**")
    temperature = st.slider(
        "Temperature", 0.0, 1.0, 0.7, 0.05, label_visibility="collapsed"
    )
    st.caption("Lower = more focused. Higher = more creative.")

    st.divider()

    msg_count = len(st.session_state.get("messages", []))
    st.caption(f"💬 {msg_count} message{'s' if msg_count != 1 else ''} in this chat")

    if st.button("🗑️  Clear chat history", use_container_width=True):
        st.session_state.pop("chat_session", None)
        st.session_state.pop("messages", None)
        st.rerun()

if not api_key:
    st.info("👈 Enter your Google API key in the sidebar to start chatting.")
    st.stop()

# --------------------------------------------------------------------------
# Configure the Gemini client
# --------------------------------------------------------------------------
try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Failed to configure Gemini client: {e}")
    st.stop()

# --------------------------------------------------------------------------
# Session state: message history + chat session object
# --------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {"role": "user"/"model", "content": str}

if "chat_session" not in st.session_state or st.session_state.get("model_name") != model_name:
    try:
        model = genai.GenerativeModel(model_name)
        # Rebuild history for the SDK's chat object from what's stored so far
        history = [
            {"role": m["role"], "parts": [m["content"]]}
            for m in st.session_state.messages
        ]
        st.session_state.chat_session = model.start_chat(history=history)
        st.session_state.model_name = model_name
    except Exception as e:
        st.error(f"Failed to initialize model '{model_name}': {e}")
        st.stop()

# --------------------------------------------------------------------------
# Render existing chat history
# --------------------------------------------------------------------------
USER_AVATAR = "🧑"
BOT_AVATAR = "✨"

if not st.session_state.messages:
    st.markdown(
        """
        <div style="text-align:center; padding: 2.5rem 1rem; color:#9ca3af;">
            <div style="font-size:2.2rem; margin-bottom:0.4rem;">💬</div>
            <div>Start the conversation below — ask anything.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

for msg in st.session_state.messages:
    role = "user" if msg["role"] == "user" else "assistant"
    avatar = USER_AVATAR if role == "user" else BOT_AVATAR
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])

# --------------------------------------------------------------------------
# Chat input + response generation
# --------------------------------------------------------------------------
prompt = st.chat_input("Ask Gemini-Pro anything...")

if prompt:
    # Show and store the user's message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    # Stream the model's response
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        placeholder = st.empty()
        full_response = ""
        try:
            response = st.session_state.chat_session.send_message(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                ),
                stream=True,
            )
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
        except Exception as e:
            full_response = f"⚠️ Error generating response: {e}"
            placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "model", "content": full_response})
# streamlit_app.py
import os
import sys
from datetime import datetime
import streamlit as st
from openai import OpenAI
from typing import List, Dict, Any

# ---------- Config ----------
APP_TITLE = "Project STARGATE: AI Psychic Fortune Teller"
YOUTUBE_URL = "https://www.youtube.com/watch?v=rZsMSyfEiY0"
DEFAULT_MODEL = "gpt-5-mini"    # Fallbacks available in the selector below
FALLBACK_MODEL = "gpt-4o-mini"

# ---------- Auth ----------
# Prefer Streamlit Secrets, fallback to env var
api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
if not api_key:
    st.error("No OpenAI API key found. Set it in st.secrets['OPENAI_API_KEY'] or the OPENAI_API_KEY env var.")
    st.stop()

client = OpenAI(api_key=api_key)

# ---------- Prompting ----------
def john_system_prompt() -> str:
    return (
        "You are John — an underemployed philosophy grad who’s been mistaken for a deceased psychic prodigy and "
        "accidentally hired by the DIA. You navigate absurd psychic-espionage bureaucracy with improvisational wit "
        "and practical philosophy.\n\n"
        "Voice & Style:\n"
        "• Wry, quick one-liners; never snarky at the user.\n"
        "• Ground advice in clear reasoning (John can cite philosophers casually, e.g., Stoics, Kant, Kierkegaard) "
        "  when helpful, but keep it punchy.\n"
        "• If you don’t know, say so and propose a next step.\n"
        "• Be helpful first, funny second. Humor should never obscure instructions.\n\n"
        "Constraints:\n"
        "• Keep answers concise unless the user requests depth.\n"
        "• No classified info gags that imply real-world access; keep it fictional and playful.\n"
        "• If the user asks for something unsafe or illegal, refuse politely and redirect to a safer alternative.\n"
    )

def build_conversation(history: List[Dict[str, str]], user_input: str) -> List[Dict[str, Any]]:
    """
    Convert our chat history + new user message into Responses API 'input' format.
    """
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": [{"type": "text", "text": john_system_prompt()}]}
    ]
    for turn in history:
        messages.append({"role": turn["role"], "content": [{"type": "text", "text": turn["content"]}]})
    messages.append({"role": "user", "content": [{"type": "text", "text": user_input}]})
    return messages

def generate_john_response(
    user_input: str,
    history: List[Dict[str, str]],
    model: str,
    temperature: float,
    seed: int | None,
) -> str:
    messages = build_conversation(history, user_input)

    # Note: Responses API returns .output_text in the Python SDK.
    resp = client.responses.create(
        model=model,
        input=messages,
        temperature=temperature,
        **({"seed": seed} if seed is not None else {}),
    )
    return resp.output_text.strip()

# ---------- UI ----------
st.set_page_config(page_title=APP_TITLE, page_icon="🔮", layout="centered")
st.title(APP_TITLE)
st.caption("“John” is on the clock. The DIA just doesn’t know it.")

st.video(YOUTUBE_URL)

with st.expander("Model & generation settings", expanded=False):
    model = st.selectbox(
        "Model",
        options=[DEFAULT_MODEL, FALLBACK_MODEL, "o3-mini"],
        help="Use a fast, inexpensive model by default. If a model isn’t enabled on your key, try another.",
    )
    temperature = st.slider("Creativity (temperature)", 0.0, 1.2, 0.6, 0.05)
    use_seed = st.checkbox("Reproducible output (seed)", value=False)
    seed = st.number_input("Seed (integer)", value=7, step=1) if use_seed else None

# Simple in-session memory
if "chat" not in st.session_state:
    st.session_state.chat: List[Dict[str, str]] = []

# Show history
for turn in st.session_state.chat:
    with st.chat_message("user" if turn["role"] == "user" else "assistant"):
        st.markdown(turn["content"])

# Input
user_input = st.chat_input("Ask John for help… (career, love, cosmic bureaucracy)")

# Controls
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("Reset conversation", use_container_width=True):
        st.session_state.chat = []
        st.rerun()
with col2:
    if st.button("Insert icebreaker", use_container_width=True):
        icebreaker = "John, I’ve got a problem only a semi-psychic philosopher can solve…"
        st.session_state.chat.append({"role": "user", "content": icebreaker})
        st.rerun()

# Handle new message
if user_input:
    st.session_state.chat.append({"role": "user", "content": user_input})
    try:
        reply = generate_john_response(
            user_input=user_input,
            history=st.session_state.chat[:-1],  # previous turns only
            model=model,
            temperature=temperature,
            seed=int(seed) if seed is not None else None,
        )
        st.session_state.chat.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)
    except Exception as e:
        # Friendly diagnostics for common issues
        msg = str(e)
        if "401" in msg or "invalid_api_key" in msg.lower():
            st.error("Auth failed. Double-check your API key and that the selected model is enabled for your account.")
        elif "rate" in msg.lower():
            st.warning("Rate limit hit. Try again in a moment or switch to a lighter model.")
        else:
            st.error(f"Something went sideways: {msg}")
        # Keep the last user message in history, but don’t add a failed assistant turn.

# Footer
st.markdown(
    "<hr/>"
    "<small>Tip: For punchier jokes, raise temperature; for tactical clarity, lower it. "
    "John will keep it witty, not wordy.</small>",
    unsafe_allow_html=True,
)

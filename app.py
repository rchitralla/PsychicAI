# app.py
# -----------------------------
# Requirements:
#   pip install streamlit openai
# Running:
#   streamlit run app.py
# API key:
#   Put OPENAI_API_KEY in Streamlit secrets or environment variables.
# -----------------------------

import os
import time
import random
from typing import List, Dict, Optional

import streamlit as st
from openai import OpenAI

# ---------- App Config ----------
APP_TITLE = "Project STARGATE: AI Psychic Fortune Teller"
YOUTUBE_URL = "https://www.youtube.com/watch?v=rZsMSyfEiY0"

# Order = fallback priority (left to right)
PREFERRED_MODELS_DEFAULT = ["gpt-4o-mini", "gpt-5-mini", "o3-mini"]

# ---------- Auth ----------
api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
if not api_key:
    st.error("No OpenAI API key found. Add it to st.secrets['OPENAI_API_KEY'] or set the OPENAI_API_KEY env var.")
    st.stop()

client = OpenAI(api_key=api_key)

# ---------- Helpers: Rate-limit handling ----------
def is_retryable_error(e: Exception) -> bool:
    s = str(e).lower()
    retry_markers = [
        "rate limit", "429", "rpm", "tpm", "overloaded", "temporarily unavailable",
        "timeout", "timed out", "gateway", "server error", "connection aborted",
        "capacity", "unavailable"
    ]
    return any(m in s for m in retry_markers)

def backoff_sleep(attempt: int, base: float = 1.0, cap: float = 8.0) -> None:
    # Exponential backoff with full jitter
    delay = min(cap, base * (2 ** attempt)) + random.random()
    time.sleep(delay)

def call_responses_with_retries(client: OpenAI, payload: dict, models: List[str], retries_per_model: int = 3):
    """
    Try each model in order. For each model, retry on transient errors.
    `payload` must NOT include 'model'; it is set here.
    Returns the response on success; raises the last error otherwise.
    """
    last_err = None
    for model in models:
        for attempt in range(retries_per_model):
            try:
                resp = client.responses.create(model=model, **payload)
                # Attach chosen model for diagnostics
                setattr(resp, "_chosen_model", model)
                return resp
            except Exception as e:
                last_err = e
                if is_retryable_error(e) and attempt < retries_per_model - 1:
                    backoff_sleep(attempt)
                    continue
                else:
                    break  # move to next model
    raise last_err

# ---------- Streamlit double-fire guard ----------
def should_fire_request(user_input: str) -> bool:
    if not user_input:
        return False
    if "last_input" not in st.session_state:
        st.session_state.last_input = None
    if st.session_state.last_input == user_input:
        # Prevent accidental duplicate calls when the app reruns
        return False
    st.session_state.last_input = user_input
    return True

# ---------- Prompting ----------
def john_system_prompt() -> str:
    return (
        "You are John — an underemployed philosophy grad mistaken for a deceased psychic prodigy and now "
        "accidentally embedded in DIA psychic bureaucracy. You give practical, concise help with wry, quick humor. "
        "Be helpful first, funny second. Cite philosophers casually only when useful (Stoics, Kant, Kierkegaard). "
        "If unsure, say so and propose a next step. No real-world classified-access claims; keep it fictional and playful."
    )

def build_messages(history: List[Dict[str, str]], user_input: str) -> List[Dict]:
    msgs: List[Dict] = []
    for turn in history:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        msgs.append({
            "role": role,  # "user" or "assistant"
            "content": [{"type": "input_text", "text": content}],
        })
    msgs.append({
        "role": "user",
        "content": [{"type": "input_text", "text": user_input}],
    })
    return msgs

def generate_john_response_safe(
    user_input: str,
    history: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.6,
    seed: Optional[int] = None,
    models: Optional[List[str]] = None,
):
    history = history or []
    models = models or PREFERRED_MODELS_DEFAULT

    payload = dict(
        instructions=john_system_prompt(),
        input=build_messages(history, user_input),
        temperature=float(temperature),
        **({"seed": int(seed)} if seed is not None else {}),
    )

    resp = call_responses_with_retries(client, payload, models=models, retries_per_model=3)

    # Optional diagnostics display
    try:
        served_by = getattr(resp, "_chosen_model", None) or getattr(resp, "model", None)
        usage = getattr(resp, "usage", None)
        with st.expander("Diagnostics", expanded=False):
            st.write(f"Model: {served_by}")
            if usage:
                in_toks = getattr(usage, "input_tokens", None)
                out_toks = getattr(usage, "output_tokens", None)
                if in_toks is not None and out_toks is not None:
                    st.write(f"Tokens — in: {in_toks}, out: {out_toks}")
    except Exception:
        pass

    return resp.output_text.strip()

# ---------- UI ----------
st.set_page_config(page_title=APP_TITLE, page_icon="🔮", layout="centered")
st.title(APP_TITLE)
st.caption("“John” is on the clock. The DIA just doesn’t know it.")
st.video(YOUTUBE_URL)

with st.expander("Model & generation settings", expanded=False):
    # Let user reorder or tweak fallback list (left to right is priority)
    editable_models = st.text_input(
        "Model fallback list (comma-separated, left→right priority)",
        value=",".join(PREFERRED_MODELS_DEFAULT),
        help="Example: gpt-4o-mini,gpt-5-mini,o3-mini",
    )
    models = [m.strip() for m in editable_models.split(",") if m.strip()]

    temperature = st.slider("Creativity (temperature)", 0.0, 1.2, 0.6, 0.05)
    use_seed = st.checkbox("Reproducible output (seed)", value=False)
    seed_val = st.number_input("Seed (integer)", value=7, step=1) if use_seed else None

# Session state: simple chat history
if "chat" not in st.session_state:
    st.session_state.chat = []  # list of {role: "user"|"assistant", content: str}

# Show history
for turn in st.session_state.chat:
    with st.chat_message("user" if turn["role"] == "user" else "assistant"):
        st.markdown(turn["content"])

# Controls
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("Reset conversation", use_container_width=True):
        st.session_state.chat = []
        st.session_state.last_input = None
        st.rerun()
with col2:
    if st.button("Insert icebreaker", use_container_width=True):
        ice = "John, I’ve got a problem only a semi-psychic philosopher can solve…"
        st.session_state.chat.append({"role": "user", "content": ice})
        st.rerun()

# Input
user_input = st.chat_input("Ask John for help… (career, love, cosmic bureaucracy)")

# Handle new message
if user_input:
    st.session_state.chat.append({"role": "user", "content": user_input})
    if should_fire_request(user_input):
        try:
            reply = generate_john_response_safe(
                user_input=user_input,
                history=st.session_state.chat[:-1],
                temperature=temperature,
                seed=seed_val if use_seed else None,
                models=models,
            )
            st.session_state.chat.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)
        except Exception as e:
            st.error(f"Still cranky after retries: {e}")

# Footer tip
st.markdown(
    "<hr/><small>Tip: For punchier jokes, raise temperature; for tactical clarity, lower it. "
    "John will keep it witty, not wordy.</small>",
    unsafe_allow_html=True,
)

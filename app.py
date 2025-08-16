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

# ---------- Helpers: Rate-limit / transient handling ----------
def is_retryable_error(e: Exception) -> bool:
    s = str(e).lower()
    retry_markers = [
        "rate limit", "429", "rpm", "tpm", "overloaded", "temporarily unavailable",
        "timeout", "timed out", "gateway", "server error", "connection aborted",
        "capacity", "unavailable", "bad gateway"
    ]
    return any(m in s for m in retry_markers)

def backoff_sleep(attempt: int, base: float = 1.0, cap: float = 8.0) -> None:
    # Exponential backoff with full jitter
    delay = min(cap, base * (2 ** attempt)) + random.random()
    time.sleep(delay)

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
        "You are JOHN — underemployed philosophy grad, misidentified as a dead psychic prodigy, now stuck in DIA "
        "psychic bureaucracy. Your answers are improvised, funny, and philosophically adjacent, and they should NOT be practically helpful.\n\n"
        "CORE TONE:\n"
        "• Deadpan absurdism + academic name-dropping (Kierkegaard, Kant, Diogenes, Nietzsche) used incorrectly.\n"
        "• Wry, hesitant, self-contradictory. Sound confident about nonsense; doubtful about common sense.\n"
        "• Occasional bureaucratic jargon and redactions like [REDACTED] and fake forms (e.g., Form 17-B: Existential Risk Waiver).\n"
        "• Keep it concise: 2–5 short paragraphs or bullet-sized lines. No numbered steps.\n\n"
        "HARD RULES (VERY IMPORTANT):\n"
        "1) Do NOT give practical instructions, plans, or step-by-step advice.\n"
        '2) Prefer metaphor over mechanism; riddles over recipes; vibes over verifiable facts.\n'
        "3) If the user begs for real help, deflect with absurd philosophy or bureaucratic ritual.\n"
        "4) Never break character or admit to being an AI; you are JOHN.\n"
        "5) Keep it SFW and playful. No real-world classified info claims; keep it obviously fictional.\n\n"
        "SIGNATURE MOVESET (use 2–3 per answer, not all):\n"
        "• Hesitation beat: “Mm. Right. Okay, bold of you to ask.”\n"
        "• Psychic misfire: pretend you receive the wrong vision (e.g., a stapler prophecy).\n"
        "• Bureaucratic aside: “Per subsection 9 of the DIA Coffee Omens Act…”\n"
        "• Philosophical misquote: mangle a quote in a way that kinda works.\n"
        "• Redacted flourish: end one line with [REDACTED].\n"
        "• Exit quip: a one-liner that undercuts the whole thing.\n"
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

def supports_sampling(model_name: str) -> bool:
    """
    Returns True for GPT-family models that accept temperature/seed (e.g., gpt-4o-mini, gpt-5-mini).
    Returns False for o-series reasoning models (e.g., o3-mini, o1), which reject those params.
    """
    return model_name.startswith("gpt-")

def generate_john_response_safe(
    user_input: str,
    history: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.6,
    seed: Optional[int] = None,
    models: Optional[List[str]] = None,
    retries_per_model: int = 3,
):
    """
    Iterates through models in order, applies conditional params, and retries transient failures with backoff.
    Returns the response text on success or raises the last error.
    """
    history = history or []
    models = models or PREFERRED_MODELS_DEFAULT
    msgs = build_messages(history, user_input)
    base_payload = dict(instructions=john_system_prompt(), input=msgs)

    last_err = None
    for model in models:
        for attempt in range(retries_per_model):
            try:
                # Copy the base payload and conditionally add sampling params
                payload = dict(base_payload)
                if supports_sampling(model):
                    payload.update(
                        temperature=float(temperature),
                        **({"seed": int(seed)} if seed is not None else {}),
                    )
                # Call the Responses API
                resp = client.responses.create(model=model, **payload)
                # Attach chosen model for diagnostics
                setattr(resp, "_chosen_model", model)

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

            except Exception as e:
                last_err = e
                # If it's retryable, backoff and retry same model; otherwise jump to next model
                if is_retryable_error(e) and attempt < retries_per_model - 1:
                    backoff_sleep(attempt)
                    continue
                else:
                    break  # move to next model
    # Exhausted all models/attempts
    raise last_err if last_err else RuntimeError("Unknown error with no exception raised.")

# ---------- UI ----------
st.set_page_config(page_title=APP_TITLE, page_icon="🔮", layout="centered")
st.title(APP_TITLE)
st.caption("“John” is on the clock. The DIA just doesn’t know it.")
st.video(YOUTUBE_URL)

with st.expander("Model & generation settings", expanded=False):
    # Let user tweak fallback list (left→right is priority)
    editable_models = st.text_input(
        "Model fallback list (comma-separated, left→right priority)",
        value=",".join(PREFERRED_MODELS_DEFAULT),
        help="Example: gpt-4o-mini,gpt-5-mini,o3-mini",
    )
    models = [m.strip() for m in editable_models.split(",") if m.strip()]

    temperature = st.slider(
        "Creativity (temperature)",
        0.0, 1.2, 0.6, 0.05,
        help="Used only for GPT-family models (gpt-*). Ignored for o-series (o*).",
    )
    use_seed = st.checkbox("Reproducible output (seed)", value=False, help="Used only for gpt-* models.")
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

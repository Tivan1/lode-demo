# app.py
import os
import time
import random
import requests
import streamlit as st
from typing import List, Dict

# -----------------------
# Config & secrets
# -----------------------
st.set_page_config(page_title="EDOL – Groq Demo", page_icon="🍕", layout="wide")

# Prefer streamlit secrets (for Cloud). Fallback naar env var for local usage.
GROQ_API_KEY = ""
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

GROQ_MODEL = st.secrets.get("GROQ_MODEL", "llama3-8b-8192") if "GROQ_MODEL" in st.secrets else os.getenv("GROQ_MODEL", "llama3-8b-8192")

# safety: warn if key missing
if not GROQ_API_KEY:
    st.warning("GROQ API key niet gevonden. De app gebruikt fallback-antwoordmodus. (zet GROQ_API_KEY in Streamlit secrets of als env var)")
    
# -----------------------
# Utilities
# -----------------------
def groq_chat(messages: List[Dict], max_tokens: int = 200, timeout: int = 25) -> str:
    """
    Veilige Groq-aanroep met retry en fallback.
    messages: lijst van {"role": "system|user|assistant", "content": "..."}
    returns: tekst antwoord (str)
    """
    if not GROQ_API_KEY:
        return groq_fallback_reply(messages)

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
    }

    # retry logic
    retries = 2
    backoff = 1.0
    for attempt in range(1, retries + 2):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            # usual OpenAI-like shape
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content") or message.get("role") or ""
            if isinstance(content, dict):
                # sometimes nested; safe stringify
                content = str(content)
            return content.strip()
        except requests.exceptions.RequestException as e:
            # transient network issue: retry
            if attempt <= retries:
                time.sleep(backoff)
                backoff *= 2
                continue
            # permanent failure -> fallback
            return groq_fallback_reply(messages, error=str(e))
        except Exception as e:
            return groq_fallback_reply(messages, error=str(e))

def groq_fallback_reply(messages: List[Dict], error: str = None) -> str:
    """
    Nette fallback reply — zorgt dat demo nooit stilvalt.
    Probeert context te gebruiken (laatste user message).
    """
    last_user = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user = m.get("content", "")
            break

    canned = [
        "Haha, ik zweef met extra kaas! 🚀🧀",
        "Pepperoni in de ruimte smaakt fantastisch! 🪐🍕",
        "Wist je dat ik dromen van olijven? 😴🫒",
        "Klinkt goed! Meer saus, alstublieft! 🍅",
        "Ik snap het — laten we dat doen! ✨"
    ]
    base = random.choice(canned)
    if last_user:
        return f"{base} (fallback) — Je zei: \"{last_user[:120]}...\""
    if error:
        return f"{base} (fallback, error: {error})"
    return f"{base} (fallback)"

# -----------------------
# Personality & memory
# -----------------------
DEFAULT_SYSTEM_PROMPT = (
    "Je bent een vrolijke, speelse 'pizza-EDOL' avatar: kort, enthousiast, soms absurd. "
    "Houd antwoorden vriendelijk, maximaal ~120 tokens. Gebruik emoji’s spaarzaam. "
    "Antwoorden moeten direct bruikbaar zijn in een demo (geen lange disclaimers)."
)

def build_messages(history: List[Dict], mood: str, edol_name: str) -> List[Dict]:
    """
    Bouw de messages array voor Groq: system + short memory + conversation
    """
    system_text = DEFAULT_SYSTEM_PROMPT + f" Huidige mood: {mood}. Naam: {edol_name}."
    messages = [{"role": "system", "content": system_text}]
    # optionally include short memory (last 3 assistant replies)
    memory = [m for m in history if m["role"] == "assistant"][-3:]
    if memory:
        mem_text = "Kort geheugen van vorige antwoorden: " + " || ".join([m["content"] for m in memory])
        messages.append({"role": "system", "content": mem_text})
    # then append full history (user/assistant)
    for m in history:
        messages.append({"role": m["role"], "content": m["content"]})
    return messages

# -----------------------
# Streamlit UI & state
# -----------------------
st.title("EDOL — Groq-powered Demo (Secure) 🍕")
col1, col2 = st.columns([1.2, 0.8])

# EDOL config
with col2:
    st.header("EDOL Config")
    edol_id = st.text_input("EDOL ID", value=st.session_state.get("edol_id", "pizza-edol-001"))
    edol_name = st.text_input("Naam", value=st.session_state.get("edol_name", "Vliegende Pizza"))
    mood = st.selectbox("Mood", options=["blij", "grappig", "slaperig", "sarkastisch"], index=0)
    if st.button("Laad EDOL"):
        st.session_state.edol_id = edol_id
        st.session_state.edol_name = edol_name
        st.session_state.mood = mood
        st.success("EDOL geladen!")

    st.markdown("**Avatar**")
    avatar_url = st.text_input("Avatar URL", value=st.session_state.get("avatar_url", "https://cdn.pixabay.com/photo/2021/07/21/12/49/pizza-6482319_1280.png"))
    st.image(avatar_url, use_column_width=True)

# messages state
if "messages" not in st.session_state:
    # seed with a system message visible in UI
    st.session_state.messages = [
        {"role": "system", "content": "Session gestart."}
    ]
if "edol_name" not in st.session_state:
    st.session_state.edol_name = st.session_state.get("edol_name", "Vliegende Pizza")
if "mood" not in st.session_state:
    st.session_state.mood = "blij"

# Chat area
with col1:
    st.header("Chat met je EDOL")
    # render messages
    for msg in st.session_state.messages:
        if msg["role"] == "system":
            continue
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # input
    user_input = st.chat_input("Typ hier je bericht…")
    if user_input:
        # append user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # build messages for model
        history = st.session_state.messages[-20:]  # limit context
        messages_for_model = build_messages(history, st.session_state.get("mood", "blij"), st.session_state.get("edol_name", "Vliegende Pizza"))

        # call Groq (or fallback)
        with st.spinner("EDOL denkt..."):
            answer = groq_chat(messages_for_model, max_tokens=140)
            time.sleep(0.35)

        # append assistant reply
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.write(answer)

    # action buttons
    st.markdown("---")
    if st.button("Simpel demo-antwoord (no AI)"):
        canned = groq_fallback_reply([])
        st.session_state.messages.append({"role": "assistant", "content": canned})
        with st.chat_message("assistant"):
            st.write(canned)

st.caption("Veilig: zet je GROQ_API_KEY in Streamlit secrets (Settings -> Secrets) of als env var.")

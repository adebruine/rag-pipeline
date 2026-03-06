import os, json, time, uuid, re
from datetime import datetime
from typing import Dict, List
import pandas as pd
import requests
import streamlit as st
import logging

# Setup logging at the top of your file
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="EYEgotthis", page_icon="⚖️", layout="wide")
VERSION = "3.0.0"

st.markdown(
    """
<style>
.ub-bottom {
  position: sticky;
  bottom: 0;
  z-index: 50;
  background: var(--background-color);
  padding: 0.5rem 0 0.75rem 0;
  border-top: 1px solid rgba(255,255,255,0.08);
}
.ub-bottom form { margin: 0; }
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# Backend
# =========================
API_URL = os.getenv("UNBARRED_API", "").strip()
API_KEY = os.getenv("UNBARRED_API_KEY", "").strip()


def call_backend_api(payload: dict) -> dict:
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    r = requests.post(API_URL, json=payload, headers=headers, timeout=180)
    r.raise_for_status()
    return r.json()


# =========================
# Session
# =========================
ss = st.session_state
if "messages" not in ss:
    ss.messages = []
if "run_id" not in ss:
    ss.run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "-" + uuid.uuid4().hex[:6]

# =========================
# Sidebar
# =========================
with st.sidebar:
    st.header("Eyegotthis")
    st.caption(f"Run: {ss.run_id} • v{VERSION}")
    if st.button("Clear conversation"):
        ss.messages = []
        st.rerun()

# =========================
# Main
# =========================
st.title("Eyegotthis Search")

# Render history
for m in ss.messages:
    with st.chat_message(m["role"]):
        content = m["content"]
        if content and m["role"] == "assistant":
            content = content.replace("$", r"\$")
        st.markdown(content)

# ---- Sticky bottom form ----
st.markdown('<div class="ub-bottom">', unsafe_allow_html=True)
with st.form("ub_search_form", clear_on_submit=True):
    user_text = st.text_input(
        "Ask a question…",
        placeholder="Ask a question…",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Search", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if submitted and user_text.strip():
    logger.info(f"User Query: '{user_text}' [RunID: {ss.run_id}]")
    ss.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    payload = {"query": user_text}

    with st.spinner("Running search…"):
        try:
            t0 = time.perf_counter()
            data = call_backend_api(payload)
            took_ms = int((time.perf_counter() - t0) * 1000)
            logger.info(f"Search Success in {took_ms}ms [RunID: {ss.run_id}]")
        except requests.HTTPError as e:
            logger.error(f"Backend Error: {str(e)} [RunID: {ss.run_id}]")
            st.error(f"Backend error: {e}\n\n{getattr(e.response, 'text', '')}")
            st.stop()
        except Exception as e:
            logger.error(f"Unexpected Error: {str(e)} [RunID: {ss.run_id}]")
            st.error(str(e))
            st.stop()

    response_text = data.get("response", "")

    with st.chat_message("assistant"):
        if response_text:
            st.markdown(response_text.replace("$", r"\$"))
        st.caption(f"Latency: {took_ms} ms")

    ss.messages.append({"role": "assistant", "content": response_text})
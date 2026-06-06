import json
import os
import urllib.error
import urllib.request
from html import escape

import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def api_request(path: str, method: str = "GET", payload: dict | None = None):
    url = f"{API_BASE_URL}{path}"
    data = None
    headers = {"Content-Type": "application/json"}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            response_text = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        error_text = error.read().decode("utf-8")
        try:
            detail = json.loads(error_text).get("detail", error_text)
        except json.JSONDecodeError:
            detail = error_text
        raise RuntimeError(detail) from error
    except urllib.error.URLError as error:
        raise RuntimeError(
            "Could not reach the FastAPI backend. Make sure it is running."
        ) from error

    if not response_text:
        return None

    return json.loads(response_text)


def get_notes():
    return api_request("/notes")


def create_note(text: str):
    return api_request("/notes", method="POST", payload={"text": text})


def ask_question(question: str):
    return api_request("/ask", method="POST", payload={"question": question})


st.set_page_config(
    page_title="Local AI Notes",
    page_icon=":memo:",
    layout="wide",
)

st.markdown(
    """
    <style>
        :root {
            --ink: #252422;
            --muted: #6f6a60;
            --paper: #fffaf0;
            --line: #e6dcc8;
            --accent: #2f7d6d;
            --accent-soft: #d9f0ea;
            --rose: #c45f6c;
        }

        .stApp {
            background: linear-gradient(135deg, #f8fbf9 0%, #eef4ff 54%, #fff5f7 100%);
            color: var(--ink);
        }

        .main .block-container {
            max-width: 1120px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            color: var(--ink);
            letter-spacing: 0;
        }

        .app-header {
            border-bottom: 1px solid var(--line);
            padding-bottom: 1.2rem;
            margin-bottom: 1.4rem;
        }

        .eyebrow {
            color: var(--accent);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08rem;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }

        .subtitle {
            color: var(--muted);
            font-size: 1.05rem;
            line-height: 1.6;
            max-width: 720px;
        }

        .status-pill {
            display: inline-block;
            border: 1px solid var(--line);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.62);
            color: var(--muted);
            font-size: 0.88rem;
            padding: 0.35rem 0.75rem;
            margin-top: 0.5rem;
        }

        .note-card {
            background: rgba(255, 255, 255, 0.76);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 4px 18px rgba(55, 45, 28, 0.06);
            white-space: pre-wrap;
        }

        .note-id {
            color: var(--accent);
            font-size: 0.78rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .answer-box {
            background: #f2fbf7;
            border: 1px solid #b7ded2;
            border-left: 5px solid var(--accent);
            border-radius: 8px;
            padding: 1rem 1.1rem;
            line-height: 1.6;
            white-space: pre-wrap;
        }

        div.stButton > button {
            border-radius: 8px;
            border: 1px solid #247064;
            background: var(--accent);
            color: #ffffff;
            font-weight: 700;
        }

        div.stButton > button:hover {
            border-color: #1f5f55;
            background: #286f62;
            color: #ffffff;
        }

        textarea, input {
            border-radius: 8px !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="app-header">
        <div class="eyebrow">Local SQLite + Ollama</div>
        <h1>Local AI Notes</h1>
        <div class="subtitle">
            Capture notes on your laptop, then ask questions grounded in what you saved.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    health = api_request("/health")
    backend_ready = health == {"status": "ok"}
except RuntimeError as error:
    backend_ready = False
    st.error(str(error))

if backend_ready:
    st.markdown(
        f'<div class="status-pill">Backend connected: {API_BASE_URL}</div>',
        unsafe_allow_html=True,
    )

left_column, right_column = st.columns([1, 1], gap="large")

with left_column:
    st.subheader("Add a note")
    note_text = st.text_area(
        "Note text",
        placeholder="Write a note you may want to ask about later...",
        height=150,
        label_visibility="collapsed",
    )

    if st.button("Save note", use_container_width=True):
        cleaned_note = note_text.strip()
        if not cleaned_note:
            st.warning("Write a note before saving.")
        else:
            try:
                saved_note = create_note(cleaned_note)
                st.success(f"Saved note #{saved_note['id']}.")
                st.rerun()
            except RuntimeError as error:
                st.error(str(error))

    st.subheader("Saved notes")
    try:
        notes = get_notes() if backend_ready else []
    except RuntimeError as error:
        notes = []
        st.error(str(error))

    if notes:
        for note in reversed(notes):
            note_text = escape(note["text"])
            st.markdown(
                f"""
                <div class="note-card">
                    <div class="note-id">Note #{note["id"]}</div>
                    <div>{note_text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No notes yet. Add one above to start building your local memory.")

with right_column:
    st.subheader("Ask your notes")
    question = st.text_input(
        "Question",
        placeholder="What should I remember from my notes?",
        label_visibility="collapsed",
    )

    if st.button("Ask Ollama", use_container_width=True):
        cleaned_question = question.strip()
        if not cleaned_question:
            st.warning("Type a question before asking.")
        else:
            with st.spinner("Reading your notes and asking Ollama..."):
                try:
                    result = ask_question(cleaned_question)
                    st.session_state["last_answer"] = result
                except RuntimeError as error:
                    st.error(str(error))

    last_answer = st.session_state.get("last_answer")
    if last_answer:
        answer_text = escape(last_answer["answer"])
        st.markdown(
            f"""
            <div class="answer-box">
                <strong>Answer</strong><br>
                {answer_text}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"Notes sent to Ollama: {last_answer['notes_used']}")
    else:
        st.info("Ask a question to get an answer based on your saved notes.")

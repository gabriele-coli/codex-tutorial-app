import json
import logging
import os
import sqlite3
import urllib.error
import urllib.request
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DATABASE_PATH = Path("notes.db")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_TIMEOUT_SECONDS = 60

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


@contextmanager
def get_database_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def create_notes_table():
    logger.info("Creating notes table if it does not already exist")

    with get_database_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL
            )
            """
        )
        connection.commit()


def save_note(text: str):
    logger.info("Saving a new note")

    with get_database_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO notes (text) VALUES (?)",
            (text,),
        )
        note_id = cursor.lastrowid
        connection.commit()

    return {
        "id": note_id,
        "text": text,
    }


def get_all_notes():
    logger.info("Loading notes from the database")

    with get_database_connection() as connection:
        rows = connection.execute(
            "SELECT id, text FROM notes ORDER BY id"
        ).fetchall()

    return [dict(row) for row in rows]


def build_prompt(question: str, notes: list[dict]):
    if notes:
        notes_text = "\n".join(
            f"- Note {note['id']}: {note['text']}" for note in notes
        )
    else:
        notes_text = "No notes have been saved yet."

    return f"""
You are a helpful assistant for a local notes app.

Answer the user's question using only the notes below.
If the notes do not contain enough information, say that you do not know based on the saved notes.

Saved notes:
{notes_text}

User question:
{question}
""".strip()


def ask_ollama(question: str, notes: list[dict]):
    prompt = build_prompt(question, notes)
    logger.info("Sending question to Ollama model %s", OLLAMA_MODEL)

    request_body = json.dumps(
        {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_URL,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=OLLAMA_TIMEOUT_SECONDS,
        ) as response:
            response_text = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as error:
        logger.exception("Failed to get an answer from Ollama")
        raise HTTPException(
            status_code=502,
            detail=(
                "Could not get an answer from Ollama. "
                "Make sure Ollama is running and the model is available."
            ),
        ) from error

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as error:
        logger.exception("Ollama returned invalid JSON")
        raise HTTPException(
            status_code=502,
            detail="Ollama returned an unexpected response.",
        ) from error

    answer = data.get("response")

    if not answer:
        logger.error("Ollama response did not include an answer")
        raise HTTPException(
            status_code=502,
            detail="Ollama returned an unexpected response.",
        )

    logger.info("Received answer from Ollama")
    return answer.strip()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Local AI Notes API")
    try:
        create_notes_table()
    except sqlite3.Error:
        logger.exception("Failed to prepare the SQLite database")
        raise

    yield
    logger.info("Stopping Local AI Notes API")


app = FastAPI(title="Local AI Notes API", lifespan=lifespan)


class NoteCreate(BaseModel):
    text: str = Field(min_length=1)


class Note(BaseModel):
    id: int
    text: str


class AskRequest(BaseModel):
    question: str = Field(min_length=1)


class AskResponse(BaseModel):
    answer: str
    notes_used: int


@app.get("/health")
def health_check():
    logger.info("Health check requested")
    return {"status": "ok"}


@app.post("/notes", response_model=Note)
def create_note(note: NoteCreate):
    try:
        return save_note(note.text)
    except sqlite3.Error:
        logger.exception("Failed to save note")
        raise HTTPException(
            status_code=500,
            detail="Could not save the note. Please try again.",
        )


@app.get("/notes", response_model=list[Note])
def list_notes():
    try:
        notes = get_all_notes()
    except sqlite3.Error:
        logger.exception("Failed to list notes")
        raise HTTPException(
            status_code=500,
            detail="Could not load notes. Please try again.",
        )

    logger.info("Returning %s notes", len(notes))
    return notes


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    logger.info("Received question for Ollama")

    try:
        notes = get_all_notes()
    except sqlite3.Error:
        logger.exception("Failed to load notes for question")
        raise HTTPException(
            status_code=500,
            detail="Could not load notes for the question. Please try again.",
        )

    answer = ask_ollama(request.question, notes)

    return {
        "answer": answer,
        "notes_used": len(notes),
    }

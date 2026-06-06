import logging
import sqlite3
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DATABASE_PATH = Path("notes.db")

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
    question: str


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
    logger.info("Received question for placeholder answer")

    try:
        notes = get_all_notes()
    except sqlite3.Error:
        logger.exception("Failed to load notes for question")
        raise HTTPException(
            status_code=500,
            detail="Could not load notes for the question. Please try again.",
        )

    return {
        "answer": (
            f"You asked: '{request.question}'. This is a placeholder answer. "
            "Later, this endpoint will use "
            "your saved notes and a local Ollama model to answer the question."
        ),
        "notes_used": len(notes),
    }

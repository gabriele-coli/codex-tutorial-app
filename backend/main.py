import sqlite3
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

DATABASE_PATH = Path("notes.db")


@contextmanager
def get_database_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def create_notes_table():
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
    with get_database_connection() as connection:
        rows = connection.execute(
            "SELECT id, text FROM notes ORDER BY id"
        ).fetchall()

    return [dict(row) for row in rows]


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_notes_table()
    yield


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
    return {"status": "ok"}


@app.post("/notes", response_model=Note)
def create_note(note: NoteCreate):
    return save_note(note.text)


@app.get("/notes", response_model=list[Note])
def list_notes():
    return get_all_notes()


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    return {
        "answer": (
            f"You asked: '{request.question}'. This is a placeholder answer. "
            "Later, this endpoint will use "
            "your saved notes and a local Ollama model to answer the question."
        ),
        "notes_used": len(get_all_notes()),
    }

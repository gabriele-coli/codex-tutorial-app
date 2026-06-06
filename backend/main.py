from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Local AI Notes API")

notes = []
next_note_id = 1


class NoteCreate(BaseModel):
    text: str


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
    global next_note_id

    saved_note = {
        "id": next_note_id,
        "text": note.text,
    }
    notes.append(saved_note)
    next_note_id += 1

    return saved_note


@app.get("/notes", response_model=list[Note])
def list_notes():
    return notes


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    return {
        "answer": (
            f"You asked: '{request.question}'. This is a placeholder answer. "
            "Later, this endpoint will use "
            "your saved notes and a local Ollama model to answer the question."
        ),
        "notes_used": len(notes),
    }

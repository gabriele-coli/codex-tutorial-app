# Local AI Notes App

A beginner-friendly starter project for a local AI notes app.

This version includes a small FastAPI backend with beginner-friendly API endpoints. Notes are stored in a local SQLite database file. There is no frontend or LLM integration yet.

## Project Structure

```text
.
├── backend/
│   └── main.py
├── requirements.txt
├── notes.db        # Created automatically when you run the backend
└── README.md
```

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the backend dependencies:

```bash
pip install -r requirements.txt
```

## Run the Backend

Start the FastAPI development server:

```bash
uvicorn backend.main:app --reload
```

Open the health check in your browser:

[http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

You should see:

```json
{"status":"ok"}
```

## API Docs

FastAPI also provides interactive docs while the server is running:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Current API Endpoints

### Health Check

Check that the backend is running:

```bash
curl http://127.0.0.1:8000/health
```

Example response:

```json
{"status":"ok"}
```

### Add a Note

Save a note in SQLite:

```bash
curl -X POST http://127.0.0.1:8000/notes \
  -H "Content-Type: application/json" \
  -d '{"text":"Remember to test the notes API."}'
```

Example response:

```json
{"id":1,"text":"Remember to test the notes API."}
```

### List Notes

Get all notes currently stored in SQLite:

```bash
curl http://127.0.0.1:8000/notes
```

Example response:

```json
[{"id":1,"text":"Remember to test the notes API."}]
```

### Ask a Question

Ask a question. For now, this returns a placeholder answer:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What should I remember?"}'
```

Example response:

```json
{
  "answer": "You asked: 'What should I remember?'. This is a placeholder answer. Later, this endpoint will use your saved notes and a local Ollama model to answer the question.",
  "notes_used": 1
}
```

## What This Version Teaches

- FastAPI creates the web API.
- Pydantic models describe the JSON inputs and outputs.
- SQLite stores notes locally on your laptop.
- `POST /notes` accepts a note and saves it in `notes.db`.
- `GET /notes` returns all saved notes from `notes.db`.
- `POST /ask` accepts a question and returns a fake answer for now.

The next step is to connect `POST /ask` to a local Ollama model.

## Local Database

The backend automatically creates a local SQLite database file called `notes.db` the first time it starts.

That file is ignored by Git, so your personal notes do not get committed to the repository.

To reset your local notes, stop the server and delete `notes.db`. The backend will create a fresh empty database the next time it starts.

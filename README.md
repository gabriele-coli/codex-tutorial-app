# Local AI Notes App

A beginner-friendly starter project for a local AI notes app.

This version includes a small FastAPI backend and a Streamlit frontend. Notes are stored in a local SQLite database file. Questions are answered by a local Ollama model.

## Project Structure

```text
.
├── backend/
│   └── main.py
├── frontend/
│   └── app.py
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

Install Ollama from [https://ollama.com](https://ollama.com), then pull the default model:

```bash
ollama pull llama3.2
```

## Run the App

The app has two local servers:

- FastAPI backend: stores notes and talks to Ollama
- Streamlit frontend: shows the browser interface

Start the FastAPI backend in one terminal:


```bash
uvicorn backend.main:app --reload
```

Make sure Ollama is also running locally. By default, the backend calls:

```text
http://localhost:11434/api/generate
```

Start the Streamlit frontend in a second terminal:

```bash
streamlit run frontend/app.py
```

Open the Streamlit app in your browser:

[http://localhost:8501](http://localhost:8501)

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

Ask a question. The backend sends your question and saved notes to Ollama:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What should I remember?"}'
```

Example response:

```json
{
  "answer": "Based on your saved notes, you should remember to test the notes API.",
  "notes_used": 1
}
```

## What This Version Teaches

- FastAPI creates the web API.
- Streamlit creates the browser interface.
- Pydantic models describe the JSON inputs and outputs.
- SQLite stores notes locally on your laptop.
- `POST /notes` accepts a note and saves it in `notes.db`.
- `GET /notes` returns all saved notes from `notes.db`.
- Ollama runs a local LLM on your laptop.
- `POST /ask` sends the question and saved notes to Ollama.
- Logging prints important backend events in the server terminal.
- Basic error handling returns cleaner messages if SQLite or Ollama has a problem.

The next step is to retrieve only the most relevant notes for each question.

## Local Database

The backend automatically creates a local SQLite database file called `notes.db` the first time it starts.

That file is ignored by Git, so your personal notes do not get committed to the repository.

To reset your local notes, stop the server and delete `notes.db`. The backend will create a fresh empty database the next time it starts.

## Logging and Errors

When the backend is running, it prints useful messages in the terminal. For example, you may see messages when:

- the app starts
- the notes table is prepared
- a note is saved
- notes are loaded
- a question is received

These logs help you understand what the backend is doing.

If SQLite or Ollama has a problem, the backend logs the detailed error in the terminal and returns a simple error message to the API caller.

## Ollama Settings

The backend uses these default Ollama settings:

```text
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2
```

You can override them with environment variables before starting the backend:

```bash
export OLLAMA_MODEL=mistral
uvicorn backend.main:app --reload
```

## Frontend Settings

The Streamlit frontend calls this backend by default:

```text
API_BASE_URL=http://127.0.0.1:8000
```

You can override it before starting Streamlit:

```bash
export API_BASE_URL=http://127.0.0.1:8000
streamlit run frontend/app.py
```

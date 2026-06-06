# Local AI Notes App

A beginner-friendly starter project for a local AI notes app.

This version only includes a small FastAPI backend with a health check. There is no database, frontend, or LLM integration yet.

## Project Structure

```text
.
├── backend/
│   └── main.py
├── requirements.txt
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

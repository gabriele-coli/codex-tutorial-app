from fastapi import FastAPI

app = FastAPI(title="Local AI Notes API")


@app.get("/health")
def health_check():
    return {"status": "ok"}

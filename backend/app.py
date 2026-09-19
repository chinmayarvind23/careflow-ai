from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from routes.documents import router as documents_router
from routes.runs import router as runs_router
from routes.tinyfish import router as tinyfish_router

app = FastAPI(title="Home Health Referral Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(runs_router)
app.include_router(tinyfish_router)

BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "storage", "uploads")
MOCK_DIR = os.path.join(BASE_DIR, "mock_sites")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(MOCK_DIR, exist_ok=True)

app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")
app.mount("/mock", StaticFiles(directory=MOCK_DIR), name="mock")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
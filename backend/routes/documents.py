import os
import uuid

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from workflows.document_graph import create_document_run, start_document_workflow

router = APIRouter(prefix="/api/documents", tags=["documents"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/process")
async def process_document(file: UploadFile = File(...)) -> JSONResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported right now.")

    unique_name = f"{uuid.uuid4()}{ext}"
    save_path = os.path.join(UPLOAD_DIR, unique_name)

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    state = create_document_run(file_name=file.filename, pdf_path=save_path)
    start_document_workflow(state.run_id)

    return JSONResponse(
        {
            "run_id": state.run_id,
            "status": state.status,
            "file_name": state.file_name,
            "source": "uploaded",
        }
    )


@router.post("/process-sample")
async def process_sample_document() -> JSONResponse:
    sample_name = "sample_referral.pdf"
    sample_path = os.path.join(UPLOAD_DIR, sample_name)

    if not os.path.exists(sample_path):
        raise HTTPException(
            status_code=404,
            detail="sample_referral.pdf not found in backend/storage/uploads.",
        )

    state = create_document_run(file_name=sample_name, pdf_path=sample_path)
    start_document_workflow(state.run_id)

    return JSONResponse(
        {
            "run_id": state.run_id,
            "status": state.status,
            "file_name": state.file_name,
            "source": "sample",
        }
    )
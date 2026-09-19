from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from services.run_store import run_store

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("/{run_id}")
def get_run(run_id: str) -> JSONResponse:
    state = run_store.get_run(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Run not found.")

    return JSONResponse(state.model_dump())
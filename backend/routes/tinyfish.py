from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from models.referral import ReferralExtraction
from services.run_store import run_store
from services.tinyfish_run_store import tinyfish_run_store
from services.tinyfish_service import (
    create_eligibility_run,
    start_eligibility_run,
    create_placement_run,
    start_placement_run,
    create_scheduling_run,
    start_scheduling_run,
)

router = APIRouter(prefix="/api/tinyfish", tags=["tinyfish"])


class TinyFishEligibilityStartRequest(BaseModel):
    run_id: str
    insurance_provider: Optional[str] = None
    zip_code: Optional[str] = None


class TinyFishStartRequest(BaseModel):
    run_id: str


@router.post("/eligibility/start")
def start_tinyfish_eligibility(payload: TinyFishEligibilityStartRequest) -> JSONResponse:
    document_state = run_store.get_run(payload.run_id)
    if document_state is None:
        raise HTTPException(status_code=404, detail="Document run not found.")

    if document_state.referral is None:
        raise HTTPException(status_code=400, detail="Referral extraction not available for this run.")

    referral = ReferralExtraction(**document_state.referral.model_dump())

    tinyfish_state = create_eligibility_run(
        document_run_id=payload.run_id,
        referral=referral,
        insurance_provider_override=payload.insurance_provider,
        zip_code_override=payload.zip_code,
    )

    start_eligibility_run(
        tinyfish_run_id=tinyfish_state.tinyfish_run_id,
        referral=referral,
        insurance_provider_override=payload.insurance_provider,
        zip_code_override=payload.zip_code,
    )

    return JSONResponse(
        {
            "tinyfish_run_id": tinyfish_state.tinyfish_run_id,
            "status": tinyfish_state.status,
        }
    )


@router.post("/placement/start")
def start_tinyfish_placement(payload: TinyFishStartRequest) -> JSONResponse:
    document_state = run_store.get_run(payload.run_id)
    if document_state is None:
        raise HTTPException(status_code=404, detail="Document run not found.")

    if document_state.referral is None:
        raise HTTPException(status_code=400, detail="Referral extraction not available for this run.")

    referral = ReferralExtraction(**document_state.referral.model_dump())

    tinyfish_state = create_placement_run(
        document_run_id=payload.run_id,
        referral=referral,
    )

    start_placement_run(
        tinyfish_run_id=tinyfish_state.tinyfish_run_id,
        referral=referral,
    )

    return JSONResponse(
        {
            "tinyfish_run_id": tinyfish_state.tinyfish_run_id,
            "status": tinyfish_state.status,
        }
    )


@router.post("/schedule/start")
def start_tinyfish_schedule(payload: TinyFishStartRequest) -> JSONResponse:
    document_state = run_store.get_run(payload.run_id)
    if document_state is None:
        raise HTTPException(status_code=404, detail="Document run not found.")

    if document_state.referral is None:
        raise HTTPException(status_code=400, detail="Referral extraction not available for this run.")

    referral = ReferralExtraction(**document_state.referral.model_dump())

    tinyfish_state = create_scheduling_run(
        document_run_id=payload.run_id,
        referral=referral,
    )

    start_scheduling_run(
        tinyfish_run_id=tinyfish_state.tinyfish_run_id,
        referral=referral,
    )

    return JSONResponse(
        {
            "tinyfish_run_id": tinyfish_state.tinyfish_run_id,
            "status": tinyfish_state.status,
        }
    )


@router.get("/runs/{tinyfish_run_id}")
def get_tinyfish_run(tinyfish_run_id: str) -> JSONResponse:
    state = tinyfish_run_store.get_run(tinyfish_run_id)
    if state is None:
        raise HTTPException(status_code=404, detail="TinyFish run not found.")

    return JSONResponse(state.model_dump())
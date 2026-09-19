from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


TinyFishStatus = Literal["queued", "running", "complete", "failed"]


class TinyFishAgentTrace(BaseModel):
    id: str
    name: str
    status: TinyFishStatus = "queued"
    site: str
    goal: str
    observation: str
    action: str
    updates: List[str] = Field(default_factory=list)
    external_run_id: Optional[str] = None
    streaming_url: Optional[str] = None


class TinyFishLog(BaseModel):
    message: str


class TinyFishEligibilityState(BaseModel):
    tinyfish_run_id: str
    document_run_id: str

    status: TinyFishStatus = "queued"
    stage: str = "eligibility"

    insurance_provider: Optional[str] = None
    zip_code: Optional[str] = None

    insurance_accepted: Optional[bool] = None
    serviceable_zip: Optional[bool] = None
    matched_branch: Optional[str] = None

    placement_submitted: Optional[bool] = None

    assigned_nurse: Optional[str] = None
    scheduled_slot: Optional[str] = None
    call_initialized: Optional[bool] = None

    insurance_site: Optional[str] = None
    zip_site: Optional[str] = None
    nurses_site: Optional[str] = None
    placement_site: Optional[str] = None

    agents: List[TinyFishAgentTrace] = Field(default_factory=list)
    logs: List[TinyFishLog] = Field(default_factory=list)

    insurance_run: Optional[Dict[str, Any]] = None
    zip_run: Optional[Dict[str, Any]] = None
    placement_run: Optional[Dict[str, Any]] = None
    scheduling_run: Optional[Dict[str, Any]] = None

    error: Optional[str] = None
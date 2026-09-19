from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field

from models.referral import ReferralExtraction


AgentStatus = Literal["queued", "running", "complete", "failed"]
RunStatus = Literal["queued", "running", "complete", "failed"]


class AgentTrace(BaseModel):
    id: str
    name: str
    status: AgentStatus = "queued"
    goal: str
    current_task: str
    observation: str
    action: str
    updates: List[str] = Field(default_factory=list)


class WorkflowLog(BaseModel):
    timestamp: float
    message: str


class DocumentWorkflowState(BaseModel):
    run_id: str
    file_name: str
    pdf_path: str

    status: RunStatus = "queued"
    current_stage: str = "queued"
    progress: int = 0

    document_type: Optional[str] = None
    raw_text: Optional[str] = None
    parsed_sections: Dict[str, Any] = Field(default_factory=dict)

    referral: Optional[ReferralExtraction] = None

    agents: List[AgentTrace] = Field(default_factory=list)
    logs: List[WorkflowLog] = Field(default_factory=list)

    error: Optional[str] = None
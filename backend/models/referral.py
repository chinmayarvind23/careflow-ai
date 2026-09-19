from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class ReferralExtraction(BaseModel):
    id: Optional[str] = None

    patient_name: Optional[str] = None
    mrn: Optional[str] = None
    dob: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    zip_code: Optional[str] = None

    hospital_name: Optional[str] = None
    insurance_provider: Optional[str] = None
    member_id: Optional[str] = None

    services_required: List[str] = Field(default_factory=list)

    primary_care_physician: Optional[str] = None
    ordering_physician: Optional[str] = None
    diagnosis: Optional[str] = None
    discharge_date: Optional[str] = None

    missing_fields: List[str] = Field(default_factory=list)
    validation_notes: List[str] = Field(default_factory=list)

    field_confidence: Dict[str, float] = Field(default_factory=dict)
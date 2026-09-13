from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from app.services.error_codes import IncidentStatus

class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus


class IncidentResponse(BaseModel):
    id: int
    incident_id: str
    event_id: int

    error_code: str
    error_type: str
    severity: str
    status: str

    error_message: str

    source_system: str
    target_system: str

    remediation_action: Optional[str]

    created_at: datetime

    investigation_started_at: Optional[datetime]
    remediation_started_at: Optional[datetime]
    remediated_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resolved_at: Optional[datetime]

    model_config = {
        "from_attributes": True
    }
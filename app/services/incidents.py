import uuid
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.interface_incident import InterfaceIncident
from app.services.error_catalog import ERROR_CATALOG
from app.services.error_codes import ErrorCode, IncidentStatus


VALID_STATUS_TRANSITIONS = {

    IncidentStatus.OPEN: {
        IncidentStatus.INVESTIGATING
    },

    IncidentStatus.INVESTIGATING: {
        IncidentStatus.REMEDIATION_PENDING
    },

    IncidentStatus.REMEDIATION_PENDING: {
        IncidentStatus.REMEDIATED
    },

    IncidentStatus.REMEDIATED: {
        IncidentStatus.CLOSED
    },

    IncidentStatus.CLOSED: set()
}

def create_incident(
    db: Session,
    event_db_id: int,
    error_code: ErrorCode,
    error_message: str
) -> InterfaceIncident:

    error_definition = ERROR_CATALOG[error_code]

    incident = InterfaceIncident(
        incident_id=f"INC-{uuid.uuid4().hex[:8].upper()}",
        event_id=event_db_id,
        error_code=error_code.value,
        error_type=error_definition["error_type"],
        severity=error_definition["severity"].value,
        status=IncidentStatus.OPEN.value,
        error_message=error_message
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return incident


def update_incident_status(
    db: Session,
    incident: InterfaceIncident,
    new_status: IncidentStatus
) -> InterfaceIncident:

    current_status = IncidentStatus(
        incident.status
    )

    allowed_statuses = VALID_STATUS_TRANSITIONS[
        current_status
    ]

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Invalid incident transition: "
                f"{current_status.value} -> "
                f"{new_status.value}"
            )
        )

    incident.status = new_status.value

    if new_status == IncidentStatus.INVESTIGATING:
        incident.investigation_started_at = datetime.now

    elif new_status == IncidentStatus.REMEDIATION_PENDING:
        incident.remediation_started_at = datetime.now

    elif new_status == IncidentStatus.REMEDIATED:
        incident.remediated_at = datetime.now

    elif new_status == IncidentStatus.CLOSED:
        incident.resolved_at = datetime.now

    db.commit()
    db.refresh(incident)

    return incident
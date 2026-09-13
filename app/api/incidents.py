from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.interface_incident import InterfaceIncident
from app.schemas.interface_incident import (
    IncidentResponse,
    IncidentStatusUpdate
)
from app.services.incidents import update_incident_status


router = APIRouter(
    prefix="/api/v1/incidents",
    tags=["Sentinel Incidents"]
)

@router.get(
    "",
    response_model=list[IncidentResponse]
)
def get_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    error_type: Optional[str] = None,
    db: Session = Depends(get_db)
):

    statement = select(
        InterfaceIncident
    )

    if status:
        statement = statement.where(
            InterfaceIncident.status == status.upper()
        )

    if severity:
        statement = statement.where(
            InterfaceIncident.severity == severity.upper()
        )

    if error_type:
        statement = statement.where(
            InterfaceIncident.error_type
            == error_type
        )

    statement = statement.order_by(
        InterfaceIncident.created_at.desc()
    )

    return db.scalars(statement).all()

@router.get(
    "/{incident_id}",
    response_model=IncidentResponse
)
def get_incident(
    incident_id: str,
    db: Session = Depends(get_db)
):

    statement = select(
        InterfaceIncident
    ).where(
        InterfaceIncident.incident_id
        == incident_id
    )

    incident = db.scalar(statement)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Incident {incident_id} not found"
            )
        )

    return incident
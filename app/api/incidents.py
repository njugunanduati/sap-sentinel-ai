from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.interface_incident import InterfaceIncident
from app.schemas.interface_incident import (
    IncidentResponse,
    IncidentStatusUpdate
)


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


@router.get("/metrics/summary")
def get_incident_metrics(
    db: Session = Depends(get_db)
):

    total = db.scalar(
        select(
            func.count(InterfaceIncident.id)
        )
    ) or 0

    open_incidents = db.scalar(
        select(
            func.count(InterfaceIncident.id)
        ).where(
            InterfaceIncident.status == "OPEN"
        )
    ) or 0

    critical = db.scalar(
        select(
            func.count(InterfaceIncident.id)
        ).where(
            InterfaceIncident.severity == "CRITICAL"
        )
    ) or 0

    remediated = db.scalar(
        select(
            func.count(InterfaceIncident.id)
        ).where(
            InterfaceIncident.status.in_(
                ["REMEDIATED", "CLOSED"]
            )
        )
    ) or 0

    return {
        "total_incidents": total,
        "open_incidents": open_incidents,
        "critical_incidents": critical,
        "remediated_incidents": remediated
    }

@router.get("/metrics/errors")
def get_error_distribution(
    db: Session = Depends(get_db)
):

    statement = (
        select(
            InterfaceIncident.error_code,
            func.count(
                InterfaceIncident.id
            ).label("count")
        )
        .group_by(
            InterfaceIncident.error_code
        )
        .order_by(
            func.count(
                InterfaceIncident.id
            ).desc()
        )
    )

    results = db.execute(statement).all()

    return [
        {
            "error_code": row.error_code,
            "count": row.count
        }
        for row in results
    ]
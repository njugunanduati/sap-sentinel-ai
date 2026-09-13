from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.interface_event import InterfaceEvent


router = APIRouter(
    prefix="/api/v1/interfaces",
    tags=["SAP Interfaces"]
)


@router.get("/events")
def get_events(db: Session = Depends(get_db)):

    statement = (
        select(InterfaceEvent)
        .order_by(InterfaceEvent.timestamp.desc())
    )

    events = db.scalars(statement).all()

    return events


@router.get("/events/{event_id}")
def get_event(
    event_id: str,
    db: Session = Depends(get_db)
):

    statement = select(InterfaceEvent).where(
        InterfaceEvent.event_id == event_id
    )

    event = db.scalar(statement)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail=f"Event {event_id} not found"
        )

    return event


@router.get("/errors/reconciliation")
def get_reconciliation_errors(
    db: Session = Depends(get_db)
):

    statement = (
        select(InterfaceEvent)
        .where(
            InterfaceEvent.reconciliation_status
            == "RECONCILIATION_REQUIRED"
        )
        .order_by(InterfaceEvent.timestamp.desc())
    )

    return db.scalars(statement).all()


@router.get("/metrics")
def get_interface_metrics(
    db: Session = Depends(get_db)
):

    total_events = db.scalar(
        select(func.count(InterfaceEvent.id))
    ) or 0

    reconciliation_errors = db.scalar(
        select(func.count(InterfaceEvent.id))
        .where(
            InterfaceEvent.reconciliation_status
            == "RECONCILIATION_REQUIRED"
        )
    ) or 0

    total_exposure = db.scalar(
        select(
            func.sum(InterfaceEvent.financial_exposure)
        )
        .where(
            InterfaceEvent.reconciliation_status
            == "RECONCILIATION_REQUIRED"
        )
    ) or 0

    matched = db.scalar(
        select(func.count(InterfaceEvent.id))
        .where(
            InterfaceEvent.reconciliation_status
            == "MATCHED"
        )
    ) or 0

    return {
        "total_events": total_events,
        "matched_events": matched,
        "reconciliation_errors": reconciliation_errors,
        "total_financial_exposure": round(
            float(total_exposure),
            2
        )
    }
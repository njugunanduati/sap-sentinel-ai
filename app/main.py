from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.interface_event import InterfaceEvent
from app.models.interface_incident import InterfaceIncident
from app.schemas.interface_event import InterfaceEventCreate
from app.services.reconciliation import reconcile_inventory
from app.services.error_detector import detect_errors
from app.services.incidents import create_incident
from app.api.interfaces import router as interfaces_router
from app.api.incidents import router as incident_router


app = FastAPI(
    title="SAP Sentinel AI",
    description="AI-powered SAP Retail interface monitoring and reconciliation",
    version="0.1.0"
)
app.include_router(interfaces_router)
app.include_router(incident_router)

@app.get("/health")
def health():
    return {
        "status": "UP",
        "service": "sap-sentinel-ai"
    }

@app.post("/api/v1/interface/event")
def receive_interface_event(event: InterfaceEventCreate, db: Session=Depends(get_db)):
    try:
        reconciliation = reconcile_inventory(
            system_quantity=event.system_quantity,
            physical_quantity=event.physical_quantity,
            unit_price=event.unit_price
        )

        database_event = InterfaceEvent(
            event_id=event.event_id,
            interface_id=event.interface_id,
            store_id=event.store_id,
            material_id=event.material_id,
            movement_type=event.movement_type,
            system_quantity=event.system_quantity,
            physical_quantity=event.physical_quantity,
            unit_price=event.unit_price,
            currency=event.currency,
            variance=reconciliation["variance"],
            financial_exposure=reconciliation["financial_exposure"],
            reconciliation_status=reconciliation["status"],
            timestamp=event.timestamp
        )

        db.add(database_event)
        db.commit()
        db.refresh(database_event)

        detected_errors = detect_errors(event)

        incidents = []

        for error in detected_errors:
            incident = create_incident(
                db=db,
                event_db_id=database_event.id,
                error_code=error["code"],
                error_message=error["message"]
            )

            incidents.append({
                "incident_id": incident.incident_id,
                "error_code": incident.error_code,
                "severity": incident.severity,
                "status": incident.status
            })

        return {
            "id": database_event.id,
            "event_id": database_event.event_id,
            "interface_id": database_event.interface_id,
            "store_id": database_event.store_id,
            "material_id": database_event.material_id,
            "reconciliation": reconciliation,
            "incidents": incidents
        }
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=f"Event {event.event_id} already exists"
        )
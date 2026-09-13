from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models.interface_event import InterfaceEvent
from app.schemas.interface_event import InterfaceEventCreate
from app.services.reconciliation import reconcile_inventory
from app.api.interfaces import router as interfaces_router




Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SAP Sentinel AI",
    description="AI-powered SAP Retail interface monitoring and reconciliation",
    version="0.1.0"
)
app.include_router(interfaces_router)

@app.get("/health")
def health():
    return {
        "status": "UP",
        "service": "sap-sentinel-ai"
    }

@app.post("/api/v1/interface/event")
def receive_interface_event(event: InterfaceEventCreate, db: Session=Depends(get_db)):

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

    return {
        "id": database_event.id,
        "event_id": database_event.event_id,
        "interface_id": database_event.interface_id,
        "store_id": database_event.store_id,
        "material_id": database_event.material_id,
        "reconciliation": reconciliation
    }
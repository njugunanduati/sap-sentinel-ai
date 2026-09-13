from datetime import datetime
from pydantic import BaseModel, Field

class InterfaceEventCreate(BaseModel):
    interface_id: str
    event_id: str
    store_id: str
    material_id: str
    movement_type: str

    system_quantity: int = Field(ge=0)
    physical_quantity: int = Field(ge=0)

    unit_price: float = Field(ge=0)

    currency: str = "USD"
    timestamp: datetime
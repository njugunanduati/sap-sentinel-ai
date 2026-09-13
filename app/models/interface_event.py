from typing import Optional
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InterfaceEvent(Base):

    __tablename__ = "interface_events"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    event_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True
    )

    interface_id: Mapped[str] = mapped_column(
        String(100),
        index=True
    )

    store_id: Mapped[str] = mapped_column(
        String(50),
        index=True
    )

    material_id: Mapped[str] = mapped_column(
        String(50),
        index=True
    )

    movement_type: Mapped[str] = mapped_column(
        String(50)
    )

    system_quantity: Mapped[int] = mapped_column(
        Integer
    )

    physical_quantity: Mapped[int] = mapped_column(
        Integer
    )

    unit_price: Mapped[float] = mapped_column(
        Float
    )

    currency: Mapped[str] = mapped_column(
        String(3)
    )

    variance: Mapped[int] = mapped_column(
        Integer
    )

    financial_exposure: Mapped[float] = mapped_column(
        Float
    )

    reconciliation_status: Mapped[str] = mapped_column(
        String(50),
        index=True
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime
    )
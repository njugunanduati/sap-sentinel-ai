from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InterfaceIncident(Base):
    __tablename__ = "interface_incidents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    incident_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True
    )

    # Links the incident to the original SAP event
    event_id: Mapped[int] = mapped_column(
        ForeignKey("interface_events.id"),
        index=True
    )

    error_code: Mapped[str] = mapped_column(
        String(100),
        index=True
    )

    error_type: Mapped[str] = mapped_column(
        String(100),
        index=True
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        index=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="OPEN",
        index=True
    )

    error_message: Mapped[str] = mapped_column(
        Text
    )

    source_system: Mapped[str] = mapped_column(
        String(100),
        default="SAP_S4_RETAIL"
    )

    target_system: Mapped[str] = mapped_column(
        String(100),
        default="SENTINEL"
    )

    remediation_action: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )
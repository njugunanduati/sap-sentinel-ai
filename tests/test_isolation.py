import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.models.interface_event import InterfaceEvent
from app.models.interface_incident import InterfaceIncident


@pytest.mark.parametrize("iteration", range(2))
def test_each_test_starts_empty_even_after_previous_commits(client, iteration, payload):
    assert client.get("/api/v1/interfaces/events").json() == []
    assert client.get("/api/v1/incidents").json() == []
    # Deliberately reuse the same unique event ID across independent tests.
    assert client.post("/api/v1/interface/event", json={**payload, "store_id": "UNKNOWN"}).status_code == 200


def test_session_rollback_does_not_leak(client, session_factory, payload):
    client.post("/api/v1/interface/event", json=payload)
    with session_factory() as first:
        record = first.scalar(select(InterfaceEvent))
        record.store_id = "UNCOMMITTED"
        first.flush()
        with session_factory() as second:
            assert second.scalar(select(InterfaceEvent)).store_id == "STORE-101"
        first.rollback()
    with session_factory() as third:
        assert third.scalar(select(InterfaceEvent)).store_id == "STORE-101"


def test_database_enforces_foreign_keys(db):
    assert db.scalar(text("PRAGMA foreign_keys")) == 1
    db.add(InterfaceIncident(incident_id="ORPHAN", event_id=999,
        error_code="INVALID_STORE", error_type="MASTER_DATA_ERROR",
        severity="HIGH", error_message="Missing event"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    assert db.scalar(select(InterfaceIncident)) is None

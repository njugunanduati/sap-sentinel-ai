from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models.interface_incident import InterfaceIncident
from app.services.error_codes import IncidentStatus
from app.services.incidents import update_incident_status

POST = "/api/v1/interface/event"


@pytest.mark.parametrize("changes,code,severity,error_type", [
    ({"store_id": "UNKNOWN"}, "INVALID_STORE", "HIGH", "MASTER_DATA_ERROR"),
    ({"material_id": "UNKNOWN"}, "MISSING_MASTER_DATA", "HIGH", "MASTER_DATA_ERROR"),
    ({"material_id": ""}, "MISSING_MATERIAL", "HIGH", "VALIDATION_ERROR"),
    ({"currency": "EUR"}, "INVALID_CURRENCY", "MEDIUM", "VALIDATION_ERROR"),
])
def test_incident_creation_and_nullable_response(client, db, payload, changes, code, severity, error_type):
    response = client.post(POST, json={**payload, **changes})
    assert response.status_code == 200
    body = response.json()
    assert len(body["incidents"]) == 1
    incident_id = body["incidents"][0]["incident_id"]
    result = client.get(f"/api/v1/incidents/{incident_id}")
    assert result.status_code == 200
    incident = result.json()
    assert incident["event_id"] == body["id"]
    assert incident["error_code"] == code
    assert incident["severity"] == severity
    assert incident["error_type"] == error_type
    assert incident["status"] == "OPEN"
    assert incident["error_message"]
    assert incident["remediation_action"] is None
    assert incident["resolved_at"] is None
    assert datetime.fromisoformat(incident["created_at"])
    listing = client.get("/api/v1/incidents")
    assert listing.status_code == 200
    assert listing.json() == [incident]
    assert db.scalar(select(InterfaceIncident)).event_id == body["id"]


@pytest.mark.parametrize("status", ["open", "OPEN", "Open", "oPeN"])
def test_status_filter_case_insensitive_and_combined_filters(client, db, payload, status):
    client.post(POST, json={**payload, "store_id": "UNKNOWN", "currency": "EUR", "material_id": "UNKNOWN"})
    rows = db.scalars(select(InterfaceIncident).order_by(InterfaceIncident.id)).all()
    for index, row in enumerate(rows):
        row.created_at = datetime(2026, 1, 1) + timedelta(seconds=index)
    rows[0].status = "CLOSED"
    rows[0].remediation_action = "Corrected store"
    rows[0].resolved_at = datetime(2026, 1, 2)
    db.commit()
    all_rows = client.get("/api/v1/incidents").json()
    assert [r["id"] for r in all_rows] == [r.id for r in reversed(rows)]
    response = client.get("/api/v1/incidents", params={"status": status})
    assert response.status_code == 200
    assert {r["id"] for r in response.json()} == {rows[1].id, rows[2].id}
    filtered = client.get("/api/v1/incidents", params={"status": status, "severity": "high", "error_type": "MASTER_DATA_ERROR"})
    assert [r["error_code"] for r in filtered.json()] == ["MISSING_MASTER_DATA"]
    closed = client.get("/api/v1/incidents", params={"status": "closed"}).json()
    assert closed[0]["remediation_action"] == "Corrected store"
    assert closed[0]["resolved_at"] == "2026-01-02T00:00:00"
    assert client.get("/api/v1/incidents", params={"status": "absent"}).json() == []


def test_empty_and_missing_incidents(client):
    response = client.get("/api/v1/incidents")
    assert response.status_code == 200
    assert response.json() == []
    assert client.get("/api/v1/incidents/absent").status_code == 404


def test_status_service_lifecycle(client, db, payload):
    client.post(POST, json={**payload, "store_id": "UNKNOWN"})
    incident = db.scalar(select(InterfaceIncident))
    for status, field in [
        (IncidentStatus.INVESTIGATING, "investigation_started_at"),
        (IncidentStatus.REMEDIATION_PENDING, "remediation_started_at"),
        (IncidentStatus.REMEDIATED, "remediated_at"),
        (IncidentStatus.CLOSED, "resolved_at"),
    ]:
        updated = update_incident_status(db, incident, status)
        assert updated.status == status.value
        assert isinstance(getattr(updated, field), datetime)
    with pytest.raises(HTTPException) as exc:
        update_incident_status(db, incident, IncidentStatus.OPEN)
    assert exc.value.status_code == 409
    db.refresh(incident)
    assert incident.status == "CLOSED"


def test_status_service_rejects_skipped_transition(client, db, payload):
    client.post(POST, json={**payload, "store_id": "UNKNOWN"})
    incident = db.scalar(select(InterfaceIncident))
    with pytest.raises(HTTPException) as exc:
        update_incident_status(db, incident, IncidentStatus.CLOSED)
    assert exc.value.status_code == 409
    db.refresh(incident)
    assert incident.status == "OPEN"
    assert incident.resolved_at is None

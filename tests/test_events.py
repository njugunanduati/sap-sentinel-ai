import pytest
from sqlalchemy import func, select

from app.models.interface_event import InterfaceEvent
from app.models.interface_incident import InterfaceIncident

POST = "/api/v1/interface/event"


@pytest.mark.parametrize("physical,variance,status", [
    (10, 0, "MATCHED"), (9, -1, "MINOR_VARIANCE"),
    (12, 2, "MINOR_VARIANCE"), (8, -2, "MINOR_VARIANCE"),
    (13, 3, "RECONCILIATION_REQUIRED"), (7, -3, "RECONCILIATION_REQUIRED"),
])
def test_create_and_reconcile(client, db, payload, physical, variance, status):
    payload["physical_quantity"] = physical
    response = client.post(POST, json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["event_id"] == payload["event_id"]
    assert body["incidents"] == []
    assert body["reconciliation"]["variance"] == variance
    assert body["reconciliation"]["status"] == status
    assert body["reconciliation"]["financial_exposure"] == abs(variance) * 12.5
    saved = db.get(InterfaceEvent, body["id"])
    assert saved.currency == "USD"
    assert saved.variance == variance
    assert saved.reconciliation_status == status
    assert saved.financial_exposure == abs(variance) * 12.5
    detail = client.get(f"/api/v1/interfaces/events/{payload['event_id']}")
    assert detail.status_code == 200
    assert detail.json()["id"] == saved.id


@pytest.mark.parametrize("changed_retry", [False, True])
def test_duplicate_is_conflict_without_repeating_side_effects(client, db, payload, changed_retry):
    payload["store_id"] = "UNKNOWN"
    original = client.post(POST, json=payload).json()
    retry = dict(payload)
    if changed_retry:
        retry.update(physical_quantity=99, material_id="UNKNOWN")
    response = client.post(POST, json=retry)
    assert response.status_code == 409
    assert response.json() == {"detail": "Event EVT-001 already exists"}
    assert db.scalar(select(func.count(InterfaceEvent.id))) == 1
    assert db.scalar(select(func.count(InterfaceIncident.id))) == 1
    assert db.get(InterfaceEvent, original["id"]).physical_quantity == 10
    assert client.get("/api/v1/incidents").json()[0]["incident_id"] == original["incidents"][0]["incident_id"]
    # A uniqueness failure must not poison the next request's session.
    assert client.post(POST, json={**payload, "event_id": "EVT-002"}).status_code == 200


@pytest.mark.parametrize("field,value", [
    ("system_quantity", -1), ("physical_quantity", -1),
    ("unit_price", -0.01), ("timestamp", "invalid"),
])
def test_invalid_payload_has_no_database_side_effects(client, db, payload, field, value):
    response = client.post(POST, json={**payload, field: value})
    assert response.status_code == 422
    assert db.scalar(select(func.count(InterfaceEvent.id))) == 0
    assert db.scalar(select(func.count(InterfaceIncident.id))) == 0


def test_lists_metrics_and_missing_event(client, payload):
    assert client.get("/health").json()["status"] == "UP"
    assert client.get("/api/v1/interfaces/events").json() == []
    assert client.get("/api/v1/interfaces/metrics").json() == {
        "total_events": 0, "matched_events": 0, "reconciliation_errors": 0,
        "total_financial_exposure": 0,
    }
    for index, quantity in enumerate([10, 12, 6]):
        response = client.post(POST, json={**payload, "event_id": f"EVT-{index}",
            "physical_quantity": quantity, "timestamp": f"2026-09-13T10:0{index}:00"})
        assert response.status_code == 200
    assert [e["event_id"] for e in client.get("/api/v1/interfaces/events").json()] == ["EVT-2", "EVT-1", "EVT-0"]
    assert [e["event_id"] for e in client.get("/api/v1/interfaces/errors/reconciliation").json()] == ["EVT-2"]
    assert client.get("/api/v1/interfaces/metrics").json() == {
        "total_events": 3, "matched_events": 1, "reconciliation_errors": 1,
        "total_financial_exposure": 50.0,
    }
    assert client.get("/api/v1/interfaces/events/absent").status_code == 404

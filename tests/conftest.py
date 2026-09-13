"""Real ORM/API tests; never import the application against the developer DB."""
import os

# main.py runs create_all at import time. Override before *any* application import;
# load_dotenv does not override this. This engine never connects to PostgreSQL.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.interface_event import InterfaceEvent
from app.models.interface_incident import InterfaceIncident


@pytest.fixture
def session_factory(tmp_path):
    # Separate files per test permit real commits/rollbacks and independent request
    # sessions, without SQLite savepoint semantics masking transaction behavior.
    engine = create_engine(
        f"sqlite:///{tmp_path / 'sentinel-test.sqlite3'}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with factory() as session:
        assert session.scalar(select(func.count(InterfaceEvent.id))) == 0
        assert session.scalar(select(func.count(InterfaceIncident.id))) == 0
    try:
        yield factory
    finally:
        engine.dispose()


@pytest.fixture
def db(session_factory):
    with session_factory() as session:
        yield session


@pytest.fixture
def client(session_factory):
    def override_db():
        with session_factory() as session:
            yield session

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


@pytest.fixture
def payload():
    return {
        "interface_id": "INVENTORY-001",
        "event_id": "EVT-001",
        "store_id": "STORE-101",
        "material_id": "MAT-10001",
        "movement_type": "COUNT",
        "system_quantity": 10,
        "physical_quantity": 10,
        "unit_price": 12.50,
        "timestamp": "2026-09-13T10:00:00",
    }

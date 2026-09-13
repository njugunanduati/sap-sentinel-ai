# SAP Sentinel AI

**SAP Retail interface monitoring, inventory reconciliation, and structured incident tracking.**

SAP Sentinel AI is a FastAPI backend that accepts inventory events, compares system and physical quantities, calculates financial exposure, and records business/data errors as incidents. PostgreSQL stores events and incidents; REST endpoints expose results and aggregate metrics.

The current implementation is a rule-based prototype. Live SAP connectivity, AI inference, automated remediation, and a production deployment target are not implemented.

## Architecture

![SAP Sentinel architecture: simulator, interface gateway, reconciliation and error detection, incident lifecycle, metrics and PostgreSQL](docs/assets/architecture.png)

The diagram describes the intended system flow. Today, FastAPI provides the interface gateway, Python services perform reconciliation and error detection, and SQLAlchemy persists results. Incident lifecycle transitions exist as a service; there is no HTTP status-update endpoint or separate history API yet.

## Current capabilities

- Receive inventory events and reject duplicate event IDs with HTTP **409**, preserving the original record (duplicates do not replay the successful response).
- Compute `variance = physical_quantity - system_quantity` and `financial_exposure = abs(variance) × unit_price`.
- Classify zero variance as `MATCHED`, absolute variance of one or two as `MINOR_VARIANCE`, and larger differences as `RECONCILIATION_REQUIRED`.
- Create linked incidents for invalid stores, missing/unknown materials, and unsupported currencies. Inventory variance is tracked separately from these incidents.
- List and retrieve events/incidents; expose reconciliation exceptions, financial exposure, incident counts, and error distributions.
- Filter incidents by status, severity, and error type. Status/severity inputs are case-insensitive; error type is an exact match.
- Validate incident transitions through `OPEN → INVESTIGATING → REMEDIATION_PENDING → REMEDIATED → CLOSED`, recording lifecycle timestamps in the service.

Demo master data currently accepts `STORE-101` through `STORE-105`, `MAT-10001` through `MAT-10005`, and `USD` only. These are local fixtures, not an SAP master-data integration.

## Prerequisites

- Python **3.11** for the documented setup, GitHub Actions, and container. The existing local suite also runs on Python 3.9.
- Git, pip, and Python's `venv` module.
- Docker Engine/Desktop with Docker Compose v2 for local PostgreSQL and container builds, or an existing PostgreSQL 16 instance.
- Available ports **5431** (host PostgreSQL) and **8000** (API).

Run the following commands from the repository root. Shell examples use macOS/Linux; on Windows use WSL for the same commands.

## Local setup

### 1. Create a virtual environment and install

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
# Include the test entry point for development:
python -m pip install -r requirements-test.txt
```

### 2. Configure the environment

Create or update your local `.env` without overwriting any existing settings:

```dotenv
DATABASE_URL=postgresql+psycopg://sentinel:sentinel_dev@localhost:5431/sentinel
```

This example uses only the development credentials already declared in `docker-compose.yml`. `.env` is ignored by Git. Do not commit real credentials; inject them through the eventual hosting platform's secret manager.

| Variable | Used by | Description |
| --- | --- | --- |
| `DATABASE_URL` | API / SQLAlchemy | Required SQLAlchemy connection URL. No application default. Use the `postgresql+psycopg` driver for PostgreSQL. |
| `API_URL` | Simulator only | Legacy base URL; the script appends `interfaces/events`. It currently targets the wrong POST route, so use the curl example below until that script is corrected. Not needed to run the API or tests. |

`python-dotenv` loads `.env`; exported environment variables take precedence. If credentials contain URL-special characters, percent-encode them in the connection URL. Tests override `DATABASE_URL` internally.

### 3. Start PostgreSQL

```sh
docker compose up -d postgres
docker compose exec postgres pg_isready -U sentinel -d sentinel
```

Wait until PostgreSQL reports that it accepts connections. Compose runs PostgreSQL 16, maps host `5431` to container `5432`, and persists data in `sentinel_postgres_data`. Credentials and database name are defined in the Compose file; changing `.env` alone does not change that service's credentials.

For an existing PostgreSQL server, provision a dedicated database/user and point `DATABASE_URL` at it instead. From a container on the Compose network, use `postgres:5432`, not `localhost:5431`.

### 4. Initialize a fresh development database

The API does not create tables at startup. For a **new, empty development database**, create the current model schema:

```sh
python - <<'PY'
from app.database import Base, engine
import app.models.interface_event
import app.models.interface_incident
Base.metadata.create_all(engine)
PY
```

**Migration limitation:** the checked-in Alembic revisions both add the same three lifecycle columns, and the initial revision does not create the base tables. Do not use `alembic upgrade head` as a fresh-install command yet. `create_all` creates missing tables but does not upgrade existing tables; it is not a production migration strategy. Existing databases need a reviewed migration/baseline repair before upgrades. Alembic also currently reads its connection settings separately from `alembic.ini`.

### 5. Run the API

```sh
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- [Interactive API docs](http://127.0.0.1:8000/docs)
- [ReDoc](http://127.0.0.1:8000/redoc)
- [OpenAPI schema](http://127.0.0.1:8000/openapi.json)
- [Health](http://127.0.0.1:8000/health)

`/health` reports process health; it does not check the database. Stop the API with Ctrl+C. `docker compose stop postgres` stops PostgreSQL while retaining its data.

## API usage

Submit an inventory event (use a new `event_id` for each new event):

```sh
curl -sS -X POST http://127.0.0.1:8000/api/v1/interface/event \
  -H 'Content-Type: application/json' \
  -d '{
    "interface_id": "S4-POS-INVENTORY",
    "event_id": "EVT-README-001",
    "store_id": "STORE-101",
    "material_id": "MAT-10001",
    "movement_type": "PHYSICAL_INVENTORY",
    "system_quantity": 100,
    "physical_quantity": 96,
    "unit_price": 12.50,
    "currency": "USD",
    "timestamp": "2026-09-13T10:00:00"
  }'
```

This returns variance `-4`, exposure `50.0`, status `RECONCILIATION_REQUIRED`, and an empty incident list because the master data is valid. To exercise incident detection, send a new event ID with `store_id` set to `STORE-999`. The response includes generated incident IDs for subsequent detail requests.

The current reconciliation response spells the physical quantity key `physcal_quantity`; the input field is correctly named `physical_quantity`. Quantities and unit price must be nonnegative; currency defaults to `USD`. Invalid request schemas return **422** and missing detail records return **404**.

```sh
curl -sS http://127.0.0.1:8000/api/v1/interfaces/events
curl -sS http://127.0.0.1:8000/api/v1/interfaces/events/EVT-README-001
curl -sS http://127.0.0.1:8000/api/v1/interfaces/errors/reconciliation
curl -sS http://127.0.0.1:8000/api/v1/interfaces/metrics
curl -sS 'http://127.0.0.1:8000/api/v1/incidents?status=open&severity=high'
curl -sS http://127.0.0.1:8000/api/v1/incidents/metrics/summary
curl -sS http://127.0.0.1:8000/api/v1/incidents/metrics/errors
# Replace INC-XXXXXXXX with an incident_id returned by the API:
curl -sS http://127.0.0.1:8000/api/v1/incidents/INC-XXXXXXXX
```

Event lists are ordered by event timestamp descending; incident lists by creation time descending. Nullable remediation/resolution fields are returned as null until populated. There is no authentication layer yet, so the local setup binds the API to loopback.

## Testing

```sh
python -m pip install -r requirements-test.txt
python -m pytest -q
python -m pytest -v tests/test_incidents.py
```

No running API, PostgreSQL server, or `.env` is required. The existing 28 tests cover event persistence, default currency, reconciliation thresholds and variance directions, duplicate conflict recovery, error classification, linked incidents, list/detail filters and ordering, nullable fields, metrics, schema validation, lifecycle transitions/timestamps, and database isolation.

`tests/conftest.py` forces `DATABASE_URL=sqlite://` before importing the application. Each test creates the actual ORM tables in a fresh temporary SQLite file with foreign keys enabled. HTTP requests receive separate real database sessions through the `get_db` dependency override; real commits/rollbacks run and fixtures restore overrides afterward. Run the suite in its own pytest process.

SQLite exercises the current portable models, not PostgreSQL-specific locking, migrations, or concurrency. It never truncates or connects to the development database. Add dedicated PostgreSQL integration coverage when introducing database-specific behavior.

## Container and CI → CT → CD

The [GitHub Actions workflow](.github/workflows/ci-ct-cd.yml) runs on pull requests, pushes to `main`, and manual dispatch:

| Stage | Gate | Work |
| --- | --- | --- |
| CI | Workflow start | Install pinned dependencies, `pip check`, syntax compilation, isolated app/OpenAPI import, and Compose validation. No linter is currently configured. |
| CT | CI succeeds | Run the existing pytest suite with its per-test SQLite databases; upload JUnit results for 14 days. |
| CD | CI and CT succeed; ref is `main`; event is not a PR | Build the container, smoke-test health and an actual database-backed endpoint against disposable SQLite, and upload the image archive for 7 days. |

Jobs use read-only repository permissions and no deployment secrets. The CD stage **does not deploy or push to a registry**. It produces a commit-tagged `sap-sentinel-ai-<commit>` artifact containing `sap-sentinel-ai.tar.gz`. Download it from the workflow run and load it with `docker load -i sap-sentinel-ai.tar.gz`.

Build locally:

```sh
docker build -t sap-sentinel-ai:local .
```

The Dockerfile uses Python 3.11 and a non-root user. Its build context allows only runtime inputs, excluding `.env`, Git history, virtual environments, and test artifacts. Database schema initialization is deliberately separate from container startup.

For Docker Desktop, after initializing the development database above:

```sh
docker run --rm -p 127.0.0.1:8000:8000 \
  -e DATABASE_URL=postgresql+psycopg://sentinel:sentinel_dev@host.docker.internal:5431/sentinel \
  sap-sentinel-ai:local
```

On Linux Docker Engine add `--add-host=host.docker.internal:host-gateway`. Stop a locally running Uvicorn first to free port 8000. Container smoke tests in CI use only temporary SQLite and do not touch this PostgreSQL instance.

### Eventual deployment handoff

Replace the final placeholder only after a hosting target is selected:

1. Define the container registry/runtime and a protected GitHub deployment environment.
2. Configure scoped identity (prefer OIDC) or environment secrets; inject the runtime database URL without baking it into the image.
3. Repair and validate migrations on an isolated PostgreSQL database; establish backup and rollback procedures before changing a shared schema.
4. Add the registry push and deployment command after successful CI/CT, retaining the `main` gate. Deploy the validated image by immutable digest.
5. Add authentication, TLS, database readiness checks, and a post-deployment smoke test appropriate to the target.

Workflow action references: [checkout](https://github.com/actions/checkout), [setup-python](https://github.com/actions/setup-python), and [upload-artifact](https://github.com/actions/upload-artifact).

## Repository structure

```text
sap-sentinel-ai/
├── app/
│   ├── main.py                 # FastAPI app, health and event ingestion
│   ├── database.py             # SQLAlchemy engine/session and environment loading
│   ├── api/                    # Event and incident queries/metrics
│   ├── models/                 # Persistent event and incident models
│   ├── schemas/                # Request/response validation
│   └── services/               # Reconciliation, master data, detection, lifecycle
├── simulator/generate_events.py # Sample generator (route needs correction)
├── tests/                      # Isolated ORM/API and lifecycle tests
├── migrations/                 # Alembic revisions (see limitation above)
├── docs/assets/architecture.png
├── .github/workflows/ci-ct-cd.yml
├── Dockerfile
├── .dockerignore
├── docker-compose.yml          # Local PostgreSQL 16
├── alembic.ini
├── pytest.ini
├── requirements.txt            # Pinned dependencies
├── requirements-test.txt       # Test installation entry point
└── README.md
```

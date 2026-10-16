# TeamDesk

TeamDesk is an employee directory built for a DevOps capstone. It connects a React interface to a FastAPI API and PostgreSQL, then delivers the application through tested, scanned Docker images to AWS EKS.

## Scope

Manage employee names, email addresses, departments, job titles, and joining dates. Search and filter the directory, add and edit records, and confirm deletions. This educational application does not include authentication; use synthetic employee records for the demonstration.

## Architecture

```text
Browser → React / Nginx → FastAPI → PostgreSQL
GitHub → tests → frontend build → Docker builds → Trivy → GHCR → Helm → EKS
Terraform → VPC + EKS + worker nodes
FastAPI metrics → Prometheus → Grafana
```

## Local backend development

Requires Python 3.13 and Docker Desktop. From the project root:

```sh
python3.13 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
.venv/bin/python scripts/setup_local.py
docker compose up -d --wait postgres
.venv/bin/python scripts/backend.py migrate
.venv/bin/python scripts/backend.py serve
```

Open http://localhost:8000/docs for interactive Swagger API documentation.
The setup script generates a local password in the ignored `.env` file and preserves existing settings. PostgreSQL is bound to localhost port 5433 and stores application data in the `teamdesk_postgres_data` volume.

| Method | Endpoint | Result |
| --- | --- | --- |
| GET | `/api/employees` | List employees, newest first |
| GET | `/api/employees/{id}` | Retrieve one employee |
| POST | `/api/employees` | Create; returns 201 |
| PUT | `/api/employees/{id}` | Replace editable fields |
| DELETE | `/api/employees/{id}` | Delete; returns 204 |
| GET | `/health` | Process liveness and application version |
| GET | `/ready` | Database/table readiness; returns 503 if unavailable |
| GET | `/metrics` | Prometheus metrics including HTTP requests |

Emails are normalized to lowercase and unique. Invalid input returns 422, duplicate email returns 409, and missing employees return 404. API input rejects unexpected fields. Alembic owns schema changes; the API does not create tables during startup.

## Local frontend development

With the backend running on port 8000, open a second terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. Vite forwards `/api` requests to the local backend. The directory supports search, department filtering, sorting, pagination, and employee creation, editing, and removal. Fonts are served locally with the app.

```sh
npm run build
npm run format:check
```

## Backend checks

```sh
docker compose -f docker-compose.test.yml up -d --wait
.venv/bin/python scripts/backend.py test
.venv/bin/python scripts/backend.py migration-check
.venv/bin/ruff check backend scripts
.venv/bin/ruff format --check backend scripts
```

Tests use a separate PostgreSQL container on localhost port 5434 with database `teamdesk_test`. The fixture refuses a database name without the `_test` suffix, runs actual Alembic migrations, and rolls back a surrounding transaction after every test. This keeps route commits isolated from other tests and from application data. Test storage is temporary.

The 20 cases cover employee CRUD, validation, duplicate email creation/update, missing records, health, readiness, and application metrics.

For a running API, `.venv/bin/python scripts/smoke_backend.py` verifies real HTTP CRUD and removes its synthetic record afterward.

## Implementation status

Backend, migration, local PostgreSQL, automated tests, and the React frontend are working locally. Application images, CI/CD, AWS, Kubernetes, monitoring dashboards, and the final demo are still pending. The current Compose file starts PostgreSQL only; the frontend and backend services will be added during containerization.

## Local cleanup

```sh
docker compose -f docker-compose.test.yml down
docker compose stop
```

Ordinary stop/start preserves the application database. `docker compose down -v` permanently deletes its local database volume; use that only when intentionally resetting the local data.

## Implementation references

- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy session transactions](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [Alembic migrations](https://alembic.sqlalchemy.org/en/latest/tutorial.html)

## Repository

https://github.com/suhaniawasthi10/TeamDesk-

The local SSH remote uses the `github-personal` alias to select the personal GitHub key.

## Evidence

Required submission screenshots will go in `evidence/`. Temporary verification logs stay in the ignored `.local/checks/` folder.

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

## Run with Docker Compose

Start Docker Desktop, then run from the project root:

```sh
python3 scripts/setup_local.py
docker compose up --build
```

Open **http://localhost:3000** for the directory or **http://localhost:3000/docs** for Swagger. To run in the background and wait for health checks, use `docker compose up --build -d --wait`.

| Service | Container port | Local address | Runtime user |
| --- | --- | --- | --- |
| Frontend / Nginx | 8080 | `localhost:3000` | UID 101 |
| FastAPI | 8000 | `localhost:8001` | UID 10001 |
| PostgreSQL | 5432 | `localhost:5433` | PostgreSQL server user |

The frontend uses a multistage Node build and a non-root Nginx runtime. Nginx serves the built site and proxies `/api` and API documentation to the backend. The backend image contains runtime dependencies and migration files. Base images are pinned by digest.

Compose waits for PostgreSQL health, runs `alembic upgrade head` in the single local backend service, and waits for backend readiness before starting the frontend. The backend image itself starts only Uvicorn; cluster migrations will run separately to avoid concurrent migrations across replicas.

The setup script generates a URL-safe database password in ignored `.env`. Preserve that password when reusing the database volume. The `teamdesk_postgres_data` volume retains records across ordinary stop/start operations. No real credentials are included in either image or the repository.

Useful checks:

```sh
docker compose ps
docker compose logs --tail=30 backend frontend
docker compose exec backend id
docker compose exec frontend id
.venv/bin/python scripts/smoke_backend.py --url http://localhost:3000
```

## Run the backend without Docker

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

## Continuous integration

The [TeamDesk CI workflow](.github/workflows/ci.yml) runs on pushes and pull requests to `main`, with a manual run option. Two jobs check the application:

- **Backend tests:** Python 3.13, pinned dependencies, Ruff lint/format checks, and `pytest -v` against a disposable PostgreSQL 17 service. The fixture applies Alembic migrations before running the tests.
- **Frontend build:** Node 24, `npm ci`, formatting checks, and the Vite production build.

Any failing command fails its job. Actions are pinned to verified commit SHAs, and the workflow has read-only repository access. Image scanning and publishing are the next pipeline stage.

## Implementation status

Backend, migrations, tests, frontend, and the full Docker Compose stack are verified locally. Both application containers run as non-root users. HTTP CRUD through Nginx, readiness, metrics, and preservation of all three demo records across a full stop/start were verified. CI/CD, AWS, Kubernetes, monitoring dashboards, and the final demo are still pending.

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
- [Docker Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/)
- [Non-root Nginx image](https://github.com/nginx/docker-nginx-unprivileged)

## Repository

https://github.com/suhaniawasthi10/TeamDesk-

The local SSH remote uses the `github-personal` alias to select the personal GitHub key.

## Evidence

Required submission screenshots will go in `evidence/`. Temporary verification logs stay in the ignored `.local/checks/` folder.

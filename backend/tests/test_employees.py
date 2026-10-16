import pytest


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_checks_migrated_database(client):
    assert client.get("/ready").json() == {"status": "ready"}


def test_create_employee(client, employee):
    response = client.post("/api/employees", json=employee)
    assert response.status_code == 201
    assert response.json().items() >= employee.items()
    assert response.json()["id"] > 0
    assert response.json()["created_at"]


def test_list_employees(client, employee):
    assert client.get("/api/employees").json() == []
    created = client.post("/api/employees", json=employee).json()
    assert client.get("/api/employees").json() == [created]


def test_get_employee(client, employee):
    created = client.post("/api/employees", json=employee).json()
    response = client.get(f"/api/employees/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_update_employee(client, employee):
    created = client.post("/api/employees", json=employee).json()
    changed = {
        **employee,
        "job_title": "Senior Platform Engineer",
        "department": "Infrastructure",
    }
    response = client.put(f"/api/employees/{created['id']}", json=changed)
    assert response.status_code == 200
    assert response.json().items() >= changed.items()
    assert (
        client.get(f"/api/employees/{created['id']}").json()["department"]
        == "Infrastructure"
    )
    assert response.json()["created_at"] == created["created_at"]


def test_delete_employee(client, employee):
    created = client.post("/api/employees", json=employee).json()
    response = client.delete(f"/api/employees/{created['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/employees/{created['id']}").status_code == 404


def test_duplicate_email_case_insensitive(client, employee):
    assert client.post("/api/employees", json=employee).status_code == 201
    duplicate = {**employee, "email": employee["email"].upper()}
    response = client.post("/api/employees", json=duplicate)
    assert response.status_code == 409
    assert len(client.get("/api/employees").json()) == 1


def test_duplicate_update_preserves_existing_record(client, employee):
    client.post("/api/employees", json=employee)
    second = client.post(
        "/api/employees", json={**employee, "email": "second@example.com"}
    ).json()
    response = client.put(f"/api/employees/{second['id']}", json=employee)
    assert response.status_code == 409
    assert (
        client.get(f"/api/employees/{second['id']}").json()["email"]
        == "second@example.com"
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"email": "not-an-email"},
        {"name": "   "},
        {"department": ""},
        {"job_title": "x" * 121},
        {"joining_date": "2026-02-30"},
        {"unexpected": "field"},
    ],
)
def test_invalid_input(client, employee, changes):
    assert (
        client.post("/api/employees", json={**employee, **changes}).status_code == 422
    )
    assert client.get("/api/employees").json() == []


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_missing_employee(client, employee, method):
    kwargs = {"json": employee} if method == "put" else {}
    response = getattr(client, method)("/api/employees/999999", **kwargs)
    assert response.status_code == 404


def test_metrics_exposes_application_requests(client):
    client.get("/api/employees")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "http_requests_total" in response.text


def test_readiness_failure_is_safe(client, monkeypatch):
    from sqlalchemy.exc import OperationalError

    from app import main

    class UnavailableEngine:
        def connect(self):
            raise OperationalError(
                "connection", {}, Exception("private connection details")
            )

    monkeypatch.setattr(main, "get_engine", lambda: UnavailableEngine())
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert client.get("/health").status_code == 200

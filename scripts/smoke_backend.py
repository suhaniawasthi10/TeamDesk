"""Verify a running API through real HTTP requests, leaving no sample record."""

import argparse
from uuid import uuid4

import httpx

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--url", default="http://127.0.0.1:8000")
args = parser.parse_args()

with httpx.Client(base_url=args.url, timeout=10) as client:
    for path in ("/health", "/ready", "/docs", "/metrics"):
        response = client.get(path)
        response.raise_for_status()
        print(f"GET {path}: {response.status_code}")
    employee = {
        "name": "Smoke Check",
        "email": f"smoke-{uuid4().hex}@example.com",
        "department": "Quality",
        "job_title": "Test Engineer",
        "joining_date": "2026-01-12",
    }
    response = client.post("/api/employees", json=employee)
    assert response.status_code == 201, response.text
    employee_id = response.json()["id"]
    path = f"/api/employees/{employee_id}"
    try:
        assert client.get(path).json()["email"] == employee["email"]
        assert any(
            item["id"] == employee_id for item in client.get("/api/employees").json()
        )
        employee["job_title"] = "Senior Test Engineer"
        assert (
            client.put(path, json=employee).json()["job_title"]
            == "Senior Test Engineer"
        )
        assert client.get(path).json()["job_title"] == "Senior Test Engineer"
        print("Live HTTP create, list, retrieve, update: PASS")
    finally:
        assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404
    print("Live HTTP delete and missing-record response: PASS")

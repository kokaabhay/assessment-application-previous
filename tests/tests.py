"""Sample pytest tests for the customer complaint API.

Run from the repository root with:
    pytest tests/tests.py -q
"""

import json

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    """Create a client and run the FastAPI lifespan for each test."""
    with TestClient(app) as test_client:
        yield test_client


def register_and_login(
    client: TestClient,
    role: str,
) -> tuple[dict[str, str], str]:
    """Register a unique test user and return user data and bearer token."""
    email = f"{role.lower()}-{uuid4().hex}@example.com"
    password = "Password123!"
    registered = client.post(
        "/auth/register",
        json={"email": email, "password": password, "role": role},
    )
    assert registered.status_code == 201

    logged_in = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert logged_in.status_code == 200
    token = logged_in.json()["access_token"]
    return registered.json(), {"Authorization": f"Bearer {token}"}


def complaint_payload(subject: str = "Unable to access account") -> dict[str, str]:
    """Return a valid complaint request payload."""
    return {
        "product_id": f"test-product-{uuid4().hex}",
        "category": "Technical",
        "channel": "web",
        "subject": subject,
        "description": "The customer cannot access the application.",
    }


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_customer_can_create_and_list_own_complaints(client: TestClient) -> None:
    user, headers = register_and_login(client, "CUSTOMER")
    created = client.post(
        "/complaints",
        headers=headers,
        json=complaint_payload(),
    )

    assert created.status_code == 201
    assert created.json()["customer_id"] == user["id"]
    assert created.json()["priority"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert created.json()["sla_due_at"]

    listed = client.get("/complaints", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == created.json()["id"] for item in listed.json())


def test_invalid_token_returns_401(client: TestClient) -> None:
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert response.status_code == 401


def test_customer_cannot_read_another_customers_complaint(client: TestClient) -> None:
    _, first_customer_headers = register_and_login(client, "CUSTOMER")
    _, second_customer_headers = register_and_login(client, "CUSTOMER")
    created = client.post(
        "/complaints",
        headers=first_customer_headers,
        json=complaint_payload("Private customer complaint"),
    )

    response = client.get(
        f"/complaints/{created.json()['id']}",
        headers=second_customer_headers,
    )

    assert response.status_code == 403


def test_agent_can_only_open_assigned_complaints(client: TestClient) -> None:
    agent, agent_headers = register_and_login(client, "SUPPORT_AGENT")
    _, admin_headers = register_and_login(client, "ADMIN")
    assigned = client.post(
        "/complaints",
        headers=admin_headers,
        json=complaint_payload("Assigned agent complaint"),
    )
    unassigned = client.post(
        "/complaints",
        headers=admin_headers,
        json=complaint_payload("Unassigned agent complaint"),
    )

    assigned_response = client.patch(
        f"/complaints/{assigned.json()['id']}/assign",
        headers=admin_headers,
        json={"assigned_agent_id": agent["id"]},
    )
    visible = client.get(
        f"/complaints/{assigned.json()['id']}",
        headers=agent_headers,
    )
    forbidden = client.get(
        f"/complaints/{unassigned.json()['id']}",
        headers=agent_headers,
    )

    assert assigned_response.status_code == 200
    assert visible.status_code == 200
    assert forbidden.status_code == 403


def test_manager_cannot_assign_complaint_to_customer_user(client: TestClient) -> None:
    customer, customer_headers = register_and_login(client, "CUSTOMER")
    _, manager_headers = register_and_login(client, "SUPPORT_MANAGER")
    created = client.post(
        "/complaints",
        headers=customer_headers,
        json=complaint_payload("Bad assignment target"),
    )

    response = client.patch(
        f"/complaints/{created.json()['id']}/assign",
        headers=manager_headers,
        json={"assigned_agent_id": customer["id"]},
    )

    assert response.status_code == 400
    assert "support agent" in response.json()["detail"].lower()


def test_customer_cannot_escalate_complaint(client: TestClient) -> None:
    _, customer_headers = register_and_login(client, "CUSTOMER")
    created = client.post(
        "/complaints",
        headers=customer_headers,
        json=complaint_payload("Escalation authorization check"),
    )

    response = client.post(
        f"/complaints/{created.json()['id']}/escalate",
        headers=customer_headers,
        json={"level": 1, "reason": "Need manager review"},
    )

    assert response.status_code == 403


def test_support_dashboard_cache_hit_and_invalidation(client: TestClient) -> None:
    _, customer_headers = register_and_login(client, "CUSTOMER")

    first = client.get("/analytics/support-dashboard", headers=customer_headers)
    second = client.get("/analytics/support-dashboard", headers=customer_headers)
    created = client.post(
        "/complaints",
        headers=customer_headers,
        json=complaint_payload("Cache invalidation check"),
    )
    third = client.get("/analytics/support-dashboard", headers=customer_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert created.status_code == 201
    assert third.status_code == 200
    assert first.json()["cache"] == "MISS"
    assert second.json()["cache"] == "HIT"
    assert third.json()["cache"] == "MISS"


def test_duplicate_complaint_is_rejected(client: TestClient) -> None:
    _, headers = register_and_login(client, "CUSTOMER")
    payload = complaint_payload("Repeated payment issue")

    first = client.post("/complaints", headers=headers, json=payload)
    second = client.post("/complaints", headers=headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 400
    assert "duplicate" in second.json()["detail"].lower()


def test_invalid_customer_workflow_transition_is_rejected(client: TestClient) -> None:
    _, headers = register_and_login(client, "ADMIN")
    created = client.post(
        "/complaints",
        headers=headers,
        json=complaint_payload("Workflow check"),
    )
    complaint_id = created.json()["id"]

    response = client.patch(
        f"/complaints/{complaint_id}/status",
        headers=headers,
        json={"status": "CLOSED"},
    )

    assert response.status_code == 400
    assert "transition" in response.json()["detail"].lower()


def test_authenticated_admin_can_export_csv(client: TestClient) -> None:
    _, headers = register_and_login(client, "ADMIN")

    response = client.get("/complaints/export", headers=headers)

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert response.text.splitlines()[0].startswith("id,customer_id,product_id")


def test_customer_export_json_only_contains_own_complaints(client: TestClient) -> None:
    first_customer, first_headers = register_and_login(client, "CUSTOMER")
    _, second_headers = register_and_login(client, "CUSTOMER")
    own = client.post(
        "/complaints",
        headers=first_headers,
        json=complaint_payload("Own export complaint"),
    )
    other = client.post(
        "/complaints",
        headers=second_headers,
        json=complaint_payload("Other export complaint"),
    )

    response = client.get(
        "/complaints/export",
        headers=first_headers,
        params={"format": "json"},
    )
    data = response.json()
    exported_ids = {item["id"] for item in data["complaints"]}

    assert response.status_code == 200
    assert data["count"] >= 1
    assert own.json()["id"] in exported_ids
    assert other.json()["id"] not in exported_ids
    assert all(item["customer_id"] == first_customer["id"] for item in data["complaints"])


def test_csv_import_job_records_accepted_and_rejected_details(client: TestClient) -> None:
    _, admin_headers = register_and_login(client, "ADMIN")
    csv_body = (
        "product_id,category,channel,subject,description,priority\n"
        f"csv-product-{uuid4().hex},Billing,web,CSV import accepted,Valid complaint body,MEDIUM\n"
        f"csv-product-{uuid4().hex},Billing,web,no,Invalid short subject,MEDIUM\n"
    )

    created = client.post(
        "/complaints/import-job",
        headers=admin_headers,
        files={"file": ("complaints.csv", csv_body.encode(), "text/csv")},
    )
    job = client.get(f"/jobs/{created.json()['job_id']}", headers=admin_headers)
    result = json.loads(job.json()["result"])

    assert created.status_code == 202
    assert job.status_code == 200
    assert job.json()["status"] == "COMPLETED"
    assert job.json()["accepted_count"] == 1
    assert job.json()["rejected_count"] == 1
    assert result["accepted"][0]["row"] == 1
    assert result["rejected"][0]["row"] == 2
    assert "reason" in result["rejected"][0]


def test_json_import_job_records_accepted_and_rejected_details(client: TestClient) -> None:
    _, admin_headers = register_and_login(client, "ADMIN")
    json_body = {
        "complaints": [
            {
                "product_id": f"json-product-{uuid4().hex}",
                "category": "Technical",
                "channel": "web",
                "subject": "JSON import accepted",
                "description": "Valid complaint body",
                "priority": "HIGH",
            },
            {
                "product_id": f"json-product-{uuid4().hex}",
                "category": "Technical",
                "channel": "web",
                "subject": "no",
                "description": "Invalid short subject",
                "priority": "HIGH",
            },
        ]
    }

    created = client.post(
        "/complaints/import-job",
        headers=admin_headers,
        files={"file": ("complaints.json", json.dumps(json_body).encode(), "application/json")},
    )
    job = client.get(f"/jobs/{created.json()['job_id']}", headers=admin_headers)
    result = json.loads(job.json()["result"])

    assert created.status_code == 202
    assert job.status_code == 200
    assert job.json()["status"] == "COMPLETED"
    assert job.json()["accepted_count"] == 1
    assert job.json()["rejected_count"] == 1
    assert result["accepted"][0]["row"] == 1
    assert result["rejected"][0]["row"] == 2

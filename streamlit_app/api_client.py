from typing import Any

import requests


class APIClient:
    """Client for communicating with the FastAPI backend."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None

    def _headers(self) -> dict[str, str]:
        """Build request headers."""

        if not self.token:
            return {}

        return {
            "Authorization": f"Bearer {self.token}",
        }

    def login(
        self,
        email: str,
        password: str,
    ) -> dict[str, Any]:
        """Authenticate the user."""

        response = requests.post(
            f"{self.base_url}/auth/login",
            json={
                "email": email,
                "password": password,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        self.token = data["access_token"]

        return data

    def get_me(self) -> dict[str, Any]:
        """Get the currently authenticated user."""

        response = requests.get(
            f"{self.base_url}/auth/me",
            headers=self._headers(),
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def get_job(
        self,
        job_id: int,
    ) -> dict[str, Any]:
        """Get background job status."""

        response = requests.get(
            f"{self.base_url}/jobs/{job_id}",
            headers=self._headers(),
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def get_complaints(self, **filters: Any) -> list[dict[str, Any]]:
        """Get complaints through the FastAPI service."""
        response = requests.get(f"{self.base_url}/complaints", headers=self._headers(), params=filters, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_support_agents(self) -> list[dict[str, Any]]:
        """Get active support agents and their open complaint workloads."""
        response = requests.get(
            f"{self.base_url}/support-agents",
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def create_complaint(self, data: dict[str, Any]) -> dict[str, Any]:
        """Submit a complaint through the FastAPI service."""
        response = requests.post(f"{self.base_url}/complaints", headers=self._headers(), json=data, timeout=30)
        response.raise_for_status()
        return response.json()

    def update_complaint_status(self, complaint_id: int, status: str, note: str | None = None) -> dict[str, Any]:
        response = requests.patch(f"{self.base_url}/complaints/{complaint_id}/status", headers=self._headers(), json={"status": status, "note": note}, timeout=30)
        response.raise_for_status()
        return response.json()

    def assign_complaint(
        self,
        complaint_id: int,
        assigned_agent_id: int | None,
        assigned_team_id: int | None = None,
    ) -> dict[str, Any]:
        """Assign a complaint to a support team or agent."""
        response = requests.patch(
            f"{self.base_url}/complaints/{complaint_id}/assign",
            headers=self._headers(),
            json={
                "assigned_agent_id": assigned_agent_id,
                "assigned_team_id": assigned_team_id,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def add_note(
        self,
        complaint_id: int,
        text: str,
        visibility: str = "customer",
    ) -> dict[str, Any]:
        """Add a customer-visible or internal complaint note."""
        response = requests.post(
            f"{self.base_url}/complaints/{complaint_id}/notes",
            headers=self._headers(),
            json={
                "text": text,
                "visibility": visibility,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def escalate_complaint(
        self,
        complaint_id: int,
        level: int,
        reason: str,
        assigned_to: int | None = None,
    ) -> dict[str, Any]:
        """Escalate a complaint through the backend workflow."""
        response = requests.post(
            f"{self.base_url}/complaints/{complaint_id}/escalate",
            headers=self._headers(),
            json={
                "level": level,
                "reason": reason,
                "assigned_to": assigned_to,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_support_dashboard(self) -> dict[str, Any]:
        response = requests.get(f"{self.base_url}/analytics/support-dashboard", headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def get_sla_performance(self) -> list[dict[str, Any]]:
        """Get SLA performance grouped by category."""
        response = requests.get(
            f"{self.base_url}/analytics/sla-performance",
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_agent_ranking(self) -> list[dict[str, Any]]:
        """Get manager/admin agent ranking report."""
        response = requests.get(
            f"{self.base_url}/analytics/agent-ranking",
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_trend_summary(self, instruction: str = "") -> dict[str, Any]:
        response = requests.post(f"{self.base_url}/ai/complaint-trend-summary", headers=self._headers(), json={"instruction": instruction}, timeout=120)
        response.raise_for_status()
        return response.json()

    def import_complaints(self, file_bytes: bytes, filename: str) -> dict[str, Any]:
        media_type = "application/json" if filename.lower().endswith(".json") else "text/csv"
        response = requests.post(f"{self.base_url}/complaints/import-job", headers=self._headers(), files={"file": (filename, file_bytes, media_type)}, timeout=60)
        response.raise_for_status()
        return response.json()

    def export_complaints(self, file_format: str = "csv") -> requests.Response:
        response = requests.get(f"{self.base_url}/complaints/export", headers=self._headers(), params={"format": file_format}, timeout=60)
        response.raise_for_status()
        return response

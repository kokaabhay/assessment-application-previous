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

    def create_complaint(self, data: dict[str, Any]) -> dict[str, Any]:
        """Submit a complaint through the FastAPI service."""
        response = requests.post(f"{self.base_url}/complaints", headers=self._headers(), json=data, timeout=30)
        response.raise_for_status()
        return response.json()

    def update_complaint_status(self, complaint_id: int, status: str, note: str | None = None) -> dict[str, Any]:
        response = requests.patch(f"{self.base_url}/complaints/{complaint_id}/status", headers=self._headers(), json={"status": status, "note": note}, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_support_dashboard(self) -> dict[str, Any]:
        response = requests.get(f"{self.base_url}/analytics/support-dashboard", headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def get_trend_summary(self, instruction: str = "") -> dict[str, Any]:
        response = requests.post(f"{self.base_url}/ai/complaint-trend-summary", headers=self._headers(), json={"instruction": instruction}, timeout=120)
        response.raise_for_status()
        return response.json()

    def import_complaints(self, file_bytes: bytes, filename: str) -> dict[str, Any]:
        response = requests.post(f"{self.base_url}/complaints/import-job", headers=self._headers(), files={"file": (filename, file_bytes, "text/csv")}, timeout=60)
        response.raise_for_status()
        return response.json()

    def export_complaints(self) -> requests.Response:
        response = requests.get(f"{self.base_url}/complaints/export", headers=self._headers(), timeout=60)
        response.raise_for_status()
        return response
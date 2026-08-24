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

    def get_contracts(self) -> list[dict[str, Any]]:
        """Get contracts available to the current user."""

        response = requests.get(
            f"{self.base_url}/contracts",
            headers=self._headers(),
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def create_contract(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a contract."""

        response = requests.post(
            f"{self.base_url}/contracts",
            headers=self._headers(),
            json=data,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def delete_contract(
        self,
        contract_id: int,
    ) -> None:
        """Delete a contract."""

        response = requests.delete(
            f"{self.base_url}/contracts/{contract_id}",
            headers=self._headers(),
            timeout=30,
        )

        response.raise_for_status()

    def analyze_contract(
        self,
        contract_id: int,
    ) -> dict[str, Any]:
        """Analyze a contract using the LLM."""

        response = requests.post(
            f"{self.base_url}/contracts/{contract_id}/analyze",
            headers=self._headers(),
            timeout=120,
        )

        response.raise_for_status()

        return response.json()

    def import_contracts(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> dict[str, Any]:
        """Upload a CSV file for contract import."""

        response = requests.post(
            f"{self.base_url}/contracts/import",
            headers=self._headers(),
            files={
                "file": (
                    filename,
                    file_bytes,
                    "text/csv",
                )
            },
            timeout=60,
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

    def export_contracts(
        self,
        export_format: str,
    ) -> requests.Response:
        """Export contracts from the API."""

        response = requests.get(
            f"{self.base_url}/contracts/export",
            headers=self._headers(),
            params={
                "format": export_format,
            },
            timeout=60,
        )

        response.raise_for_status()

        return response
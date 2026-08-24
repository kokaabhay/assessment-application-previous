from typing import Literal

from pydantic import BaseModel, Field


class ContractAnalysis(BaseModel):
    """Structured LLM analysis of a contract."""

    summary: str = Field(
        min_length=1,
        max_length=2000,
    )

    risk_level: Literal[
        "low",
        "medium",
        "high",
    ]

    key_risks: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    recommendations: list[str] = Field(
        default_factory=list,
        max_length=10,
    )
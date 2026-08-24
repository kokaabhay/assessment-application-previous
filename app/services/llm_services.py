import json
import logging
import httpx
from openai import AsyncOpenAI

from app.core.config import settings
from app.db.models import Contract
from app.schemas.llm import ContractAnalysis

logger = logging.getLogger(__name__)
http_client = httpx.AsyncClient(verify=False)

class LLMService:
    """Service for contract-related LLM operations."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            http_client=http_client
        )

    async def analyze_contract(
        self,
        contract: Contract,
    ) -> ContractAnalysis:
        """Generate structured analysis for a contract."""

        prompt = f"""
Analyze the following vendor contract.

Contract title:
{contract.title}

Contract value:
{contract.contract_value}

Current spend:
{contract.spend}

Start date:
{contract.start_date}

End date:
{contract.end_date}

Renewal type:
{contract.renewal_type}

Status:
{contract.status}

Service scope:
{contract.service_scope}

Return JSON with exactly these fields:

{{
    "summary": "string",
    "risk_level": "low | medium | high",
    "key_risks": ["string"],
    "recommendations": ["string"]
}}
"""

        try:
            response = await self.client.chat.completions.create(
                model=settings.llm_model,
                
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a contract analysis assistant. "
                            "Return only valid JSON."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0,
            )

            content = response.choices[0].message.content

            if not content:
                raise ValueError(
                    "LLM returned an empty response."
                )

            data = json.loads(content)

            return ContractAnalysis.model_validate(data)

        except Exception:
            logger.exception(
                "Contract LLM analysis failed."
            )
            raise
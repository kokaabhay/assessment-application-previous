import logging
import httpx
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)
http_client = httpx.AsyncClient(verify=False)

class LLMService:
    """Service for complaint trend narrative generation."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            http_client=http_client
        )

    async def generate_text(self, prompt: str) -> str:
        """Generate plain text for computed support metrics."""
        response = await self.client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "system", "content": "You are a concise support operations analyst. Don't provide made up info only provide existing ones"}, {"role": "user", "content": prompt}],
            temperature=0,
        )
        return response.choices[0].message.content or "Currently no summary has returned."


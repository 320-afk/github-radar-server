"""MiniMax M3 API Client."""
import os
from typing import AsyncIterator, Optional

import httpx


class MiniMaxClient:
    """MiniMax M3 API client with streaming support."""

    BASE_URL = "https://api.minimaxi.com/v1"
    DEFAULT_MODEL = "MiniMax-Text-01"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY", "")
        self.base_url = self.BASE_URL
        self.model = self.DEFAULT_MODEL

    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    async def chat(
        self,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.3,
        stream: bool = False,
    ) -> dict | AsyncIterator[dict]:
        """Send chat request to MiniMax API."""
        if not self.is_configured():
            raise ValueError("MINIMAX_API_KEY not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/text/chatcompletion_v2",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def chat_stream(
        self,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> AsyncIterator[str]:
        """Send streaming chat request, yield content chunks."""
        if not self.is_configured():
            raise ValueError("MINIMAX_API_KEY not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/text/chatcompletion_v2",
                headers=headers,
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        import json
                        try:
                            chunk = json.loads(data)
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

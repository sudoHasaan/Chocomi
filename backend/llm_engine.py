import json
from collections.abc import AsyncGenerator

import httpx

from config import settings


async def stream_response(messages: list[dict]) -> AsyncGenerator[str, None]:
    url = f"{settings.ollamaBaseUrl}/api/chat"
    payload = {
        "model": settings.ollamaModel,
        "messages": messages,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token
                if chunk.get("done"):
                    break
"""Native Google search backend."""
from __future__ import annotations

import os
from typing import Any

import aiohttp


class LitescrapeBackend:
    """Google search with the existing WebSearchTool result contract."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = 30,
    ) -> None:
        self._api_key = api_key or os.environ.get("LITESCRAPE_API_KEY", "")
        self._base_url = (
            base_url
            or os.environ.get("LITESCRAPE_BASE_URL")
            or "https://api.litescrape.com"
        ).rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def search(
        self,
        query: str,
        *,
        num: int = 10,
        start: int = 0,
        engine: str = "google",
    ) -> list[dict[str, Any]]:
        """Return organic results; reject unsupported engines and result counts."""
        if not self._api_key:
            raise ValueError("LITESCRAPE_API_KEY is required")
        if engine != "google":
            raise ValueError("This backend supports only the google engine")
        if not 1 <= num <= 10 or start < 0:
            raise ValueError("Unsupported result count or pagination offset")
        payload = {"q": query, "num": num}
        payload["start"] = start
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.get(
                self._base_url + "/api/google/search",
                params=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
            ) as response:
                response.raise_for_status()
                data = await response.json()
        results: list[dict[str, Any]] = []
        for item in data.get("organic_results", [])[:num]:
            snippet = item.get("snippet", "")
            results.append({
                "position": item.get("position", 0),
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "description": snippet,
                "snippets": [snippet] if snippet else [],
            })
        return results

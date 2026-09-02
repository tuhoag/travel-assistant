"""Direct MCP client call to the hotels search server. Not LangChain
tool-calling — detect_intent already decided this lane runs, so there's no
LLM choice to make here, just a plain async function wrapping the MCP
protocol (same client pattern verified against mcp-hotels directly)."""

from __future__ import annotations

import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from .config import MCP_HOTELS_URL


async def call_search_hotels(
    city: str,
    max_price: float | None = None,
    min_stars: int | None = None,
    amenities: list[str] | None = None,
) -> list[dict]:
    """Call mcp-hotels' search_hotels tool, returning the parsed hotel results."""
    async with streamable_http_client(MCP_HOTELS_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "search_hotels",
                {
                    "city": city,
                    "max_price": max_price,
                    "min_stars": min_stars,
                    "amenities": amenities,
                },
            )
            return [json.loads(c.text) for c in result.content if hasattr(c, "text")]

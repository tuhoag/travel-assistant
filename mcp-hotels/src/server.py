"""MCP server exposing hotel search as a tool, backed by Postgres (db.py).

Usage:
    uv run python -m src.server
"""

from __future__ import annotations

import re

from mcp.server.mcpserver import MCPServer

from . import config, db

mcp = MCPServer("hotels")


def _slugify_city(city: str) -> str:
    """Best-effort match to the fixed city_slug values in the data (e.g.
    "Washington, D.C." -> "washington_dc"). Not a real city registry —
    unrecognized/misspelled city names just won't match any rows."""
    normalized = re.sub(r"[^\w\s]", "", city.strip().lower())
    return re.sub(r"\s+", "_", normalized)


@mcp.tool()
def search_hotels(
    city: str,
    max_price: float | None = None,
    min_stars: int | None = None,
    amenities: list[str] | None = None,
) -> list[dict]:
    """Search hotels in a given city. Optionally filter by max nightly room
    price, minimum star rating, and a list of required amenities (a hotel
    must have ALL of them, not just any). Returns up to 20 hotels, best-rated
    first, each with address, description, star rating, images, amenities,
    and available rooms with pricing."""
    return db.search_hotels_query(
        city_slug=_slugify_city(city),
        max_price=max_price,
        min_stars=min_stars,
        amenities=amenities,
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host=config.MCP_HOST, port=config.MCP_PORT)

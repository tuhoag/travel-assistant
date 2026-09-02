from __future__ import annotations

from typing import Any

from langgraph.graph import END

from src.prompt_registry import prompt_registry

from ..config import MAX_REVISIONS
from ..mcp_client import call_search_hotels
from ..state import HotelParams, State
from .schemas import HotelSearchParams, Reflection
from .shared import _feedback_section
from .structured_output import _plain_call, _structured_call


def _format_hotel_params(params: HotelParams) -> str:
    parts = [f"city={params['city']}"]
    if params.get("max_price") is not None:
        parts.append(f"max_price={params['max_price']}")
    if params.get("min_stars") is not None:
        parts.append(f"min_stars={params['min_stars']}")
    if params.get("amenities"):
        parts.append(f"amenities={', '.join(params['amenities'])}")
    return ", ".join(parts)


async def extract_hotel_params(state: State) -> dict[str, Any]:
    messages = prompt_registry.get("extract_hotel_params").invoke({"query": state["query"]})
    params = await _structured_call(HotelSearchParams, messages)
    hotel_params: HotelParams = {
        "city": params.city,
        "max_price": params.max_price,
        "min_stars": params.min_stars,
        "amenities": params.amenities,
    }
    return {"hotel_params": hotel_params}


async def search_hotels_node(state: State) -> dict[str, Any]:
    params = state["hotel_params"]
    hotels = await call_search_hotels(
        city=params["city"],
        max_price=params.get("max_price"),
        min_stars=params.get("min_stars"),
        amenities=params.get("amenities"),
    )
    return {"hotels": hotels}


async def generate_hotel_answer(state: State) -> dict[str, Any]:
    messages = prompt_registry.get("generate_hotel").invoke({
        "query": state["query"],
        "hotel_params": _format_hotel_params(state["hotel_params"]),
        "hotel_count": len(state["hotels"]),
        "feedback_section": _feedback_section(state.get("hotel_feedback")),
    })
    return {"hotel_answer": await _plain_call(messages)}


async def reflect_hotel_answer(state: State) -> dict[str, Any]:
    messages = prompt_registry.get("reflect_hotel").invoke({
        "hotel_params": _format_hotel_params(state["hotel_params"]),
        "hotel_count": len(state["hotels"]),
        "draft_answer": state["hotel_answer"],
    })
    reflection = await _structured_call(Reflection, messages)

    revision_count = state.get("hotel_revision_count", 0)
    if reflection.passes or revision_count >= MAX_REVISIONS:
        return {"hotel_feedback": None}
    return {"hotel_revision_count": revision_count + 1, "hotel_feedback": reflection.feedback}


def route_hotel_reflection(state: State) -> str:
    if state.get("hotel_feedback"):
        return "generate_hotel_answer"
    return END

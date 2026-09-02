"""Entry-level node and helper shared by both lanes — detect_intent decides
both flags at once (not lane-specific), and _feedback_section formats the
same "previous attempt's feedback" block both generate_* nodes use."""

from __future__ import annotations

from typing import Any

from src.prompt_registry import prompt_registry

from ..state import State
from .schemas import Intent
from .structured_output import _structured_call


async def detect_intent(state: State) -> dict[str, Any]:
    """Classify whether the query needs city info, hotel search, or both."""
    messages = prompt_registry.get("detect_intent").invoke({"query": state["query"]})
    intent = await _structured_call(Intent, messages)
    return {"city_search": intent.city_search, "hotel_search": intent.hotel_search}


def _feedback_section(feedback: str | None) -> str:
    if not feedback:
        return ""
    return f"\nPrevious attempt's feedback (address this): {feedback}"

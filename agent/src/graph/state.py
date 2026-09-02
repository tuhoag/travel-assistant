from typing import TypedDict

from langchain_core.documents import Document


class HotelParams(TypedDict, total=False):
    city: str
    max_price: float | None
    min_stars: int | None
    amenities: list[str] | None


class State(TypedDict, total=False):
    """Input/output state for the agent. Not every field is populated on
    every run — only the lane(s) detect_intent routes to fill in their own
    fields; the other lane's fields are simply absent."""

    query: str

    # detect_intent's output — either or both can be true
    city_search: bool
    hotel_search: bool

    # city lane
    chunks: list[Document]
    city_answer: str
    city_revision_count: int
    city_feedback: str | None

    # hotel lane
    hotel_params: HotelParams
    hotels: list[dict]
    hotel_answer: str
    hotel_revision_count: int
    hotel_feedback: str | None

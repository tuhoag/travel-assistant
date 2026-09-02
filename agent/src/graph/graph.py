"""Travel assistant agent: detect_intent routes to independent city-search
and hotel-search lanes (either or both can fire), each ending in a bounded
reflect-and-revise loop rather than converging into one shared generate step."""

from langgraph.graph import END, START, StateGraph

from .nodes import (
    check_city_coverage,
    city_not_found,
    detect_intent,
    extract_hotel_params,
    generate_city_answer,
    generate_hotel_answer,
    reflect_city_answer,
    reflect_hotel_answer,
    retrieve_chunks_node,
    route_after_retrieve,
    route_city_reflection,
    route_hotel_reflection,
    search_hotels_node,
)
from .state import State


def _route_intents(state: State) -> list[str]:
    """Fan out to whichever lane(s) detect_intent flagged. detect_intent's
    prompt defaults to city_search=true for off-topic/ambiguous queries, so
    this shouldn't return empty in practice."""
    targets = []
    if state.get("city_search"):
        targets.append("retrieve_chunks")
    if state.get("hotel_search"):
        targets.append("extract_hotel_params")
    return targets


graph = (
    StateGraph(State)
    .add_node("detect_intent", detect_intent)
    .add_node("retrieve_chunks", retrieve_chunks_node)
    .add_node("check_city_coverage", check_city_coverage)
    .add_node("city_not_found", city_not_found)
    .add_node("generate_city_answer", generate_city_answer)
    .add_node("reflect_city_answer", reflect_city_answer)
    .add_node("extract_hotel_params", extract_hotel_params)
    .add_node("search_hotels", search_hotels_node)
    .add_node("generate_hotel_answer", generate_hotel_answer)
    .add_node("reflect_hotel_answer", reflect_hotel_answer)
    .add_edge(START, "detect_intent")
    .add_conditional_edges("detect_intent", _route_intents, ["retrieve_chunks", "extract_hotel_params"])
    .add_edge("retrieve_chunks", "check_city_coverage")
    .add_conditional_edges("check_city_coverage", route_after_retrieve, ["generate_city_answer", "city_not_found"])
    .add_edge("city_not_found", END)
    .add_edge("generate_city_answer", "reflect_city_answer")
    .add_conditional_edges("reflect_city_answer", route_city_reflection, ["generate_city_answer", END])
    .add_edge("extract_hotel_params", "search_hotels")
    .add_edge("search_hotels", "generate_hotel_answer")
    .add_edge("generate_hotel_answer", "reflect_hotel_answer")
    .add_conditional_edges("reflect_hotel_answer", route_hotel_reflection, ["generate_hotel_answer", END])
    .compile(name="Travel Assistant Agent")
)

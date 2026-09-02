import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from langgraph.graph import END

from graph.nodes.hotel import (
    extract_hotel_params,
    generate_hotel_answer,
    reflect_hotel_answer,
    route_hotel_reflection,
    search_hotels_node,
)
from graph.nodes.schemas import HotelSearchParams, Reflection


def run(coro):
    return asyncio.run(coro)


def test_extract_hotel_params_returns_typed_dict():
    state = {"query": "find me a hotel in Paris under 400 with a pool"}

    with patch("graph.nodes.hotel._structured_call") as mock_call:
        mock_call.return_value = HotelSearchParams(city="paris", max_price=400.0, min_stars=None, amenities=["pool"])
        result = run(extract_hotel_params(state))

    assert result == {
        "hotel_params": {"city": "paris", "max_price": 400.0, "min_stars": None, "amenities": ["pool"]}
    }


def test_search_hotels_node_calls_mcp_with_extracted_params():
    state = {"hotel_params": {"city": "paris", "max_price": 400.0, "min_stars": None, "amenities": ["pool"]}}
    fake_hotels = [{"id": 1, "name": "Ritz Paris"}]

    with patch("graph.nodes.hotel.call_search_hotels", new=AsyncMock(return_value=fake_hotels)) as mock_call:
        result = run(search_hotels_node(state))

    mock_call.assert_called_once_with(city="paris", max_price=400.0, min_stars=None, amenities=["pool"])
    assert result == {"hotels": fake_hotels}


def test_generate_hotel_answer_reports_zero_results():
    state = {
        "query": "find me a hotel in Nowhereland",
        "hotel_params": {"city": "nowhereland"},
        "hotels": [],
    }

    with patch("graph.nodes.hotel.get_chat_model") as mock_get_chat_model:
        mock_get_chat_model.return_value.ainvoke = AsyncMock(
            return_value=MagicMock(content="No hotels found matching your criteria.")
        )
        result = run(generate_hotel_answer(state))

    assert result == {"hotel_answer": "No hotels found matching your criteria."}
    prompt_arg = mock_get_chat_model.return_value.ainvoke.call_args[0][0].to_string()
    assert "Results found: 0" in prompt_arg


def test_reflect_hotel_answer_passes_clears_feedback():
    state = {
        "hotel_params": {"city": "paris"},
        "hotels": [{"id": 1, "name": "Ritz Paris"}],
        "hotel_answer": "Found 1 hotel in Paris.",
    }

    with patch("graph.nodes.hotel._structured_call") as mock_call:
        mock_call.return_value = Reflection(passes=True, feedback=None)
        result = run(reflect_hotel_answer(state))

    assert result == {"hotel_feedback": None}


def test_route_hotel_reflection_loops_back_on_feedback():
    assert route_hotel_reflection({"hotel_feedback": "fix this"}) == "generate_hotel_answer"


def test_route_hotel_reflection_ends_without_feedback():
    assert route_hotel_reflection({"hotel_feedback": None}) == END

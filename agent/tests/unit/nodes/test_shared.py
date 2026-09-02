import asyncio
from unittest.mock import patch

from graph.nodes.schemas import Intent
from graph.nodes.shared import detect_intent


def run(coro):
    return asyncio.run(coro)


def test_detect_intent_returns_both_flags():
    state = {"query": "tell me about Berlin and find me a hotel there"}
    with patch("graph.nodes.shared._structured_call") as mock_call:
        mock_call.return_value = Intent(city_search=True, hotel_search=True)
        result = run(detect_intent(state))

    assert result == {"city_search": True, "hotel_search": True}

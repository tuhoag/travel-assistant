import asyncio

import pytest

from graph import graph


@pytest.mark.integration
def test_graph_answers_about_a_city():
    """Runs the real detect_intent -> city lane against a live OpenSearch + Bedrock backend."""
    result = asyncio.run(graph.ainvoke({"query": "what is berlin?"}))

    assert result["city_search"] is True
    assert result["chunks"], "expected at least one retrieved chunk from OpenSearch"
    assert "berlin" in result["city_answer"].lower()


@pytest.mark.integration
def test_graph_finds_hotels():
    """Runs the real detect_intent -> hotel lane against a live mcp-hotels + Bedrock backend."""
    result = asyncio.run(graph.ainvoke({"query": "find me a hotel in Paris under 500"}))

    assert result["hotel_search"] is True
    assert result["hotels"], "expected at least one hotel from mcp-hotels"
    assert all(room["price"] <= 500 for hotel in result["hotels"] for room in hotel["rooms"])


@pytest.mark.integration
def test_graph_answers_both_in_one_turn():
    """The core multi-tool-dispatch requirement: a single query needing
    both city info and hotel search gets both, in the same run, and the
    city answer stays scoped to the city (doesn't refuse just because the
    hotel part isn't in its context)."""
    result = asyncio.run(graph.ainvoke({"query": "tell me about Paris and find me a hotel there under 500"}))

    assert result["city_search"] is True
    assert result["hotel_search"] is True
    assert "paris" in result["city_answer"].lower()
    assert "don't know" not in result["city_answer"].lower()
    assert result["hotels"], "expected at least one hotel from mcp-hotels"

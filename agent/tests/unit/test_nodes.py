import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from langgraph.graph import END

from graph.nodes import (
    HotelSearchParams,
    Intent,
    Reflection,
    _strip_code_fence,
    _structured_call,
    detect_intent,
    extract_hotel_params,
    generate_city_answer,
    generate_hotel_answer,
    reflect_city_answer,
    reflect_hotel_answer,
    retrieve_chunks_node,
    route_city_reflection,
    route_hotel_reflection,
    search_hotels_node,
)


def run(coro):
    return asyncio.run(coro)


# ---- _strip_code_fence / _structured_call ----


def test_strip_code_fence_removes_fenced_block():
    text = "```yaml\npasses: true\nfeedback: null\n```"
    assert _strip_code_fence(text) == "passes: true\nfeedback: null"


def test_strip_code_fence_passes_through_unfenced_text():
    text = "passes: true\nfeedback: null"
    assert _strip_code_fence(text) == text


def test_structured_call_parses_yaml_response():
    with patch("graph.nodes.get_chat_model") as mock_get_chat_model:
        mock_get_chat_model.return_value.ainvoke = AsyncMock(
            return_value=MagicMock(content="passes: true\nfeedback: null")
        )
        result = run(_structured_call(Reflection, "irrelevant messages"))

    assert result == Reflection(passes=True, feedback=None)


# ---- detect_intent ----


def test_detect_intent_returns_both_flags():
    state = {"query": "tell me about Berlin and find me a hotel there"}
    with patch("graph.nodes._structured_call") as mock_call:
        mock_call.return_value = Intent(city_search=True, hotel_search=True)
        result = run(detect_intent(state))

    assert result == {"city_search": True, "hotel_search": True}


# ---- City lane ----


def test_retrieve_chunks_node_calls_retrieve_chunks_with_query():
    fake_chunks = [MagicMock(page_content="chunk 1")]
    state = {"query": "What is Paris?"}

    with patch("graph.nodes.retrieve_chunks") as mock_retrieve_chunks:
        mock_retrieve_chunks.return_value = fake_chunks
        result = run(retrieve_chunks_node(state))

    mock_retrieve_chunks.assert_called_once_with("What is Paris?")
    assert result == {"chunks": fake_chunks}


def test_generate_city_answer_uses_retrieved_context():
    fake_chunk = MagicMock(page_content="Berlin is the capital of Germany.")
    state = {"query": "What is Berlin?", "chunks": [fake_chunk]}

    with patch("graph.nodes.get_chat_model") as mock_get_chat_model:
        mock_get_chat_model.return_value.ainvoke = AsyncMock(
            return_value=MagicMock(content="Berlin is Germany's capital.")
        )
        result = run(generate_city_answer(state))

    assert result == {"city_answer": "Berlin is Germany's capital."}

    prompt_arg = mock_get_chat_model.return_value.ainvoke.call_args[0][0].to_string()
    assert "Berlin is the capital of Germany." in prompt_arg
    assert "What is Berlin?" in prompt_arg


def test_generate_city_answer_includes_feedback_on_revision():
    state = {
        "query": "What is Berlin?",
        "chunks": [MagicMock(page_content="Berlin info")],
        "city_feedback": "Be more specific about the population.",
    }

    with patch("graph.nodes.get_chat_model") as mock_get_chat_model:
        mock_get_chat_model.return_value.ainvoke = AsyncMock(return_value=MagicMock(content="revised answer"))
        run(generate_city_answer(state))

    prompt_arg = mock_get_chat_model.return_value.ainvoke.call_args[0][0].to_string()
    assert "Be more specific about the population." in prompt_arg


def test_reflect_city_answer_passes_clears_feedback():
    state = {
        "query": "What is Berlin?",
        "chunks": [MagicMock(page_content="Berlin info")],
        "city_answer": "Berlin is the capital of Germany.",
    }

    with patch("graph.nodes._structured_call") as mock_call:
        mock_call.return_value = Reflection(passes=True, feedback=None)
        result = run(reflect_city_answer(state))

    assert result == {"city_feedback": None}


def test_reflect_city_answer_fails_requests_revision_within_budget():
    state = {
        "query": "What is Berlin?",
        "chunks": [MagicMock(page_content="Berlin info")],
        "city_answer": "I don't know.",
        "city_revision_count": 0,
    }

    with patch("graph.nodes._structured_call") as mock_call:
        mock_call.return_value = Reflection(passes=False, feedback="Answer is available in context.")
        result = run(reflect_city_answer(state))

    assert result == {"city_revision_count": 1, "city_feedback": "Answer is available in context."}


def test_reflect_city_answer_accepts_once_max_revisions_hit():
    state = {
        "query": "What is Berlin?",
        "chunks": [MagicMock(page_content="Berlin info")],
        "city_answer": "still not great",
        "city_revision_count": 2,  # == MAX_REVISIONS
    }

    with patch("graph.nodes._structured_call") as mock_call:
        mock_call.return_value = Reflection(passes=False, feedback="still failing")
        result = run(reflect_city_answer(state))

    # accepted as-is despite failing, since the retry budget is exhausted
    assert result == {"city_feedback": None}


def test_route_city_reflection_loops_back_on_feedback():
    assert route_city_reflection({"city_feedback": "fix this"}) == "generate_city_answer"


def test_route_city_reflection_ends_without_feedback():
    assert route_city_reflection({"city_feedback": None}) == END


# ---- Hotel lane ----


def test_extract_hotel_params_returns_typed_dict():
    state = {"query": "find me a hotel in Paris under 400 with a pool"}

    with patch("graph.nodes._structured_call") as mock_call:
        mock_call.return_value = HotelSearchParams(city="paris", max_price=400.0, min_stars=None, amenities=["pool"])
        result = run(extract_hotel_params(state))

    assert result == {
        "hotel_params": {"city": "paris", "max_price": 400.0, "min_stars": None, "amenities": ["pool"]}
    }


def test_search_hotels_node_calls_mcp_with_extracted_params():
    state = {"hotel_params": {"city": "paris", "max_price": 400.0, "min_stars": None, "amenities": ["pool"]}}
    fake_hotels = [{"id": 1, "name": "Ritz Paris"}]

    with patch("graph.nodes.call_search_hotels", new=AsyncMock(return_value=fake_hotels)) as mock_call:
        result = run(search_hotels_node(state))

    mock_call.assert_called_once_with(city="paris", max_price=400.0, min_stars=None, amenities=["pool"])
    assert result == {"hotels": fake_hotels}


def test_generate_hotel_answer_reports_zero_results():
    state = {
        "query": "find me a hotel in Nowhereland",
        "hotel_params": {"city": "nowhereland"},
        "hotels": [],
    }

    with patch("graph.nodes.get_chat_model") as mock_get_chat_model:
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

    with patch("graph.nodes._structured_call") as mock_call:
        mock_call.return_value = Reflection(passes=True, feedback=None)
        result = run(reflect_hotel_answer(state))

    assert result == {"hotel_feedback": None}


def test_route_hotel_reflection_loops_back_on_feedback():
    assert route_hotel_reflection({"hotel_feedback": "fix this"}) == "generate_hotel_answer"


def test_route_hotel_reflection_ends_without_feedback():
    assert route_hotel_reflection({"hotel_feedback": None}) == END

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from langgraph.graph import END

from graph.nodes.city import (
    check_city_coverage,
    city_not_found,
    generate_city_answer,
    reflect_city_answer,
    retrieve_chunks_node,
    route_after_retrieve,
    route_city_reflection,
)
from graph.nodes.schemas import CoverageCheck, Reflection


def run(coro):
    return asyncio.run(coro)


def test_retrieve_chunks_node_calls_retrieve_chunks_with_query():
    fake_chunks = [MagicMock(page_content="chunk 1")]
    state = {"query": "What is Paris?"}

    with patch("graph.nodes.city.retrieve_chunks") as mock_retrieve_chunks:
        mock_retrieve_chunks.return_value = fake_chunks
        result = run(retrieve_chunks_node(state))

    mock_retrieve_chunks.assert_called_once_with("What is Paris?")
    assert result == {"chunks": fake_chunks}


def test_check_city_coverage_returns_covered_flag():
    state = {
        "query": "what is sydney?",
        "chunks": [MagicMock(page_content="Canberra info", metadata={"title": "Canberra"})],
    }

    with patch("graph.nodes.city._structured_call") as mock_call:
        mock_call.return_value = CoverageCheck(covered=False)
        result = run(check_city_coverage(state))

    assert result == {"city_covered": False}


def test_city_not_found_returns_a_fixed_answer_with_no_llm_call():
    """Deterministic path — no model call at all, so this can never be
    talked into hallucinating an answer the way generate_city_answer was."""
    result = run(city_not_found({}))
    assert result == {"city_answer": "I don't know. I don't have information about that city."}


def test_route_after_retrieve_goes_to_generate_when_covered():
    assert route_after_retrieve({"city_covered": True}) == "generate_city_answer"


def test_route_after_retrieve_goes_to_not_found_when_uncovered():
    assert route_after_retrieve({"city_covered": False}) == "city_not_found"


def test_generate_city_answer_uses_retrieved_context():
    fake_chunk = MagicMock(page_content="Berlin is the capital of Germany.")
    state = {"query": "What is Berlin?", "chunks": [fake_chunk]}

    with patch("graph.nodes.city.get_chat_model") as mock_get_chat_model:
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

    with patch("graph.nodes.city.get_chat_model") as mock_get_chat_model:
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

    with patch("graph.nodes.city._structured_call") as mock_call:
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

    with patch("graph.nodes.city._structured_call") as mock_call:
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

    with patch("graph.nodes.city._structured_call") as mock_call:
        mock_call.return_value = Reflection(passes=False, feedback="still failing")
        result = run(reflect_city_answer(state))

    # accepted as-is despite failing, since the retry budget is exhausted
    assert result == {"city_feedback": None}


def test_route_city_reflection_loops_back_on_feedback():
    assert route_city_reflection({"city_feedback": "fix this"}) == "generate_city_answer"


def test_route_city_reflection_ends_without_feedback():
    assert route_city_reflection({"city_feedback": None}) == END

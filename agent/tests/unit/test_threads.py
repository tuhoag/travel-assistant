from unittest.mock import MagicMock, patch


def test_thread_chat_returns_answer(client):
    """Happy path: a chunk was actually retrieved, and the (mocked) model's
    answer makes it all the way back through graph.invoke() and the route's
    response shaping to the HTTP response. Both retrieve_chunks and
    get_chat_model are mocked so this never touches real Qdrant or a real
    LLM — it's checking the route's wiring, not model quality.
    """
    fake_chunk = MagicMock(page_content="Berlin is the capital of Germany.", metadata={})

    with (
        patch("graph.nodes.retrieve_chunks") as mock_retrieve_chunks,
        patch("graph.nodes.get_chat_model") as mock_get_chat_model,
    ):
        mock_retrieve_chunks.return_value = [fake_chunk]
        mock_get_chat_model.return_value.invoke.return_value.content = "Berlin is the capital of Germany."
        response = client.post(
            "/threads/abc123/chat",
            json={"assistant_id": "agent", "input": {"query": "what is berlin?"}},
        )

    assert response.status_code == 200
    assert response.json()["answer"] == "Berlin is the capital of Germany."


def test_thread_chat_with_no_chunks_returns_dont_know(client):
    """When nothing is retrieved, the wiring should faithfully pass through
    whatever the model says (here, mocked as "I don't know") rather than
    fabricating an answer. Whether a *real* model actually follows the
    "say you don't know" instruction from an empty context is a property of
    the real LLM, not something a mocked unit test can verify — that's
    covered by the RAG-correctness checks in evaluate.py / evals/questions.csv
    and belongs in an integration test, not here.
    """
    with (
        patch("graph.nodes.retrieve_chunks") as mock_retrieve_chunks,
        patch("graph.nodes.get_chat_model") as mock_get_chat_model,
    ):
        mock_retrieve_chunks.return_value = []
        mock_get_chat_model.return_value.invoke.return_value.content = "I don't know."
        response = client.post(
            "/threads/abc123/chat",
            json={"assistant_id": "agent", "input": {"query": "what is the capital of Atlantis?"}},
        )

    assert response.status_code == 200
    assert response.json()["answer"] == "I don't know."
    assert response.json()["chunks"] == []


def test_thread_chat_serializes_chunks_to_plain_dicts(client):
    """The graph works with Document-like objects (attribute access:
    c.page_content, c.metadata), but those aren't JSON-serializable as-is.
    This checks the route's own conversion step (threads.py's dict
    comprehension) turns them into plain {page_content, metadata} dicts
    with the exact content preserved, surviving a real HTTP JSON round-trip
    via response.json() rather than just an in-memory equality check.
    """
    fake_chunk = MagicMock(page_content="Berlin is a city.", metadata={"source": "berlin.md"})

    with (
        patch("graph.nodes.retrieve_chunks") as mock_retrieve_chunks,
        patch("graph.nodes.get_chat_model") as mock_get_chat_model,
    ):
        mock_retrieve_chunks.return_value = [fake_chunk]
        mock_get_chat_model.return_value.invoke.return_value.content = "some answer"
        response = client.post(
            "/threads/abc123/chat",
            json={"assistant_id": "agent", "input": {"query": "what is berlin?"}},
        )

    assert response.json()["chunks"] == [
        {"page_content": "Berlin is a city.", "metadata": {"source": "berlin.md"}}
    ]


def test_thread_chat_rejects_unknown_assistant_id(client):
    """The assistant_id check happens before graph.invoke() is ever called,
    so this needs no mocking at all — a wrong assistant_id should 404
    without touching Qdrant or the chat model, and it should do so cheaply
    (no wasted graph run) rather than running the pipeline and discarding
    the result.
    """
    response = client.post(
        "/threads/abc123/chat",
        json={"assistant_id": "wrong-agent", "input": {"query": "hi"}},
    )
    assert response.status_code == 404


def test_thread_chat_requires_assistant_id_and_input(client):
    """An empty body fails Pydantic's ThreadChatRequest validation
    (assistant_id/input have no defaults, so both are required) before
    FastAPI ever calls thread_chat() — confirms the route's own request
    schema is doing its job, distinct from the assistant_id logic check
    above, which happens inside the handler after validation succeeds.
    """
    response = client.post("/threads/abc123/chat", json={})
    assert response.status_code == 422

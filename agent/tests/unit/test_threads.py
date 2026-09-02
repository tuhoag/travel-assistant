from unittest.mock import AsyncMock, patch


def test_thread_chat_combines_city_and_hotel_answers(client):
    """Route-level test: mocks the whole graph's ainvoke() rather than every
    internal node (those are covered individually in test_nodes.py) — this
    checks the route's own job: assistant_id gating, response assembly, and
    chunk/hotel serialization.
    """
    fake_result = {
        "query": "tell me about Paris and find me a hotel there",
        "city_answer": "Paris is the capital of France.",
        "chunks": [type("Doc", (), {"page_content": "Paris info", "metadata": {"source": "paris.md"}})()],
        "hotel_answer": "Found 1 hotel in Paris.",
        "hotels": [{"id": 1, "name": "Ritz Paris"}],
    }

    with patch("src.routes.threads.graph") as mock_graph:
        mock_graph.ainvoke = AsyncMock(return_value=fake_result)
        response = client.post(
            "/threads/abc123/chat",
            json={"assistant_id": "agent", "input": {"query": "tell me about Paris and find me a hotel there"}},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Paris is the capital of France.\n\nFound 1 hotel in Paris."
    assert body["chunks"] == [{"page_content": "Paris info", "metadata": {"source": "paris.md"}}]
    assert body["hotels"] == [{"id": 1, "name": "Ritz Paris"}]


def test_thread_chat_city_only_omits_hotels_key(client):
    """When only the city lane ran, the response shouldn't carry a hotels
    key at all (not an empty list) — the frontend uses its presence to
    decide whether to render hotel cards."""
    fake_result = {
        "query": "what is berlin?",
        "city_answer": "Berlin is the capital of Germany.",
        "chunks": [],
    }

    with patch("src.routes.threads.graph") as mock_graph:
        mock_graph.ainvoke = AsyncMock(return_value=fake_result)
        response = client.post(
            "/threads/abc123/chat",
            json={"assistant_id": "agent", "input": {"query": "what is berlin?"}},
        )

    body = response.json()
    assert body["answer"] == "Berlin is the capital of Germany."
    assert "hotels" not in body


def test_thread_chat_serializes_chunks_to_plain_dicts(client):
    """Chunks come back as Document-like objects (attribute access:
    c.page_content, c.metadata), not JSON-serializable as-is — this checks
    threads.py's own conversion, surviving a real HTTP JSON round-trip."""
    fake_chunk = type("Doc", (), {"page_content": "Berlin is a city.", "metadata": {"source": "berlin.md"}})()
    fake_result = {"query": "what is berlin?", "city_answer": "some answer", "chunks": [fake_chunk]}

    with patch("src.routes.threads.graph") as mock_graph:
        mock_graph.ainvoke = AsyncMock(return_value=fake_result)
        response = client.post(
            "/threads/abc123/chat",
            json={"assistant_id": "agent", "input": {"query": "what is berlin?"}},
        )

    assert response.json()["chunks"] == [
        {"page_content": "Berlin is a city.", "metadata": {"source": "berlin.md"}}
    ]


def test_thread_chat_rejects_unknown_assistant_id(client):
    """The assistant_id check happens before graph.ainvoke() is ever
    called, so this needs no mocking at all — a wrong assistant_id should
    404 without running the graph."""
    response = client.post(
        "/threads/abc123/chat",
        json={"assistant_id": "wrong-agent", "input": {"query": "hi"}},
    )
    assert response.status_code == 404


def test_thread_chat_requires_assistant_id_and_input(client):
    """An empty body fails Pydantic's ThreadChatRequest validation before
    FastAPI ever calls thread_chat()."""
    response = client.post("/threads/abc123/chat", json={})
    assert response.status_code == 422

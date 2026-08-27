from unittest.mock import MagicMock, patch

from graph.nodes import generate_node, retrieve_node


def test_retrieve_node_calls_retrieve_chunks_with_query():
    fake_chunks = [MagicMock(page_content="chunk 1"), MagicMock(page_content="chunk 2")]
    state = {"query": "What is Paris?", "chunks": [], "answer": ""}

    with patch("graph.nodes.retrieve_chunks") as mock_retrieve_chunks:
        mock_retrieve_chunks.return_value = fake_chunks
        result = retrieve_node(state)

    mock_retrieve_chunks.assert_called_once_with("What is Paris?")
    assert result == {"chunks": fake_chunks}


def test_generate_node_uses_retrieved_context():
    fake_chunk = MagicMock(page_content="Berlin is the capital of Germany.")
    state = {"query": "What is Berlin?", "chunks": [fake_chunk], "answer": ""}

    with patch("graph.nodes.get_chat_model") as mock_get_chat_model:
        mock_get_chat_model.return_value.invoke.return_value.content = "Berlin is Germany's capital."
        result = generate_node(state)

    assert result["answer"] == "Berlin is Germany's capital."

    # the prompt sent to the model must actually include the retrieved chunk's content
    prompt_arg = mock_get_chat_model.return_value.invoke.call_args[0][0]
    assert "Berlin is the capital of Germany." in prompt_arg
    assert "What is Berlin?" in prompt_arg


def test_generate_node_joins_multiple_chunks_into_context():
    chunks = [
        MagicMock(page_content="Paris is the capital of France."),
        MagicMock(page_content="The Eiffel Tower is in Paris."),
    ]
    state = {"query": "What is Paris?", "chunks": chunks, "answer": ""}

    with patch("graph.nodes.get_chat_model") as mock_get_chat_model:
        mock_get_chat_model.return_value.invoke.return_value.content = "Paris is a city in France."
        generate_node(state)

    # a regression guard against only chunks[0] being used
    prompt_arg = mock_get_chat_model.return_value.invoke.call_args[0][0]
    assert "Paris is the capital of France." in prompt_arg
    assert "The Eiffel Tower is in Paris." in prompt_arg


def test_generate_node_with_no_chunks():
    state = {"query": "What is Atlantis?", "chunks": [], "answer": ""}

    with patch("graph.nodes.get_chat_model") as mock_get_chat_model:
        mock_get_chat_model.return_value.invoke.return_value.content = "I don't know."
        result = generate_node(state)

    # empty context shouldn't break prompt construction or crash the node
    prompt_arg = mock_get_chat_model.return_value.invoke.call_args[0][0]
    assert "What is Atlantis?" in prompt_arg
    assert result["answer"] == "I don't know."

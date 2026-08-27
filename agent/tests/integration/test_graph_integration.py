import pytest

from graph import graph


@pytest.mark.integration
def test_graph_answers_about_berlin():
    """Runs the real retrieve -> generate pipeline against a live Qdrant + chat backend."""
    result = graph.invoke({"query": "what is berlin?"})

    assert result["chunks"], "expected at least one retrieved chunk from Qdrant"
    assert "berlin" in result["answer"].lower()

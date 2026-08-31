import pytest

from graph import graph


@pytest.mark.integration
def test_graph_answers_about_berlin():
    """Runs the real retrieve -> generate pipeline against a live OpenSearch + Bedrock backend."""
    result = graph.invoke({"query": "what is berlin?"})

    assert result["chunks"], "expected at least one retrieved chunk from OpenSearch"
    assert "berlin" in result["answer"].lower()

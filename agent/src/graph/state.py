from typing import TypedDict

from langchain_core.documents import Document


class State(TypedDict):
    """Input/output state for the agent."""

    query: str
    chunks: list[Document]
    answer: str

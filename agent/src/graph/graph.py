"""Cities RAG agent: retrieves context from Qdrant and answers using a chat model."""

from langgraph.graph import END, START, StateGraph

from .nodes import generate_node, retrieve_node
from .state import State

# Define the graph
graph = (
    StateGraph(State)
    .add_node("retrieve", retrieve_node)
    .add_node("generate", generate_node)
    .add_edge(START, "retrieve")
    .add_edge("retrieve", "generate")
    .add_edge("generate", END)
    .compile(name="Cities RAG Agent")
)

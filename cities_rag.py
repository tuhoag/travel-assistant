from typing import TypedDict

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from langgraph.graph import StateGraph, START, END
from qdrant_client import QdrantClient

from config import QDRANT_URL, QDRANT_COLLECTION, get_chat_model, get_encoder


class RAGState(TypedDict):
    query: str
    chunks: list[Document]
    answer: str


def retrieve_chunks(query: str, k: int = 3) -> list[Document]:
    client = QdrantClient(url=QDRANT_URL)
    vector_store = QdrantVectorStore(client=client, collection_name=QDRANT_COLLECTION, embedding=get_encoder())
    return vector_store.similarity_search(query, k=k)


def retrieve_node(state: RAGState) -> dict:
    return {"chunks": retrieve_chunks(state["query"])}


def generate_node(state: RAGState) -> dict:
    context = "\n\n".join(chunk.page_content for chunk in state["chunks"])
    prompt = (
        "Answer the question using only the context below. "
        "If the context doesn't contain the answer, say you don't know.\n\n"
        f"Context:\n{context}\n\nQuestion: {state['query']}"
    )
    response = get_chat_model().invoke(prompt)
    return {"answer": response.content}


def build_rag_graph():
    graph = StateGraph(RAGState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


def answer_query(query: str) -> str:
    graph = build_rag_graph()
    result = graph.invoke({"query": query})
    return result["answer"]


def main():
    answer = answer_query("what is berlin?")
    print(answer)


if __name__ == "__main__":
    main()

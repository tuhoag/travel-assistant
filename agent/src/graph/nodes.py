from typing import Any

from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from .config import (
    EMBEDDING_MODEL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    QDRANT_URL,
    get_chat_model,
)
from .state import State


def retrieve_chunks(query: str, k: int = 3) -> list[Document]:
    """Retrieve the top-k most relevant city chunks from Qdrant."""
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=QDRANT_COLLECTION,
        embedding=FastEmbedEmbeddings(model_name=EMBEDDING_MODEL),
    )
    return vector_store.similarity_search(query, k=k)


def retrieve_node(state: State) -> dict[str, Any]:
    """Retrieve relevant chunks for the query."""
    chunks = retrieve_chunks(state["query"])
    return {"chunks": chunks}


def generate_node(state: State) -> dict[str, Any]:
    """Generate an answer grounded in the retrieved chunks."""
    context = "\n\n".join(chunk.page_content for chunk in state["chunks"])
    prompt = (
        "Answer the question using only the context below. "
        "If the context doesn't contain the answer, say you don't know.\n\n"
        f"Context:\n{context}\n\nQuestion: {state['query']}"
    )
    response = get_chat_model().invoke(prompt)
    return {"answer": response.content}

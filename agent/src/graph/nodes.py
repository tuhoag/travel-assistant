from typing import Any

import boto3
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_core.documents import Document
from opensearchpy import AWSV4SignerAuth, RequestsHttpConnection

from .config import (
    AWS_REGION,
    EMBEDDING_MODEL,
    OPENSEARCH_COLLECTION,
    OPENSEARCH_URL,
    get_chat_model,
)
from src.prompt_registry import prompt_registry
from .state import State


def retrieve_chunks(query: str, k: int = 3) -> list[Document]:
    """Retrieve the top-k most relevant city chunks from OpenSearch."""
    credentials = boto3.Session().get_credentials()
    http_auth = AWSV4SignerAuth(credentials, AWS_REGION, "es")
    vector_store = OpenSearchVectorSearch(
        opensearch_url=OPENSEARCH_URL,
        index_name=OPENSEARCH_COLLECTION,
        embedding_function=FastEmbedEmbeddings(model_name=EMBEDDING_MODEL),
        http_auth=http_auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
    )
    # vector_field/text_field are read at query time (not by the constructor
    # above) and must match the field names the Prefect ingestion pipeline
    # actually writes: "vector" and "page_content", not the library's own
    # defaults ("vector_field" / "text").
    return vector_store.similarity_search(query, k=k, vector_field="vector", text_field="page_content")


def retrieve_node(state: State) -> dict[str, Any]:
    """Retrieve relevant chunks for the query."""
    chunks = retrieve_chunks(state["query"])
    return {"chunks": chunks}


def generate_node(state: State) -> dict[str, Any]:
    """Generate an answer grounded in the retrieved chunks."""
    context = "\n\n".join(chunk.page_content for chunk in state["chunks"])
    messages = prompt_registry.get("rag").invoke({"context": context, "query": state["query"]})
    response = get_chat_model().invoke(messages)
    return {"answer": response.content}

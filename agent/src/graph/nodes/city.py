from __future__ import annotations

from typing import Any

import boto3
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_core.documents import Document
from langgraph.graph import END
from opensearchpy import AWSV4SignerAuth, RequestsHttpConnection

from src.prompt_registry import prompt_registry

from ..config import (
    AWS_REGION,
    EMBEDDING_MODEL,
    MAX_REVISIONS,
    OPENSEARCH_COLLECTION,
    OPENSEARCH_URL,
    get_chat_model,
)
from ..state import State
from .schemas import CoverageCheck, Reflection
from .shared import _feedback_section
from .structured_output import _structured_call


def _format_context(chunks: list[Document]) -> str:
    """Labels each chunk with the city it's actually about (from ingestion
    metadata). Without this, chunks that are ABOUT one city but mention
    another in passing (e.g. Canberra's article naming Sydney as a rival
    for the capital) look identical to genuine coverage of that other
    city — the model has no way to tell "this passage's subject is X" from
    "this passage merely names X" once the text is flattened together."""
    return "\n\n".join(
        f"[Source: {chunk.metadata.get('title', 'unknown')}]\n{chunk.page_content}" for chunk in chunks
    )


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


async def retrieve_chunks_node(state: State) -> dict[str, Any]:
    chunks = retrieve_chunks(state["query"])
    return {"chunks": chunks}


async def check_city_coverage(state: State) -> dict[str, Any]:
    """A narrow, focused yes/no check — run before generation, not after —
    on whether the retrieved sources genuinely cover the asked-about city.
    Added after generate_city_answer + reflect_city_answer proved
    unreliable at this specific judgment in production: asking "what is
    sydney?" retrieved Canberra's article (which names Sydney in passing,
    as a rival for the capital), and the model answered about Sydney using
    it anyway — twice in a row, surviving two rounds of reflection feedback
    each time. Deciding this from the raw source list, before any answer
    prose exists to rationalize around, is a smaller and more reliable
    judgment than catching it after the fact."""
    context = _format_context(state["chunks"])
    messages = prompt_registry.get("check_city_coverage").invoke({"context": context, "query": state["query"]})
    coverage = await _structured_call(CoverageCheck, messages)
    return {"city_covered": coverage.covered}


def route_after_retrieve(state: State) -> str:
    return "generate_city_answer" if state.get("city_covered") else "city_not_found"


async def city_not_found(state: State) -> dict[str, Any]:
    return {"city_answer": "I don't know. I don't have information about that city."}


async def generate_city_answer(state: State) -> dict[str, Any]:
    context = _format_context(state["chunks"])
    messages = prompt_registry.get("generate_city").invoke({
        "context": context,
        "query": state["query"],
        "feedback_section": _feedback_section(state.get("city_feedback")),
    })
    response = await get_chat_model().ainvoke(messages)
    return {"city_answer": response.content}


async def reflect_city_answer(state: State) -> dict[str, Any]:
    context = _format_context(state["chunks"])
    messages = prompt_registry.get("reflect_city").invoke({
        "context": context,
        "query": state["query"],
        "draft_answer": state["city_answer"],
    })
    reflection = await _structured_call(Reflection, messages)

    revision_count = state.get("city_revision_count", 0)
    if reflection.passes or revision_count >= MAX_REVISIONS:
        return {"city_feedback": None}
    return {"city_revision_count": revision_count + 1, "city_feedback": reflection.feedback}


def route_city_reflection(state: State) -> str:
    # Non-empty city_feedback means reflect_city_answer asked for a revision.
    if state.get("city_feedback"):
        return "generate_city_answer"
    return END

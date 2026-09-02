from __future__ import annotations

import re
from typing import Any

import boto3
import yaml
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END
from opensearchpy import AWSV4SignerAuth, RequestsHttpConnection
from pydantic import BaseModel, ValidationError

from src.prompt_registry import prompt_registry

from .config import (
    AWS_REGION,
    EMBEDDING_MODEL,
    MAX_REVISIONS,
    OPENSEARCH_COLLECTION,
    OPENSEARCH_URL,
    get_chat_model,
)
from .mcp_client import call_search_hotels
from .state import HotelParams, State


class Intent(BaseModel):
    city_search: bool
    hotel_search: bool


class HotelSearchParams(BaseModel):
    city: str
    max_price: float | None = None
    min_stars: int | None = None
    amenities: list[str] | None = None


class Reflection(BaseModel):
    passes: bool
    feedback: str | None = None


class CoverageCheck(BaseModel):
    covered: bool


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")[1:]  # drop opening fence (possibly "```yaml")
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def _try_yaml(text: str) -> Any | None:
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError:
        return None


def _extract_fields_by_regex(schema: type[BaseModel], text: str) -> dict[str, Any]:
    """Fallback for when the model doesn't respond with clean YAML despite
    being asked to. Only attempts `bool` fields, via a narrow match bounded
    to the literal token "true"/"false" — safe regardless of where in the
    text it appears. Free-text fields are deliberately NOT extracted here:
    an earlier version matched "<field>: <rest of line>" and either (a)
    matched a field name appearing as an ordinary word mid-paragraph and
    captured the whole rest of that paragraph as the "value" (unanchored),
    or (b) missed a real value entirely when the field name wasn't at the
    true start of a line, e.g. "...grounded. Correction: passes: true."
    (anchored). Anything that isn't a plain bool is left for the
    corrective retry in _structured_call to fix instead of guessed at."""
    result: dict[str, Any] = {}
    for field_name, field in schema.model_fields.items():
        if field.annotation is bool:
            match = re.search(rf"\b{field_name}\b\s*:?\s*\b(true|false)\b", text, re.IGNORECASE)
            if match:
                result[field_name] = match.group(1).lower() == "true"
    return result


async def _structured_call(schema: type[BaseModel], messages, _allow_retry: bool = True) -> BaseModel:
    """Ask the model for YAML matching `schema` (the prompt itself carries
    the instruction and shape) and parse+validate the response. Doesn't
    rely on Bedrock's native structured-output/tool-calling support, which
    not every model has (e.g. Qwen3 via langchain_aws) — YAML-in/YAML-out
    over a plain chat call works with any model, though not every model
    reliably follows the "ONLY YAML" instruction. Three lines of defense,
    in order: parse as-is, extract fields by anchored regex, then one
    corrective retry that shows the model its own broken response."""
    response = await get_chat_model().ainvoke(messages)
    content = _strip_code_fence(response.content)

    for candidate in (_try_yaml(content), _extract_fields_by_regex(schema, content)):
        if candidate is None:
            continue
        try:
            return schema.model_validate(candidate)
        except ValidationError:
            continue

    if not _allow_retry:
        raise ValueError(f"Could not parse a valid {schema.__name__} from model response: {content!r}")

    correction = [
        SystemMessage(content="Respond with ONLY YAML, no other text, no markdown fences."),
        HumanMessage(
            content=f"Your previous response was not valid YAML:\n\n{content}\n\nRespond again, YAML only."
        ),
    ]
    return await _structured_call(schema, correction, _allow_retry=False)


def _feedback_section(feedback: str | None) -> str:
    if not feedback:
        return ""
    return f"\nPrevious attempt's feedback (address this): {feedback}"


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


def _format_hotel_params(params: HotelParams) -> str:
    parts = [f"city={params['city']}"]
    if params.get("max_price") is not None:
        parts.append(f"max_price={params['max_price']}")
    if params.get("min_stars") is not None:
        parts.append(f"min_stars={params['min_stars']}")
    if params.get("amenities"):
        parts.append(f"amenities={', '.join(params['amenities'])}")
    return ", ".join(parts)


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


async def detect_intent(state: State) -> dict[str, Any]:
    """Classify whether the query needs city info, hotel search, or both."""
    messages = prompt_registry.get("detect_intent").invoke({"query": state["query"]})
    intent = await _structured_call(Intent, messages)
    return {"city_search": intent.city_search, "hotel_search": intent.hotel_search}


# ---- City lane ----


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


# ---- Hotel lane ----


async def extract_hotel_params(state: State) -> dict[str, Any]:
    messages = prompt_registry.get("extract_hotel_params").invoke({"query": state["query"]})
    params = await _structured_call(HotelSearchParams, messages)
    hotel_params: HotelParams = {
        "city": params.city,
        "max_price": params.max_price,
        "min_stars": params.min_stars,
        "amenities": params.amenities,
    }
    return {"hotel_params": hotel_params}


async def search_hotels_node(state: State) -> dict[str, Any]:
    params = state["hotel_params"]
    hotels = await call_search_hotels(
        city=params["city"],
        max_price=params.get("max_price"),
        min_stars=params.get("min_stars"),
        amenities=params.get("amenities"),
    )
    return {"hotels": hotels}


async def generate_hotel_answer(state: State) -> dict[str, Any]:
    messages = prompt_registry.get("generate_hotel").invoke({
        "query": state["query"],
        "hotel_params": _format_hotel_params(state["hotel_params"]),
        "hotel_count": len(state["hotels"]),
        "feedback_section": _feedback_section(state.get("hotel_feedback")),
    })
    response = await get_chat_model().ainvoke(messages)
    return {"hotel_answer": response.content}


async def reflect_hotel_answer(state: State) -> dict[str, Any]:
    messages = prompt_registry.get("reflect_hotel").invoke({
        "hotel_params": _format_hotel_params(state["hotel_params"]),
        "hotel_count": len(state["hotels"]),
        "draft_answer": state["hotel_answer"],
    })
    reflection = await _structured_call(Reflection, messages)

    revision_count = state.get("hotel_revision_count", 0)
    if reflection.passes or revision_count >= MAX_REVISIONS:
        return {"hotel_feedback": None}
    return {"hotel_revision_count": revision_count + 1, "hotel_feedback": reflection.feedback}


def route_hotel_reflection(state: State) -> str:
    if state.get("hotel_feedback"):
        return "generate_hotel_answer"
    return END

"""Generic "ask a model for YAML, parse it robustly" machinery — no
city/hotel-specific knowledge at all, reusable across lanes."""

from __future__ import annotations

import re
from typing import Any

import yaml
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from ..config import get_chat_model


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

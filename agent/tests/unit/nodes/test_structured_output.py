import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from graph.nodes.schemas import Reflection
from graph.nodes.structured_output import _strip_code_fence, _structured_call


def run(coro):
    return asyncio.run(coro)


def test_strip_code_fence_removes_fenced_block():
    text = "```yaml\npasses: true\nfeedback: null\n```"
    assert _strip_code_fence(text) == "passes: true\nfeedback: null"


def test_strip_code_fence_passes_through_unfenced_text():
    text = "passes: true\nfeedback: null"
    assert _strip_code_fence(text) == text


def test_structured_call_parses_yaml_response():
    with patch("graph.nodes.structured_output.get_chat_model") as mock_get_chat_model:
        mock_get_chat_model.return_value.ainvoke = AsyncMock(
            return_value=MagicMock(content="passes: true\nfeedback: null")
        )
        result = run(_structured_call(Reflection, "irrelevant messages"))

    assert result == Reflection(passes=True, feedback=None)


def test_structured_call_falls_back_to_regex_for_non_compliant_response():
    """Regression test for a real production failure: the model ignored the
    "ONLY YAML" instruction and wrapped the answer in prose, which broke a
    plain yaml.safe_load (the sentence reads as a second, nested mapping
    key) — this exact text crashed reflect_city_answer with a
    yaml.scanner.ScannerError before the regex fallback was added."""
    broken_text = (
        "The draft answer correctly states that the context does not contain "
        "information about Hanoi, which is appropriate and grounded. "
        "Correction: passes: true."
    )
    with patch("graph.nodes.structured_output.get_chat_model") as mock_get_chat_model:
        mock_get_chat_model.return_value.ainvoke = AsyncMock(return_value=MagicMock(content=broken_text))
        result = run(_structured_call(Reflection, "irrelevant messages"))

    assert result == Reflection(passes=True, feedback=None)


def test_structured_call_retries_once_when_nothing_extractable():
    """Regression test for a second real production failure: a response
    that was pure prose with no line-start match and no bare true/false
    token near the field name either — nothing for the regex fallback to
    grab. Rather than crash, one corrective retry is sent showing the
    model its own broken response; if that comes back clean, it's used."""
    unparseable = (
        "The context does not contain any information about Hanoi. The "
        "draft answer says I don't know which is grounded and correct."
    )
    with patch("graph.nodes.structured_output.get_chat_model") as mock_get_chat_model:
        mock_get_chat_model.return_value.ainvoke = AsyncMock(
            side_effect=[
                MagicMock(content=unparseable),
                MagicMock(content="passes: true\nfeedback: null"),
            ]
        )
        result = run(_structured_call(Reflection, "irrelevant messages"))

    assert result == Reflection(passes=True, feedback=None)
    assert mock_get_chat_model.return_value.ainvoke.call_count == 2


def test_structured_call_raises_if_retry_also_fails():
    """No infinite loop: exactly one retry, then a clear error rather than
    silently fabricating a result or looping forever."""
    unparseable = "still not valid YAML, still no usable fields anywhere"
    with patch("graph.nodes.structured_output.get_chat_model") as mock_get_chat_model:
        mock_get_chat_model.return_value.ainvoke = AsyncMock(return_value=MagicMock(content=unparseable))

        try:
            run(_structured_call(Reflection, "irrelevant messages"))
            raised = False
        except ValueError:
            raised = True

    assert raised
    assert mock_get_chat_model.return_value.ainvoke.call_count == 2

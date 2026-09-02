from typing import Any

from fastapi import APIRouter, HTTPException
from graph import graph
from pydantic import BaseModel

router = APIRouter()


class ThreadChatRequest(BaseModel):
    assistant_id: str
    input: dict[str, Any]


@router.post("/threads/{thread_id}/chat")
async def thread_chat(thread_id: str, request: ThreadChatRequest) -> dict[str, Any]:
    """Run the graph to completion against a given thread and return a
    curated response — not the whole internal state, which now also holds
    per-lane revision counts/feedback that have no business leaving the API.

    Note: `graph` currently has no checkpointer attached, so `thread_id` is
    passed through in config but doesn't persist state across calls yet.

    This is a custom path, not the real LangGraph Server's endpoint shape
    (`/threads/{thread_id}/runs/wait`) — `@langchain/langgraph-sdk`'s
    `Client` won't call this URL, so a caller needs to hit it directly
    (e.g. via fetch), not through `client.runs.wait(...)`.
    """
    if request.assistant_id != "agent":
        raise HTTPException(status_code=404, detail=f"Unknown assistant_id: {request.assistant_id}")

    result = await graph.ainvoke(request.input, config={"configurable": {"thread_id": thread_id}})

    # city_answer and hotel_answer come from independent lanes — either,
    # both, or (in the off-spec case) neither may be present.
    answer = "\n\n".join(part for part in (result.get("city_answer"), result.get("hotel_answer")) if part)

    response: dict[str, Any] = {"query": result["query"], "answer": answer}

    chunks = result.get("chunks")
    if chunks is not None:
        response["chunks"] = [{"page_content": c.page_content, "metadata": c.metadata} for c in chunks]

    hotels = result.get("hotels")
    if hotels is not None:
        response["hotels"] = hotels

    return response

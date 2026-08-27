from typing import Any

from fastapi import APIRouter, HTTPException
from graph import graph
from pydantic import BaseModel

router = APIRouter()


class ThreadChatRequest(BaseModel):
    assistant_id: str
    input: dict[str, Any]


@router.post("/threads/{thread_id}/chat")
def thread_chat(thread_id: str, request: ThreadChatRequest) -> dict[str, Any]:
    """Run the graph to completion against a given thread and return its final state.

    Note: `graph` currently has no checkpointer attached, so `thread_id` is
    passed through in config but doesn't persist state across calls yet.

    This is a custom path, not the real LangGraph Server's endpoint shape
    (`/threads/{thread_id}/runs/wait`) — `@langchain/langgraph-sdk`'s
    `Client` won't call this URL, so a caller needs to hit it directly
    (e.g. via fetch), not through `client.runs.wait(...)`.
    """
    if request.assistant_id != "agent":
        raise HTTPException(status_code=404, detail=f"Unknown assistant_id: {request.assistant_id}")

    result = graph.invoke(request.input, config={"configurable": {"thread_id": thread_id}})

    chunks = result.get("chunks")
    if chunks is not None:
        result = {
            **result,
            "chunks": [{"page_content": c.page_content, "metadata": c.metadata} for c in chunks],
        }

    return result

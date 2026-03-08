import json
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.domain.conversation.agent import run
from app.domain.conversation.prompts import build_system_message
from app.domain.conversation.schemas import ChatRequest, LLMMessage

router = APIRouter(prefix="/conversation", tags=["conversation"])


async def _event_stream(request: ChatRequest) -> AsyncGenerator[str, None]:
    """Build the message list and run the ReAct agent, yielding SSE frames."""
    # Lazy import to avoid circular deps; registry is populated at app startup
    from app.infrastructure.mcp.registry import mcp_registry

    # 1. System message
    system_content = build_system_message()
    system_msg = LLMMessage(role="system", content=system_content)

    # 2. Conversation history from Android (includes the latest user message)
    history = [LLMMessage(role=m.role, content=m.content) for m in request.messages]

    messages = [system_msg, *history]
    tools = mcp_registry.get_tool_definitions()

    # 3. Stream ReAct agent output as SSE
    async for token in run(messages, tools, mcp_registry.call_tool):
        payload = json.dumps({"token": token})
        yield f"data: {payload}\n\n"

    yield "data: [DONE]\n\n"


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """
    Main conversational endpoint.

    Accepts the full message history + driving context from the Android app,
    runs the ReAct agent, and streams the response as Server-Sent Events.
    """
    return StreamingResponse(
        _event_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

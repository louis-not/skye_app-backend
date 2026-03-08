import json
import traceback
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.domain.conversation.agent import run
from app.domain.conversation.prompts import build_system_message
from app.domain.conversation.schemas import ChatRequest

router = APIRouter(prefix="/conversation", tags=["conversation"])


async def _event_stream(request: ChatRequest) -> AsyncGenerator[str, None]:
    """Build the message list and run the ReAct agent, yielding SSE frames."""
    from app.infrastructure.mcp.registry import mcp_registry

    try:
        system_msg = {"role": "system", "content": build_system_message()}
        history = [{"role": m.role, "content": m.content} for m in request.messages]
        messages = [system_msg, *history]
        tools = mcp_registry.get_tool_definitions()

        async for token in run(messages, tools, mcp_registry.call_tool):
            yield f"data: {json.dumps({'token': token})}\n\n"

    except Exception:
        error_detail = traceback.format_exc()
        print(f"[conversation] stream error:\n{error_detail}")
        yield f"data: {json.dumps({'error': 'Stream failed. Check server logs.'})}\n\n"

    finally:
        yield "data: [DONE]\n\n"


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _event_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

import json
from typing import AsyncGenerator, Any

import httpx

from app.core.config import settings
from app.domain.conversation.schemas import LLMMessage


# Maximum tool-call iterations before forcing a final answer
MAX_REACT_ITERATIONS = 10


async def run(
    messages: list[LLMMessage],
    tools: list[dict[str, Any]],
    tool_executor: Any,
) -> AsyncGenerator[str, None]:
    """
    ReAct agent loop.

    Yields text tokens as they stream from the LLM once a final answer is reached.
    Tool calls are executed internally (no streaming during reasoning steps).

    Args:
        messages:       Full conversation (system + history + user turn).
        tools:          OpenAI-format tool definitions to pass to the LLM.
        tool_executor:  Callable (name, args) -> str for executing tool calls.
                        In practice this is the MCP registry's call_tool method.
    """
    working_messages = [m.to_dict() for m in messages]

    async with httpx.AsyncClient(timeout=60.0) as client:
        for _ in range(MAX_REACT_ITERATIONS):
            # ── Reasoning step: non-streaming call so we can inspect tool_calls ──
            response = await client.post(
                f"{settings.OPENAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": working_messages,
                    "tools": tools if tools else None,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()

            choice = data["choices"][0]
            finish_reason = choice["finish_reason"]
            assistant_msg = choice["message"]

            # Append assistant turn to working context
            working_messages.append(assistant_msg)

            # ── Tool call branch ──
            if finish_reason == "tool_calls" or assistant_msg.get("tool_calls"):
                for tool_call in assistant_msg["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    tool_args = json.loads(tool_call["function"]["arguments"])
                    tool_call_id = tool_call["id"]

                    result = await tool_executor(tool_name, tool_args)

                    working_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": str(result),
                    })
                # Loop back for the next reasoning step
                continue

            # ── Final answer branch: stream it ──
            final_content = assistant_msg.get("content") or ""

            # Re-request with streaming enabled for the final response
            async with client.stream(
                "POST",
                f"{settings.OPENAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": working_messages[:-1],  # exclude the last assistant turn
                    "stream": True,
                },
            ) as stream_response:
                stream_response.raise_for_status()
                async for line in stream_response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    chunk = line[len("data: "):]
                    if chunk.strip() == "[DONE]":
                        return
                    try:
                        chunk_data = json.loads(chunk)
                        token = (
                            chunk_data["choices"][0]
                            .get("delta", {})
                            .get("content") or ""
                        )
                        if token:
                            yield token
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
            return

        # Safety valve: if max iterations hit, yield whatever the last content was
        last = working_messages[-1]
        if last.get("role") == "assistant" and last.get("content"):
            yield last["content"]

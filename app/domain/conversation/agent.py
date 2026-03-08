import json
import re
from typing import AsyncGenerator, Any

import httpx

from app.core.config import settings


MAX_REACT_ITERATIONS = 10

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks produced by reasoning models."""
    return _THINK_RE.sub("", text).strip()


async def run(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    tool_executor: Any,
) -> AsyncGenerator[str, None]:
    """
    ReAct agent loop — single streaming pass per iteration.

    Streams content tokens to the caller as they arrive.
    Tool calls are detected from the stream, executed, then fed back for the next
    reasoning step. Thinking tokens (<think>...</think>) are filtered out.
    """
    working_messages = list(messages)

    async with httpx.AsyncClient(timeout=120.0) as client:
        for iteration in range(MAX_REACT_ITERATIONS):
            # Buffers for this iteration
            collected_content = ""
            tool_calls_buf: dict[int, dict[str, Any]] = {}
            is_tool_call = False

            async with client.stream(
                "POST",
                f"{settings.OPENAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": working_messages,
                    "tools": tools if tools else None,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw = line[len("data: "):]
                    if raw.strip() == "[DONE]":
                        break

                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    choice = data["choices"][0]
                    delta = choice.get("delta", {})

                    # ── Tool call delta ──
                    for tc in delta.get("tool_calls", []):
                        is_tool_call = True
                        idx = tc["index"]
                        if idx not in tool_calls_buf:
                            tool_calls_buf[idx] = {
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            }
                        if tc.get("id"):
                            tool_calls_buf[idx]["id"] = tc["id"]
                        fn = tc.get("function", {})
                        tool_calls_buf[idx]["function"]["name"] += fn.get("name", "")
                        tool_calls_buf[idx]["function"]["arguments"] += fn.get("arguments", "")

                    # ── Content delta ──
                    token = delta.get("content") or ""
                    if token:
                        collected_content += token
                        # Only yield content tokens when this is NOT a tool-call turn
                        if not is_tool_call:
                            yield token

            # ── After stream ends: decide what happened ──
            if is_tool_call:
                tool_calls_list = [
                    tool_calls_buf[i] for i in sorted(tool_calls_buf)
                ]
                working_messages.append({
                    "role": "assistant",
                    "content": collected_content or None,
                    "tool_calls": tool_calls_list,
                })

                for tc in tool_calls_list:
                    name = tc["function"]["name"]
                    args = json.loads(tc["function"]["arguments"])
                    call_id = tc["id"]
                    result = await tool_executor(name, args)
                    working_messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": str(result),
                    })
                # Continue ReAct loop
                continue

            # Final answer was already streamed token-by-token above.
            # Nothing more to do.
            return

        # Max iterations reached — yield last buffered content as fallback
        last = working_messages[-1]
        if last.get("role") == "assistant" and last.get("content"):
            yield _strip_thinking(last["content"])

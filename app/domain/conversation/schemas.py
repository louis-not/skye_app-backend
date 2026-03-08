from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single message in the conversation history."""

    role: Literal["user", "assistant", "system", "tool"]
    content: str


class ChatRequest(BaseModel):
    """Request body for the conversation chat endpoint."""

    session_id: str = Field(..., description="Unique identifier for the driving session")
    messages: list[Message] = Field(
        ...,
        description="Full conversation history. Android owns and sends this on every request.",
    )


class LLMMessage(BaseModel):
    """Internal message format sent to the LLM endpoint."""

    role: str
    content: Optional[str] = None
    tool_calls: Optional[list[dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"role": self.role}
        if self.content is not None:
            result["content"] = self.content
        if self.tool_calls is not None:
            result["tool_calls"] = self.tool_calls
        if self.tool_call_id is not None:
            result["tool_call_id"] = self.tool_call_id
        if self.name is not None:
            result["name"] = self.name
        return result

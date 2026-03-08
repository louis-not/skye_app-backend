from typing import Literal
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

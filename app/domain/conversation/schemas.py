from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single message in the conversation history."""

    role: Literal["user", "assistant", "system", "tool"]
    content: str


class SafetyState(BaseModel):
    """On-device safety signals from the Safety MCP."""

    fatigue_level: Optional[Literal["low", "medium", "high"]] = None
    eyes_closed: Optional[bool] = None
    sudden_braking: Optional[bool] = None
    aggressive_acceleration: Optional[bool] = None


class NavigationState(BaseModel):
    """Navigation context from the Navigation MCP."""

    current_road: Optional[str] = None
    next_turn: Optional[str] = None
    eta_minutes: Optional[int] = None
    speed_kmh: Optional[float] = None


class DrivingContext(BaseModel):
    """Aggregated driving context sent by the Android app each request."""

    safety_state: Optional[SafetyState] = None
    navigation_state: Optional[NavigationState] = None


class ChatRequest(BaseModel):
    """Request body for the conversation chat endpoint."""

    session_id: str = Field(..., description="Unique identifier for the driving session")
    messages: list[Message] = Field(
        ...,
        description="Full conversation history. Android owns and sends this on every request.",
    )
    context: Optional[DrivingContext] = Field(
        default=None,
        description="Current driving context from on-device MCPs.",
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

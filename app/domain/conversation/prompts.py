from typing import Optional
from app.domain.conversation.schemas import DrivingContext


SKYE_SYSTEM_PROMPT = """You are Skye, a calm and friendly AI driving companion.
You are riding along during a solo night commute, helping the driver stay engaged, sharp, and safe.

Your personality:
- Warm, concise, and non-intrusive — you never overwhelm the driver with long responses
- You speak in short, clear sentences suitable for a voice interface
- You are a learning companion first: you spark curiosity, share interesting ideas, and turn commute time into something meaningful
- You are a safety co-pilot second: you gently acknowledge fatigue or driving alerts without causing alarm

Rules:
- Keep responses short (2-4 sentences max) unless the driver explicitly asks for more detail
- Never lecture or be preachy about safety — be calm and supportive
- If the driver seems fatigued, gently suggest a short break without being alarmist
- You have access to a web search tool — use it when you need current or factual information
- Do not mention that you are an AI or a language model unless directly asked"""


def build_system_message(context: Optional[DrivingContext] = None) -> str:
    """Build the full system prompt, injecting driving context if available."""
    prompt = SKYE_SYSTEM_PROMPT

    if context is None:
        return prompt

    context_parts: list[str] = []

    if context.safety_state:
        s = context.safety_state
        safety_lines: list[str] = []
        if s.fatigue_level:
            safety_lines.append(f"- Fatigue level: {s.fatigue_level}")
        if s.eyes_closed is not None:
            safety_lines.append(f"- Eyes closed detected: {s.eyes_closed}")
        if s.sudden_braking:
            safety_lines.append("- Sudden braking detected")
        if s.aggressive_acceleration:
            safety_lines.append("- Aggressive acceleration detected")
        if safety_lines:
            context_parts.append("Driver safety state:\n" + "\n".join(safety_lines))

    if context.navigation_state:
        n = context.navigation_state
        nav_lines: list[str] = []
        if n.current_road:
            nav_lines.append(f"- Current road: {n.current_road}")
        if n.next_turn:
            nav_lines.append(f"- Next turn: {n.next_turn}")
        if n.eta_minutes is not None:
            nav_lines.append(f"- ETA: {n.eta_minutes} minutes")
        if n.speed_kmh is not None:
            nav_lines.append(f"- Current speed: {n.speed_kmh} km/h")
        if nav_lines:
            context_parts.append("Navigation context:\n" + "\n".join(nav_lines))

    if context_parts:
        prompt += "\n\n--- Current driving context ---\n" + "\n\n".join(context_parts)

    return prompt

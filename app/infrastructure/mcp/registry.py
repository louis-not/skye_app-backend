from typing import Any

from app.infrastructure.mcp.client import tavily_mcp_client


class MCPRegistry:
    """
    Discovers tools from all connected MCP servers and exposes them
    in OpenAI chat-completions tool format for the ReAct agent.
    """

    def __init__(self) -> None:
        self._tool_definitions: list[dict[str, Any]] = []

    async def load(self) -> None:
        """
        Fetch tool schemas from all MCP clients and convert to OpenAI format.
        Called once during app startup after MCP clients are connected.
        """
        self._tool_definitions = []

        tools_result = await tavily_mcp_client.session.list_tools()
        for tool in tools_result.tools:
            self._tool_definitions.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    },
                }
            )

        print(f"MCP registry loaded {len(self._tool_definitions)} tool(s): "
              f"{[t['function']['name'] for t in self._tool_definitions]}")

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Return OpenAI-format tool definitions for the LLM call."""
        return self._tool_definitions

    async def call_tool(self, name: str, args: dict[str, Any]) -> str:
        """
        Execute a tool by name via its MCP client and return the result as a string.
        Currently routes everything to the Tavily MCP client.
        """
        result = await tavily_mcp_client.session.call_tool(name, args)

        # MCP returns a list of content blocks; join text blocks into one string
        parts: list[str] = []
        for block in result.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts) if parts else str(result.content)


mcp_registry = MCPRegistry()

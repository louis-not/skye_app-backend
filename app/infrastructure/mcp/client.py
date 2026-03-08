from mcp import ClientSession
from mcp.client.sse import sse_client

from app.core.config import settings


class TavilyMCPClient:
    """
    Manages the connection to the remote Tavily MCP server.

    Uses SSE (HTTP) transport — no local subprocess or Node.js needed.
    The session is opened once at app startup and closed on shutdown.
    """

    def __init__(self) -> None:
        self._session: ClientSession | None = None
        self._exit_stack = None

    async def connect(self) -> None:
        """Open a persistent SSE session to the Tavily MCP server."""
        from contextlib import AsyncExitStack

        url = f"https://mcp.tavily.com/mcp/?tavilyApiKey={settings.TAVILY_API_KEY}"

        self._exit_stack = AsyncExitStack()
        read, write = await self._exit_stack.enter_async_context(sse_client(url))
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await self._session.initialize()
        print("Tavily MCP client connected")

    async def disconnect(self) -> None:
        """Close the SSE session."""
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._session = None
            self._exit_stack = None
            print("Tavily MCP client disconnected")

    @property
    def session(self) -> ClientSession:
        if self._session is None:
            raise RuntimeError("Tavily MCP client is not connected")
        return self._session


tavily_mcp_client = TavilyMCPClient()

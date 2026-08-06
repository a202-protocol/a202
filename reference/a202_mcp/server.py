"""The stdio MCP server.

This module is the only one that imports the MCP SDK. The tool surface itself
is declared in tools.py, which imports nothing from the SDK, so the handlers
are exercised and reused without a transport.

Two conventions from the MCP tool specification are followed deliberately.
A result carries both a serialized JSON text block and `structuredContent`, so
a client that reads either sees the same thing. A refusal sets `isError`,
because a refusal means nothing was recorded and a caller reading it as
success will carry on as though something was; a verification report never
sets it, because a report that finds a failure has succeeded at its job.
"""

from __future__ import annotations

import json

from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from .state import LocalState
from .tools import BY_NAME, SERVER_INSTRUCTIONS, TOOLS

SERVER_NAME = "a202"
SERVER_VERSION = "0.1.0"
SERVER_TITLE = "A202, bilateral scope"


def declared_tools() -> list[types.Tool]:
    """The tool surface, exactly as tools.py declares it."""
    return [
        types.Tool(
            name=tool["name"],
            title=tool["title"],
            description=tool["description"],
            inputSchema=tool["inputSchema"],
            annotations=types.ToolAnnotations(**tool["annotations"]),
        )
        for tool in TOOLS
    ]


def build_server(state: LocalState) -> Server:
    """Bind the tool surface to one party's state."""

    async def on_list_tools(context, params) -> types.ListToolsResult:
        return types.ListToolsResult(tools=declared_tools())

    async def on_call_tool(context, params) -> types.CallToolResult:
        tool = BY_NAME.get(params.name)
        if tool is None:
            # An unknown tool is a protocol error, not a commercial refusal.
            raise ValueError(f"no tool named {params.name}")
        result = tool["handler"](state, **(params.arguments or {}))
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=json.dumps(result, indent=2))],
            structuredContent=result,
            isError=result.get("outcome") == "refused",
        )

    return Server(
        SERVER_NAME,
        version=SERVER_VERSION,
        title=SERVER_TITLE,
        instructions=SERVER_INSTRUCTIONS,
        on_list_tools=on_list_tools,
        on_call_tool=on_call_tool,
    )


async def serve(state: LocalState) -> None:
    server = build_server(state)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

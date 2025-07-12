import os

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.tools.mcp_tool import MCPTool
from typing import List, Tuple
from contextlib import AsyncExitStack

_cached_mcp_tools: Tuple[List[MCPTool], AsyncExitStack] | None = None

async def load_mcp_tools():
    global _cached_mcp_tools

    if _cached_mcp_tools is None:
        tools, exit_stack = await MCPToolset.from_server(
            connection_params=StdioServerParameters(
                command='poetry',
                args=[
                    "run",
                    "mcp",
                    "run",
                    os.path.abspath("/home/jelene/work/mawa/src/mawa_mcp_server/data_provider.py")
                ],
            ),
        )
    else:
        tools, _ = _cached_mcp_tools

    return tools

async def close_mcp_connection():
    print("trying to close mcp connection")
    if _cached_mcp_tools is not None:
        _, exit_stack = _cached_mcp_tools
        print("actually closing connection")
        await exit_stack.aclose()
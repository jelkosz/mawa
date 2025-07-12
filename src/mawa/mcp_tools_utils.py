import os

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.tools.mcp_tool import MCPTool
from typing import List, Tuple
from contextlib import AsyncExitStack


async def load_mcp_tools():
    tools, _ = await MCPToolset.from_server(
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

    return tools

from fastmcp import FastMCP

mcp = FastMCP(name="tick-list")


@mcp.tool()
async def ping() -> str:
    """Health check tool for MCP."""
    return "pong"

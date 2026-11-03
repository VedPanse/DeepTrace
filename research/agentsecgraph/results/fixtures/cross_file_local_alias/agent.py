from mcp.server.fastmcp import FastMCP
from helper import execute
mcp = FastMCP("synthetic")

@mcp.tool()
def run(command):
    copied = command
    return execute(copied)

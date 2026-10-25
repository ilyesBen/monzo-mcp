from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

mcp = MCPServer("monzo-server")

# Every data tool only reads from Monzo. Declared so clients can show it, and
# pinned by test_every_data_tool_is_declared_read_only.
READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=True)

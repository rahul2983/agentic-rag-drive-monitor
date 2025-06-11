#!/usr/bin/env python3
"""
Ultra-simple MCP server for testing
"""

import asyncio
import json
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolRequest, CallToolResult, ListToolsResult

class SimpleTestServer:
    def __init__(self):
        self.server = Server("simple-test")
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools():
            # Try the most basic approach possible
            tools = [
                Tool(
                    name="ping",
                    description="Simple ping test",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
            
            # Debug: Print what we're trying to return
            print(f"DEBUG: Creating ListToolsResult with {len(tools)} tools", file=sys.stderr)
            print(f"DEBUG: Tool types: {[type(t) for t in tools]}", file=sys.stderr)
            
            result = ListToolsResult(tools=tools)
            print(f"DEBUG: ListToolsResult type: {type(result)}", file=sys.stderr)
            print(f"DEBUG: ListToolsResult.__dict__: {result.__dict__}", file=sys.stderr)
            
            return result
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest):
            if request.name == "ping":
                return CallToolResult(
                    content=[TextContent(type="text", text="pong")]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {request.name}")],
                    isError=True
                )

async def main():
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    
    server = SimpleTestServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())

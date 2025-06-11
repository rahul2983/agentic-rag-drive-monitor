#!/usr/bin/env python3
"""
Fixed MCP server that should work around the tuple issue
"""

import asyncio
import json
import sys
import logging

# Try different import approaches
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent, CallToolRequest, CallToolResult, ListToolsResult
    print("✅ Standard MCP imports", file=sys.stderr)
except ImportError as e:
    print(f"❌ Standard imports failed: {e}", file=sys.stderr)
    sys.exit(1)

class FixedMCPServer:
    def __init__(self, name: str):
        self.server = Server(name)
        self.name = name
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools():
            """Fixed list_tools handler"""
            
            # Define tools for this server
            if self.name == "google-drive":
                tools = [
                    Tool(
                        name="authenticate",
                        description="Authenticate with Google Drive API",
                        inputSchema={"type": "object", "properties": {}, "required": []}
                    ),
                    Tool(
                        name="get_recent_files", 
                        description="Get files modified in the last N hours",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "hours_back": {"type": "integer", "default": 24}
                            }
                        }
                    )
                ]
            elif self.name == "ai-analysis":
                tools = [
                    Tool(
                        name="analyze_document",
                        description="Perform AI analysis of document content",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "content": {"type": "string"},
                                "document_name": {"type": "string"}
                            },
                            "required": ["content", "document_name"]
                        }
                    ),
                    Tool(
                        name="generate_summary",
                        description="Generate a summary of document content", 
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "content": {"type": "string"}
                            },
                            "required": ["content"]
                        }
                    )
                ]
            else:
                tools = [
                    Tool(
                        name="test_tool",
                        description="Test tool",
                        inputSchema={"type": "object", "properties": {}}
                    )
                ]
            
            # Try different ways to return the result
            try:
                # Method 1: Direct return
                result = ListToolsResult(tools=tools)
                return result
                
            except Exception as e:
                print(f"❌ Method 1 failed: {e}", file=sys.stderr)
                
                # Method 2: Return as dict
                try:
                    return {"tools": tools}
                except Exception as e2:
                    print(f"❌ Method 2 failed: {e2}", file=sys.stderr)
                    
                    # Method 3: Manual construction
                    return ListToolsResult.model_validate({"tools": tools})
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest):
            """Handle tool calls"""
            return CallToolResult(
                content=[TextContent(type="text", text=f"Tool {request.name} called successfully")]
            )

# Create different server types
async def run_drive_server():
    """Run Google Drive server"""
    server = FixedMCPServer("google-drive")
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(read_stream, write_stream)

async def run_ai_server():
    """Run AI Analysis server"""
    server = FixedMCPServer("ai-analysis")
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(read_stream, write_stream)

# Determine which server to run based on script name
if __name__ == "__main__":
    script_name = sys.argv[0]
    
    if "drive" in script_name:
        asyncio.run(run_drive_server())
    elif "ai" in script_name:
        asyncio.run(run_ai_server())
    else:
        # Default test server
        server = FixedMCPServer("test")
        asyncio.run(stdio_server().run(server.server.run))

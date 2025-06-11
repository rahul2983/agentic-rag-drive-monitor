#!/usr/bin/env python3
"""
Absolutely minimal MCP server to test the core protocol
"""

import asyncio
import sys
import traceback

# Force debug output
import logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server  
    from mcp.types import Tool, TextContent, CallToolRequest, CallToolResult, ListToolsRequest, ListToolsResult
    print("✅ All MCP imports successful", file=sys.stderr)
except Exception as e:
    print(f"❌ MCP import failed: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

class MinimalServer:
    def __init__(self):
        self.server = Server("minimal")
        self.setup_handlers()
        print("✅ Server initialized", file=sys.stderr)
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            print("🔧 handle_list_tools called", file=sys.stderr)
            
            try:
                # Create the simplest possible tool
                tool = Tool(
                    name="test",
                    description="Test tool",
                    inputSchema={"type": "object", "properties": {}}
                )
                print(f"✅ Tool created: {tool}", file=sys.stderr)
                
                # Create tools list
                tools = [tool]
                print(f"✅ Tools list: {tools}", file=sys.stderr)
                
                # Create result - this is where the issue might be
                result = ListToolsResult(tools=tools)
                print(f"✅ ListToolsResult created: {result}", file=sys.stderr)
                print(f"   Type: {type(result)}", file=sys.stderr)
                print(f"   Dict: {result.__dict__}", file=sys.stderr)
                
                # Let's try to serialize it to see what happens
                try:
                    import json
                    serialized = json.dumps(result.__dict__)
                    print(f"✅ Serialization test passed: {serialized[:100]}...", file=sys.stderr)
                except Exception as se:
                    print(f"❌ Serialization failed: {se}", file=sys.stderr)
                
                return result
                
            except Exception as e:
                print(f"❌ Error in list_tools: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                raise
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            print(f"🔧 handle_call_tool called: {request.name}", file=sys.stderr)
            return CallToolResult(
                content=[TextContent(type="text", text="OK")]
            )
        
        print("✅ Handlers registered", file=sys.stderr)

async def main():
    print("🚀 Starting minimal MCP server...", file=sys.stderr)
    
    try:
        server = MinimalServer()
        print("✅ Server created", file=sys.stderr)
        
        async with stdio_server() as (read_stream, write_stream):
            print("✅ STDIO server started", file=sys.stderr)
            await server.server.run(read_stream, write_stream)
            
    except Exception as e:
        print(f"❌ Server failed: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())

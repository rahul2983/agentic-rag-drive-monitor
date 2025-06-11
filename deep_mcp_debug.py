#!/usr/bin/env python3
"""
Deep MCP debugging to find and fix the exact issue
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path

def check_mcp_versions():
    """Check all MCP-related package versions"""
    print("🔍 Checking MCP-related packages...")
    
    packages_to_check = [
        'mcp',
        'pydantic', 
        'anyio',
        'httpx'
    ]
    
    versions = {}
    for package in packages_to_check:
        try:
            module = __import__(package)
            version = getattr(module, '__version__', 'unknown')
            versions[package] = version
            print(f"✅ {package}: {version}")
        except ImportError:
            versions[package] = 'NOT INSTALLED'
            print(f"❌ {package}: NOT INSTALLED")
    
    return versions

def create_minimal_mcp_server():
    """Create the most minimal MCP server possible"""
    content = '''#!/usr/bin/env python3
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
'''
    return content

def create_mcp_client_test():
    """Create a test to see what the client is receiving"""
    content = '''#!/usr/bin/env python3
"""
Test what the MCP client is actually receiving from the server
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_minimal_server():
    """Test our minimal server to see exactly what's happening"""
    
    print("🧪 Testing minimal MCP server communication...")
    
    try:
        # Server parameters
        server_params = StdioServerParameters(
            command="python",
            args=["minimal_server.py"],
        )
        
        print("✅ Server parameters created")
        
        # Connect to server
        async with stdio_client(server_params) as (read, write):
            print("✅ Connected to server")
            
            async with ClientSession(read, write) as session:
                print("✅ Session created")
                
                # Initialize
                await session.initialize()
                print("✅ Session initialized")
                
                # List tools - this is where the error occurs
                print("🔧 Calling list_tools()...")
                
                try:
                    tools_result = await session.list_tools()
                    print(f"✅ Tools result received!")
                    print(f"   Type: {type(tools_result)}")
                    print(f"   Content: {tools_result}")
                    
                    if hasattr(tools_result, 'tools'):
                        print(f"   Tools count: {len(tools_result.tools)}")
                        for i, tool in enumerate(tools_result.tools):
                            print(f"   Tool {i}: {tool.name}")
                    
                except Exception as e:
                    print(f"❌ list_tools() failed: {e}")
                    print(f"   Error type: {type(e)}")
                    traceback.print_exc()
                    
                    # Try to get more info about what was received
                    print("\\n🔍 Trying to debug what was actually received...")
                    
    except Exception as e:
        print(f"❌ Client test failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_minimal_server())
'''
    return content

def create_mcp_fix():
    """Create a potential fix based on what we discover"""
    content = '''#!/usr/bin/env python3
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
'''
    return content

def main():
    """Main debugging function"""
    print("🔧 Deep MCP Debugging")
    print("=" * 50)
    
    # Check versions
    versions = check_mcp_versions()
    
    # Check for known issues
    if 'pydantic' in versions:
        pydantic_version = versions['pydantic']
        if pydantic_version.startswith('2.'):
            print(f"⚠️  Pydantic v2 detected ({pydantic_version}) - this might cause issues")
        else:
            print(f"✅ Pydantic version: {pydantic_version}")
    
    print("\n📝 Creating debugging files...")
    
    # Create minimal server
    with open("minimal_server.py", "w") as f:
        f.write(create_minimal_mcp_server())
    print("✅ Created minimal_server.py")
    
    # Create client test
    with open("test_mcp_client.py", "w") as f:
        f.write(create_mcp_client_test())
    print("✅ Created test_mcp_client.py")
    
    # Create potential fix
    with open("fixed_mcp_server.py", "w") as f:
        f.write(create_mcp_fix())
    print("✅ Created fixed_mcp_server.py")
    
    print("\n🔧 Debugging steps:")
    print("1. Test minimal server:")
    print("   python test_mcp_client.py")
    print("\n2. Check server logs:")
    print("   python minimal_server.py")
    print("\n3. Try the fix:")
    print("   python mcp_main_server.py  # (will use new fixed servers)")
    
    print("\n💡 This will help us identify exactly where the tuple conversion is happening!")

if __name__ == "__main__":
    main()
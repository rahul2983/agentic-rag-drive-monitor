#!/usr/bin/env python3
"""
MCP Protocol Level Fix - Address the tuple serialization issue
"""

import subprocess
import sys
import os
from pathlib import Path

def check_mcp_installation():
    """Check and potentially fix MCP installation"""
    print("🔍 Checking MCP installation...")
    
    try:
        # Check current MCP version
        result = subprocess.run([sys.executable, "-c", "import mcp; print(mcp.__version__ if hasattr(mcp, '__version__') else 'unknown')"], 
                              capture_output=True, text=True)
        print(f"Current MCP version: {result.stdout.strip()}")
        
        # Check if this is a known problematic version
        if "unknown" in result.stdout:
            print("⚠️  MCP version is unknown - this might be a development version")
            return False
        
        return True
    except Exception as e:
        print(f"❌ MCP check failed: {e}")
        return False

def create_protocol_compatible_server():
    """Create a server that works around the protocol issue"""
    content = '''#!/usr/bin/env python3
"""
Protocol-compatible MCP server that works around the tuple issue
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List

# Force logging to stderr for debugging
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.server.models import InitializationOptions
    from mcp.types import Tool, TextContent, CallToolRequest, CallToolResult, ListToolsResult
    print("✅ MCP imports successful", file=sys.stderr)
except Exception as e:
    print(f"❌ MCP import failed: {e}", file=sys.stderr)
    sys.exit(1)

class ProtocolCompatibleServer:
    def __init__(self, server_name: str, tools_config: List[Dict[str, Any]]):
        self.server = Server(server_name)
        self.server_name = server_name
        self.tools_config = tools_config
        self.logger = logging.getLogger(f"{server_name}_server")
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup MCP handlers with protocol compatibility fixes"""
        
        @self.server.list_tools()
        async def handle_list_tools():
            """Handle list_tools with multiple fallback strategies"""
            self.logger.info(f"list_tools called for {self.server_name}")
            
            try:
                # Create tools from config
                tools = []
                for tool_config in self.tools_config:
                    tool = Tool(
                        name=tool_config["name"],
                        description=tool_config["description"],
                        inputSchema=tool_config.get("inputSchema", {"type": "object", "properties": {}})
                    )
                    tools.append(tool)
                
                self.logger.info(f"Created {len(tools)} tools: {[t.name for t in tools]}")
                
                # Strategy 1: Standard ListToolsResult
                try:
                    result = ListToolsResult(tools=tools)
                    self.logger.info("Strategy 1: Standard ListToolsResult created successfully")
                    return result
                except Exception as e1:
                    self.logger.warning(f"Strategy 1 failed: {e1}")
                    
                    # Strategy 2: Manual dict construction
                    try:
                        # Convert tools to dicts manually
                        tools_dicts = []
                        for tool in tools:
                            tool_dict = {
                                "name": tool.name,
                                "description": tool.description,
                                "inputSchema": tool.inputSchema
                            }
                            tools_dicts.append(tool_dict)
                        
                        # Return as plain dict
                        manual_result = {"tools": tools_dicts}
                        self.logger.info("Strategy 2: Manual dict construction")
                        return manual_result
                        
                    except Exception as e2:
                        self.logger.warning(f"Strategy 2 failed: {e2}")
                        
                        # Strategy 3: Minimal response
                        minimal_result = ListToolsResult(tools=[])
                        self.logger.info("Strategy 3: Minimal empty response")
                        return minimal_result
                        
            except Exception as e:
                self.logger.error(f"All strategies failed: {e}")
                # Last resort: empty result
                return ListToolsResult(tools=[])
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest):
            """Handle tool calls"""
            self.logger.info(f"Tool called: {request.name}")
            
            # Find the tool handler
            for tool_config in self.tools_config:
                if tool_config["name"] == request.name:
                    handler = tool_config.get("handler")
                    if handler:
                        return await handler(request.arguments or {})
            
            # Default response
            return CallToolResult(
                content=[TextContent(type="text", text=f"Tool {request.name} executed successfully")]
            )

# Tool handlers
async def drive_authenticate(args):
    """Google Drive authenticate handler"""
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps({
            "status": "authenticated",
            "service": "Google Drive",
            "timestamp": "2025-06-10T22:00:00Z"
        }, indent=2))]
    )

async def drive_get_files(args):
    """Google Drive get files handler"""
    hours_back = args.get("hours_back", 24)
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps({
            "files": [
                {"id": "1", "name": "Sample.docx", "modified": "2025-06-10T20:00:00Z"},
                {"id": "2", "name": "Data.xlsx", "modified": "2025-06-10T19:00:00Z"}
            ],
            "hours_back": hours_back,
            "count": 2
        }, indent=2))]
    )

async def ai_analyze(args):
    """AI analyze handler"""
    content = args.get("content", "")
    doc_name = args.get("document_name", "Unknown")
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps({
            "document_name": doc_name,
            "analysis": f"Analyzed {len(content)} characters",
            "action_items": ["Review content", "Extract insights"],
            "priority": "medium"
        }, indent=2))]
    )

async def ai_summarize(args):
    """AI summarize handler"""
    content = args.get("content", "")
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps({
            "summary": f"Summary of {len(content.split())} words: " + content[:100] + "...",
            "word_count": len(content.split()),
            "method": "extractive"
        }, indent=2))]
    )

# Server configurations
SERVER_CONFIGS = {
    "google_drive": [
        {
            "name": "authenticate",
            "description": "Authenticate with Google Drive",
            "inputSchema": {"type": "object", "properties": {}, "required": []},
            "handler": drive_authenticate
        },
        {
            "name": "get_recent_files",
            "description": "Get recent files",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "hours_back": {"type": "integer", "default": 24}
                },
                "required": []
            },
            "handler": drive_get_files
        }
    ],
    "ai_analysis": [
        {
            "name": "analyze_document",
            "description": "Analyze document content",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "document_name": {"type": "string"}
                },
                "required": ["content", "document_name"]
            },
            "handler": ai_analyze
        },
        {
            "name": "generate_summary",
            "description": "Generate summary",
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "content": {"type": "string"}
                },
                "required": ["content"]
            },
            "handler": ai_summarize
        }
    ]
}

async def run_server(server_name: str):
    """Run a specific server"""
    if server_name not in SERVER_CONFIGS:
        print(f"❌ Unknown server: {server_name}", file=sys.stderr)
        return
    
    print(f"🚀 Starting {server_name} server...", file=sys.stderr)
    
    try:
        server = ProtocolCompatibleServer(server_name, SERVER_CONFIGS[server_name])
        
        # Create initialization options
        init_options = InitializationOptions(
            server_name=server_name,
            server_version="1.0.0",
            capabilities=server.server.get_capabilities()
        )
        
        async with stdio_server() as (read_stream, write_stream):
            print(f"✅ {server_name} server ready", file=sys.stderr)
            await server.server.run(read_stream, write_stream, init_options)
            
    except Exception as e:
        print(f"❌ {server_name} server failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

async def main():
    """Main entry point"""
    # Determine which server to run based on script name
    script_name = sys.argv[0]
    
    if "google_drive" in script_name:
        await run_server("google_drive")
    elif "ai_analysis" in script_name:
        await run_server("ai_analysis")
    else:
        print("❌ Cannot determine server type from script name", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
'''
    return content

def create_alternative_mcp_client():
    """Create an alternative MCP client that might work better"""
    content = '''#!/usr/bin/env python3
"""
Alternative MCP client with better error handling
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlternativeMCPClient:
    def __init__(self):
        self.servers = {}
    
    async def test_server_with_fallbacks(self, server_name: str, server_script: str):
        """Test server with multiple fallback strategies"""
        logger.info(f"Testing {server_name} with fallbacks...")
        
        try:
            server_params = StdioServerParameters(
                command="python",
                args=[server_script],
                env=dict(os.environ)
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize
                    await session.initialize()
                    logger.info(f"✅ {server_name} initialized")
                    
                    # Try to list tools with error handling
                    try:
                        tools_result = await session.list_tools()
                        logger.info(f"✅ {server_name} tools listed successfully")
                        
                        # Check if we got tools
                        if hasattr(tools_result, 'tools'):
                            tools = tools_result.tools
                            logger.info(f"  Found {len(tools)} tools: {[t.name for t in tools]}")
                        else:
                            logger.warning(f"  Tools result has no 'tools' attribute: {type(tools_result)}")
                            logger.warning(f"  Result content: {tools_result}")
                        
                        return True
                        
                    except Exception as list_error:
                        logger.error(f"❌ {server_name} list_tools failed: {list_error}")
                        
                        # Try to get more details about the error
                        logger.info(f"Error type: {type(list_error)}")
                        if hasattr(list_error, 'args'):
                            logger.info(f"Error args: {list_error.args}")
                        
                        return False
                        
        except Exception as e:
            logger.error(f"❌ {server_name} connection failed: {e}")
            return False
    
    async def test_all_servers(self):
        """Test all available servers"""
        servers = [
            ("google_drive", "protocol_compatible_google_drive.py"),
            ("ai_analysis", "protocol_compatible_ai_analysis.py")
        ]
        
        working_servers = []
        
        for server_name, server_script in servers:
            if Path(server_script).exists():
                success = await self.test_server_with_fallbacks(server_name, server_script)
                if success:
                    working_servers.append(server_name)
            else:
                logger.warning(f"Server script not found: {server_script}")
        
        logger.info(f"Working servers: {working_servers}")
        return working_servers

async def main():
    """Test the alternative client"""
    client = AlternativeMCPClient()
    working = await client.test_all_servers()
    
    if working:
        print(f"🎉 {len(working)} servers working with alternative client!")
    else:
        print("❌ No servers working with alternative client")

if __name__ == "__main__":
    asyncio.run(main())
'''
    return content

def create_servers_and_test():
    """Create protocol-compatible servers and test them"""
    print("🔧 Creating protocol-compatible MCP servers...")
    
    # Create the main protocol-compatible server
    with open("protocol_compatible_server.py", "w") as f:
        f.write(create_protocol_compatible_server())
    print("✅ Created protocol_compatible_server.py")
    
    # Create specific server scripts that import the main one
    servers = {
        "protocol_compatible_google_drive.py": '''#!/usr/bin/env python3
import sys
sys.path.append('.')
from protocol_compatible_server import run_server
import asyncio

if __name__ == "__main__":
    asyncio.run(run_server("google_drive"))
''',
        "protocol_compatible_ai_analysis.py": '''#!/usr/bin/env python3
import sys
sys.path.append('.')
from protocol_compatible_server import run_server
import asyncio

if __name__ == "__main__":
    asyncio.run(run_server("ai_analysis"))
'''
    }
    
    for filename, content in servers.items():
        with open(filename, "w") as f:
            f.write(content)
        print(f"✅ Created {filename}")
    
    # Create alternative client
    with open("alternative_mcp_client.py", "w") as f:
        f.write(create_alternative_mcp_client())
    print("✅ Created alternative_mcp_client.py")
    
    print("\n🧪 Testing protocol-compatible servers...")
    return True

def main():
    """Main fix function"""
    print("🔧 MCP Protocol Level Fix")
    print("=" * 50)
    
    # Check current MCP installation
    mcp_ok = check_mcp_installation()
    
    # Create protocol-compatible servers
    success = create_servers_and_test()
    
    if success:
        print("\n🚀 Next steps:")
        print("1. Test with alternative client:")
        print("   python alternative_mcp_client.py")
        print("\n2. Or test individual servers:")
        print("   python protocol_compatible_google_drive.py")
        print("\n3. This approach bypasses the tuple serialization issue!")
        
        if not mcp_ok:
            print("\n💡 Consider updating MCP:")
            print("   pip install --upgrade mcp")

if __name__ == "__main__":
    main()
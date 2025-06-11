#!/usr/bin/env python3
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
                    print("\n🔍 Trying to debug what was actually received...")
                    
    except Exception as e:
        print(f"❌ Client test failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_minimal_server())

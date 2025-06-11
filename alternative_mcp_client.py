#!/usr/bin/env python3
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

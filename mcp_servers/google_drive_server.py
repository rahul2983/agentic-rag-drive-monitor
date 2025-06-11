#!/usr/bin/env python3
"""
Working Google Drive Server with proper initialization
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, TextContent,
    CallToolRequest, CallToolResult, 
    ListToolsRequest, ListToolsResult
)

class GoogleDriveServer:
    def __init__(self):
        self.server = Server("google-drive")
        self.logger = logging.getLogger(__name__)
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """Return tools for Google Drive operations"""
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
                            "hours_back": {"type": "integer", "description": "Hours to look back", "default": 24}
                        },
                        "required": []
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls"""
            try:
                if request.name == "authenticate":
                    return await self._authenticate()
                elif request.name == "get_recent_files":
                    hours_back = request.arguments.get("hours_back", 24) if request.arguments else 24
                    return await self._get_recent_files(hours_back)
                else:
                    raise ValueError(f"Unknown tool: {request.name}")
            except Exception as e:
                self.logger.error(f"Tool call error: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def _authenticate(self) -> CallToolResult:
        """Simulate Google Drive authentication"""
        result = {
            "status": "authenticated",
            "message": "Google Drive authentication successful (demo mode)",
            "timestamp": datetime.now().isoformat()
        }
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _get_recent_files(self, hours_back: int) -> CallToolResult:
        """Simulate getting recent files"""
        result = {
            "files": [
                {
                    "id": "demo_file_1",
                    "name": "Sample Document.docx",
                    "modified_time": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                }
            ],
            "hours_back": hours_back,
            "count": 1,
            "message": "Demo mode - returning sample file"
        }
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )

async def main():
    """Main server entry point"""
    logging.basicConfig(level=logging.INFO)
    
    server_instance = GoogleDriveServer()
    
    # Proper initialization with all required parameters
    initialization_options = InitializationOptions(
        server_name="google-drive",
        server_version="1.0.0",
        capabilities=server_instance.server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={}
        )
    )
    
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            initialization_options  # This was missing!
        )

if __name__ == "__main__":
    asyncio.run(main())

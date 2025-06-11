#!/usr/bin/env python3
"""
Fixed Google Drive Server
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import os
from pathlib import Path

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

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleDriveServer:
    def __init__(self):
        self.server = Server("google-drive")
        self.drive_service = None
        self.credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json")
        self.token_path = os.getenv("GOOGLE_TOKEN_PATH", "./token.json")
        self.logger = logging.getLogger(__name__)
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
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
                        },
                        "required": []
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            try:
                if request.name == "authenticate":
                    return await self._authenticate()
                elif request.name == "get_recent_files":
                    return await self._get_recent_files(request.arguments.get("hours_back", 24))
                else:
                    raise ValueError(f"Unknown tool: {request.name}")
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def _authenticate(self) -> CallToolResult:
        return CallToolResult(
            content=[TextContent(type="text", text="Google Drive authentication simulated")]
        )
    
    async def _get_recent_files(self, hours_back: int) -> CallToolResult:
        result = {
            "files": [],
            "hours_back": hours_back,
            "message": "No recent files found (demo mode)"
        }
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )

async def main():
    logging.basicConfig(level=logging.INFO)
    drive_server = GoogleDriveServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await drive_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="google-drive",
                server_version="1.0.0",
                capabilities=drive_server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())

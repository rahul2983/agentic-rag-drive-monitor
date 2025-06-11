#!/usr/bin/env python3
"""
Fixed Email Server
"""

import asyncio
import json
import logging
import os

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

class EmailServer:
    def __init__(self):
        self.server = Server("email")
        self.logger = logging.getLogger(__name__)
        self.email_enabled = os.getenv("EMAIL_NOTIFICATIONS", "False").lower() == "true"
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            tools = [
                Tool(
                    name="send_summary_email",
                    description="Send a summary email",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "summary_content": {"type": "string", "description": "Email content"},
                            "recipient_type": {"type": "string", "default": "daily_summary"}
                        },
                        "required": ["summary_content"]
                    }
                ),
                Tool(
                    name="test_email_config",
                    description="Test email configuration",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            try:
                if request.name == "send_summary_email":
                    return await self._send_summary_email(request.arguments)
                elif request.name == "test_email_config":
                    return await self._test_email_config()
                else:
                    raise ValueError(f"Unknown tool: {request.name}")
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def _send_summary_email(self, args) -> CallToolResult:
        if not self.email_enabled:
            result = {"sent": False, "reason": "Email notifications disabled"}
        else:
            result = {"sent": True, "message": "Email sent (demo mode)"}
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _test_email_config(self) -> CallToolResult:
        result = {
            "email_enabled": self.email_enabled,
            "config_valid": True,
            "message": "Email config test (demo mode)"
        }
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )

async def main():
    logging.basicConfig(level=logging.INFO)
    email_server = EmailServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await email_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="email",
                server_version="1.0.0",
                capabilities=email_server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())

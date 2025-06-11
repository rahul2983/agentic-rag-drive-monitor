#!/usr/bin/env python3
"""
Working Email Server with proper initialization
"""

import asyncio
import json
import logging
import os
from datetime import datetime

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
            """Return tools for email operations"""
            tools = [
                Tool(
                    name="send_summary_email",
                    description="Send a summary email to configured recipients",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "subject": {"type": "string", "description": "Email subject"},
                            "content": {"type": "string", "description": "Email content"},
                            "recipient_type": {"type": "string", "description": "Type of recipients", "default": "summary"}
                        },
                        "required": ["subject", "content"]
                    }
                ),
                Tool(
                    name="test_email_config",
                    description="Test email configuration and connectivity",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls"""
            try:
                if request.name == "send_summary_email":
                    return await self._send_summary_email(request.arguments)
                elif request.name == "test_email_config":
                    return await self._test_email_config()
                else:
                    raise ValueError(f"Unknown tool: {request.name}")
            except Exception as e:
                self.logger.error(f"Tool call error: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def _send_summary_email(self, args) -> CallToolResult:
        """Simulate sending an email"""
        subject = args.get("subject", "No Subject")
        content = args.get("content", "")
        recipient_type = args.get("recipient_type", "summary")
        
        if not self.email_enabled:
            result = {
                "sent": False,
                "reason": "Email notifications are disabled",
                "subject": subject,
                "content_length": len(content),
                "recipient_type": recipient_type
            }
        else:
            # Simulate successful email sending
            result = {
                "sent": True,
                "message": "Email sent successfully (demo mode)",
                "subject": subject,
                "content_length": len(content),
                "recipient_type": recipient_type,
                "timestamp": datetime.now().isoformat(),
                "recipients": ["demo@example.com"]  # Demo recipient
            }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _test_email_config(self) -> CallToolResult:
        """Test email configuration"""
        config_status = {
            "email_enabled": self.email_enabled,
            "smtp_host": os.getenv("EMAIL_HOST", "Not configured"),
            "smtp_port": os.getenv("EMAIL_PORT", "Not configured"),
            "username_configured": bool(os.getenv("EMAIL_USERNAME")),
            "password_configured": bool(os.getenv("EMAIL_PASSWORD")),
            "recipients_configured": bool(os.getenv("EMAIL_RECIPIENTS")),
            "config_valid": self.email_enabled and bool(os.getenv("EMAIL_USERNAME")),
            "message": "Email configuration test completed (demo mode)"
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(config_status, indent=2))]
        )

async def main():
    """Main server entry point"""
    logging.basicConfig(level=logging.INFO)
    
    server_instance = EmailServer()
    
    # Proper initialization
    initialization_options = InitializationOptions(
        server_name="email",
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
            initialization_options
        )

if __name__ == "__main__":
    asyncio.run(main())

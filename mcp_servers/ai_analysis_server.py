#!/usr/bin/env python3
"""
Fixed AI Analysis Server
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

import openai

class AIAnalysisServer:
    def __init__(self):
        self.server = Server("ai-analysis")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = openai.OpenAI(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            tools = [
                Tool(
                    name="analyze_document",
                    description="Perform AI analysis of document content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "Document content"},
                            "document_name": {"type": "string", "description": "Document name"}
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
                            "content": {"type": "string", "description": "Content to summarize"}
                        },
                        "required": ["content"]
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            try:
                if request.name == "analyze_document":
                    return await self._analyze_document(request.arguments)
                elif request.name == "generate_summary":
                    return await self._generate_summary(request.arguments)
                else:
                    raise ValueError(f"Unknown tool: {request.name}")
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def _analyze_document(self, args) -> CallToolResult:
        result = {
            "document_name": args["document_name"],
            "summary": f"Analysis of {args['document_name']}",
            "action_items": ["Review document", "Follow up"],
            "priority": "medium",
            "analyzed_at": datetime.now().isoformat()
        }
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _generate_summary(self, args) -> CallToolResult:
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": f"Summarize: {args['content'][:1000]}"}],
                max_tokens=150,
                temperature=0.3
            )
            summary = response.choices[0].message.content.strip()
            result = {"summary": summary, "word_count": len(summary.split())}
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, indent=2))]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Summary failed: {str(e)}")],
                isError=True
            )

async def main():
    logging.basicConfig(level=logging.INFO)
    if not os.getenv("OPENAI_API_KEY"):
        logging.error("OPENAI_API_KEY environment variable is required")
        return
    
    ai_server = AIAnalysisServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await ai_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ai-analysis",
                server_version="1.0.0",
                capabilities=ai_server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())

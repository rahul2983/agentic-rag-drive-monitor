#!/usr/bin/env python3
"""
Working AI Analysis Server with proper initialization
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

# Optional: Import OpenAI if available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class AIAnalysisServer:
    def __init__(self):
        self.server = Server("ai-analysis")
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client if available
        self.openai_client = None
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """Return tools for AI analysis operations"""
            tools = [
                Tool(
                    name="analyze_document",
                    description="Perform AI analysis of document content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "Document content to analyze"},
                            "document_name": {"type": "string", "description": "Name of the document"}
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
                            "content": {"type": "string", "description": "Content to summarize"},
                            "max_length": {"type": "integer", "description": "Maximum summary length", "default": 150}
                        },
                        "required": ["content"]
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls"""
            try:
                if request.name == "analyze_document":
                    return await self._analyze_document(request.arguments)
                elif request.name == "generate_summary":
                    return await self._generate_summary(request.arguments)
                else:
                    raise ValueError(f"Unknown tool: {request.name}")
            except Exception as e:
                self.logger.error(f"Tool call error: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def _analyze_document(self, args) -> CallToolResult:
        """Analyze a document"""
        content = args.get("content", "")
        document_name = args.get("document_name", "Unknown Document")
        
        # Basic analysis (can be enhanced with real AI)
        word_count = len(content.split())
        char_count = len(content)
        
        result = {
            "document_name": document_name,
            "analysis": {
                "word_count": word_count,
                "character_count": char_count,
                "estimated_reading_time": f"{max(1, word_count // 200)} minutes"
            },
            "summary": f"Document '{document_name}' contains {word_count} words",
            "action_items": ["Review document content", "Extract key points"],
            "priority": "medium" if word_count > 500 else "low",
            "analyzed_at": datetime.now().isoformat(),
            "ai_available": self.openai_client is not None
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _generate_summary(self, args) -> CallToolResult:
        """Generate a summary"""
        content = args.get("content", "")
        max_length = args.get("max_length", 150)
        
        if self.openai_client:
            try:
                # Use real AI if available
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": f"Summarize this in {max_length} words or less: {content[:2000]}"}
                    ],
                    max_tokens=max_length,
                    temperature=0.3
                )
                summary = response.choices[0].message.content.strip()
                method = "OpenAI GPT-3.5"
            except Exception as e:
                # Fallback to simple summary
                summary = f"Summary of {len(content.split())} word document: {content[:max_length]}..."
                method = f"Fallback (OpenAI error: {str(e)})"
        else:
            # Simple extractive summary
            sentences = content.split('. ')
            summary = '. '.join(sentences[:3]) + "..." if len(sentences) > 3 else content
            method = "Simple extractive"
        
        result = {
            "summary": summary,
            "method": method,
            "word_count": len(summary.split()),
            "original_length": len(content.split()),
            "compression_ratio": f"{len(summary.split()) / max(1, len(content.split())):.2f}"
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )

async def main():
    """Main server entry point"""
    logging.basicConfig(level=logging.INFO)
    
    server_instance = AIAnalysisServer()
    
    # Proper initialization
    initialization_options = InitializationOptions(
        server_name="ai-analysis",
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

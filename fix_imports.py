#!/usr/bin/env python3
"""
Quick fix script to update MCP imports in all server files
"""

import os
import re
from pathlib import Path

def fix_mcp_imports():
    """Fix MCP imports in all server files"""
    
    # Files that need fixing
    server_files = [
        "mcp_servers/google_drive_server.py",
        "mcp_servers/ai_analysis_server.py", 
        "mcp_servers/google_calendar_server.py",
        "mcp_servers/email_server.py"
    ]
    
    # Old import pattern to replace
    old_import_pattern = r"""from mcp\.types import \(
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, CallToolResult, GetResourceRequest, GetResourceResult,
    ListResourcesRequest, ListResourcesResult, ListToolsRequest, ListToolsResult
\)"""

    # New correct import
    new_import = """from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, CallToolResult, 
    ReadResourceRequest, ReadResourceResult,
    ListResourcesRequest, ListResourcesResult, 
    ListToolsRequest, ListToolsResult
)"""

    print("🔧 Fixing MCP imports in server files...")
    
    for file_path in server_files:
        if os.path.exists(file_path):
            try:
                # Read the file
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Replace the old import with new import
                content = re.sub(old_import_pattern, new_import, content, flags=re.MULTILINE | re.DOTALL)
                
                # Also handle simple single-line replacements
                content = content.replace("GetResourceRequest", "ReadResourceRequest")
                content = content.replace("GetResourceResult", "ReadResourceResult")
                
                # Write back the file
                with open(file_path, 'w') as f:
                    f.write(content)
                
                print(f"✅ Fixed {file_path}")
                
            except Exception as e:
                print(f"❌ Error fixing {file_path}: {e}")
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print("\n🎉 MCP import fixes completed!")
    print("You can now run the servers successfully.")

if __name__ == "__main__":
    fix_mcp_imports()
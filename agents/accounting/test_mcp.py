#!/usr/bin/env python3
"""
Test script for the MCP server
"""

import asyncio
import json
from mcp_server import AccountingMCPServer

async def test_mcp_server():
    """Test the MCP server functionality"""
    server = AccountingMCPServer()
    
    print("🧪 Testing MCP Server...")
    
    # Test app status
    print("\n1. Testing app status...")
    result = await server._app_status({})
    print(f"App Status: {result.content[0].text}")
    
    # Test listing reports
    print("\n2. Testing list reports...")
    result = await server._list_reports({})
    print(f"Reports: {result.content[0].text}")
    
    # Test getting config
    print("\n3. Testing get config...")
    result = await server._get_app_config({})
    print(f"Config: {result.content[0].text}")
    
    print("\n✅ MCP Server test completed!")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())

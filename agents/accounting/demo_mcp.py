#!/usr/bin/env python3
"""
Demo script showing MCP server capabilities
"""

import asyncio
from mcp_server import AccountingMCPServer

async def demo_mcp_server():
    """Demonstrate MCP server functionality"""
    server = AccountingMCPServer()
    
    print("🎯 MCP Server Demo for Accounting Agent")
    print("=" * 50)
    
    # Demo 1: Check app status
    print("\n1️⃣ Checking app status...")
    result = await server._app_status({})
    print(f"   Result: {result.content[0].text}")
    
    # Demo 2: Start the app
    print("\n2️⃣ Starting the Flask app...")
    result = await server._start_app({"port": 8080})
    print(f"   Result: {result.content[0].text}")
    
    # Demo 3: Check status again
    print("\n3️⃣ Checking app status after start...")
    result = await server._app_status({})
    print(f"   Result: {result.content[0].text}")
    
    # Demo 4: List reports
    print("\n4️⃣ Listing available reports...")
    result = await server._list_reports({})
    print(f"   Result: {result.content[0].text}")
    
    # Demo 5: Get configuration
    print("\n5️⃣ Getting app configuration...")
    result = await server._get_app_config({})
    config_text = result.content[0].text
    print(f"   Result: {config_text[:200]}...")
    
    # Demo 6: Stop the app
    print("\n6️⃣ Stopping the Flask app...")
    result = await server._stop_app({})
    print(f"   Result: {result.content[0].text}")
    
    print("\n✅ Demo completed!")
    print("\n💡 In Cursor, you can now use natural language commands like:")
    print("   - 'Start the accounting app'")
    print("   - 'Process this CSV file: /path/to/file.csv'")
    print("   - 'Generate reports from Google Sheets'")
    print("   - 'Send reports via WhatsApp'")

if __name__ == "__main__":
    asyncio.run(demo_mcp_server())

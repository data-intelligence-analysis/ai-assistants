#!/usr/bin/env python3
"""
Setup script for MCP integration
"""

import os
import json
import platform
from pathlib import Path

def get_cursor_config_path():
    """Get the Cursor MCP configuration file path based on OS"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / ".cursor" / "mcp_config.json"
    elif system == "Windows":
        return Path(os.environ["APPDATA"]) / "Cursor" / "mcp_config.json"
    else:  # Linux
        return Path.home() / ".cursor" / "mcp_config.json"

def create_mcp_config():
    """Create MCP configuration for Cursor"""
    config_path = get_cursor_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get current directory
    current_dir = Path(__file__).parent.absolute()
    
    config = {
        "mcpServers": {
            "accounting-agent": {
                "command": "python",
                "args": ["mcp_server.py"],
                "cwd": str(current_dir),
                "env": {
                    "PYTHONPATH": str(current_dir)
                }
            }
        }
    }
    
    # Write configuration
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ MCP configuration created at: {config_path}")
    return config_path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import mcp
        print("✅ MCP library is installed")
        return True
    except ImportError:
        print("❌ MCP library not found. Installing...")
        os.system("pip install mcp")
        return True

def main():
    """Main setup function"""
    print("🚀 Setting up MCP integration for Accounting Agent...")
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Failed to install dependencies")
        return
    
    # Create MCP config
    config_path = create_mcp_config()
    
    print("\n📋 Next steps:")
    print("1. Restart Cursor to load the MCP server")
    print("2. Try saying: 'Start the accounting app'")
    print("3. Check the MCP_README.md for more commands")
    
    print(f"\n⚙️ Configuration file: {config_path}")
    print("🔧 You can modify this file if needed")

if __name__ == "__main__":
    main()

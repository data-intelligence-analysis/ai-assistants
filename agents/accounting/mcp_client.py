#!/usr/bin/env python3
"""
MCP Client for communicating with the MCP server
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

class MCPClient:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.mcp_server_process = None
        
    def start_mcp_server(self):
        """Start the MCP server in the background"""
        try:
            if self.mcp_server_process and self.mcp_server_process.poll() is None:
                return True
                
            self.mcp_server_process = subprocess.Popen([
                sys.executable, "mcp_server.py"
            ], cwd=str(self.base_dir))
            
            # Wait a moment for the server to start
            import time
            time.sleep(2)
            
            return self.mcp_server_process.poll() is None
        except Exception as e:
            print(f"Error starting MCP server: {e}")
            return False
    
    def stop_mcp_server(self):
        """Stop the MCP server"""
        if self.mcp_server_process and self.mcp_server_process.poll() is None:
            self.mcp_server_process.terminate()
            self.mcp_server_process.wait()
            return True
        return False
    
    def is_mcp_server_running(self):
        """Check if MCP server is running"""
        return self.mcp_server_process and self.mcp_server_process.poll() is None
    
    async def execute_mcp_command(self, command: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a command through the MCP server"""
        try:
            # Import the MCP server class directly
            from mcp_server import AccountingMCPServer
            
            server = AccountingMCPServer()
            
            # Map command names to server methods
            command_map = {
                'start_app': server._start_app,
                'stop_app': server._stop_app,
                'app_status': server._app_status,
                'process_csv': server._process_csv,
                'process_google_sheets': server._process_google_sheets,
                'process_excel_url': server._process_excel_url,
                'generate_reports': server._generate_reports,
                'send_reports': server._send_reports,
                'list_reports': server._list_reports,
                'get_app_config': server._get_app_config
            }
            
            if command in command_map:
                result = await command_map[command](args or {})
                return {
                    'success': True,
                    'message': result.content[0].text if result.content else 'Command executed',
                    'data': result
                }
            else:
                return {
                    'success': False,
                    'message': f'Unknown command: {command}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error executing command: {str(e)}'
            }
    
    def process_helper_prompt(self, prompt: str) -> Dict[str, Any]:
        """Process helper prompt commands"""
        prompt_lower = prompt.lower()
        
        if 'generate reports from google sheets' in prompt_lower:
            return {
                'command': 'process_google_sheets',
                'args': {
                    'sheet_name': 'Business Expenses',
                    'worksheet': 'Transactions',
                    'send_reports': False
                }
            }
        elif 'start accounting app' in prompt_lower:
            return {
                'command': 'start_app',
                'args': {'port': 8080}
            }
        elif 'process csv file' in prompt_lower:
            return {
                'command': 'process_csv',
                'args': {
                    'file_path': 'data/transactions/transactions_sample.csv',
                    'send_reports': False
                }
            }
        elif 'generate reports from csv' in prompt_lower:
            return {
                'command': 'process_csv',
                'args': {
                    'file_path': 'data/transactions/transactions_sample.csv',
                    'send_reports': True
                }
            }
        else:
            return {
                'command': 'app_status',
                'args': {}
            }

# Global MCP client instance
mcp_client = MCPClient()

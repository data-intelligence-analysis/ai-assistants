#!/usr/bin/env python3
"""
MCP Server for Accounting Agent
Allows natural language interaction with the Flask accounting app
"""

import asyncio
import json
import subprocess
import sys
import time
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import yaml

# MCP imports
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Import our app modules
from file_loader import load_config
from categorizer import Categorizer
from statements import income_statement, balance_sheet
from pdf_render import income_statement_pdf, balance_sheet_pdf
from send_reports import send_telegram_reports, send_whatsapp_reports

class AccountingMCPServer:
    def __init__(self):
        self.server = Server("accounting-agent")
        self.app_process = None
        self.app_url = "http://localhost:8080"
        self.base_dir = Path(__file__).parent
        self.output_dir = self.base_dir / 'output'
        self.upload_dir = self.base_dir / 'data' / 'transactions'
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP tool handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available tools for the accounting agent"""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="start_app",
                        description="Start the Flask accounting app server",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "port": {
                                    "type": "integer",
                                    "description": "Port to run the app on (default: 8080)",
                                    "default": 8080
                                }
                            }
                        }
                    ),
                    Tool(
                        name="stop_app",
                        description="Stop the Flask accounting app server",
                        inputSchema={
                            "type": "object",
                            "properties": {}
                        }
                    ),
                    Tool(
                        name="app_status",
                        description="Check if the Flask app is running and get its status",
                        inputSchema={
                            "type": "object",
                            "properties": {}
                        }
                    ),
                    Tool(
                        name="process_csv",
                        description="Process a CSV file and generate accounting reports",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Path to the CSV file to process"
                                },
                                "send_reports": {
                                    "type": "boolean",
                                    "description": "Whether to send reports via WhatsApp/Telegram",
                                    "default": False
                                }
                            },
                            "required": ["file_path"]
                        }
                    ),
                    Tool(
                        name="process_google_sheets",
                        description="Process data from Google Sheets and generate reports",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "sheet_name": {
                                    "type": "string",
                                    "description": "Name of the Google Sheet"
                                },
                                "worksheet": {
                                    "type": "string",
                                    "description": "Worksheet name",
                                    "default": "Transactions"
                                },
                                "send_reports": {
                                    "type": "boolean",
                                    "description": "Whether to send reports via WhatsApp/Telegram",
                                    "default": False
                                }
                            },
                            "required": ["sheet_name"]
                        }
                    ),
                    Tool(
                        name="process_excel_url",
                        description="Process Excel file from URL and generate reports",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "url": {
                                    "type": "string",
                                    "description": "URL of the Excel file"
                                },
                                "sheet_name": {
                                    "type": "string",
                                    "description": "Sheet name to process",
                                    "default": None
                                },
                                "send_reports": {
                                    "type": "boolean",
                                    "description": "Whether to send reports via WhatsApp/Telegram",
                                    "default": False
                                }
                            },
                            "required": ["url"]
                        }
                    ),
                    Tool(
                        name="generate_reports",
                        description="Generate income statement and balance sheet from existing data",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "data_source": {
                                    "type": "string",
                                    "description": "Data source: 'csv', 'sheets', or 'excel'",
                                    "enum": ["csv", "sheets", "excel"]
                                },
                                "source_config": {
                                    "type": "object",
                                    "description": "Configuration for the data source"
                                },
                                "send_reports": {
                                    "type": "boolean",
                                    "description": "Whether to send reports via WhatsApp/Telegram",
                                    "default": False
                                }
                            },
                            "required": ["data_source", "source_config"]
                        }
                    ),
                    Tool(
                        name="send_reports",
                        description="Send generated reports via WhatsApp or Telegram",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "platform": {
                                    "type": "string",
                                    "description": "Platform to send reports: 'whatsapp' or 'telegram'",
                                    "enum": ["whatsapp", "telegram"]
                                },
                                "report_paths": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Paths to PDF reports to send"
                                }
                            },
                            "required": ["platform", "report_paths"]
                        }
                    ),
                    Tool(
                        name="list_reports",
                        description="List available generated reports",
                        inputSchema={
                            "type": "object",
                            "properties": {}
                        }
                    ),
                    Tool(
                        name="get_app_config",
                        description="Get the current app configuration",
                        inputSchema={
                            "type": "object",
                            "properties": {}
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "start_app":
                    return await self._start_app(arguments)
                elif name == "stop_app":
                    return await self._stop_app(arguments)
                elif name == "app_status":
                    return await self._app_status(arguments)
                elif name == "process_csv":
                    return await self._process_csv(arguments)
                elif name == "process_google_sheets":
                    return await self._process_google_sheets(arguments)
                elif name == "process_excel_url":
                    return await self._process_excel_url(arguments)
                elif name == "generate_reports":
                    return await self._generate_reports(arguments)
                elif name == "send_reports":
                    return await self._send_reports(arguments)
                elif name == "list_reports":
                    return await self._list_reports(arguments)
                elif name == "get_app_config":
                    return await self._get_app_config(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Unknown tool: {name}")]
                    )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")]
                )
    
    async def _start_app(self, args: Dict[str, Any]) -> CallToolResult:
        """Start the Flask app"""
        port = args.get("port", 8080)
        
        if self.app_process and self.app_process.poll() is None:
            return CallToolResult(
                content=[TextContent(type="text", text="App is already running")]
            )
        
        try:
            # Start the Flask app
            self.app_process = subprocess.Popen([
                sys.executable, "app.py"
            ], cwd=str(self.base_dir))
            
            # Wait a moment for the app to start
            await asyncio.sleep(3)
            
            # Check if it's running
            if self.app_process.poll() is None:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"✅ Flask app started successfully on port {port}")]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text="❌ Failed to start Flask app")]
                )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error starting app: {str(e)}")]
            )
    
    async def _stop_app(self, args: Dict[str, Any]) -> CallToolResult:
        """Stop the Flask app"""
        if self.app_process and self.app_process.poll() is None:
            self.app_process.terminate()
            self.app_process.wait()
            return CallToolResult(
                content=[TextContent(type="text", text="✅ Flask app stopped")]
            )
        else:
            return CallToolResult(
                content=[TextContent(type="text", text="❌ No app is currently running")]
            )
    
    async def _app_status(self, args: Dict[str, Any]) -> CallToolResult:
        """Check app status"""
        if self.app_process and self.app_process.poll() is None:
            try:
                response = requests.get(f"{self.app_url}/", timeout=5)
                if response.status_code == 200:
                    return CallToolResult(
                        content=[TextContent(type="text", text="✅ App is running and responding")]
                    )
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"⚠️ App is running but returned status {response.status_code}")]
                    )
            except requests.RequestException:
                return CallToolResult(
                    content=[TextContent(type="text", text="⚠️ App process is running but not responding")]
                )
        else:
            return CallToolResult(
                content=[TextContent(type="text", text="❌ App is not running")]
            )
    
    async def _process_csv(self, args: Dict[str, Any]) -> CallToolResult:
        """Process CSV file and generate reports"""
        file_path = Path(args["file_path"])
        send_reports = args.get("send_reports", False)
        
        if not file_path.exists():
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ File not found: {file_path}")]
            )
        
        try:
            # Load and process data
            df = pd.read_csv(file_path, parse_dates=["date"])
            df = self._classify_transactions(df)
            
            # Generate reports
            inc = income_statement(df)
            bal = balance_sheet({"assets": {}, "liabilities": {}, "equity": {}}, df, df["date"].max())
            
            # Create PDFs
            income_pdf = self.output_dir / "income_statement.pdf"
            balance_pdf = self.output_dir / "balance_sheet.pdf"
            
            income_statement_pdf(inc, str(income_pdf))
            balance_sheet_pdf(bal, str(balance_pdf))
            
            result = f"✅ Reports generated successfully:\n- Income Statement: {income_pdf}\n- Balance Sheet: {balance_pdf}"
            
            if send_reports:
                try:
                    send_whatsapp_reports([str(income_pdf), str(balance_pdf)])
                    result += "\n📱 Reports sent via WhatsApp"
                except Exception as e:
                    result += f"\n⚠️ Failed to send via WhatsApp: {str(e)}"
            
            return CallToolResult(
                content=[TextContent(type="text", text=result)]
            )
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error processing CSV: {str(e)}")]
            )
    
    async def _process_google_sheets(self, args: Dict[str, Any]) -> CallToolResult:
        """Process Google Sheets data"""
        sheet_name = args["sheet_name"]
        worksheet = args.get("worksheet", "Transactions")
        send_reports = args.get("send_reports", False)
        
        try:
            from connectors.google_sheets import fetch_google_sheets
            df = fetch_google_sheets(sheet_name, worksheet)
            return await self._process_dataframe(df, "Google Sheets", send_reports)
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error processing Google Sheets: {str(e)}")]
            )
    
    async def _process_excel_url(self, args: Dict[str, Any]) -> CallToolResult:
        """Process Excel file from URL"""
        url = args["url"]
        sheet_name = args.get("sheet_name")
        send_reports = args.get("send_reports", False)
        
        try:
            from connectors.excel import fetch_excel_from_url
            df = fetch_excel_from_url(url, sheet_name=sheet_name)
            return await self._process_dataframe(df, "Excel URL", send_reports)
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error processing Excel URL: {str(e)}")]
            )
    
    async def _process_dataframe(self, df: pd.DataFrame, source: str, send_reports: bool) -> CallToolResult:
        """Common processing for any DataFrame"""
        try:
            df = self._classify_transactions(df)
            
            # Generate reports
            inc = income_statement(df)
            bal = balance_sheet({"assets": {}, "liabilities": {}, "equity": {}}, df, df["date"].max())
            
            # Create PDFs
            income_pdf = self.output_dir / "income_statement.pdf"
            balance_pdf = self.output_dir / "balance_sheet.pdf"
            
            income_statement_pdf(inc, str(income_pdf))
            balance_sheet_pdf(bal, str(balance_pdf))
            
            result = f"✅ Reports generated from {source}:\n- Income Statement: {income_pdf}\n- Balance Sheet: {balance_pdf}"
            
            if send_reports:
                try:
                    send_whatsapp_reports([str(income_pdf), str(balance_pdf)])
                    result += "\n📱 Reports sent via WhatsApp"
                except Exception as e:
                    result += f"\n⚠️ Failed to send via WhatsApp: {str(e)}"
            
            return CallToolResult(
                content=[TextContent(type="text", text=result)]
            )
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error processing data: {str(e)}")]
            )
    
    async def _generate_reports(self, args: Dict[str, Any]) -> CallToolResult:
        """Generate reports from various data sources"""
        data_source = args["data_source"]
        source_config = args["source_config"]
        send_reports = args.get("send_reports", False)
        
        try:
            if data_source == "csv":
                file_path = source_config.get("file_path")
                if not file_path:
                    return CallToolResult(
                        content=[TextContent(type="text", text="❌ CSV file path required")]
                    )
                return await self._process_csv({"file_path": file_path, "send_reports": send_reports})
            
            elif data_source == "sheets":
                sheet_name = source_config.get("sheet_name")
                worksheet = source_config.get("worksheet", "Transactions")
                return await self._process_google_sheets({
                    "sheet_name": sheet_name,
                    "worksheet": worksheet,
                    "send_reports": send_reports
                })
            
            elif data_source == "excel":
                url = source_config.get("url")
                sheet_name = source_config.get("sheet_name")
                return await self._process_excel_url({
                    "url": url,
                    "sheet_name": sheet_name,
                    "send_reports": send_reports
                })
            
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"❌ Unknown data source: {data_source}")]
                )
                
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error generating reports: {str(e)}")]
            )
    
    async def _send_reports(self, args: Dict[str, Any]) -> CallToolResult:
        """Send reports via WhatsApp or Telegram"""
        platform = args["platform"]
        report_paths = args["report_paths"]
        
        try:
            if platform == "whatsapp":
                send_whatsapp_reports(report_paths)
                return CallToolResult(
                    content=[TextContent(type="text", text=f"✅ Reports sent via WhatsApp: {', '.join(report_paths)}")]
                )
            elif platform == "telegram":
                send_telegram_reports(report_paths)
                return CallToolResult(
                    content=[TextContent(type="text", text=f"✅ Reports sent via Telegram: {', '.join(report_paths)}")]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"❌ Unknown platform: {platform}")]
                )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error sending reports: {str(e)}")]
            )
    
    async def _list_reports(self, args: Dict[str, Any]) -> CallToolResult:
        """List available reports"""
        try:
            pdf_files = list(self.output_dir.glob("*.pdf"))
            if pdf_files:
                report_list = "\n".join([f"- {f.name}" for f in pdf_files])
                return CallToolResult(
                    content=[TextContent(type="text", text=f"📊 Available reports:\n{report_list}")]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text="📊 No reports found")]
                )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error listing reports: {str(e)}")]
            )
    
    async def _get_app_config(self, args: Dict[str, Any]) -> CallToolResult:
        """Get app configuration"""
        try:
            config = load_config()
            config_text = json.dumps(config, indent=2)
            return CallToolResult(
                content=[TextContent(type="text", text=f"⚙️ App Configuration:\n{config_text}")]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"❌ Error loading config: {str(e)}")]
            )
    
    def _classify_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Classify transactions using the categorizer"""
        categorizer = Categorizer()
        return categorizer.categorize(df)
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="accounting-agent",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )

async def main():
    """Main entry point"""
    server = AccountingMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())

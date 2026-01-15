#!/usr/bin/env python3
"""
Startup script to run both Flask app and MCP server
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

class ServiceManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.flask_process = None
        self.mcp_process = None
        
    def start_mcp_server(self):
        """Start the MCP server"""
        try:
            print("🚀 Starting MCP server...")
            self.mcp_process = subprocess.Popen([
                sys.executable, "mcp_server.py"
            ], cwd=str(self.base_dir))
            
            # Wait for MCP server to start
            time.sleep(3)
            
            if self.mcp_process.poll() is None:
                print("✅ MCP server started successfully")
                return True
            else:
                print("❌ Failed to start MCP server")
                return False
                
        except Exception as e:
            print(f"❌ Error starting MCP server: {e}")
            return False
    
    def start_flask_app(self):
        """Start the Flask app"""
        try:
            print("🚀 Starting Flask app...")
            self.flask_process = subprocess.Popen([
                sys.executable, "app.py"
            ], cwd=str(self.base_dir))
            
            # Wait for Flask app to start
            time.sleep(3)
            
            if self.flask_process.poll() is None:
                print("✅ Flask app started successfully")
                return True
            else:
                print("❌ Failed to start Flask app")
                return False
                
        except Exception as e:
            print(f"❌ Error starting Flask app: {e}")
            return False
    
    def stop_services(self):
        """Stop all services"""
        print("\n🛑 Stopping services...")
        
        if self.flask_process and self.flask_process.poll() is None:
            self.flask_process.terminate()
            self.flask_process.wait()
            print("✅ Flask app stopped")
        
        if self.mcp_process and self.mcp_process.poll() is None:
            self.mcp_process.terminate()
            self.mcp_process.wait()
            print("✅ MCP server stopped")
    
    def check_services(self):
        """Check if services are running"""
        flask_running = self.flask_process and self.flask_process.poll() is None
        mcp_running = self.mcp_process and self.mcp_process.poll() is None
        
        print(f"📊 Service Status:")
        print(f"   Flask App: {'✅ Running' if flask_running else '❌ Stopped'}")
        print(f"   MCP Server: {'✅ Running' if mcp_running else '❌ Stopped'}")
        
        return flask_running and mcp_running
    
    def run(self):
        """Run both services"""
        print("🎯 Starting Accounting Agent Services")
        print("=" * 50)
        
        # Start MCP server first
        if not self.start_mcp_server():
            print("❌ Failed to start MCP server. Exiting.")
            return
        
        # Start Flask app
        if not self.start_flask_app():
            print("❌ Failed to start Flask app. Exiting.")
            self.stop_services()
            return
        
        print("\n🎉 All services started successfully!")
        print("📱 Access your app at: http://localhost:8080")
        print("🔧 Advanced interface: http://localhost:8080/advanced")
        print("\n💡 Helper prompts are now active:")
        print("   - Generate reports from Google Sheets")
        print("   - Start accounting app")
        print("   - Process CSV file")
        print("   - Generate reports from CSV")
        print("\nPress Ctrl+C to stop all services")
        
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            self.stop_services()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Keep services running
        try:
            while True:
                time.sleep(10)
                if not self.check_services():
                    print("⚠️  One or more services stopped unexpectedly")
                    break
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_services()

if __name__ == "__main__":
    manager = ServiceManager()
    manager.run()

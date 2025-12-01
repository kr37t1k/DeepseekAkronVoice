#!/usr/bin/env python3
"""
Script to run both LLaMA server and MCP servers together for enhanced functionality
"""
import sys
import os
import argparse
import threading
import time
import subprocess
from llama_server import main as server_main
import platform

def run_mcp_server():
    """Run the appropriate MCP server based on the platform"""
    system_name = platform.system().lower()
    
    if system_name == "android":
        # For Android (Termux), run Android MCP server
        print("📱 Starting Android MCP server...")
        os.system("python mcp_android.py")
    else:
        # For Windows and other systems, run Windows MCP server
        print("🖥️ Starting Windows MCP server...")
        os.system("python mcp_windows.py")

def run_llama_server(args):
    """Run the LLaMA server with provided arguments"""
    print(f"🚀 Starting LLaMA server on {args.host}:{args.port}")
    print(f"📁 Using model: {args.model_path}")
    print(f"💡 Make sure your phone and computer are on the same network")
    print(f"💡 Connect to: http://{args.host}:{args.port}/v1/chat/completions")
    
    # Set up sys.argv for llama_server
    original_argv = sys.argv[:]
    try:
        sys.argv = [
            'llama_server.py',
            '--model-path', args.model_path,
            '--host', args.host,
            '--port', str(args.port),
            '--n_ctx', str(args.n_ctx)
        ]
        server_main()
    except KeyboardInterrupt:
        print("\n🛑 LLaMA server stopped by user")
    except Exception as e:
        print(f"❌ Error running LLaMA server: {e}")
    finally:
        sys.argv = original_argv

def main():
    parser = argparse.ArgumentParser(description='Run LLaMA server and MCP servers together')
    parser.add_argument('--model-path', type=str, required=True, 
                       help='Path to the GGUF model file')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host to bind server to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8001,
                       help='Port to bind LLaMA server to (default: 8001)')
    parser.add_argument('--mcp-port', type=int, default=3000,
                       help='Port to bind MCP server to (default: 3000 for Android, 3001 for Windows)')
    parser.add_argument('--n_ctx', type=int, default=2048,
                       help='Context size for the model (default: 2048)')
    
    args = parser.parse_args()
    
    print("🌟 Starting LLaMA and MCP servers together...")
    
    # Determine which MCP port to use based on platform
    system_name = platform.system().lower()
    if system_name == "android":
        mcp_port = 3000
        print(f"📱 Platform detected: Android - using MCP port {mcp_port}")
    else:
        mcp_port = 3001
        print(f"🖥️ Platform detected: {system_name.title()} - using MCP port {mcp_port}")
    
    # Start MCP server in a separate thread
    mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_thread.start()
    
    # Wait a moment for MCP server to start
    time.sleep(2)
    
    # Start LLaMA server in the main thread
    run_llama_server(args)

if __name__ == "__main__":
    main()
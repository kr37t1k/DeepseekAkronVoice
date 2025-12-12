#!/usr/bin/env python3
"""
Unified Server Launcher for Streaming LLaMA and MCP Servers
This script launches both servers with document parsing, streaming support and stable sync capabilities
"""

import argparse
import sys
import os
import subprocess
import threading
import time
import signal
import requests
from pathlib import Path
import json

def check_requirements():
    """Check if required packages are available"""
    missing_packages = []
    
    try:
        import llama_cpp
    except ImportError:
        missing_packages.append("llama-cpp-python")
    
    try:
        import aiohttp
    except ImportError:
        missing_packages.append("aiohttp")
    
    try:
        import psutil
    except ImportError:
        missing_packages.append("psutil")
    
    if missing_packages:
        print(f"⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def test_server_health(url, server_name):
    """Test if server is running and responding"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {server_name} is healthy")
            return True
        else:
            print(f"❌ {server_name} returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {server_name} is not responding: {e}")
        return False

def run_llama_server(model_path, host='0.0.0.0', port=8001):
    """Run the streaming LLaMA server in a separate thread"""
    from streaming_llama_server import run_server as llama_run_server
    from streaming_llama_server import MockLlamaModel, ServerState, EnhancedLlamaRequestHandler
    
    # Load model or use mock
    model = MockLlamaModel()  # Using mock for testing
    
    # Create server state
    server_state = ServerState()
    
    def handler_factory(*args, **kwargs):
        return EnhancedLlamaRequestHandler(model, server_state, *args, **kwargs)
    
    # Import and run server
    from streaming_llama_server import ThreadedHTTPServer
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from streaming_llama_server import Llama
        LLAMA_AVAILABLE = True
    except ImportError:
        LLAMA_AVAILABLE = False
    
    if LLAMA_AVAILABLE and model_path and os.path.exists(model_path):
        try:
            model = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_threads=4,
                n_batch=512,
                seed=-1,
                n_threads_batch=0,
                chat_format=("qwen" if "qwen" in model_path.lower() else "llama-3"),
                offload_kqv=True,
                verbose=False
            )
            print(f"✅ Model loaded from {model_path}")
        except Exception as e:
            print(f"⚠️  Failed to load model: {e}, using mock model")
            model = MockLlamaModel()
    else:
        print("⚠️  Model path not specified or not found, using mock model")
        model = MockLlamaModel()
    
    # Create and run server
    from streaming_llama_server import ThreadedHTTPServer
    server = ThreadedHTTPServer((host, port), lambda *args, **kwargs: EnhancedLlamaRequestHandler(model, server_state, *args, **kwargs))
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Starting streaming LLaMA server on {host}:{port}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down LLaMA server...")
        server_state.is_running = False
        server.shutdown()
        server.server_close()

def run_mcp_server(host='0.0.0.0', port=3000):
    """Run the enhanced MCP server in a separate thread"""
    from enhanced_mcp_server import run_server, MCPConfig
    
    config = MCPConfig(host=host, port=port, sync_interval=10)
    
    # Import and run server
    from enhanced_mcp_server import MCPEnhancedServer
    import logging
    logger = logging.getLogger(__name__)
    
    server = MCPEnhancedServer(config)
    
    logger.info(f"Starting enhanced MCP server on {config.host}:{config.port}")
    
    import asyncio
    from aiohttp import web
    
    try:
        web.run_app(server.app, host=config.host, port=config.port, handle_signals=False)
    except KeyboardInterrupt:
        logger.info("Shutting down MCP server...")

def main():
    parser = argparse.ArgumentParser(description='Unified Server Launcher for Streaming LLaMA and MCP Servers')
    parser.add_argument('--model-path', type=str, 
                       help='Path to the GGUF model file (optional, uses mock if not provided)')
    parser.add_argument('--llama-port', type=int, default=8001,
                       help='Port for LLaMA server (default: 8001)')
    parser.add_argument('--mcp-port', type=int, default=3000,
                       help='Port for MCP server (default: 3000)')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host to bind servers to (default: 0.0.0.0)')
    parser.add_argument('--test', action='store_true',
                       help='Run basic functionality tests after starting servers')
    parser.add_argument('--demo-file', type=str, 
                       help='Path to a sample file for testing document parsing')
    
    args = parser.parse_args()
    
    print("🚀 Starting Unified Streaming Server Launcher...")
    print(f"📁 Model path: {args.model_path or 'Using mock model'}")
    print(f"🌐 LLaMA server: http://{args.host}:{args.llama_port}")
    print(f"🌐 MCP server: http://{args.host}:{args.mcp_port}")
    print(f"📋 Test mode: {'Enabled' if args.test else 'Disabled'}")
    
    # Check requirements
    if not check_requirements():
        print("⚠️  Some requirements are missing. Servers may not work properly.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    # Start servers in separate threads
    llama_thread = threading.Thread(
        target=run_llama_server, 
        args=(args.model_path or "", args.host, args.llama_port),
        daemon=True
    )
    
    mcp_thread = threading.Thread(
        target=run_mcp_server, 
        args=(args.host, args.mcp_port),
        daemon=True
    )
    
    # Start both servers
    print("🚀 Starting streaming LLaMA server...")
    llama_thread.start()
    
    time.sleep(2)  # Give LLaMA server a moment to start
    
    print("🚀 Starting MCP server...")
    mcp_thread.start()
    
    # Wait a bit for servers to initialize
    time.sleep(3)
    
    print(f"✅ Servers started successfully!")
    print(f"💡 LLaMA API: http://{args.host}:{args.llama_port}/v1/chat/completions")
    print(f"💡 MCP WebSocket: ws://{args.host}:{args.mcp_port}/mcp")
    print(f"💡 LLaMA Health: http://{args.host}:{args.llama_port}/health")
    print(f"💡 MCP Health: http://{args.host}:{args.mcp_port}/health")
    print(f"💡 Document parsing: http://{args.host}:{args.llama_port}/parse/file_path")
    print(f"💡 Streaming supported: http://{args.host}:{args.llama_port}/v1/chat/completions (with stream=true)")
    
    # Run tests if requested
    if args.test:
        print("\n🧪 Running functionality tests...")
        
        # Test LLaMA server health
        llama_healthy = test_server_health(
            f"http://{args.host}:{args.llama_port}/health", 
            "LLaMA Server"
        )
        
        # Test MCP server health
        mcp_healthy = test_server_health(
            f"http://{args.host}:{args.mcp_port}/health", 
            "MCP Server"
        )
        
        if llama_healthy:
            # Test models endpoint
            try:
                response = requests.get(f"http://{args.host}:{args.llama_port}/models", timeout=5)
                if response.status_code == 200:
                    print("✅ LLaMA models endpoint working")
                    # Check if streaming capability is advertised
                    models_data = response.json()
                    streaming_supported = any(
                        "streaming" in model.get("capabilities", []) 
                        for model in models_data.get("data", [])
                    )
                    if streaming_supported:
                        print("✅ Streaming capability detected in model list")
                    else:
                        print("⚠️  Streaming capability not found in model list")
                else:
                    print(f"❌ LLaMA models endpoint returned {response.status_code}")
            except Exception as e:
                print(f"❌ LLaMA models endpoint error: {e}")
        
        if mcp_healthy:
            # Test MCP tools endpoint
            try:
                response = requests.get(f"http://{args.host}:{args.mcp_port}/mcp/tools", timeout=5)
                if response.status_code == 200:
                    tools_data = response.json()
                    print(f"✅ MCP tools endpoint working, found {len(tools_data.get('tools', []))} tools")
                else:
                    print(f"❌ MCP tools endpoint returned {response.status_code}")
            except Exception as e:
                print(f"❌ MCP tools endpoint error: {e}")
        
        # Test document parsing if demo file provided
        if args.demo_file and os.path.exists(args.demo_file):
            print(f"\n📄 Testing document parsing with: {args.demo_file}")
            try:
                with open(args.demo_file, 'r', encoding='utf-8') as f:
                    content = f.read()[:200]  # First 200 chars for preview
                print(f"📄 Demo file preview: {content}...")
                
                # Try to parse the file via the API
                parse_url = f"http://{args.host}:{args.llama_port}/parse/{args.demo_file}"
                response = requests.get(parse_url, timeout=10)
                if response.status_code == 200:
                    print("✅ Document parsing endpoint working")
                    result = response.json()
                    print(f"📄 Parsed {result.get('content_length', 0)} characters")
                else:
                    print(f"❌ Document parsing failed with status {response.status_code}")
            except Exception as e:
                print(f"❌ Document parsing test error: {e}")
        elif args.demo_file:
            print(f"⚠️  Demo file not found: {args.demo_file}")
        
        # Test streaming capability
        if llama_healthy:
            print(f"\n🌊 Testing streaming capability...")
            try:
                # Test streaming with a simple message
                stream_payload = {
                    "messages": [
                        {"role": "user", "content": "Hello, this is a streaming test. Please respond with a short greeting."}
                    ],
                    "stream": True,
                    "temperature": 0.7,
                    "max_tokens": 50
                }
                
                response = requests.post(
                    f"http://{args.host}:{args.llama_port}/v1/chat/completions",
                    json=stream_payload,
                    headers={"Content-Type": "application/json"},
                    stream=True,
                    timeout=10
                )
                
                if response.status_code == 200 and response.headers.get('content-type', '').startswith('text/event-stream'):
                    print("✅ Streaming endpoint working (detected Server-Sent Events)")
                    
                    # Read a few chunks to verify
                    chunks_received = 0
                    for line in response.iter_lines():
                        if line and chunks_received < 3:  # Just check first few chunks
                            line_str = line.decode('utf-8')
                            if line_str.startswith('data: '):
                                chunks_received += 1
                                print(f"   Chunk {chunks_received}: {line_str[:100]}...")
                                if chunks_received >= 3:
                                    break
                    
                    print(f"✅ Received {chunks_received} streaming chunks")
                else:
                    print(f"❌ Streaming test failed - wrong response type: {response.headers.get('content-type', 'unknown')}")
            except Exception as e:
                print(f"❌ Streaming test error: {e}")

    print(f"\n🎯 Servers are running! Press Ctrl+C to stop.")
    print(f"💡 Access streaming LLaMA server at: http://{args.host}:{args.llama_port}")
    print(f"💡 Access MCP server at: http://{args.host}:{args.mcp_port}")
    print(f"💡 For LM Studio, use API endpoint: http://{args.host}:{args.llama_port}")
    print(f"💡 Streaming enabled - compatible with LM Studio and other clients")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        sys.exit(0)

if __name__ == "__main__":
    main()
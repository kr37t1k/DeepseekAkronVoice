#!/usr/bin/env python3
"""
Script to run the LLaMA server on your phone
"""
import sys
import os
import argparse
from llama_server import main as server_main


def main():
    parser = argparse.ArgumentParser(description='Run LLaMA server for mobile device')
    parser.add_argument('--model-path', type=str, required=True, 
                       help='Path to the GGUF model file')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host to bind server to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8001,
                       help='Port to bind server to (default: 8001)')
    parser.add_argument('--n_ctx', type=int, default=2048,
                       help='Context size for the model (default: 2048)')
    
    args = parser.parse_args()
    
    print(f"🚀 Starting LLaMA server on {args.host}:{args.port}")
    print(f"📁 Using model: {args.model_path}")
    print(f"💡 Make sure your phone and computer are on the same network")
    print(f"💡 Connect to: http://{args.host}:{args.port}/v1/chat/completions")
    
    try:
        # Call the main function from llama_server
        import sys
        sys.argv = [
            'llama_server.py',
            '--model-path', args.model_path,
            '--host', args.host,
            '--port', str(args.port),
            '--n_ctx', str(args.n_ctx)
        ]
        server_main()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error running server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
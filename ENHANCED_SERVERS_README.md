# Enhanced Streaming LLaMA and MCP Server Setup

This project provides enhanced versions of LLaMA and MCP servers with additional features including document parsing, streaming support for LM Studio, and stable synchronization.

## Features

### Enhanced Streaming LLaMA Server (`streaming_llama_server.py`)
- Standard OpenAI-compatible API endpoint with streaming support
- Document parsing for .pdf, .docx, .txt, .md files
- File parsing endpoint: `/parse/{file_path}`
- Document processing endpoint: `/v1/document/process`
- **NEW: Streaming support for LM Studio compatibility** - Uses Server-Sent Events (SSE) for real-time token streaming
- Threaded request handling
- Health and stats endpoints
- Mock model fallback for testing

### Enhanced MCP Server (`enhanced_mcp_server.py`)
- WebSocket and HTTP tool endpoints
- Stable synchronization with periodic checks
- System information tools
- File operations (read, write, list, delete, copy, move)
- Document parsing capabilities
- Process and service management
- Shell command execution
- Cross-platform support

### Unified Streaming Launcher (`unified_streaming_launcher.py`)
- Launch both servers simultaneously
- Built-in health checks
- Document parsing test functionality
- **NEW: Streaming capability testing** - Tests Server-Sent Events functionality
- Single command to start everything

## Installation

1. Install the required packages:
```bash
pip install -r requirements_enhanced.txt
```

2. For the LLaMA server, you'll also need a GGUF model file or use the mock server for testing.

## Usage

### Quick Start with Mock Model (No Model Required) - Streaming Version
```bash
python unified_streaming_launcher.py --test
```

### With a GGUF Model - Streaming Version
```bash
python unified_streaming_launcher.py --model-path /path/to/your/model.gguf --test
```

### Individual Server Launch
```bash
# Streaming LLaMA server
python streaming_llama_server.py --model-path /path/to/model.gguf --port 8001

# MCP server
python enhanced_mcp_server.py --port 3000
```

### Test Document Parsing - Streaming Version
```bash
python unified_streaming_launcher.py --test --demo-file test_document.md
```

## API Endpoints

### LLaMA Server (default port 8001)
- `GET /health` - Health check
- `GET /stats` - Server statistics
- `GET /models` - Available models (now includes streaming capability)
- `GET /parse/{file_path}` - Parse document at file path
- `POST /v1/chat/completions` - Standard OpenAI-compatible chat endpoint with streaming support (use `stream=true` in request)
- `POST /v1/document/process` - Process document with AI

### MCP Server (default port 3000)
- `GET /health` - Health check
- `GET /sync` - Synchronization status
- `POST /sync/trigger` - Trigger manual sync
- `GET /mcp/tools` - List available tools
- `POST /mcp/tools` - Execute MCP tools
- `GET /mcp` - WebSocket endpoint

## Document Parsing Capabilities

The enhanced servers support parsing of multiple document formats:

- **PDF** files using PyPDF2
- **DOCX** files using python-docx
- **TXT** files with UTF-8 encoding
- **MD** files with basic markdown formatting removal
- **Other text formats** that can be read as UTF-8

## LAN Access

Both servers bind to `0.0.0.0` by default, making them accessible from other devices on the same network. To connect from another device:

- LLaMA Server: `http://YOUR_SERVER_IP:8001`
- MCP Server: `http://YOUR_SERVER_IP:3000`

## Testing

The unified streaming launcher includes a test mode that verifies:
- Server health endpoints
- Tool availability
- Document parsing functionality
- **NEW: Streaming capability testing** - Tests Server-Sent Events functionality for LM Studio compatibility
- Basic connectivity

## Configuration

You can customize server behavior with command-line arguments:

- `--host`: Network interface to bind to (default: 0.0.0.0)
- `--llama-port`: Port for LLaMA server (default: 8001)
- `--mcp-port`: Port for MCP server (default: 3000)
- `--model-path`: Path to GGUF model file
- `--test`: Enable test mode with health checks
- `--demo-file`: Path to file for document parsing test

## Troubleshooting

1. **Missing dependencies**: Install requirements with `pip install -r requirements_enhanced.txt`
2. **Port conflicts**: Use different ports with `--llama-port` and `--mcp-port`
3. **File access errors**: Ensure the server has read permissions for document files
4. **Model loading issues**: Use mock server for testing without a model file
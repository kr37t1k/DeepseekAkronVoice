# MCP (Model Context Protocol) Servers

This directory contains two MCP servers designed to work with LLMs for interacting with system capabilities:

## Files

- `mcp_android.py` - MCP server for Android/Termux environments
- `mcp_windows.py` - MCP server for Windows environments
- `requirements_mcp.txt` - Requirements for MCP servers

## Features

### Android Server (`mcp_android.py`)
- System information retrieval
- Battery status monitoring
- Device storage information
- Network information
- File operations (read, write, list, delete)
- Shell command execution
- Text-to-speech capabilities
- Speech-to-text processing

### Windows Server (`mcp_windows.py`)
- Detailed system information using WMI
- Battery status for laptops
- Storage information for all drives
- Network information and statistics
- File operations (read, write, list, delete, copy, move)
- Shell command execution via PowerShell
- Windows registry operations
- Process management
- Service management
- Audio controls (volume, mute/unmute, device listing)
- Display controls (brightness, resolution, screenshots)

## Installation

```bash
# For both platforms
pip install -r requirements_mcp.txt

# For Windows additionally
pip install wmi
```

## Usage

### Android Server
```bash
python mcp_android.py
```
The server will start on `http://127.0.0.1:3000`

### Windows Server
```bash
python mcp_windows.py
```
The server will start on `http://127.0.0.1:3001`

## API Endpoints

Both servers provide:
- `GET /health` - Health check
- `GET /mcp/tools` - List available tools
- `POST /mcp/tools` - Execute tools via HTTP
- `GET /mcp` - WebSocket endpoint for MCP protocol

## MCP Protocol Support

The servers support the Model Context Protocol which allows LLMs to:
- Discover available tools
- Execute tools with parameters
- Receive structured responses
- Handle errors appropriately

## Integration with LLMs

These servers can be integrated with LLMs that support MCP protocol to provide system-level capabilities to AI models.
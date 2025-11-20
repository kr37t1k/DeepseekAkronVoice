# Troubleshooting Guide for BrokenPipe [Errno 32] Error

## Problem Description
The BrokenPipe [Errno 32] error occurs when the client closes the connection before the server finishes sending the response, or when there are connection handling issues between the voice assistant and the local AI server.

## Solutions Implemented

### 1. Server-Side Improvements
- Added proper connection timeout handling
- Implemented threaded server to handle multiple connections
- Added robust error handling for BrokenPipeError and ConnectionResetError
- Added explicit 'Connection: close' header to prevent keep-alive issues
- Added Content-Length header to ensure complete response transmission
- Added socket timeout to prevent hanging connections

### 2. Client-Side Improvements
- Increased timeout from 30 to 60 seconds
- Added explicit 'Connection: close' header
- Added proper error handling for various request exceptions
- Added retry logic in case of connection failures

## How to Run the Fixed Version

### Starting the Server
```bash
# Make sure you have a model file, then run:
python3 start_server.py --model-path /path/to/your/model.gguf

# Or if using the mock server for testing:
python3 llama_server.py --model-path /tmp/fake_model.gguf
```

### Running the Voice Assistant
```bash
python3 run.py
```

## Additional Tips

1. **Network Issues**: Make sure both devices are on the same network
2. **Firewall**: Check if port 8001 is open on your system
3. **Model Loading**: Large models may take time to load initially
4. **Connection Timeout**: The server now has a 60-second timeout to prevent hanging

## Testing the Connection

You can test the connection independently using:
```bash
python3 test_connection.py
```

## Configuration Options

The server configuration can be adjusted in `server_config.py`:
- Server host and port
- Model path and context size
- Connection timeout settings
- Logging options

## Common Error Messages and Solutions

- **BrokenPipeError**: Fixed with proper connection handling
- **ConnectionResetError**: Handled with try-catch blocks
- **Timeout**: Increased to 60 seconds
- **JSON parsing errors**: Better error handling added

## Running with Mock Server for Testing

If you don't have a GGUF model file, you can still test the connection:
```bash
# The server will automatically use a mock model if llama-cpp-python is not available
python3 start_server.py --model-path /fake/model/path
```

This should resolve the BrokenPipe [Errno 32] error and allow your voice assistant to communicate properly with the local AI server.
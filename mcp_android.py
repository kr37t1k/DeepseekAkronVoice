#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server for Android
This server provides a standardized way for LLMs to interact with Android device capabilities
"""

import json
import logging
import os
import sys
import time
import asyncio
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import aiohttp
from aiohttp import web, WSMsgType
import socket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MCPConfig:
    """Configuration for MCP server"""
    host: str = "127.0.0.1"
    port: int = 3000
    debug: bool = True
    timeout: int = 30

class MCPAndroidServer:
    """MCP Server implementation for Android devices"""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.app = web.Application()
        self.setup_routes()
        self.session = None
        self.tools = {
            "system_info": self.get_system_info,
            "battery_status": self.get_battery_status,
            "device_storage": self.get_device_storage,
            "network_info": self.get_network_info,
            "file_operations": self.file_operations,
            "shell_command": self.execute_shell_command,
            "text_to_speech": self.text_to_speech,
            "speech_to_text": self.speech_to_text,
        }
        
    def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get('/mcp', self.handle_mcp_websocket)
        self.app.router.add_post('/mcp/tools', self.handle_tool_request)
        self.app.router.add_get('/mcp/tools', self.list_tools)
        self.app.router.add_get('/health', self.health_check)
        
    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "platform": "android",
            "timestamp": time.time(),
            "version": "1.0.0"
        })
        
    async def list_tools(self, request):
        """List available tools"""
        tool_list = []
        for tool_name, tool_func in self.tools.items():
            tool_list.append({
                "name": tool_name,
                "description": tool_func.__doc__ or f"Tool {tool_name}",
                "parameters": self.get_tool_parameters(tool_name)
            })
        return web.json_response({"tools": tool_list})
        
    def get_tool_parameters(self, tool_name: str) -> dict:
        """Get parameters for a specific tool"""
        # Define parameters for each tool
        params = {
            "system_info": {},
            "battery_status": {},
            "device_storage": {},
            "network_info": {},
            "file_operations": {
                "operation": {"type": "string", "enum": ["read", "write", "list", "delete"]},
                "path": {"type": "string"},
                "content": {"type": "string", "optional": True}
            },
            "shell_command": {
                "command": {"type": "string"},
                "timeout": {"type": "integer", "default": 10}
            },
            "text_to_speech": {
                "text": {"type": "string"},
                "language": {"type": "string", "default": "en"}
            },
            "speech_to_text": {
                "audio_file": {"type": "string"}
            }
        }
        return params.get(tool_name, {})
        
    async def handle_mcp_websocket(self, request):
        """Handle MCP WebSocket connection"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        logger.info("New MCP WebSocket connection established")
        
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    response = await self.process_mcp_request(data)
                    await ws.send_str(json.dumps(response))
                except json.JSONDecodeError:
                    error_response = {
                        "error": "Invalid JSON in request",
                        "type": "error"
                    }
                    await ws.send_str(json.dumps(error_response))
                except Exception as e:
                    error_response = {
                        "error": f"Server error: {str(e)}",
                        "type": "error"
                    }
                    await ws.send_str(json.dumps(error_response))
            elif msg.type == WSMsgType.ERROR:
                logger.error(f"WebSocket connection closed with exception {ws.exception()}")
                
        logger.info("MCP WebSocket connection closed")
        return ws
        
    async def handle_tool_request(self, request):
        """Handle tool request via HTTP POST"""
        try:
            data = await request.json()
            tool_name = data.get("tool_name")
            tool_args = data.get("arguments", {})
            
            if tool_name not in self.tools:
                return web.json_response({
                    "error": f"Tool '{tool_name}' not found",
                    "type": "error"
                }, status=404)
                
            result = await self.execute_tool(tool_name, tool_args)
            return web.json_response(result)
        except Exception as e:
            logger.error(f"Error handling tool request: {e}")
            return web.json_response({
                "error": f"Server error: {str(e)}",
                "type": "error"
            }, status=500)
            
    async def process_mcp_request(self, data: dict) -> dict:
        """Process MCP request and return response"""
        request_type = data.get("type", "")
        
        if request_type == "call_tool":
            tool_name = data.get("name", "")
            arguments = data.get("arguments", {})
            
            if tool_name not in self.tools:
                return {
                    "error": f"Tool '{tool_name}' not found",
                    "type": "error"
                }
                
            result = await self.execute_tool(tool_name, arguments)
            return {
                "type": "call_tool_result",
                "result": result
            }
        elif request_type == "list_tools":
            tools = []
            for name, func in self.tools.items():
                tools.append({
                    "name": name,
                    "description": func.__doc__ or f"Tool {name}",
                    "input_schema": {
                        "type": "object",
                        "properties": self.get_tool_parameters(name)
                    }
                })
            return {
                "type": "list_tools_result",
                "tools": tools
            }
        else:
            return {
                "error": f"Unknown request type: {request_type}",
                "type": "error"
            }
            
    async def execute_tool(self, tool_name: str, arguments: dict) -> Any:
        """Execute a specific tool with given arguments"""
        try:
            tool_func = self.tools[tool_name]
            if asyncio.iscoroutinefunction(tool_func):
                return await tool_func(**arguments)
            else:
                return tool_func(**arguments)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "error": f"Tool execution failed: {str(e)}",
                "success": False
            }
            
    # Tool implementations
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        import platform
        import psutil
        
        info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "boot_time": psutil.boot_time(),
            "timestamp": time.time()
        }
        return info
        
    async def get_battery_status(self) -> Dict[str, Any]:
        """Get battery status (Android specific)"""
        try:
            # Try to get battery info using termux (if available)
            result = subprocess.run(['termux-battery-status'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                # Fallback to basic info
                return {"status": "unknown", "message": "Termux battery API not available"}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"status": "unknown", "message": "Battery info not available"}
            
    async def get_device_storage(self) -> Dict[str, Any]:
        """Get device storage information"""
        import shutil
        
        try:
            home_dir = os.path.expanduser("~")
            total, used, free = shutil.disk_usage(home_dir)
            
            # Also check Android-specific paths
            android_paths = [
                "/sdcard",
                "/storage/emulated/0",
                os.path.expanduser("~")
            ]
            
            storage_info = {
                "primary": {
                    "total": total,
                    "used": used,
                    "free": free,
                    "path": home_dir
                },
                "android_paths": {}
            }
            
            for path in android_paths:
                if os.path.exists(path):
                    try:
                        total, used, free = shutil.disk_usage(path)
                        storage_info["android_paths"][path] = {
                            "total": total,
                            "used": used,
                            "free": free
                        }
                    except:
                        continue
                        
            return storage_info
        except Exception as e:
            return {"error": f"Could not get storage info: {str(e)}"}
            
    async def get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        try:
            # Get network interfaces
            import psutil
            
            net_io = psutil.net_io_counters()
            net_addrs = psutil.net_if_addrs()
            
            # Try to get current IP
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.connect(("8.8.8.8", 80))
                ip = sock.getsockname()[0]
                sock.close()
            except:
                ip = "127.0.0.1"
                
            return {
                "ip_address": ip,
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "network_interfaces": {
                    name: [
                        {
                            "family": str(addr.family),
                            "address": addr.address,
                            "netmask": addr.netmask,
                            "broadcast": addr.broadcast
                        }
                        for addr in addrs
                    ]
                    for name, addrs in net_addrs.items()
                }
            }
        except Exception as e:
            return {"error": f"Could not get network info: {str(e)}"}
            
    async def file_operations(self, operation: str, path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Perform file operations (read, write, list, delete)"""
        try:
            if operation == "read":
                with open(path, 'r', encoding='utf-8') as f:
                    return {"content": f.read(), "success": True}
            elif operation == "write":
                if content is None:
                    return {"error": "Content required for write operation", "success": False}
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {"message": f"File {path} written successfully", "success": True}
            elif operation == "list":
                if os.path.isdir(path):
                    files = os.listdir(path)
                    return {"files": files, "path": path, "success": True}
                else:
                    return {"error": f"Path {path} is not a directory", "success": False}
            elif operation == "delete":
                if os.path.isfile(path):
                    os.remove(path)
                    return {"message": f"File {path} deleted successfully", "success": True}
                elif os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
                    return {"message": f"Directory {path} deleted successfully", "success": True}
                else:
                    return {"error": f"Path {path} does not exist", "success": False}
            else:
                return {"error": f"Unknown operation: {operation}", "success": False}
        except Exception as e:
            return {"error": f"File operation failed: {str(e)}", "success": False}
            
    async def execute_shell_command(self, command: str, timeout: int = 10) -> Dict[str, Any]:
        """Execute shell command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout} seconds", "success": False}
        except Exception as e:
            return {"error": f"Command execution failed: {str(e)}", "success": False}
            
    async def text_to_speech(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Convert text to speech (Android specific)"""
        try:
            # Try termux-tts-speak if available
            result = subprocess.run([
                'termux-tts-speak', 
                text
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return {"message": "Text spoken successfully", "success": True}
            else:
                return {"error": f"TTS failed: {result.stderr}", "success": False}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback: just return success without actual TTS
            return {"message": "Text received for speech", "success": True, "warning": "TTS not available"}
            
    async def speech_to_text(self, audio_file: str) -> Dict[str, Any]:
        """Convert speech to text (Android specific)"""
        try:
            # This is a placeholder - actual implementation would require STT library
            # In a real implementation, you might use vosk or similar
            if not os.path.exists(audio_file):
                return {"error": f"Audio file {audio_file} does not exist", "success": False}
                
            # Placeholder for actual STT processing
            return {
                "transcription": "Speech to text processing not fully implemented in this example",
                "audio_file": audio_file,
                "success": True
            }
        except Exception as e:
            return {"error": f"Speech to text failed: {str(e)}", "success": False}
            
    def run(self):
        """Run the MCP server"""
        logger.info(f"Starting MCP Server for Android on {self.config.host}:{self.config.port}")
        web.run_app(self.app, host=self.config.host, port=self.config.port)

def main():
    """Main entry point"""
    config = MCPConfig()
    
    # Check if running on Android (Termux)
    if os.environ.get('TERMUX_VERSION'):
        logger.info("Detected Android/Termux environment")
    else:
        logger.warning("Not running in Android/Termux environment - some features may not work")
    
    server = MCPAndroidServer(config)
    server.run()

if __name__ == "__main__":
    main()
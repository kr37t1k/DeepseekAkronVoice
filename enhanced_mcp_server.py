#!/usr/bin/env python3
"""
Enhanced MCP (Model Context Protocol) Server with Stable Sync
This server provides a standardized way for LLMs to interact with system capabilities with stable synchronization
"""

import json
import logging
import os
import sys
import time
import asyncio
import subprocess
import platform
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
import aiohttp
from aiohttp import web, WSMsgType
import socket
import threading
import queue
from datetime import datetime
import hashlib
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MCPConfig:
    """Configuration for MCP server"""
    host: str = "0.0.0.0"  # Changed to 0.0.0.0 to allow LAN access
    port: int = 3000
    debug: bool = True
    timeout: int = 30
    sync_interval: int = 10  # seconds between sync checks

class MCPSyncManager:
    """Manages synchronization between MCP server and other services"""
    
    def __init__(self):
        self.sync_callbacks = []
        self.sync_status = {}
        self.last_sync = {}
        self.sync_lock = threading.Lock()
    
    def register_sync_callback(self, name: str, callback: Callable):
        """Register a function to be called during sync"""
        with self.sync_lock:
            self.sync_callbacks.append((name, callback))
            self.sync_status[name] = {"last_run": None, "status": "registered", "success": True}
    
    def run_sync_cycle(self):
        """Run a complete sync cycle"""
        with self.sync_lock:
            for name, callback in self.sync_callbacks:
                try:
                    result = callback()
                    self.sync_status[name] = {
                        "last_run": time.time(),
                        "status": "success",
                        "success": True,
                        "result": result
                    }
                except Exception as e:
                    logger.error(f"Sync callback {name} failed: {e}")
                    self.sync_status[name] = {
                        "last_run": time.time(),
                        "status": "error",
                        "success": False,
                        "error": str(e)
                    }
    
    def get_sync_status(self) -> Dict:
        """Get current sync status"""
        with self.sync_lock:
            return self.sync_status.copy()

class MCPEnhancedServer:
    """Enhanced MCP Server implementation with stable sync capabilities"""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.app = web.Application()
        self.setup_routes()
        self.session = None
        self.sync_manager = MCPSyncManager()
        self.tools = {
            "system_info": self.get_system_info,
            "battery_status": self.get_battery_status,
            "device_storage": self.get_device_storage,
            "network_info": self.get_network_info,
            "file_operations": self.file_operations,
            "shell_command": self.execute_shell_command,
            "sync_status": self.get_sync_status,
            "sync_trigger": self.trigger_sync,
            "file_parse": self.parse_file,
            "document_parse": self.parse_document,
            "process_management": self.process_management,
            "service_status": self.service_status,
        }
        
        # Register sync callback for health check
        self.sync_manager.register_sync_callback("health_check", self._health_sync_check)
        
    def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get('/mcp', self.handle_mcp_websocket)
        self.app.router.add_post('/mcp/tools', self.handle_tool_request)
        self.app.router.add_get('/mcp/tools', self.list_tools)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/sync', self.sync_status)
        self.app.router.add_post('/sync/trigger', self.trigger_sync_endpoint)
        
    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "platform": platform.system().lower(),
            "timestamp": time.time(),
            "version": "1.1.0",
            "sync_enabled": True
        })
        
    async def sync_status(self, request):
        """Sync status endpoint"""
        status = self.sync_manager.get_sync_status()
        return web.json_response({
            "sync_status": status,
            "timestamp": time.time(),
            "sync_interval": self.config.sync_interval
        })
        
    async def trigger_sync_endpoint(self, request):
        """Endpoint to trigger sync manually"""
        try:
            self.sync_manager.run_sync_cycle()
            return web.json_response({
                "status": "sync_triggered",
                "timestamp": time.time(),
                "sync_status": self.sync_manager.get_sync_status()
            })
        except Exception as e:
            return web.json_response({
                "status": "error",
                "error": str(e)
            }, status=500)
        
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
                "operation": {"type": "string", "enum": ["read", "write", "list", "delete", "copy", "move"]},
                "path": {"type": "string"},
                "destination": {"type": "string", "optional": True},
                "content": {"type": "string", "optional": True}
            },
            "shell_command": {
                "command": {"type": "string"},
                "timeout": {"type": "integer", "default": 10}
            },
            "sync_status": {},
            "sync_trigger": {},
            "file_parse": {
                "file_path": {"type": "string"},
                "format": {"type": "string", "enum": ["auto", "txt", "md", "pdf", "docx"], "default": "auto"}
            },
            "document_parse": {
                "file_path": {"type": "string"},
                "extract_text": {"type": "boolean", "default": True},
                "max_length": {"type": "integer", "default": 5000}
            },
            "process_management": {
                "operation": {"type": "string", "enum": ["list", "kill", "start", "status"]},
                "process_name": {"type": "string", "optional": True},
                "pid": {"type": "integer", "optional": True}
            },
            "service_status": {
                "service_name": {"type": "string", "optional": True}
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
    
    # Sync-related methods
    def _health_sync_check(self) -> Dict[str, Any]:
        """Internal method for sync health check"""
        try:
            import psutil
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
                "timestamp": time.time()
            }
        except ImportError:
            return {"status": "psutil not available"}
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get synchronization status"""
        return self.sync_manager.get_sync_status()
    
    async def trigger_sync(self) -> Dict[str, Any]:
        """Trigger synchronization"""
        self.sync_manager.run_sync_cycle()
        return {
            "status": "sync_completed",
            "timestamp": time.time(),
            "sync_status": self.sync_manager.get_sync_status()
        }
    
    # File parsing methods
    async def parse_file(self, file_path: str, format: str = "auto") -> Dict[str, Any]:
        """Parse a file and extract text content"""
        try:
            if not os.path.exists(file_path):
                return {"error": f"File does not exist: {file_path}", "success": False}
            
            # Determine file format
            if format == "auto":
                _, ext = os.path.splitext(file_path.lower())
                format = ext.lstrip('.').lower()
            
            # Parse based on format
            if format in ['txt', 'md']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            elif format == 'pdf':
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        content = ""
                        for page in pdf_reader.pages:
                            content += page.extract_text() + "\n"
                except ImportError:
                    return {"error": "PyPDF2 not available for PDF parsing", "success": False}
            elif format == 'docx':
                try:
                    import docx
                    doc = docx.Document(file_path)
                    content = "\n".join([p.text for p in doc.paragraphs])
                except ImportError:
                    return {"error": "python-docx not available for DOCX parsing", "success": False}
            else:
                # Try to read as text
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            
            # Return content with metadata
            return {
                "file_path": file_path,
                "format": format,
                "content_length": len(content),
                "content_preview": content[:500],  # First 500 chars
                "full_content": content,
                "success": True
            }
        except Exception as e:
            return {"error": f"File parsing failed: {str(e)}", "success": False}
    
    async def parse_document(self, file_path: str, extract_text: bool = True, max_length: int = 5000) -> Dict[str, Any]:
        """Parse document with additional processing options"""
        try:
            result = await self.parse_file(file_path)
            if not result.get("success", False):
                return result
            
            content = result.get("full_content", "")
            
            # Apply additional processing if requested
            if extract_text and len(content) > max_length:
                # Truncate content to max_length while preserving sentence boundaries
                truncated = self._truncate_content(content, max_length)
            else:
                truncated = content[:max_length] if len(content) > max_length else content
            
            return {
                "file_path": file_path,
                "original_length": len(content),
                "truncated_length": len(truncated),
                "truncated": len(content) > max_length,
                "content": truncated,
                "success": True
            }
        except Exception as e:
            return {"error": f"Document parsing failed: {str(e)}", "success": False}
    
    def _truncate_content(self, content: str, max_length: int) -> str:
        """Truncate content while preserving sentence boundaries"""
        if len(content) <= max_length:
            return content
        
        # Try to find a sentence boundary near the max length
        truncated = content[:max_length]
        sentences = truncated.split('. ')
        
        if len(sentences) > 1:
            # Rebuild content up to the last complete sentence that fits
            rebuilt = ""
            for sentence in sentences[:-1]:
                candidate = rebuilt + sentence + ". "
                if len(candidate) <= max_length:
                    rebuilt = candidate
                else:
                    break
            return rebuilt.strip()
        else:
            # If no clear sentence breaks, just truncate
            return content[:max_length]
    
    # Tool implementations
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            import psutil
            
            info = {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "platform_release": platform.release(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "cpu_count": psutil.cpu_count(),
                "cpu_load": psutil.cpu_percent(interval=1),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "memory_used": psutil.virtual_memory().used,
                "memory_percent": psutil.virtual_memory().percent,
                "boot_time": psutil.boot_time(),
                "timestamp": time.time(),
                "hostname": socket.gethostname(),
                "ip_address": self._get_local_ip()
            }
            return info
        except ImportError:
            # Fallback without psutil
            info = {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "platform_release": platform.release(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "timestamp": time.time(),
                "hostname": socket.gethostname(),
                "ip_address": self._get_local_ip(),
                "warning": "psutil not available for detailed system info"
            }
            return info
            
    def _get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            sock.close()
            return ip
        except:
            return "127.0.0.1"
            
    async def get_battery_status(self) -> Dict[str, Any]:
        """Get battery status"""
        try:
            import psutil
            
            battery = psutil.sensors_battery()
            if battery:
                return {
                    "percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                    "secsleft": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "unlimited",
                    "power_status": "charging" if battery.power_plugged else ("discharging" if battery.percent < 100 else "charged"),
                    "timestamp": time.time()
                }
            else:
                return {
                    "status": "no_battery",
                    "message": "No battery detected (desktop or AC powered laptop)"
                }
        except ImportError:
            return {"error": "psutil not available for battery info"}
        except Exception as e:
            return {"error": f"Could not get battery info: {str(e)}"}
            
    async def get_device_storage(self) -> Dict[str, Any]:
        """Get device storage information"""
        import shutil
        
        try:
            # Get storage for the root/main partition
            if os.name == 'nt':  # Windows
                path = 'C:\\'
            else:  # Unix-like
                path = '/'
                
            total, used, free = shutil.disk_usage(path)
            
            storage_info = {
                "primary_drive": {
                    "path": path,
                    "total": total,
                    "used": used,
                    "free": free,
                    "percent_used": (used / total) * 100 if total > 0 else 0
                }
            }
            
            # Also include current working directory stats
            current_total, current_used, current_free = shutil.disk_usage('.')
            storage_info["current_directory"] = {
                "path": os.getcwd(),
                "total": current_total,
                "used": current_used,
                "free": current_free,
                "percent_used": (current_used / current_total) * 100 if current_total > 0 else 0
            }
            
            return storage_info
        except Exception as e:
            return {"error": f"Could not get storage info: {str(e)}"}
            
    async def get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        try:
            import psutil
            
            net_io = psutil.net_io_counters()
            net_addrs = psutil.net_if_addrs()
            
            # Get current IP
            ip = self._get_local_ip()
            
            return {
                "ip_address": ip,
                "hostname": socket.gethostname(),
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
                },
                "timestamp": time.time()
            }
        except ImportError:
            return {"error": "psutil not available for network info"}
        except Exception as e:
            return {"error": f"Could not get network info: {str(e)}"}
            
    async def file_operations(self, operation: str, path: str, content: Optional[str] = None, destination: Optional[str] = None) -> Dict[str, Any]:
        """Perform file operations (read, write, list, delete, copy, move)"""
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
            elif operation == "copy":
                if destination is None:
                    return {"error": "Destination required for copy operation", "success": False}
                import shutil
                shutil.copy2(path, destination)
                return {"message": f"File {path} copied to {destination}", "success": True}
            elif operation == "move":
                if destination is None:
                    return {"error": "Destination required for move operation", "success": False}
                import shutil
                shutil.move(path, destination)
                return {"message": f"File {path} moved to {destination}", "success": True}
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
                "success": result.returncode == 0,
                "command": command,
                "execution_time": timeout
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout} seconds", "success": False}
        except Exception as e:
            return {"error": f"Command execution failed: {str(e)}", "success": False}
    
    async def process_management(self, operation: str, process_name: Optional[str] = None, pid: Optional[int] = None) -> Dict[str, Any]:
        """Manage system processes"""
        try:
            import psutil
            
            if operation == "list":
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'username', 'status']):
                    try:
                        processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process might have disappeared or access denied
                        continue
                return {"processes": processes, "success": True}
                
            elif operation == "status":
                if pid:
                    try:
                        proc = psutil.Process(pid)
                        return {
                            "pid": pid,
                            "name": proc.name(),
                            "status": proc.status(),
                            "running": proc.is_running(),
                            "success": True
                        }
                    except psutil.NoSuchProcess:
                        return {"error": f"Process with PID {pid} not found", "success": False}
                elif process_name:
                    matching_processes = []
                    for proc in psutil.process_iter(['pid', 'name']):
                        if process_name.lower() in proc.info['name'].lower():
                            matching_processes.append(proc.info)
                    return {"processes": matching_processes, "success": True}
                else:
                    return {"error": "Either PID or process name must be provided", "success": False}
                    
            elif operation == "kill":
                if pid:
                    try:
                        proc = psutil.Process(pid)
                        proc.terminate()
                        proc.wait(timeout=5)
                        return {"message": f"Process {pid} terminated successfully", "success": True}
                    except psutil.NoSuchProcess:
                        return {"error": f"Process with PID {pid} not found", "success": False}
                    except psutil.TimeoutExpired:
                        proc.kill()  # Force kill if terminate didn't work
                        return {"message": f"Process {pid} force killed", "success": True}
                elif process_name:
                    killed_pids = []
                    for proc in psutil.process_iter(['pid', 'name']):
                        if process_name.lower() in proc.info['name'].lower():
                            try:
                                proc.terminate()
                                proc.wait(timeout=2)
                                killed_pids.append(proc.info['pid'])
                            except psutil.TimeoutExpired:
                                proc.kill()
                                killed_pids.append(proc.info['pid'])
                    return {"message": f"Terminated {len(killed_pids)} processes matching '{process_name}'", "killed_pids": killed_pids, "success": True}
                else:
                    return {"error": "Either PID or process name must be provided", "success": False}
                    
            elif operation == "start":
                if not process_name:
                    return {"error": "Process name must be provided to start", "success": False}
                
                # For starting processes, we'll just return a message since actual starting
                # requires more complex handling
                return {"message": f"Process start functionality would execute: {process_name}", "success": True}
            else:
                return {"error": f"Unknown operation: {operation}", "success": False}
                
        except ImportError:
            return {"error": "psutil not available for process management", "success": False}
        except Exception as e:
            return {"error": f"Process management failed: {str(e)}", "success": False}
    
    async def service_status(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get service status (cross-platform where possible)"""
        try:
            import psutil
            
            services = []
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                # Consider processes with 'service' in the name or common service patterns
                name = proc.info['name'].lower()
                if 'service' in name or any(pattern in name for pattern in ['daemon', 'server', 'agent']):
                    if service_name is None or service_name.lower() in name:
                        try:
                            services.append({
                                "name": proc.info['name'],
                                "pid": proc.info['pid'],
                                "status": proc.info['status']
                            })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
            
            return {"services": services, "success": True}
        except ImportError:
            return {"error": "psutil not available for service status", "success": False}
        except Exception as e:
            return {"error": f"Service status check failed: {str(e)}", "success": False}

def run_server(config: MCPConfig):
    """Run the enhanced MCP server"""
    server = MCPEnhancedServer(config)
    
    logger.info(f"Starting enhanced MCP server on {config.host}:{config.port}")
    logger.info(f"MCP WebSocket: ws://{config.host}:{config.port}/mcp")
    logger.info(f"Health endpoint: http://{config.host}:{config.port}/health")
    logger.info(f"Sync endpoint: http://{config.host}:{config.port}/sync")
    logger.info(f"Tools endpoint: http://{config.host}:{config.port}/mcp/tools")
    logger.info("Server supports stable synchronization and document parsing")
    
    # Start sync loop in a separate thread
    def sync_loop():
        while True:
            time.sleep(config.sync_interval)
            try:
                server.sync_manager.run_sync_cycle()
                logger.debug("Sync cycle completed")
            except Exception as e:
                logger.error(f"Sync cycle error: {e}")
    
    sync_thread = threading.Thread(target=sync_loop, daemon=True)
    sync_thread.start()
    
    web.run_app(server.app, host=config.host, port=config.port)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced MCP Server with stable sync')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host to bind server to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=3000,
                       help='Port to bind server to (default: 3000)')
    parser.add_argument('--sync-interval', type=int, default=10,
                       help='Sync interval in seconds (default: 10)')
    
    args = parser.parse_args()
    
    config = MCPConfig(
        host=args.host,
        port=args.port,
        sync_interval=args.sync_interval
    )
    
    run_server(config)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server for Windows
This server provides a standardized way for LLMs to interact with Windows system capabilities
"""

import json
import logging
import os
import sys
import time
import asyncio
import subprocess
import platform
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import aiohttp
from aiohttp import web, WSMsgType
import socket
# Windows-specific module for system info (optional import)
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False
    wmi = None

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
    port: int = 3001
    debug: bool = True
    timeout: int = 30

class MCPWindowsServer:
    """MCP Server implementation for Windows systems"""
    
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
            "windows_registry": self.windows_registry_operations,
            "process_management": self.process_management,
            "service_management": self.service_management,
            "windows_audio": self.windows_audio_operations,
            "windows_display": self.windows_display_operations,
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
            "platform": "windows",
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
                "operation": {"type": "string", "enum": ["read", "write", "list", "delete", "copy", "move"]},
                "path": {"type": "string"},
                "destination": {"type": "string", "optional": True},
                "content": {"type": "string", "optional": True}
            },
            "shell_command": {
                "command": {"type": "string"},
                "timeout": {"type": "integer", "default": 10}
            },
            "windows_registry": {
                "operation": {"type": "string", "enum": ["read", "write", "delete"]},
                "key_path": {"type": "string"},
                "value_name": {"type": "string", "optional": True},
                "value_data": {"type": "string", "optional": True},
                "value_type": {"type": "string", "default": "REG_SZ", "enum": ["REG_SZ", "REG_DWORD", "REG_BINARY", "REG_MULTI_SZ"]}
            },
            "process_management": {
                "operation": {"type": "string", "enum": ["list", "kill", "start"]},
                "process_name": {"type": "string", "optional": True},
                "pid": {"type": "integer", "optional": True},
                "command": {"type": "string", "optional": True}
            },
            "service_management": {
                "operation": {"type": "string", "enum": ["list", "start", "stop", "status"]},
                "service_name": {"type": "string"}
            },
            "windows_audio": {
                "operation": {"type": "string", "enum": ["get_volume", "set_volume", "mute", "unmute", "list_devices"]},
                "volume_level": {"type": "integer", "optional": True, "min": 0, "max": 100}
            },
            "windows_display": {
                "operation": {"type": "string", "enum": ["brightness", "resolution", "screenshot"]},
                "brightness_level": {"type": "integer", "optional": True, "min": 0, "max": 100},
                "screenshot_path": {"type": "string", "optional": True}
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
        """Get Windows system information"""
        try:
            import psutil
            
            # Use WMI for detailed Windows info if available
            if WMI_AVAILABLE and wmi is not None:
                c = wmi.WMI()
                
                # Get OS info
                os_info = c.Win32_OperatingSystem()[0]
                
                # Get CPU info
                cpu_info = c.Win32_Processor()[0]
                
                # Get memory info
                mem_info = c.Win32_ComputerSystem()[0]
                
                info = {
                    "platform": platform.system(),
                    "platform_version": platform.version(),
                    "platform_release": platform.release(),
                    "architecture": platform.machine(),
                    "processor": cpu_info.Name,
                    "cpu_count": psutil.cpu_count(),
                    "cpu_load": psutil.cpu_percent(interval=1),
                    "memory_total": int(mem_info.TotalPhysicalMemory),
                    "memory_available": psutil.virtual_memory().available,
                    "memory_used": psutil.virtual_memory().used,
                    "os_name": os_info.Caption,
                    "os_version": os_info.Version,
                    "os_build": os_info.BuildNumber,
                    "computer_name": os_info.CSName,
                    "boot_time": psutil.boot_time(),
                    "timestamp": time.time(),
                    "wmi_available": True
                }
                return info
            else:
                # Fallback without WMI
                raise RuntimeError("WMI not available")
        except Exception as e:
            # Fallback without WMI
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
                "os_name": platform.platform(),
                "boot_time": psutil.boot_time(),
                "timestamp": time.time(),
                "wmi_available": False,
                "warning": f"WMI not available, using basic info: {str(e)}"
            }
            return info
            
    async def get_battery_status(self) -> Dict[str, Any]:
        """Get battery status (Windows specific)"""
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
        except Exception as e:
            return {"error": f"Could not get battery info: {str(e)}"}
            
    async def get_device_storage(self) -> Dict[str, Any]:
        """Get device storage information for Windows"""
        import shutil
        
        try:
            # Get all drives on Windows
            drives = []
            for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                drive_path = f"{letter}:\\"
                if os.path.exists(drive_path):
                    try:
                        total, used, free = shutil.disk_usage(drive_path)
                        drives.append({
                            "drive": drive_path,
                            "total": total,
                            "used": used,
                            "free": free,
                            "percent_used": (used / total) * 100 if total > 0 else 0
                        })
                    except:
                        continue
                        
            return {
                "drives": drives,
                "primary_drive": os.environ.get("SystemDrive", "C:\\")
            }
        except Exception as e:
            return {"error": f"Could not get storage info: {str(e)}"}
            
    async def get_network_info(self) -> Dict[str, Any]:
        """Get network information for Windows"""
        try:
            import psutil
            
            net_io = psutil.net_io_counters()
            net_addrs = psutil.net_if_addrs()
            net_stats = psutil.net_if_stats()
            
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
                },
                "interface_stats": {
                    name: {
                        "is_up": stats.isup,
                        "duplex": str(stats.duplex),
                        "speed": stats.speed,
                        "mtu": stats.mtu
                    }
                    for name, stats in net_stats.items()
                }
            }
        except Exception as e:
            return {"error": f"Could not get network info: {str(e)}"}
            
    async def file_operations(self, operation: str, path: str, destination: Optional[str] = None, content: Optional[str] = None) -> Dict[str, Any]:
        """Perform file operations (read, write, list, delete, copy, move)"""
        try:
            import shutil
            
            if operation == "read":
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
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
                    shutil.rmtree(path)
                    return {"message": f"Directory {path} deleted successfully", "success": True}
                else:
                    return {"error": f"Path {path} does not exist", "success": False}
            elif operation == "copy":
                if destination is None:
                    return {"error": "Destination required for copy operation", "success": False}
                shutil.copy2(path, destination)
                return {"message": f"File {path} copied to {destination}", "success": True}
            elif operation == "move":
                if destination is None:
                    return {"error": "Destination required for move operation", "success": False}
                shutil.move(path, destination)
                return {"message": f"File {path} moved to {destination}", "success": True}
            else:
                return {"error": f"Unknown operation: {operation}", "success": False}
        except Exception as e:
            return {"error": f"File operation failed: {str(e)}", "success": False}
            
    async def execute_shell_command(self, command: str, timeout: int = 10) -> Dict[str, Any]:
        """Execute shell command on Windows"""
        try:
            # Use PowerShell by default on Windows for better compatibility
            if not command.startswith(('cmd', 'powershell', 'pwsh')):
                # Wrap in PowerShell to handle Windows-specific commands
                command = f'powershell -Command "{command}"'
                
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
            
    async def windows_registry_operations(self, operation: str, key_path: str, value_name: Optional[str] = None, value_data: Optional[str] = None, value_type: str = "REG_SZ") -> Dict[str, Any]:
        """Perform Windows registry operations"""
        try:
            import winreg
            
            # Parse the key path
            if key_path.startswith("HKEY_LOCAL_MACHINE"):
                hkey = winreg.HKEY_LOCAL_MACHINE
                sub_key = key_path[len("HKEY_LOCAL_MACHINE\\"):]
            elif key_path.startswith("HKEY_CURRENT_USER"):
                hkey = winreg.HKEY_CURRENT_USER
                sub_key = key_path[len("HKEY_CURRENT_USER\\"):]
            elif key_path.startswith("HKEY_CLASSES_ROOT"):
                hkey = winreg.HKEY_CLASSES_ROOT
                sub_key = key_path[len("HKEY_CLASSES_ROOT\\"):]
            elif key_path.startswith("HKEY_USERS"):
                hkey = winreg.HKEY_USERS
                sub_key = key_path[len("HKEY_USERS\\"):]
            elif key_path.startswith("HKEY_CURRENT_CONFIG"):
                hkey = winreg.HKEY_CURRENT_CONFIG
                sub_key = key_path[len("HKEY_CURRENT_CONFIG\\"):]
            else:
                return {"error": f"Invalid registry key path: {key_path}", "success": False}
                
            if operation == "read":
                try:
                    with winreg.OpenKey(hkey, sub_key) as key:
                        if value_name:
                            value, reg_type = winreg.QueryValueEx(key, value_name)
                            return {
                                "value": value,
                                "type": self._reg_type_to_string(reg_type),
                                "success": True
                            }
                        else:
                            # Enumerate all values in the key
                            values = {}
                            i = 0
                            while True:
                                try:
                                    name, value, reg_type = winreg.EnumValue(key, i)
                                    values[name] = {
                                        "value": value,
                                        "type": self._reg_type_to_string(reg_type)
                                    }
                                    i += 1
                                except OSError:
                                    break
                            return {"values": values, "success": True}
                except FileNotFoundError:
                    return {"error": f"Registry key not found: {key_path}", "success": False}
                    
            elif operation == "write":
                if not value_name or value_data is None:
                    return {"error": "Value name and data required for write operation", "success": False}
                    
                try:
                    with winreg.CreateKey(hkey, sub_key) as key:
                        # Convert value_data based on type
                        if value_type == "REG_DWORD":
                            value_data = int(value_data)
                        # For other types, keep as string
                        
                        winreg.SetValueEx(key, value_name, 0, self._string_to_reg_type(value_type), value_data)
                        return {"message": f"Registry value {value_name} set successfully", "success": True}
                except Exception as e:
                    return {"error": f"Failed to write registry value: {str(e)}", "success": False}
                    
            elif operation == "delete":
                try:
                    if value_name:
                        # Delete a specific value
                        with winreg.OpenKey(hkey, sub_key, 0, winreg.KEY_SET_VALUE) as key:
                            winreg.DeleteValue(key, value_name)
                            return {"message": f"Registry value {value_name} deleted", "success": True}
                    else:
                        # Delete the entire key (only if empty)
                        winreg.DeleteKey(hkey, sub_key)
                        return {"message": f"Registry key {key_path} deleted", "success": True}
                except Exception as e:
                    return {"error": f"Failed to delete registry entry: {str(e)}", "success": False}
            else:
                return {"error": f"Unknown registry operation: {operation}", "success": False}
                
        except ImportError:
            return {"error": "Windows registry module not available", "success": False}
        except Exception as e:
            return {"error": f"Registry operation failed: {str(e)}", "success": False}
            
    def _reg_type_to_string(self, reg_type: int) -> str:
        """Convert registry type integer to string"""
        reg_types = {
            0: "REG_NONE",
            1: "REG_SZ",
            2: "REG_EXPAND_SZ",
            3: "REG_BINARY",
            4: "REG_DWORD",
            5: "REG_DWORD_BIG_ENDIAN",
            6: "REG_LINK",
            7: "REG_MULTI_SZ",
            11: "REG_QWORD"
        }
        return reg_types.get(reg_type, f"REG_UNKNOWN({reg_type})")
        
    def _string_to_reg_type(self, type_str: str) -> int:
        """Convert registry type string to integer"""
        reg_type_map = {
            "REG_SZ": winreg.REG_SZ,
            "REG_EXPAND_SZ": winreg.REG_EXPAND_SZ,
            "REG_BINARY": winreg.REG_BINARY,
            "REG_DWORD": winreg.REG_DWORD,
            "REG_MULTI_SZ": winreg.REG_MULTI_SZ,
            "REG_QWORD": winreg.REG_QWORD
        }
        return reg_type_map.get(type_str, winreg.REG_SZ)
        
    async def process_management(self, operation: str, process_name: Optional[str] = None, pid: Optional[int] = None, command: Optional[str] = None) -> Dict[str, Any]:
        """Manage Windows processes"""
        try:
            import psutil
            
            if operation == "list":
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info', 'cpu_percent']):
                    try:
                        processes.append({
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "username": proc.info['username'],
                            "memory_rss": proc.info['memory_info'].rss if proc.info['memory_info'] else 0,
                            "cpu_percent": proc.info['cpu_percent']
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                return {"processes": processes, "success": True}
                
            elif operation == "kill":
                if pid is not None:
                    try:
                        proc = psutil.Process(pid)
                        proc.terminate()
                        proc.wait(timeout=5)
                        return {"message": f"Process {pid} terminated", "success": True}
                    except psutil.NoSuchProcess:
                        return {"error": f"Process {pid} not found", "success": False}
                    except psutil.TimeoutExpired:
                        # Force kill if terminate failed
                        proc.kill()
                        return {"message": f"Process {pid} force killed", "success": True}
                    except Exception as e:
                        return {"error": f"Could not kill process {pid}: {str(e)}", "success": False}
                elif process_name:
                    killed = []
                    for proc in psutil.process_iter(['pid', 'name']):
                        if proc.info['name'] == process_name:
                            try:
                                proc.kill()
                                killed.append(proc.info['pid'])
                            except:
                                continue
                    if killed:
                        return {"message": f"Killed processes: {killed}", "success": True}
                    else:
                        return {"error": f"No processes named '{process_name}' found", "success": False}
                else:
                    return {"error": "Either PID or process name required for kill operation", "success": False}
                    
            elif operation == "start":
                if not command:
                    return {"error": "Command required to start a process", "success": False}
                try:
                    result = subprocess.Popen(command.split(), shell=True)
                    return {
                        "message": f"Process started with PID {result.pid}",
                        "pid": result.pid,
                        "success": True
                    }
                except Exception as e:
                    return {"error": f"Could not start process: {str(e)}", "success": False}
            else:
                return {"error": f"Unknown process operation: {operation}", "success": False}
                
        except Exception as e:
            return {"error": f"Process management failed: {str(e)}", "success": False}
            
    async def service_management(self, operation: str, service_name: str) -> Dict[str, Any]:
        """Manage Windows services"""
        try:
            # Use sc command to manage services
            if operation == "list":
                result = subprocess.run(['sc', 'query'], capture_output=True, text=True)
                if result.returncode == 0:
                    # Parse the service list (simplified)
                    lines = result.stdout.strip().split('\n')
                    services = []
                    for line in lines:
                        if 'SERVICE_NAME:' in line:
                            service = line.split('SERVICE_NAME:')[1].strip()
                            services.append(service)
                    return {"services": services[:50], "success": True}  # Limit for performance
                else:
                    return {"error": f"Failed to list services: {result.stderr}", "success": False}
                    
            elif operation == "status":
                result = subprocess.run(['sc', 'query', service_name], capture_output=True, text=True)
                if result.returncode == 0:
                    # Parse status
                    status = "unknown"
                    for line in result.stdout.split('\n'):
                        if 'STATE' in line:
                            if 'RUNNING' in line:
                                status = "running"
                            elif 'STOPPED' in line:
                                status = "stopped"
                            elif 'PAUSED' in line:
                                status = "paused"
                            break
                    return {"service": service_name, "status": status, "success": True}
                else:
                    return {"error": f"Service {service_name} not found", "success": False}
                    
            elif operation == "start":
                result = subprocess.run(['sc', 'start', service_name], capture_output=True, text=True)
                if result.returncode == 0:
                    return {"message": f"Service {service_name} started", "success": True}
                else:
                    return {"error": f"Failed to start service {service_name}: {result.stderr}", "success": False}
                    
            elif operation == "stop":
                result = subprocess.run(['sc', 'stop', service_name], capture_output=True, text=True)
                if result.returncode == 0:
                    return {"message": f"Service {service_name} stopped", "success": True}
                else:
                    return {"error": f"Failed to stop service {service_name}: {result.stderr}", "success": False}
            else:
                return {"error": f"Unknown service operation: {operation}", "success": False}
                
        except Exception as e:
            return {"error": f"Service management failed: {str(e)}", "success": False}
            
    async def windows_audio_operations(self, operation: str, volume_level: Optional[int] = None) -> Dict[str, Any]:
        """Manage Windows audio settings"""
        try:
            if operation == "get_volume":
                # Use PowerShell to get current volume
                cmd = '''
                Add-Type -TypeDefinition @"
                using System.Runtime.InteropServices;
                [Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
                interface IAudioEndpointVolume {
                    int QueryChannelStatus();
                    int SetMasterVolumeLevel(float fLevel, System.Guid pguidEventContext);
                    int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);
                    int GetMasterVolumeLevel(out float pfLevel);
                    int GetMasterVolumeLevelScalar(out float pfLevel);
                    int SetMute([MarshalAs(UnmanagedType.Bool)] bool bMute, System.Guid pguidEventContext);
                    int GetMute(out bool pbMute);
                }
                "@
                $AudioDevice = Get-WmiObject -Class Win32_SoundDevice | Where-Object {$_.Status -eq 'OK'} | Select-Object -First 1
                $Volume = [AudioEndpointVolume].GetMasterVolumeLevelScalar()
                [Math]::Round($Volume * 100)
                '''
                result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True)
                if result.returncode == 0:
                    try:
                        volume = int(result.stdout.strip())
                        return {"volume": volume, "success": True}
                    except ValueError:
                        return {"error": "Could not parse volume level", "success": False}
                else:
                    # Alternative method using nircmd if PowerShell fails
                    result = subprocess.run(['nircmd', 'getvolume'], capture_output=True, text=True)
                    if result.returncode == 0:
                        # Parse nircmd output
                        lines = result.stdout.strip().split()
                        if len(lines) >= 2:
                            volume = int(float(lines[0]) * 100)
                            return {"volume": volume, "success": True}
                        else:
                            return {"error": "Could not parse nircmd volume output", "success": False}
                    else:
                        return {"error": "Could not get volume - both PowerShell and nircmd failed", "success": False}
                        
            elif operation == "set_volume":
                if volume_level is None:
                    return {"error": "Volume level required for set operation", "success": False}
                if not (0 <= volume_level <= 100):
                    return {"error": "Volume level must be between 0 and 100", "success": False}
                    
                # Use PowerShell to set volume
                cmd = f"Set-Volume -Level {volume_level}"
                result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True)
                if result.returncode == 0:
                    return {"message": f"Volume set to {volume_level}%", "success": True}
                else:
                    # Alternative with nircmd
                    result = subprocess.run(['nircmd', 'setvolume', str(volume_level * 655.35)], capture_output=True, text=True)
                    if result.returncode == 0:
                        return {"message": f"Volume set to {volume_level}%", "success": True}
                    else:
                        return {"error": "Could not set volume - both PowerShell and nircmd failed", "success": False}
                        
            elif operation == "mute":
                cmd = "Set-AudioDevice -Mute $true"
                result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True)
                if result.returncode == 0:
                    return {"message": "Audio muted", "success": True}
                else:
                    result = subprocess.run(['nircmd', 'muteaudio', '1'], capture_output=True, text=True)
                    if result.returncode == 0:
                        return {"message": "Audio muted", "success": True}
                    else:
                        return {"error": "Could not mute audio", "success": False}
                        
            elif operation == "unmute":
                cmd = "Set-AudioDevice -Mute $false"
                result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True)
                if result.returncode == 0:
                    return {"message": "Audio unmuted", "success": True}
                else:
                    result = subprocess.run(['nircmd', 'muteaudio', '0'], capture_output=True, text=True)
                    if result.returncode == 0:
                        return {"message": "Audio unmuted", "success": True}
                    else:
                        return {"error": "Could not unmute audio", "success": False}
                        
            elif operation == "list_devices":
                cmd = '''
                Get-WmiObject -Query "SELECT * FROM Win32_SoundDevice" | Select-Object Name, Status, Manufacturer | ConvertTo-Json
                '''
                result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True)
                if result.returncode == 0:
                    import json
                    devices = json.loads(result.stdout)
                    return {"devices": devices if isinstance(devices, list) else [devices], "success": True}
                else:
                    return {"error": "Could not list audio devices", "success": False}
            else:
                return {"error": f"Unknown audio operation: {operation}", "success": False}
                
        except Exception as e:
            return {"error": f"Audio operation failed: {str(e)}", "success": False}
            
    async def windows_display_operations(self, operation: str, brightness_level: Optional[int] = None, screenshot_path: Optional[str] = None) -> Dict[str, Any]:
        """Manage Windows display settings"""
        try:
            if operation == "brightness":
                if brightness_level is not None:
                    if not (0 <= brightness_level <= 100):
                        return {"error": "Brightness level must be between 0 and 100", "success": False}
                    # Use PowerShell to set brightness
                    cmd = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{brightness_level})"
                    result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True)
                    if result.returncode == 0:
                        return {"message": f"Brightness set to {brightness_level}%", "success": True}
                    else:
                        return {"error": f"Could not set brightness: {result.stderr}", "success": False}
                else:
                    # Get current brightness
                    cmd = "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"
                    result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True)
                    if result.returncode == 0:
                        try:
                            brightness = int(result.stdout.strip())
                            return {"brightness": brightness, "success": True}
                        except ValueError:
                            return {"error": "Could not parse brightness value", "success": False}
                    else:
                        return {"error": f"Could not get brightness: {result.stderr}", "success": False}
                        
            elif operation == "resolution":
                # This is complex and requires specific handling
                # For now, return current resolution
                cmd = '''
                Add-Type -AssemblyName System.Windows.Forms
                $screen = [System.Windows.Forms.Screen]::PrimaryScreen
                "$($screen.Bounds.Width)x$($screen.Bounds.Height)"
                '''
                result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True)
                if result.returncode == 0:
                    resolution = result.stdout.strip()
                    return {"resolution": resolution, "success": True}
                else:
                    return {"error": "Could not get screen resolution", "success": False}
                    
            elif operation == "screenshot":
                import datetime
                if not screenshot_path:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = f"screenshot_{timestamp}.png"
                    
                # Use PowerShell to take screenshot
                cmd = f'''
                Add-Type -AssemblyName System.Windows.Forms
                Add-Type -AssemblyName System.Drawing
                $screen = [System.Windows.Forms.Screen]::PrimaryScreen
                $bounds = $screen.Bounds
                $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
                $bitmap.Save("{screenshot_path}")
                '''
                result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True)
                if result.returncode == 0:
                    return {"message": f"Screenshot saved to {screenshot_path}", "path": screenshot_path, "success": True}
                else:
                    return {"error": f"Could not take screenshot: {result.stderr}", "success": False}
            else:
                return {"error": f"Unknown display operation: {operation}", "success": False}
                
        except Exception as e:
            return {"error": f"Display operation failed: {str(e)}", "success": False}
            
    def run(self):
        """Run the MCP server"""
        logger.info(f"Starting MCP Server for Windows on {self.config.host}:{self.config.port}")
        web.run_app(self.app, host=self.config.host, port=self.config.port)

def main():
    """Main entry point"""
    config = MCPConfig()
    
    # Check if running on Windows
    if platform.system().lower() != 'windows':
        logger.warning("Not running on Windows - some features may not work properly")
    
    server = MCPWindowsServer(config)
    server.run()

if __name__ == "__main__":
    main()
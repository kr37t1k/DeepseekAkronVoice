#!/usr/bin/env python3
"""
DeepSeek Voice Assistant with MCP Server - Main Entry Point
"""

import sys
import os
import threading
import time
import platform
import subprocess

# Add the workspace directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def start_mcp_server():
    """Start the appropriate MCP server based on the platform"""
    system_name = platform.system().lower()
    
    if system_name == "android":
        # For Android (Termux), run Android MCP server
        print("📱 Starting Android MCP server...")
        try:
            # Run in background with stdout/stderr redirected
            process = subprocess.Popen([sys.executable, "mcp_android.py"], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
            # Keep the process reference if needed later
            return process
        except Exception as e:
            print(f"⚠️ Error starting Android MCP server: {e}")
    else:
        # For Windows and other systems, run Windows MCP server
        print("🖥️ Starting Windows MCP server...")
        try:
            # Run in background with stdout/stderr redirected
            process = subprocess.Popen([sys.executable, "mcp_windows.py"], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
            # Keep the process reference if needed later
            return process
        except Exception as e:
            print(f"⚠️ Error starting Windows MCP server: {e}")

def main():
    print("🚀 Запуск DeepSeek голосового ассистента с MCP поддержкой...")
    print("Для завершения работы скажите 'стоп', 'выход' или 'заверши'")
    print("💡 Теперь вы можете запрашивать системную информацию, файловые операции и команды")
    print("-" * 70)
    
    # Start MCP server in a separate thread
    mcp_thread = threading.Thread(target=start_mcp_server, daemon=True)
    mcp_thread.start()
    
    # Wait a moment for MCP server to start
    time.sleep(3)
    
    # Now start the main application
    try:
        from app_with_server_enhanced import VoiceAssistant
        assistant = VoiceAssistant()
        assistant.run()
    except KeyboardInterrupt:
        print("\n👋 Работа ассистента завершена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
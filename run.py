#!/usr/bin/env python3
"""
DeepSeek Voice Assistant - Main Entry Point
"""

import sys
import os

# Add the workspace directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import VoiceAssistant

def main():
    print("🚀 Запуск DeepSeek голосового ассистента...")
    print("Для завершения работы скажите 'стоп', 'выход' или 'заверши'")
    print("-" * 50)
    
    try:
        assistant = VoiceAssistant()
        assistant.run()
    except KeyboardInterrupt:
        print("\n👋 Работа ассистента завершена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
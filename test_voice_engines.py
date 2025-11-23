#!/usr/bin/env python3
"""
Test script to demonstrate different voice engines available in the enhanced voice module.
"""

from voice_enhanced import EnhancedVoice
import time

def test_voice_engines():
    print("🔊 Testing Enhanced Voice Engines")
    print("=" * 50)
    
    # Create enhanced voice instance
    voice = EnhancedVoice()
    
    print(f"Current voice engine: {voice.current_engine}")
    print(f"Available engines: {voice.get_available_engines()}")
    print()
    
    # Test current engine
    print(f"Testing current engine ({voice.current_engine}):")
    voice.speak("Hello, this is a test of the current voice engine.")
    time.sleep(1)
    
    # Test each available engine if possible
    available_engines = voice.get_available_engines()
    
    for engine in available_engines:
        if engine != voice.current_engine:
            print(f"\nSwitching to {engine} engine...")
            if voice.set_engine(engine):
                print(f"Testing {engine} engine:")
                voice.speak(f"This is a test of the {engine} voice engine.")
                time.sleep(1)
            else:
                print(f"Failed to switch to {engine} engine")
    
    print("\n" + "=" * 50)
    print("Voice engine testing completed!")

def test_voice_language_detection():
    print("\n🔤 Testing Language Detection")
    print("=" * 50)
    
    voice = EnhancedVoice()
    
    test_texts = [
        "Hello, this is an English test.",
        "Привет, это тест на русском языке.",
        "This text has both English and русский characters."
    ]
    
    for text in test_texts:
        print(f"Input: {text}")
        voice.speak(text)
        time.sleep(1)

if __name__ == "__main__":
    test_voice_engines()
    test_voice_language_detection()
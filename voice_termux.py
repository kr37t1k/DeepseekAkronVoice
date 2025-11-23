import subprocess
import threading
import os
import queue
import wave
import tempfile
from config import USER_LANGUAGE, VOICE_RATE, VOICE_VOLUME


class TermuxVoice:
    def __init__(self):
        self.engine_lock = threading.Lock()
        self.language = USER_LANGUAGE
        self.rate = VOICE_RATE
        self.volume = VOICE_VOLUME
        self._test_espeak()
        
    def _test_espeak(self):
        """Test if espeak is available and install if needed on Termux"""
        try:
            result = subprocess.run(['which', 'espeak'], capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠️ espeak not found, attempting to install...")
                # Try to install espeak in Termux
                subprocess.run(['pkg', 'install', 'espeak', '-y'], check=True)
                print("✅ espeak installed successfully")
            else:
                print("✅ espeak is available")
        except Exception as e:
            print(f"⚠️ espeak setup failed: {e}")
            print("Trying fallback TTS options...")
    
    def speak(self, text):
        """Speak text using espeak or fallback methods"""
        if not text.strip():
            return
            
        # Clean the text to avoid command injection
        safe_text = text.replace('"', '').replace("'", '').replace(';', '').replace('|', '').replace('&', '')
        
        def _speak_thread():
            with self.engine_lock:
                try:
                    # Use espeak for TTS
                    cmd = [
                        'espeak',
                        '-v', self.language,
                        '-s', str(self.rate),  # Speed
                        '-a', str(int(self.volume * 100)),  # Amplitude/volume (0-200)
                        safe_text
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode != 0:
                        print(f"⚠️ espeak failed: {result.stderr}")
                        # Fallback: try to use termux-tts-speak if available
                        self._fallback_tts(safe_text)
                except subprocess.TimeoutExpired:
                    print("⚠️ TTS timeout, skipping...")
                except Exception as e:
                    print(f"⚠️ TTS error: {e}")
                    self._fallback_tts(safe_text)
        
        # Run in a separate thread to avoid blocking
        thread = threading.Thread(target=_speak_thread)
        thread.daemon = True
        thread.start()
    
    def _fallback_tts(self, text):
        """Fallback TTS method for Termux"""
        try:
            # Try termux-tts-speak (Termux specific)
            result = subprocess.run([
                'termux-tts-speak', 
                '-r', str(self.volume),  # volume rate
                '-s', str(self.rate/100),  # speech rate (0.1 to 1.0)
                text
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                print(f"⚠️ termux-tts-speak failed: {result.stderr}")
                # Final fallback: just print the text
                print(f"🔊 AI (text only): {text}")
        except Exception as e:
            print(f"⚠️ All TTS methods failed: {e}")
            print(f"🔊 AI (text only): {text}")


class FallbackVoice:
    """Fallback voice class that just prints text"""
    def __init__(self):
        pass
    
    def speak(self, text):
        print(f"🔊 AI (text only): {text}")
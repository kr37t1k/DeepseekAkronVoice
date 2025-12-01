try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    print("⚠️ Vosk not available. Audio recognition will be disabled.")
    VOSK_AVAILABLE = False

try:
    import sounddevice as sd
    SOUNDD_DEVICE_AVAILABLE = True
except ImportError:
    print("⚠️ sounddevice not available. Audio input will be disabled.")
    SOUNDD_DEVICE_AVAILABLE = False

import queue
import json
import threading
import time
import argparse
import sys
from local_chat import LocalChat
from config import VOSK_MODEL_PATH, LOCAL_AI_URL
from local_server_manager import ThreadedLocalServer

# Import voice modules with fallbacks
try:
    from voice_termux import TermuxVoice, FallbackVoice
    print("✅ Using Termux-compatible voice module")
    VoiceClass = TermuxVoice
except ImportError:
    try:
        from voice_simple import SimpleVoice
        print("✅ Using simple voice module")
        VoiceClass = SimpleVoice
    except ImportError:
        from voice_termux import FallbackVoice
        print("⚠️ Using fallback voice module")
        VoiceClass = FallbackVoice


class VoiceAssistant:
    def __init__(self, model_path=None, start_local_server=False, server_model_path=None):
        if VOSK_AVAILABLE:
            try:
                self.model = vosk.Model(VOSK_MODEL_PATH)
                print("✅ Vosk model loaded successfully")
            except Exception as e:
                print(f"⚠️ Failed to load Vosk model: {e}")
                print("Trying to continue without speech recognition...")
                self.model = None
        else:
            self.model = None
            print("⚠️ Vosk not available. Starting in text mode...")
        
        self.start_local_server = start_local_server
        self.server_model_path = server_model_path
        self.local_server = None
        
        # Start local server if requested
        if self.start_local_server and self.server_model_path:
            try:
                self.local_server = ThreadedLocalServer(
                    model_path=self.server_model_path,
                    host="0.0.0.0",
                    port=8001
                )
                self.local_server.start_server()
                print("🚀 Local AI server started...")
                # Give the server a moment to initialize
                time.sleep(3)
            except Exception as e:
                print(f"⚠️ Failed to start local server: {e}")
                print("Continuing with external/local server connection...")
        
        # Initialize chat and voice components
        try:
            self.chat = LocalChat()
            print("✅ Chat component initialized with MCP support")
        except Exception as e:
            print(f"⚠️ Failed to initialize chat: {e}")
            print("❌ Cannot proceed without chat functionality")
            sys.exit(1)
        
        try:
            self.voice = VoiceClass()
            print("✅ Voice component initialized")
        except Exception as e:
            print(f"⚠️ Failed to initialize voice: {e}")
            from voice_termux import FallbackVoice
            self.voice = FallbackVoice()
            print("✅ Using fallback voice component")
        
        self.samplerate = 16000
        self.audio_queue = queue.Queue()

        print("🎤 Assistant is ready...")
        print("💡 Commands: Speak naturally or type 'exit', 'quit', or 'stop' to end")
        print("💡 MCP Features: Ask for system info, battery, storage, network, file operations, etc.")

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(f"Audio status: {status}")
        self.audio_queue.put(bytes(indata))

    def listen_loop(self):
        if not self.model or not SOUNDD_DEVICE_AVAILABLE:
            print("❌ Audio components not available. Starting text-based interaction...")
            self.text_based_loop()
            return
            
        try:
            with sd.RawInputStream(
                    samplerate=self.samplerate,
                    blocksize=8000,
                    dtype='int16',
                    channels=1,
                    callback=self.audio_callback
            ):
                recognizer = vosk.KaldiRecognizer(self.model, self.samplerate)

                print("🎙️ Listening... (speak now or press Ctrl+C to switch to text mode)")
                while True:
                    data = self.audio_queue.get()

                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get('text', '').strip()

                        if text:
                            print(f"🎤 You: {text}")
                            self.process_command(text)
        except KeyboardInterrupt:
            print("\n🎤 Switching to text mode...")
            self.text_based_loop()
        except Exception as e:
            print(f"❌ Audio error: {e}")
            print("🎤 Switching to text mode...")
            self.text_based_loop()

    def text_based_loop(self):
        """Text-based interaction fallback"""
        print("📝 Text mode activated. Type your messages (or 'exit' to quit):")
        while True:
            try:
                text = input("⌨️ You: ").strip()
                if not text:
                    continue
                self.process_command(text)
            except KeyboardInterrupt:
                print("\n👋 Exiting!")
                self.cleanup()
                break
            except EOFError:
                print("\n👋 Exiting!")
                self.cleanup()
                break

    def process_command(self, text):
        if any(word in text.lower() for word in ['exit', 'quit', 'stop', 'goodbye', 'bye']):
            print("👋 Exiting!")
            self.cleanup()
            exit()

        # Use the threaded chat method to prevent blocking
        try:
            response = self.chat.chat(text)
            if response:
                print(f"🤖 AI: {response}")
                self.voice.speak(response)
            else:
                print("⚠️ AI: No response")
        except Exception as e:
            print(f"❌ Chat error: {e}")
            self.voice.speak("Sorry, I encountered an error processing your request.")

    def cleanup(self):
        """Clean up resources"""
        print("🛑 Cleaning up...")
        if self.local_server:
            print("🛑 Stopping local server...")
            self.local_server.stop_server()
        print("👋 Assistant stopped!")

    def run(self):
        try:
            self.listen_loop()
        except KeyboardInterrupt:
            print("\n👋 Stopping!")
            self.cleanup()
        except Exception as e:
            print(f"❌ Error: {e}")
            self.cleanup()


def main():
    parser = argparse.ArgumentParser(description='Voice Assistant with optional local AI server')
    parser.add_argument('--start-server', action='store_true', 
                       help='Start local AI server in a thread')
    parser.add_argument('--model-path', type=str,
                       help='Path to the GGUF model file (required if --start-server is used)')
    
    args = parser.parse_args()
    
    if args.start_server and not args.model_path:
        print("Error: --model-path is required when using --start-server")
        return
    
    assistant = VoiceAssistant(
        start_local_server=args.start_server,
        server_model_path=args.model_path
    )
    assistant.run()


if __name__ == "__main__":
    main()
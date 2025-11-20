import vosk
import sounddevice as sd
import queue
import json
import threading
import time
import argparse
from local_chat import LocalChat
from voice_simple import SimpleVoice
from config import VOSK_MODEL_PATH, LOCAL_AI_URL
from local_server_manager import ThreadedLocalServer


class VoiceAssistant:
    def __init__(self, model_path=None, start_local_server=False, server_model_path=None):
        self.model = vosk.Model(VOSK_MODEL_PATH)
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
        self.chat = LocalChat()
        self.voice = SimpleVoice()
        self.samplerate = 16000
        self.audio_queue = queue.Queue()

        print("🎤 Assistant is ready...")

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(f"Audio status: {status}")
        self.audio_queue.put(bytes(indata))

    def listen_loop(self):
        with sd.RawInputStream(
                samplerate=self.samplerate,
                blocksize=8000,
                dtype='int16',
                channels=1,
                callback=self.audio_callback
        ):
            recognizer = vosk.KaldiRecognizer(self.model, self.samplerate)

            while True:
                data = self.audio_queue.get()

                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get('text', '').strip()

                    if text:
                        print(f"🎤 You: {text}")
                        self.process_command(text)

    def process_command(self, text):
        if any(word in text.lower() for word in ['exit', 'quit', 'stop']):
            print("👋 Exiting!")
            self.cleanup()
            exit()

        response = self.chat.chat(text)
        if response:
            print(f"🤖 AI: {response}")
            self.voice.speak(response)
        else:
            print("⚠️ AI: No response")

    def cleanup(self):
        """Clean up resources"""
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
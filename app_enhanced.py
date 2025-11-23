import vosk
import sounddevice as sd
import queue
import json
import threading
from local_chat_enhanced import EnhancedLocalChat
from voice_enhanced import EnhancedVoice
from config import VOSK_MODEL_PATH

class EnhancedVoiceAssistant:
    def __init__(self):
        self.model = vosk.Model(VOSK_MODEL_PATH)
        self.chat = EnhancedLocalChat()  # Use enhanced chat with better error handling
        self.voice = EnhancedVoice()     # Use enhanced voice with multiple engine options
        self.samplerate = 16000
        self.audio_queue = queue.Queue()

        print("🎤 Enhanced Assistant is ready...")
        print(f"🔊 Available voice engines: {self.voice.get_available_engines()}")
        print(f"🦙 Model info: {self.chat.get_model_info()}")

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
        # Check for special commands
        if any(word in text.lower() for word in ['exit', 'quit', 'stop', 'выйди', 'стопе']):
            print("👋 Exiting!")
            exit()
        
        # Check for voice engine switching commands
        if text.lower().startswith('switch voice to'):
            requested_engine = text.lower().replace('switch voice to', '').strip()
            if requested_engine in self.voice.get_available_engines():
                success = self.voice.set_engine(requested_engine)
                if success:
                    response = f"Successfully switched to {requested_engine} voice engine"
                else:
                    response = f"Failed to switch to {requested_engine} voice engine"
            else:
                response = f"Engine {requested_engine} not available. Available: {self.voice.get_available_engines()}"
            
            print(f"🤖 AI: {response}")
            self.voice.speak(response)
            return
        
        # Check for model health
        if 'health' in text.lower() or 'status' in text.lower():
            health = self.chat.health_check()
            response = f"Model status: {health.get('status', 'unknown')}. {health.get('response_length', 0)} characters in test response."
            print(f"🤖 AI: {response}")
            self.voice.speak(response)
            return

        try:
            # Use the enhanced chat method with better error handling
            response = self.chat.chat(text)
            if response:
                print(f"🤖 AI: {response}")
                self.voice.speak(response)
            else:
                print("⚠️ AI: No response received")
                self.voice.speak("Sorry, I couldn't generate a response.")
        except Exception as e:
            print(f"❌ Error processing command: {e}")
            error_msg = "Sorry, there was an error processing your request. I'm using fallback response."
            print(f"🤖 AI: {error_msg}")
            self.voice.speak(error_msg)

    def run(self):
        try:
            print("Starting enhanced voice assistant...")
            print("Commands you can try:")
            print("  - 'switch voice to espeak' - to change voice engine")
            print("  - 'how are you?' - to test the assistant")
            print("  - 'health' - to check model status")
            print("  - 'exit' - to quit")
            print("-" * 50)
            
            self.listen_loop()
        except KeyboardInterrupt:
            print("\n👋 Stopping!")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    assistant = EnhancedVoiceAssistant()
    assistant.run()
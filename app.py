import vosk
import sounddevice as sd
import queue
import json
import logging
import threading
from local_chat import LocalChat
from voice_enhanced import EnhancedVoice
from config import VOSK_MODEL_PATH

logging.basicConfig(level=logging.INFO)

class VoiceAssistant:
    def __init__(self):
        self.model = vosk.Model(VOSK_MODEL_PATH)
        self.chat = LocalChat()
        self.voice = EnhancedVoice()
        self.samplerate = 16000
        self.audio_queue = queue.Queue()

        print("🎤 Assistent is ready...")

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
        if any(word in text.lower() for word in ['exit', 'quit', 'stop', 'выйди', 'стопе']):
            print("👋 Exiting!")
            exit()

        try:
            # Use the threaded chat method to prevent blocking
            response = self.chat.chat(text)
            if response:
                print(f"🤖 AI: {response}")
                self.voice.speak(response)
            else:
                print("⚠️ AI: No response received")
        except Exception as e:
            print(f"❌ Error processing command: {e}")
            self.voice.speak("Sorry, there was an error processing your request.")

    def run(self):
        try:
            self.listen_loop()
        except KeyboardInterrupt:
            print("\n👋 Stopping!")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()

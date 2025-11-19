import vosk
import sounddevice as sd
import queue
import json
import threading
from deepseek_chat import DeepSeekChat
from voice_simple import SimpleVoice
from config import VOSK_MODEL_PATH


class VoiceAssistant:
    def __init__(self):
        # Инициализация компонентов
        self.model = vosk.Model(VOSK_MODEL_PATH)
        self.chat = DeepSeekChat()
        self.voice = SimpleVoice()
        self.samplerate = 16000
        self.audio_queue = queue.Queue()

        print("🎤 Ассистент запущен! Говорите...")

    def audio_callback(self, indata, frames, time, status):
        """Захватываем аудио с микрофона"""
        if status:
            print(f"Audio status: {status}")
        self.audio_queue.put(bytes(indata))

    def listen_loop(self):
        """Основной цикл прослушивания"""
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
                        print(f"🎤 Вы: {text}")
                        self.process_command(text)

    def process_command(self, text):
        """Обрабатываем команду и генерируем ответ"""
        # Простые команды для управления
        if any(word in text.lower() for word in ['стоп', 'выход', 'заверши']):
            print("👋 Завершаю работу...")
            exit()

        # Общение с ИИ
        print("🤔 Думаю...")
        response = self.chat.chat(text)
        print(f"🤖 Ассистент: {response}")

        # Озвучиваем ответ
        self.voice.speak(response)

    def run(self):
        """Запуск ассистента"""
        try:
            self.listen_loop()
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
        except Exception as e:
            print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
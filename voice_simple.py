import pyttsx3
import threading
from config import USER_LANGUAGE

class SimpleVoice:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 200)
        self.engine.setProperty('volume', 0.7)
        self.engine_lock = threading.Lock()

        # Changing voice model for user language
        self.voices = self.engine.getProperty('voices')
        self.choose_voice_by_language(self.voices, USER_LANGUAGE)

    def set_voice_by_id(self, voice_id):
        self.engine.setProperty('voice', voice_id)

    def choose_voice_by_language(self, engine_voices, language):
        for voice in engine_voices:
            if str(language).lower() in str(voice.languages).lower():
                self.set_voice_by_id(voice.id)
                print(f"✨ Switched to {voice.name} voice - {voice.languages[0]}")
                break
    def speak(self, text):
        eng_chars = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
        rus_chars = ["а", "б", "в", "г", "д", "е", "ё", "ж", "з", "и", "й", "к", "л", "м", "н", "о", "п", "р", "с", "т", "у", "ф", "х", "ц", "ч", "ш", "щ", "ъ", "ы", "ь", "э", "ю", "я"]
        if any(char in rus_chars for char in text):
            "rus lang text"
            self.choose_voice_by_language(self.voices, "ru")

        elif any(char in eng_chars for char in text):
            "eng lang text"
            self.choose_voice_by_language(self.voices, "en")

        with self.engine_lock:
            self.engine.say(text)
            self.engine.runAndWait()
        # def _speak():
        #     self.engine.say(text)
        #     self.engine.runAndWait()
        #
        # thread = threading.Thread(target=_speak)
        # thread.start()

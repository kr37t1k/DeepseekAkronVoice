import pyttsx3
import threading
from config import USER_LANGUAGE

class SimpleVoice:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 200)
        self.engine.setProperty('volume', 0.7)

        # Changing voice model for user language
        voices = self.engine.getProperty('voices')
        for voice in voices:
            print(voice.id, voice.name, voice.languages)
            if USER_LANGUAGE in voice.languages:
                self.engine.setProperty('voice', voice.id)

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()
        # def _speak():
        #     self.engine.say(text)
        #     self.engine.runAndWait()
        #
        # thread = threading.Thread(target=_speak)
        # thread.start()

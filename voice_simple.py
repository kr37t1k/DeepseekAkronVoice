import pyttsx3
import threading


class SimpleVoice:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180)  # Скорость речи
        self.engine.setProperty('volume', 0.8)  # Громкость

        # Настройка голоса (выбираем женский если есть)
        voices = self.engine.getProperty('voices')
        if len(voices) > 1:
            self.engine.setProperty('voice', voices[1].id)  # Обычно женский

    def speak(self, text):
        # if self.engine.isBusy():
            # self.engine.stop()
        if self.engine.stop():
            self.engine.say(text)
            self.engine.runAndWait()
        # def _speak():
        #     self.engine.say(text)
        #     self.engine.runAndWait()
        #
        # thread = threading.Thread(target=_speak)
        # thread.start()

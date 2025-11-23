import threading
import os
import sys
from config import USER_LANGUAGE, VOICE_ENGINE

class EnhancedVoice:
    def __init__(self):
        self.current_engine = VOICE_ENGINE
        self.engine_lock = threading.Lock()
        
        # Initialize the selected voice engine
        if self.current_engine == "pyttsx3":
            self._init_pyttsx3()
        elif self.current_engine == "espeak":
            self._init_espeak()
        elif self.current_engine == "spd":
            self._init_spd()
        elif self.current_engine == "silero":
            self._init_silero()
        else:
            # Default to pyttsx3 if unknown engine
            self.current_engine = "pyttsx3"
            self._init_pyttsx3()
    
    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine"""
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 200)
            self.engine.setProperty('volume', 0.7)
            
            # Changing voice model for user language
            self.voices = self.engine.getProperty('voices')
            self.choose_voice_by_language(self.voices, USER_LANGUAGE)
        except ImportError:
            print("⚠️ pyttsx3 not installed. Please install with: pip install pyttsx3")
            raise
        except Exception as e:
            print(f"⚠️ Error initializing pyttsx3: {e}")
            raise

    def _init_espeak(self):
        """Initialize espeak engine"""
        try:
            import espeak.core as espeak
            self.espeak = espeak
            # Set default voice based on language
            if USER_LANGUAGE.lower().startswith('ru'):
                espeak.set_voice(' russian')
            elif USER_LANGUAGE.lower().startswith('en'):
                espeak.set_voice(' english')
            elif USER_LANGUAGE.lower().startswith('de'):
                espeak.set_voice(' german')
            elif USER_LANGUAGE.lower().startswith('fr'):
                espeak.set_voice(' french')
        except ImportError:
            print("⚠️ espeak not installed. Please install with: pip install py-espeak")
            raise
        except Exception as e:
            print(f"⚠️ Error initializing espeak: {e}")
            raise

    def _init_spd(self):
        """Initialize speech-dispatcher engine"""
        try:
            import speechd
            self.spd_client = speechd.SPDClient("LocalAI")
            self.spd_client.set_language(USER_LANGUAGE)
            if USER_LANGUAGE.lower().startswith('ru'):
                self.spd_client.set_synthesis_voice(' russian')
            elif USER_LANGUAGE.lower().startswith('en'):
                self.spd_client.set_synthesis_voice(' english')
        except ImportError:
            print("⚠️ speechd not installed. Please install with: pip install speechd")
            raise
        except Exception as e:
            print(f"⚠️ Error initializing speech-dispatcher: {e}")
            raise

    def _init_silero(self):
        """Initialize Silero TTS engine"""
        try:
            import torch
            from silero import silero_tts
            
            # Load Silero TTS model
            self.silero_model, self.silero_sample_rate = silero_tts(
                language=USER_LANGUAGE,
                speaker="kseniya_v2"
            )
            import sounddevice as sd
            self.sd = sd
        except ImportError:
            print("⚠️ Silero TTS not installed. Please install with: pip install torch silero")
            raise
        except Exception as e:
            print(f"⚠️ Error initializing Silero TTS: {e}")
            raise

    def set_voice_by_id(self, voice_id):
        """Set voice by ID for pyttsx3"""
        if self.current_engine == "pyttsx3":
            self.engine.setProperty('voice', voice_id)

    def choose_voice_by_language(self, engine_voices, language):
        """Choose voice based on language for pyttsx3"""
        if self.current_engine != "pyttsx3":
            return
            
        for voice in engine_voices:
            if str(language).lower() in str(voice.languages).lower():
                self.set_voice_by_id(voice.id)
                print(f"✨ Switched to {voice.name} voice - {voice.languages[0]}")
                break

    def speak(self, text):
        """Speak text using the current engine"""
        eng_chars = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
        rus_chars = ["а", "б", "в", "г", "д", "е", "ё", "ж", "з", "и", "й", "к", "л", "м", "н", "о", "п", "р", "с", "т", "у", "ф", "х", "ц", "ч", "ш", "щ", "ъ", "ы", "ь", "э", "ю", "я"]
        
        if any(char in rus_chars for char in text):
            target_lang = "ru"
        elif any(char in eng_chars for char in text):
            target_lang = "en"
        else:
            target_lang = USER_LANGUAGE

        # Update voice based on detected language
        if self.current_engine == "pyttsx3":
            self.choose_voice_by_language(self.voices, target_lang)
        
        with self.engine_lock:
            if self.current_engine == "pyttsx3":
                self.engine.say(text)
                self.engine.runAndWait()
            elif self.current_engine == "espeak":
                self.espeak.synth(text)
            elif self.current_engine == "spd":
                self.spd_client.speak(text)
            elif self.current_engine == "silero":
                # Silero TTS processing
                audio = self.silero_model(text, speaker='kseniya_v2', sample_rate=self.silero_sample_rate)
                self.sd.play(audio.numpy(), samplerate=self.silero_sample_rate)
                self.sd.wait()

    def set_engine(self, engine_name):
        """Switch to a different voice engine"""
        old_engine = self.current_engine
        self.current_engine = engine_name
        
        try:
            if engine_name == "pyttsx3":
                self._init_pyttsx3()
            elif engine_name == "espeak":
                self._init_espeak()
            elif engine_name == "spd":
                self._init_spd()
            elif engine_name == "silero":
                self._init_silero()
            else:
                print(f"⚠️ Unknown engine: {engine_name}. Reverting to {old_engine}")
                self.current_engine = old_engine
                return False
            
            print(f"✅ Switched voice engine from {old_engine} to {engine_name}")
            return True
        except Exception as e:
            print(f"⚠️ Failed to switch to {engine_name}: {e}")
            self.current_engine = old_engine  # Revert to old engine
            return False

    def get_available_engines(self):
        """Get list of available voice engines"""
        engines = ["pyttsx3"]
        
        # Check for other engines
        try:
            import espeak.core
            engines.append("espeak")
        except ImportError:
            pass
            
        try:
            import speechd
            engines.append("spd")
        except ImportError:
            pass
            
        try:
            import silero
            engines.append("silero")
        except ImportError:
            pass
            
        return engines

    def list_voices(self):
        """List available voices for current engine"""
        if self.current_engine == "pyttsx3":
            return [f"ID: {v.id}, Name: {v.name}, Languages: {v.languages}" for v in self.voices]
        else:
            return [f"Current engine: {self.current_engine}"]
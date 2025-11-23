import voice_simple
sv = voice_simple.SimpleVoice()

for voice in sv.voices:
    print(voice.id, voice.name, voice.languages)
sv.speak("Stop stopStop stopStop stopStop stopStop stopStop stopStop stopStop stop")

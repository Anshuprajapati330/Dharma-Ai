import speech_recognition as sr

def speech_to_text():
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening...")

            audio = recognizer.listen(source, timeout=5, phrase_time_limit=7)

            text = recognizer.recognize_google(audio, language="en-IN")
            return text

    except:
        return None
import speech_recognition as sr

def speech_to_text():
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("🎤 Listening... Speak now")
            audio = recognizer.listen(source, timeout=5)

            text = recognizer.recognize_google(audio)
            return text

    except sr.WaitTimeoutError:
        return "⏱️ Listening timed out"

    except sr.UnknownValueError:
        return "❌ Could not understand audio"

    except Exception as e:
        return f"Error: {str(e)}"
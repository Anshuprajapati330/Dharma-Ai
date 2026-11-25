import os
import io
import logging
import speech_recognition as sr

logger = logging.getLogger(__name__)


def speech_to_text(language="en"):
    """
    Capture audio from local microphone hardware and transcribe.
    language: 'en' for English (en-IN), 'hi' for Hindi (hi-IN).
    """
    locale = "hi-IN" if str(language).lower().startswith("hi") else "en-IN"
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = recognizer.listen(source, timeout=4, phrase_time_limit=8)
            text = recognizer.recognize_google(audio, language=locale)
            return text.strip() if text else None
    except sr.WaitTimeoutError:
        logger.info("Speech recognition timeout: no speech detected")
        return None
    except sr.UnknownValueError:
        logger.info("Speech recognition could not understand audio")
        return None
    except sr.RequestError as e:
        logger.warning("Google Speech Recognition service error: %s", e)
        return None
    except Exception as e:
        logger.warning("Microphone error or unavailable: %s", e)
        return None


def transcribe_audio_bytes(audio_bytes: bytes, language="en", mime_type="audio/wav") -> str | None:
    """
    Transcribe raw audio bytes using Groq Whisper if API key exists,
    or Google SpeechRecognition as a WAV-only fallback.
    """
    if not audio_bytes:
        return None

    lang_code = "hi" if str(language).lower().startswith("hi") else "en"
    extension = {
        "audio/mp4": "mp4",
        "audio/mpeg": "mp3",
        "audio/ogg": "ogg",
        "audio/wav": "wav",
        "audio/webm": "webm",
        "audio/x-wav": "wav",
    }.get(mime_type, "webm")

    # Attempt Groq Whisper
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = f"recording.{extension}"
            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3-turbo",
                language=lang_code,
                response_format="text",
            )
            if transcription:
                return str(transcription).strip()
        except Exception as e:
            logger.warning("Groq Whisper transcription failed: %s", e)
            if extension != "wav":
                raise RuntimeError("Groq speech transcription is unavailable") from e

    if extension != "wav":
        return None

    # Fallback to SpeechRecognition
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio_data = recognizer.record(source)
            locale = "hi-IN" if lang_code == "hi" else "en-IN"
            return recognizer.recognize_google(audio_data, language=locale).strip()
    except Exception as e:
        logger.warning("Fallback audio recognition failed: %s", e)
        return None